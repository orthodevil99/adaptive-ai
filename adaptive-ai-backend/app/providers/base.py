from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Literal, Protocol


class ProviderError(Exception):
    """Base class. `status_code` is what the HTTP API should answer with."""

    status_code = 502
    code = "provider_error"
    fallback_ok = False  # may a secondary model be tried?

    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after


class ProviderNotConfigured(ProviderError):
    status_code = 503
    code = "provider_not_configured"


class ProviderAuthError(ProviderError):
    status_code = 502
    code = "provider_auth_failed"


class ProviderRateLimited(ProviderError):
    status_code = 429
    code = "provider_rate_limited"
    fallback_ok = True


class ProviderTimeout(ProviderError):
    status_code = 504
    code = "provider_timeout"
    fallback_ok = True


class ProviderUnavailable(ProviderError):
    status_code = 503
    code = "provider_unavailable"
    fallback_ok = True


class ProviderModelError(ProviderError):
    status_code = 502
    code = "provider_model_unavailable"
    fallback_ok = True


class ProviderBadRequest(ProviderError):
    status_code = 502
    code = "provider_bad_request"


class ProviderEmptyResponse(ProviderError):
    status_code = 502
    code = "provider_empty_response"


@dataclass
class GenerationRequest:
    messages: list[dict[str, str]]
    max_tokens: int = 1500
    temperature: float = 0.5
    reasoning_effort: Literal["low", "medium", "high"] | None = None
    max_tokens_ceiling: int = 8192  # upper bound for the automatic "ran out of tokens" retry
    model: str | None = None


@dataclass
class GenerationResult:
    text: str
    model: str
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: int = 0
    used_fallback: bool = False


@dataclass
class StreamEvent:
    kind: Literal["delta", "final"]
    text: str = ""
    result: GenerationResult | None = field(default=None)


class TextProvider(Protocol):
    name: str

    async def generate(self, request: GenerationRequest) -> GenerationResult: ...

    def stream(self, request: GenerationRequest) -> AsyncIterator[StreamEvent]: ...

    async def healthcheck(self) -> dict: ...

    async def close(self) -> None: ...
