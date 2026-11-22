import logging
import re
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.deps import require_api_key
from app.api.routes import router
from app.config import VERSION, settings
from app.database import repository as repo
from app.database.connection import SessionLocal, engine
from app.database.migrate import init_database
from app.errors import SessionAccessError
from app.providers.base import ProviderError
from app.providers.factory import build_provider
from app.services.orchestrator import Orchestrator
from app.utils.logging import configure_logging, request_id_var
from app.utils.ratelimit import SlidingWindowLimiter

configure_logging(settings.log_level, settings.log_json)
logger = logging.getLogger(__name__)
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,64}$")


@asynccontextmanager
async def lifespan(application: FastAPI):
    for warning in settings.check_runtime():
        logger.warning(warning)
    init_database(engine)
    if settings.session_ttl_days:
        with SessionLocal() as db:
            removed = repo.purge_older_than(db, settings.session_ttl_days)
        if removed:
            logger.info("Retention: removed %s expired sessions", removed)
    provider = build_provider(settings)
    application.state.provider = provider
    application.state.orchestrator = Orchestrator(provider, settings)
    application.state.limiter = SlidingWindowLimiter()
    logger.info("Adaptive AI %s started (env=%s, provider=%s)", VERSION, settings.app_env,
                provider.name if provider else "none")
    yield
    if provider is not None:
        await provider.close()
    engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Adaptive AI",
        version=VERSION,
        description="Adaptive persona & workflow orchestration backend (Groq gpt-oss by default).",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_on else None,
        redoc_url="/redoc" if settings.docs_on else None,
        openapi_url="/openapi.json" if settings.docs_on else None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Retry-After", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        incoming = request.headers.get("x-request-id", "")
        request_id = incoming if _REQUEST_ID_RE.match(incoming) else uuid.uuid4().hex[:16]
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            length = request.headers.get("content-length", "")
            if length.isdigit() and int(length) > settings.max_body_bytes:
                response = JSONResponse({"detail": "Request body too large."}, status_code=413)
            else:
                response = await call_next(request)
        except Exception:  # noqa: BLE001
            logger.exception("Unhandled error on %s %s", request.method, request.url.path)
            response = JSONResponse({"detail": "Internal server error.", "request_id": request_id}, status_code=500)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        logger.info("%s %s -> %s in %sms", request.method, request.url.path, response.status_code, elapsed_ms)
        request_id_var.reset(token)
        return response

    @app.exception_handler(ProviderError)
    async def provider_error_handler(request: Request, exc: ProviderError):
        headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after else None
        logger.warning("Provider error %s on %s", exc.code, request.url.path)
        return JSONResponse(
            {"detail": exc.message, "code": exc.code, "request_id": request_id_var.get()},
            status_code=exc.status_code, headers=headers,
        )

    @app.exception_handler(SessionAccessError)
    async def session_access_handler(request: Request, exc: SessionAccessError):
        return JSONResponse({"detail": str(exc), "code": "session_forbidden"}, status_code=403)

    app.include_router(router)

    @app.get("/")
    def root():
        return {"name": "Adaptive AI", "version": VERSION, "status": "running",
                "docs": "/docs" if settings.docs_on else None}

    @app.get("/health")
    def health():
        """Liveness plus a safe configuration summary (no secrets)."""
        return {
            "status": "ok", "version": VERSION, "env": settings.app_env,
            "provider": settings.provider, "provider_configured": bool(request_provider(app)),
            "auth_enabled": bool(settings.api_key_list), "adaptation_mode": settings.adaptation_mode,
        }

    @app.get("/health/ready")
    def ready():
        """Readiness: can we reach the database?"""
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception:  # noqa: BLE001
            logger.exception("Readiness check failed")
            return JSONResponse({"status": "unavailable", "database": "down"}, status_code=503)
        return {"status": "ready", "database": "up"}

    @app.get("/health/model", dependencies=[Depends(require_api_key)])
    async def model_health(probe: bool = Query(default=False)):
        """Config status; with `?probe=true` also checks the key and model against the provider."""
        provider = request_provider(app)
        info = {"provider": settings.provider, "model": settings.groq_model,
                "fallback_model": settings.groq_fallback_model or None, "configured": provider is not None}
        if probe and provider is not None:
            info["probe"] = await provider.healthcheck()
        return info

    return app


def request_provider(app: FastAPI):
    return getattr(app.state, "provider", None)


app = create_app()
