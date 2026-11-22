from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.config import settings

Persona = Literal[
    "balanced", "educational", "technical", "concise", "creative",
    "professional", "researcher", "planner", "analyst",
]
ResponseLength = Literal["short", "medium", "detailed"]
# Identifiers are echoed into logs and URLs, so keep them to a safe alphabet.
ID_PATTERN = r"^[A-Za-z0-9_\-:.@]+$"
Identifier = Annotated[str, Field(min_length=1, max_length=100, pattern=ID_PATTERN)]


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AssistantRequest(StrictRequest):
    message: str = Field(min_length=1, max_length=settings.max_request_length)
    session_id: Identifier | None = None
    user_id: Identifier | None = None
    preferred_persona: Persona | None = None
    response_length: ResponseLength | None = None


class FeedbackRequest(StrictRequest):
    interaction_id: str = Field(min_length=1, max_length=36)
    session_id: Identifier | None = None
    rating: int = Field(ge=1, le=5)
    feedback_text: str | None = Field(default=None, max_length=2000)


class PreferenceRequest(StrictRequest):
    preferred_persona: Persona | None = None
    response_length: ResponseLength | None = None
    explanation_style: Literal["simple", "balanced", "technical"] | None = None
