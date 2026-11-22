import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_orchestrator, rate_limited, require_api_key
from app.config import settings
from app.database import repository as repo
from app.database.connection import get_db
from app.database.models import Interaction
from app.errors import FeedbackExistsError
from app.providers.base import ProviderError
from app.schemas.requests import ID_PATTERN, AssistantRequest, FeedbackRequest, PreferenceRequest
from app.schemas.responses import AssistantResponse
from app.services.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(require_api_key), Depends(rate_limited("api", "rate_limit_per_minute"))],
)
generation_limit = Depends(rate_limited("respond", "respond_rate_limit_per_minute"))


def _id_path():
    return Path(min_length=1, max_length=100, pattern=ID_PATTERN)


def _id_query():
    return Query(default=None, min_length=1, max_length=100, pattern=ID_PATTERN)


# ---- assistant --------------------------------------------------------------
@router.post("/assistant/analyze")
async def analyze(payload: AssistantRequest, orchestrator: Orchestrator = Depends(get_orchestrator)):
    """Intent, complexity, persona and strategy decision without calling the LLM."""
    return await orchestrator.analyze(payload)


@router.post("/assistant/respond", response_model=AssistantResponse, dependencies=[generation_limit])
async def respond(payload: AssistantRequest, orchestrator: Orchestrator = Depends(get_orchestrator)):
    return await orchestrator.respond(payload)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


@router.post("/assistant/respond/stream", dependencies=[generation_limit])
async def respond_stream(payload: AssistantRequest, orchestrator: Orchestrator = Depends(get_orchestrator)):
    """Server-Sent Events: `meta`, many `delta`, then `done` (or `error`)."""

    # Resolve access/config problems as normal HTTP errors (403/503) before the stream starts.
    prepared = await orchestrator.prepare(payload)
    if not prepared.needs_clarification:
        orchestrator.require_provider()

    async def events():
        try:
            async for event, data in orchestrator.stream_prepared(prepared):
                yield _sse(event, data)
        except ProviderError as exc:
            yield _sse("error", {"code": exc.code, "detail": exc.message, "retry_after": exc.retry_after})
        except Exception as exc:  # noqa: BLE001
            logger.exception("Streaming failed")
            yield _sse("error", {"code": "internal_error", "detail": type(exc).__name__})

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/assistant/feedback")
def feedback(payload: FeedbackRequest, db: Session = Depends(get_db)):
    interaction = db.get(Interaction, payload.interaction_id)
    if interaction is None:
        raise HTTPException(status_code=404, detail="Interaction not found")
    if payload.session_id and interaction.session_id != payload.session_id:
        raise HTTPException(status_code=403, detail="Session mismatch")
    if repo.has_feedback(db, interaction.id):
        raise HTTPException(status_code=409, detail="Feedback has already been submitted for this interaction")
    try:
        repo.save_feedback(db, interaction, payload.rating, payload.feedback_text)
    except FeedbackExistsError as exc:
        raise HTTPException(status_code=409, detail="Feedback has already been submitted for this interaction") from exc
    return {
        "status": "recorded", "interaction_id": interaction.id, "rating": payload.rating,
        "adaptation": (
            f"Stored. Strategy selection for '{interaction.analysis.get('task_type')}' tasks starts using "
            f"ratings once the default strategy has {settings.min_feedback_samples} of them "
            f"(mode: {settings.adaptation_mode})."
        ),
    }


# ---- sessions ---------------------------------------------------------------
@router.get("/sessions/{session_id}")
def get_session(
    session_id: str = _id_path(), user_id: str | None = _id_query(),
    limit: int = Query(default=200, ge=1, le=1000), offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    repo.assert_session_access(db, session_id, user_id)
    messages = repo.session_data(db, session_id, limit, offset)
    if not messages and offset == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "messages": messages, "limit": limit, "offset": offset}


@router.delete("/sessions/{session_id}")
def remove_session(session_id: str = _id_path(), user_id: str | None = _id_query(),
                   db: Session = Depends(get_db)):
    repo.assert_session_access(db, session_id, user_id)
    repo.delete_session(db, session_id)
    return {"status": "deleted", "session_id": session_id}


@router.get("/users/{user_id}/sessions")
def list_user_sessions(
    user_id: str = _id_path(), limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return {"user_id": user_id, "sessions": repo.list_sessions(db, user_id, limit, offset)}


@router.delete("/users/{user_id}")
def erase_user(user_id: str = _id_path(), db: Session = Depends(get_db)):
    """Right-to-erasure helper: removes the user's sessions, messages, feedback and preferences."""
    removed = repo.delete_user_data(db, user_id)
    return {"status": "erased", "user_id": user_id, "sessions_removed": removed}


# ---- preferences ------------------------------------------------------------
@router.get("/preferences/{user_id}")
def get_user_preferences(user_id: str = _id_path(), db: Session = Depends(get_db)):
    return {"user_id": user_id, "preferences": repo.get_preferences(db, user_id)}


@router.put("/preferences/{user_id}")
def put_user_preferences(payload: PreferenceRequest, user_id: str = _id_path(), db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    return {"user_id": user_id, "preferences": repo.save_preferences(db, user_id, data)}


@router.delete("/preferences/{user_id}")
def reset_user_preferences(user_id: str = _id_path(), db: Session = Depends(get_db)):
    repo.delete_preferences(db, user_id)
    return {"status": "reset", "user_id": user_id}


# ---- analytics --------------------------------------------------------------
@router.get("/analytics/summary")
def analytics(db: Session = Depends(get_db)):
    """Usage, latency and per-task strategy ratings (what the adaptation layer learns from)."""
    return repo.analytics_summary(db)
