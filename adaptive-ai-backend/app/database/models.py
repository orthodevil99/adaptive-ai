from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), index=True)
    user_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    user_message: Mapped[str] = mapped_column(Text)
    assistant_response: Mapped[str] = mapped_column(Text)
    analysis: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    # v3 telemetry (all nullable so v2 databases migrate in place)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    finish_reason: Mapped[str | None] = mapped_column(String(30), nullable=True)
    evaluation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    feedback: Mapped[list["Feedback"]] = relationship(
        back_populates="interaction", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Preference(Base):
    __tablename__ = "preferences"

    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    preferred_persona: Mapped[str | None] = mapped_column(String(30), nullable=True)
    response_length: Mapped[str | None] = mapped_column(String(20), nullable=True)
    explanation_style: Mapped[str | None] = mapped_column(String(20), nullable=True)


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (UniqueConstraint("interaction_id", name="uq_feedback_interaction"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[str] = mapped_column(ForeignKey("interactions.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    strategy: Mapped[str] = mapped_column(String(40))
    task_type: Mapped[str] = mapped_column(String(40))
    persona: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    interaction: Mapped[Interaction] = relationship(back_populates="feedback")


Index("ix_feedback_strategy_task", Feedback.strategy, Feedback.task_type)
