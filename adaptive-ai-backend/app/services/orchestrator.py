"""Request pipeline: analyse -> adapt -> build prompt -> generate -> evaluate -> persist.

DB work is synchronous (SQLAlchemy) and runs in the thread pool so it never blocks the event loop.
The provider is injected, so the pipeline does not depend on Groq.
"""

import logging
import random
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from starlette.concurrency import run_in_threadpool

from app.config import Settings
from app.core.adaptation import select_strategy
from app.core.engine import analyze_request, apply_selection
from app.database import repository as repo
from app.database.connection import session_scope
from app.database.models import Interaction
from app.intelligence.generation import plan_generation
from app.intelligence.prompt_builder import build_messages
from app.intelligence.response_evaluator import evaluate_response
from app.providers.base import (
    GenerationRequest,
    GenerationResult,
    ProviderNotConfigured,
    TextProvider,
)
from app.schemas.requests import AssistantRequest
from app.utils.security import redact

logger = logging.getLogger(__name__)


@dataclass
class Prepared:
    session_id: str
    user_id: str | None
    message: str
    analysis: dict
    messages: list[dict[str, str]] = field(default_factory=list)
    plan: dict = field(default_factory=dict)

    @property
    def needs_clarification(self) -> bool:
        return bool(self.analysis["needs_clarification"])


class Orchestrator:
    def __init__(self, provider: TextProvider | None, settings: Settings, rng: random.Random | None = None) -> None:
        self.provider = provider
        self.settings = settings
        self._rng = rng or random.Random()

    # ---- shared analysis ----------------------------------------------------
    def _analyse(self, db, payload: AssistantRequest, *, for_generation: bool) -> Prepared:
        s = self.settings
        session_id = payload.session_id or str(uuid.uuid4())
        if payload.session_id:
            repo.assert_session_access(db, session_id, payload.user_id)
        preferences = repo.get_preferences(db, payload.user_id) if payload.user_id else {}
        persona = payload.preferred_persona or preferences.get("preferred_persona")
        context = repo.get_context(db, session_id, s.max_context_messages) if payload.session_id else []

        analysis = analyze_request(payload.message, persona, has_history=bool(context))
        if not analysis["needs_clarification"]:
            stats = repo.strategy_stats(db, analysis["task_type"], analysis["candidate_strategies"])
            selection = select_strategy(
                analysis["default_strategy"], analysis["candidate_strategies"], stats,
                mode=s.adaptation_mode, min_samples=s.min_feedback_samples, rng=self._rng,
            )
            apply_selection(analysis, selection)

        prepared = Prepared(session_id, payload.user_id, payload.message, analysis)
        if for_generation and not prepared.needs_clarification:
            prepared.messages = build_messages(
                payload.message, analysis, context, preferences, payload.response_length,
                max_messages=s.max_context_messages, max_chars=s.max_context_chars,
            )
            prepared.plan = plan_generation(
                analysis, payload.response_length, cap=s.max_output_tokens, preferences=preferences
            )
        return prepared

    def _prepare_sync(self, payload: AssistantRequest, for_generation: bool) -> Prepared:
        with session_scope() as db:
            return self._analyse(db, payload, for_generation=for_generation)

    # ---- public API ---------------------------------------------------------
    async def analyze(self, payload: AssistantRequest) -> dict:
        prepared = await run_in_threadpool(self._prepare_sync, payload, False)
        return prepared.analysis

    async def prepare(self, payload: AssistantRequest) -> Prepared:
        """Analyse + build the prompt. Raises SessionAccessError (403) before any model call."""
        return await run_in_threadpool(self._prepare_sync, payload, True)

    def require_provider(self) -> TextProvider:
        if self.provider is None:
            raise ProviderNotConfigured(
                "No language-model provider is configured. Set GROQ_API_KEY in .env and restart."
            )
        return self.provider

    @staticmethod
    def _generation_request(prepared: Prepared) -> GenerationRequest:
        plan = prepared.plan
        return GenerationRequest(
            messages=prepared.messages,
            max_tokens=plan["max_tokens"],
            temperature=plan["temperature"],
            reasoning_effort=plan["reasoning_effort"],
            max_tokens_ceiling=plan["max_tokens_ceiling"],
        )

    async def respond(self, payload: AssistantRequest) -> dict:
        prepared = await self.prepare(payload)
        if prepared.needs_clarification:
            return self._clarification_payload(prepared)
        provider = self.require_provider()
        result = await provider.generate(self._generation_request(prepared))
        return await self._complete(prepared, result)

    async def stream_prepared(self, prepared: Prepared) -> AsyncIterator[tuple[str, dict]]:
        """Yield (event, data) pairs: meta, delta*, done. Provider errors raise from the generator."""
        yield "meta", {"session_id": prepared.session_id, "analysis": prepared.analysis}
        if prepared.needs_clarification:
            yield "done", self._clarification_payload(prepared)
            return
        provider = self.require_provider()
        result: GenerationResult | None = None
        async for event in provider.stream(self._generation_request(prepared)):
            if event.kind == "delta":
                yield "delta", {"text": event.text}
            else:
                result = event.result
        if result is None:  # pragma: no cover - provider contract violation
            raise ProviderNotConfigured("Provider ended the stream without a result.")
        done = await self._complete(prepared, result)
        done.pop("answer", None)  # the client already has it from the deltas
        yield "done", done

    # ---- completion ---------------------------------------------------------
    @staticmethod
    def _clarification_payload(prepared: Prepared) -> dict:
        return {
            "status": "needs_clarification", "session_id": prepared.session_id,
            "analysis": prepared.analysis, "answer": prepared.analysis["clarification_question"],
        }

    async def _complete(self, prepared: Prepared, result: GenerationResult) -> dict:
        evaluation = evaluate_response(
            result.text, prepared.analysis["selected_strategy"],
            finish_reason=result.finish_reason, task_type=prepared.analysis["task_type"],
            user_message=prepared.message,
        )
        answer = redact(result.text)
        interaction_id = await run_in_threadpool(self._persist, prepared, result, answer, evaluation)
        return {
            "status": "completed",
            "interaction_id": interaction_id,
            "session_id": prepared.session_id,
            "analysis": prepared.analysis,
            "answer": answer,
            "evaluation": evaluation,
            "meta": {
                "model": result.model, "latency_ms": result.latency_ms,
                "prompt_tokens": result.prompt_tokens, "completion_tokens": result.completion_tokens,
                "finish_reason": result.finish_reason, "used_fallback_model": result.used_fallback,
            },
        }

    def _persist(self, prepared: Prepared, result: GenerationResult, answer: str, evaluation: dict) -> str:
        interaction_id = str(uuid.uuid4())
        with session_scope() as db:
            repo.ensure_session(db, prepared.session_id, prepared.user_id, prepared.message)
            repo.add_interaction(db, Interaction(
                id=interaction_id, session_id=prepared.session_id, user_id=prepared.user_id,
                user_message=prepared.message, assistant_response=answer, analysis=prepared.analysis,
                model=result.model, latency_ms=result.latency_ms,
                prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens,
                finish_reason=result.finish_reason, evaluation=evaluation,
            ))
            repo.add_messages(db, prepared.session_id, prepared.message, answer)
        return interaction_id
