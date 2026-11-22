"""Groq chat-completions provider.

Features: system/user message passthrough, gpt-oss `reasoning_effort`, SDK retries with backoff,
automatic fallback model (rate limit / 5xx / timeout / unknown model), recovery when reasoning
consumes the whole token budget, concurrency cap, streaming, and error translation to
provider-neutral exceptions. Nothing here reads global settings (see providers/factory.py).
"""

import asyncio
import logging
import time
from collections.abc import AsyncIterator

from app.providers.base import (
    GenerationRequest,
    GenerationResult,
    ProviderAuthError,
    ProviderBadRequest,
    ProviderEmptyResponse,
    ProviderError,
    ProviderModelError,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
    StreamEvent,
)
from app.utils.security import redact

logger = logging.getLogger(__name__)


def _retry_after(exc: Exception) -> int | None:
    headers = getattr(getattr(exc, "response", None), "headers", None)
    try:
        value = headers.get("retry-after") if headers else None
        return max(1, int(float(value))) if value is not None else None
    except (TypeError, ValueError):
        return None


def translate_exception(exc: Exception) -> ProviderError:
    """Map an SDK/network exception to a ProviderError (by class name and HTTP status, so it
    works without importing the SDK)."""
    if isinstance(exc, ProviderError):
        return exc
    name = type(exc).__name__
    status = getattr(exc, "status_code", None)
    detail = redact(str(exc))[:300]
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)) or name == "APITimeoutError":
        return ProviderTimeout("Groq did not answer in time.")
    if name == "APIConnectionError":
        return ProviderUnavailable("Could not reach Groq (network problem).")
    if status in (401, 403):
        return ProviderAuthError("Groq rejected the API key. Check GROQ_API_KEY and project permissions.")
    if status == 404:
        return ProviderModelError(f"Model or endpoint not found on Groq. {detail}")
    if status == 429:
        return ProviderRateLimited("Groq rate limit reached. Retry shortly.", retry_after=_retry_after(exc))
    if status in (400, 413, 422):
        return ProviderBadRequest(f"Groq rejected the request: {detail}")
    if isinstance(status, int) and status >= 500:
        return ProviderUnavailable(f"Groq is temporarily unavailable (HTTP {status}).")
    return ProviderError(f"Groq call failed ({name}).")


def _usage(obj) -> tuple[int | None, int | None]:
    usage = getattr(obj, "usage", None)
    if usage is None:
        usage = getattr(getattr(obj, "x_groq", None), "usage", None)
    if usage is None:
        return None, None
    return getattr(usage, "prompt_tokens", None), getattr(usage, "completion_tokens", None)


class GroqProvider:
    name = "groq"

    def __init__(
        self,
        *,
        api_key: str = "",
        model: str = "openai/gpt-oss-120b",
        fallback_model: str = "",
        timeout: float = 60.0,
        max_retries: int = 2,
        reasoning: bool = True,
        max_concurrency: int = 4,
        client=None,
    ) -> None:
        if client is None:
            if not api_key:
                raise ProviderError("GROQ_API_KEY is not configured")
            from groq import AsyncGroq  # lazy: analysis/tests work without the SDK

            client = AsyncGroq(api_key=api_key, timeout=timeout, max_retries=max_retries)
        self._client = client
        self.model = model
        self.fallback_model = fallback_model if fallback_model and fallback_model != model else ""
        self._reasoning = reasoning
        self._sem = asyncio.Semaphore(max_concurrency)

    # ---- helpers --------------------------------------------------------
    def _chain(self, request: GenerationRequest) -> list[str]:
        primary = request.model or self.model
        chain = [primary]
        if self.fallback_model and self.fallback_model != primary:
            chain.append(self.fallback_model)
        return chain

    @staticmethod
    def _is_gpt_oss(model: str) -> bool:
        return model.startswith("openai/gpt-oss")

    def _kwargs(self, model: str, request: GenerationRequest, *, extras: bool,
                max_tokens: int, effort: str | None) -> dict:
        kwargs: dict = {
            "model": model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_completion_tokens": max_tokens,
        }
        if extras and self._reasoning and effort and self._is_gpt_oss(model):
            kwargs["extra_body"] = {"reasoning_effort": effort, "include_reasoning": False}
        return kwargs

    # ---- non-streaming --------------------------------------------------
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        chain = self._chain(request)
        async with self._sem:
            for index, model in enumerate(chain):
                try:
                    result = await self._call(model, request)
                    result.used_fallback = index > 0
                    return result
                except ProviderError as exc:
                    if exc.fallback_ok and index < len(chain) - 1:
                        logger.warning("Model %s failed (%s); trying fallback %s", model, exc.code, chain[index + 1])
                        continue
                    raise
        raise ProviderError("No model available")  # pragma: no cover

    async def _call(self, model: str, request: GenerationRequest) -> GenerationResult:
        started = time.perf_counter()
        effort = request.reasoning_effort
        max_tokens = request.max_tokens
        extras = True
        for _ in range(4):
            kwargs = self._kwargs(model, request, extras=extras, max_tokens=max_tokens, effort=effort)
            try:
                completion = await self._client.chat.completions.create(**kwargs)
            except Exception as exc:  # noqa: BLE001 - translated below
                error = translate_exception(exc)
                if isinstance(error, ProviderBadRequest) and "extra_body" in kwargs:
                    logger.warning("Groq rejected reasoning parameters for %s; retrying without them", model)
                    extras = False
                    continue
                raise error from exc
            choice = completion.choices[0]
            text = (choice.message.content or "").strip()
            finish = choice.finish_reason
            if not text and finish == "length" and max_tokens < request.max_tokens_ceiling:
                # Reasoning used the whole budget: retry with more room and less reasoning.
                effort = "low"
                max_tokens = min(max_tokens * 2, request.max_tokens_ceiling)
                logger.warning("Empty output at token limit; retrying with max_tokens=%s", max_tokens)
                continue
            if not text:
                raise ProviderEmptyResponse("Groq returned an empty response.")
            prompt_tokens, completion_tokens = _usage(completion)
            return GenerationResult(
                text=text, model=model, finish_reason=finish,
                prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        raise ProviderEmptyResponse("Groq returned an empty response.")

    # ---- streaming ------------------------------------------------------
    async def stream(self, request: GenerationRequest) -> AsyncIterator[StreamEvent]:
        chain = self._chain(request)
        async with self._sem:
            for index, model in enumerate(chain):
                extras = True
                while True:
                    emitted = False
                    try:
                        async for event in self._stream_once(model, request, extras):
                            if event.kind == "delta":
                                emitted = True
                            if event.result is not None:
                                event.result.used_fallback = index > 0
                            yield event
                        return
                    except Exception as exc:  # noqa: BLE001
                        error = translate_exception(exc)
                        if isinstance(error, ProviderBadRequest) and extras and not emitted \
                                and self._reasoning and self._is_gpt_oss(model):
                            extras = False
                            continue
                        if not emitted and error.fallback_ok and index < len(chain) - 1:
                            logger.warning("Stream on %s failed (%s); trying fallback", model, error.code)
                            break
                        if error is exc:
                            raise
                        raise error from exc

    async def _stream_once(self, model: str, request: GenerationRequest, extras: bool) -> AsyncIterator[StreamEvent]:
        started = time.perf_counter()
        kwargs = self._kwargs(model, request, extras=extras, max_tokens=request.max_tokens,
                              effort=request.reasoning_effort)
        kwargs["stream"] = True
        stream = await self._client.chat.completions.create(**kwargs)
        parts: list[str] = []
        finish: str | None = None
        prompt_tokens = completion_tokens = None
        async for chunk in stream:
            p, c = _usage(chunk)
            prompt_tokens, completion_tokens = p or prompt_tokens, c or completion_tokens
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            delta = getattr(choice.delta, "content", None)
            if delta:
                parts.append(delta)
                yield StreamEvent("delta", delta)
            if choice.finish_reason:
                finish = choice.finish_reason
        text = "".join(parts).strip()
        if not text:
            raise ProviderEmptyResponse("Groq returned an empty response.")
        yield StreamEvent("final", result=GenerationResult(
            text=text, model=model, finish_reason=finish,
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            latency_ms=int((time.perf_counter() - started) * 1000),
        ))

    # ---- ops ------------------------------------------------------------
    async def healthcheck(self) -> dict:
        """Validate key + connectivity and whether the configured models are listed."""
        try:
            listing = await self._client.models.list()
        except Exception as exc:  # noqa: BLE001
            error = translate_exception(exc)
            return {"reachable": False, "error_code": error.code, "detail": error.message}
        ids = {getattr(item, "id", None) for item in getattr(listing, "data", [])}
        return {
            "reachable": True,
            "model": self.model, "model_available": self.model in ids,
            "fallback_model": self.fallback_model or None,
            "fallback_available": (self.fallback_model in ids) if self.fallback_model else None,
        }

    async def close(self) -> None:
        close = getattr(self._client, "close", None)
        if close is not None:
            await close()
