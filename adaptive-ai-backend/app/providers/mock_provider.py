"""Deterministic offline provider for tests, demos and frontend development (PROVIDER=mock)."""

import asyncio
import re
from collections.abc import AsyncIterator

from app.providers.base import GenerationRequest, GenerationResult, ProviderError, StreamEvent


class MockProvider:
    name = "mock"

    def __init__(self, *, fail_with: ProviderError | None = None, delay: float = 0.0) -> None:
        self.fail_with = fail_with
        self.delay = delay
        self.calls: list[GenerationRequest] = []

    def _compose(self, request: GenerationRequest) -> str:
        system = request.messages[0]["content"] if request.messages else ""
        user = request.messages[-1]["content"] if request.messages else ""
        persona = (re.search(r"PERSONA: (\w+)", system) or [None, "balanced"])[1]
        strategy = (re.search(r"RESPONSE STRATEGY: (\w+)", system) or [None, "DIRECT_ANSWER"])[1]
        return (
            f"[mock answer | persona={persona} | strategy={strategy}]\n\n"
            f"1. You asked: {user[:200]}\n"
            f"2. This is a deterministic offline response; set PROVIDER=groq for real output.\n"
            f"3. Context turns received: {max(0, len(request.messages) - 2)}."
        )

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        self.calls.append(request)
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail_with is not None:
            raise self.fail_with
        text = self._compose(request)
        return GenerationResult(text=text, model="mock-1", finish_reason="stop",
                                prompt_tokens=sum(len(m["content"]) for m in request.messages) // 4,
                                completion_tokens=len(text) // 4, latency_ms=int(self.delay * 1000))

    async def stream(self, request: GenerationRequest) -> AsyncIterator[StreamEvent]:
        result = await self.generate(request)
        for piece in re.findall(r"\S+\s*", result.text):
            yield StreamEvent("delta", piece)
        yield StreamEvent("final", result=result)

    async def healthcheck(self) -> dict:
        return {"reachable": True, "model": "mock-1", "model_available": True}

    async def close(self) -> None:
        return None
