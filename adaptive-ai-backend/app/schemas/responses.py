from typing import Any, Literal

from pydantic import BaseModel


class GenerationMeta(BaseModel):
    model: str | None = None
    latency_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    finish_reason: str | None = None
    used_fallback_model: bool = False


class AssistantResponse(BaseModel):
    status: Literal["completed", "needs_clarification"]
    interaction_id: str | None = None
    session_id: str | None = None
    analysis: dict[str, Any]
    answer: str | None = None
    evaluation: dict[str, Any] | None = None
    meta: GenerationMeta | None = None
