from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import ChatSession, Feedback, Interaction, Message, Preference, utc_now
from app.errors import FeedbackExistsError, SessionAccessError


# ---- sessions ---------------------------------------------------------------
def assert_session_access(db: Session, session_id: str, user_id: str | None) -> None:
    """Sessions with an owner are only usable by that user_id. Ownerless (anonymous/legacy)
    sessions stay open to anyone holding the id."""
    row = db.get(ChatSession, session_id)
    if row is not None and row.user_id and row.user_id != user_id:
        raise SessionAccessError("This session belongs to a different user.")


def ensure_session(db: Session, session_id: str, user_id: str | None, first_message: str) -> ChatSession:
    row = db.get(ChatSession, session_id)
    if row is None:
        row = ChatSession(id=session_id, user_id=user_id, title=first_message.strip()[:80] or None)
        db.add(row)
        try:
            db.flush()
        except IntegrityError:
            # Created concurrently by another request. This runs first in its transaction,
            # so rolling back discards nothing else.
            db.rollback()
            row = db.get(ChatSession, session_id)
    if row is not None:
        if row.user_id and row.user_id != user_id:
            raise SessionAccessError("This session belongs to a different user.")
        if row.user_id is None and user_id:
            row.user_id = user_id
        row.updated_at = utc_now()
    return row


def list_sessions(db: Session, user_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
    rows = db.scalars(
        select(ChatSession).where(ChatSession.user_id == user_id)
        .order_by(desc(ChatSession.updated_at)).limit(limit).offset(offset)
    ).all()
    return [
        {"session_id": r.id, "title": r.title, "created_at": r.created_at.isoformat(),
         "updated_at": r.updated_at.isoformat()}
        for r in rows
    ]


def session_data(db: Session, session_id: str, limit: int = 200, offset: int = 0) -> list[dict]:
    rows = db.scalars(
        select(Message).where(Message.session_id == session_id)
        .order_by(Message.id).limit(limit).offset(offset)
    ).all()
    return [
        {"role": r.role, "content": r.content, "created_at": r.created_at.isoformat()} for r in rows
    ]


def _remove_session_rows(db: Session, session_id: str) -> None:
    interaction_ids = select(Interaction.id).where(Interaction.session_id == session_id)
    db.execute(delete(Feedback).where(Feedback.interaction_id.in_(interaction_ids)))
    db.execute(delete(Interaction).where(Interaction.session_id == session_id))
    db.execute(delete(Message).where(Message.session_id == session_id))
    db.execute(delete(ChatSession).where(ChatSession.id == session_id))


def delete_session(db: Session, session_id: str) -> None:
    _remove_session_rows(db, session_id)
    db.commit()


def delete_user_data(db: Session, user_id: str) -> int:
    """Erase a user's sessions, interactions, feedback and preferences. Returns sessions removed."""
    session_ids = set(db.scalars(select(ChatSession.id).where(ChatSession.user_id == user_id)).all())
    session_ids |= set(db.scalars(select(Interaction.session_id).where(Interaction.user_id == user_id)).all())
    for session_id in session_ids:
        _remove_session_rows(db, session_id)
    db.execute(delete(Preference).where(Preference.user_id == user_id))
    db.commit()
    return len(session_ids)


def purge_older_than(db: Session, days: int) -> int:
    """Retention: delete sessions not touched for `days` days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    old = db.scalars(select(ChatSession.id).where(ChatSession.updated_at < cutoff)).all()
    for session_id in old:
        _remove_session_rows(db, session_id)
    db.commit()
    return len(old)


# ---- conversation -----------------------------------------------------------
def add_interaction(db: Session, interaction: Interaction) -> None:
    db.add(interaction)
    db.flush()


def add_messages(db: Session, session_id: str, user_text: str, answer: str) -> None:
    db.add_all([
        Message(session_id=session_id, role="user", content=user_text),
        Message(session_id=session_id, role="assistant", content=answer),
    ])


def get_context(db: Session, session_id: str, limit: int) -> list[dict[str, str]]:
    if limit <= 0:
        return []
    rows = db.scalars(
        select(Message).where(Message.session_id == session_id).order_by(desc(Message.id)).limit(limit)
    ).all()
    return [{"role": r.role, "content": r.content} for r in reversed(rows)]


# ---- preferences ------------------------------------------------------------
def get_preferences(db: Session, user_id: str) -> dict:
    preference = db.get(Preference, user_id)
    if preference is None:
        return {}
    return {
        "preferred_persona": preference.preferred_persona,
        "response_length": preference.response_length,
        "explanation_style": preference.explanation_style,
    }


def save_preferences(db: Session, user_id: str, data: dict) -> dict:
    preference = db.get(Preference, user_id) or Preference(user_id=user_id)
    for key, value in data.items():
        setattr(preference, key, value)
    db.add(preference)
    db.commit()
    return get_preferences(db, user_id)


def delete_preferences(db: Session, user_id: str) -> None:
    db.execute(delete(Preference).where(Preference.user_id == user_id))
    db.commit()


# ---- feedback / adaptation --------------------------------------------------
def has_feedback(db: Session, interaction_id: str) -> bool:
    return bool(db.scalar(select(func.count(Feedback.id)).where(Feedback.interaction_id == interaction_id)))


def save_feedback(db: Session, interaction: Interaction, rating: int, text: str | None) -> None:
    db.add(Feedback(
        interaction_id=interaction.id, rating=rating, feedback_text=text,
        strategy=interaction.analysis.get("selected_strategy", "unknown"),
        task_type=interaction.analysis.get("task_type", "unknown"),
        persona=interaction.analysis.get("selected_persona"),
    ))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise FeedbackExistsError() from exc


def strategy_stats(db: Session, task: str, strategies: list[str]) -> dict[str, tuple[int, float]]:
    """strategy -> (rating count, sum of rewards in [0, 1]) for one task type."""
    if not strategies:
        return {}
    rows = db.execute(
        select(Feedback.strategy, func.count(Feedback.id), func.sum(Feedback.rating - 1))
        .where(Feedback.task_type == task, Feedback.strategy.in_(strategies))
        .group_by(Feedback.strategy)
    ).all()
    return {strategy: (int(count), float(total or 0) / 4.0) for strategy, count, total in rows}


# ---- analytics --------------------------------------------------------------
def analytics_summary(db: Session) -> dict:
    totals = db.execute(
        select(
            func.count(Interaction.id), func.avg(Interaction.latency_ms),
            func.sum(Interaction.prompt_tokens), func.sum(Interaction.completion_tokens),
        )
    ).one()
    rated = db.execute(
        select(Feedback.task_type, Feedback.strategy, func.count(Feedback.id), func.avg(Feedback.rating))
        .group_by(Feedback.task_type, Feedback.strategy)
        .order_by(Feedback.task_type, desc(func.avg(Feedback.rating)))
    ).all()
    return {
        "interactions": int(totals[0] or 0),
        "avg_latency_ms": round(float(totals[1]), 1) if totals[1] is not None else None,
        "prompt_tokens": int(totals[2] or 0),
        "completion_tokens": int(totals[3] or 0),
        "strategy_ratings": [
            {"task_type": t, "strategy": s, "ratings": int(n), "avg_rating": round(float(a), 2)}
            for t, s, n, a in rated
        ],
    }
