import hashlib
import hmac

from fastapi import Header, HTTPException, Request, Response

from app.config import settings
from app.services.orchestrator import Orchestrator


def get_orchestrator(request: Request) -> Orchestrator:
    return request.app.state.orchestrator


async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> str:
    """Authenticate the caller. With no APP_API_KEYS configured the API is open (dev only)."""
    keys = settings.api_key_list
    if not keys:
        request.state.principal = "anonymous"
        return "anonymous"
    supplied = x_api_key
    if not supplied and authorization and authorization.lower().startswith("bearer "):
        supplied = authorization[7:].strip()
    if supplied:
        matched: str | None = None
        for key in keys:  # compare against every key so timing doesn't reveal which matched
            if hmac.compare_digest(supplied.encode(), key.encode()):
                matched = key
        if matched is not None:
            principal = "key:" + hashlib.sha256(matched.encode()).hexdigest()[:8]
            request.state.principal = principal
            return principal
    raise HTTPException(
        status_code=401, detail="Missing or invalid API key.", headers={"WWW-Authenticate": "Bearer"}
    )


def _client_id(request: Request) -> str:
    principal = getattr(request.state, "principal", "anonymous")
    host = request.client.host if request.client else "unknown"
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            host = forwarded.split(",")[0].strip() or host
    return f"{principal}|{host}"


def rate_limited(bucket: str, limit_field: str):
    """Dependency factory: sliding-window limit per caller, read from settings at request time."""

    async def dependency(request: Request, response: Response) -> None:
        limit = getattr(settings, limit_field)
        if limit <= 0:
            return
        decision = request.app.state.limiter.check(f"{bucket}|{_client_id(request)}", limit, 60.0)
        response.headers["X-RateLimit-Limit"] = str(decision.limit)
        response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
        if not decision.allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Retry in {decision.retry_after}s.",
                headers={"Retry-After": str(decision.retry_after)},
            )

    return dependency
