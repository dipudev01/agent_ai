from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class AgentRegistration(Base, IdMixin, TimestampMixin):
    """Registered agent definition. Registration is immutable-friendly: new
    versions create new registrations; the registry points to the current one."""

    __tablename__ = "agent_registrations"

    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    agent_key: Mapped[str] = mapped_column(String(64), index=True)  # e.g. loan_eligibility
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000), default="")
    version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    status: Mapped[str] = mapped_column(String(32), default="active")  # active|deprecated
    capabilities: Mapped[list] = mapped_column(JSON, default=list)
    routing_priority: Mapped[int] = mapped_column(default=100)


class AgentRun(Base, IdMixin, TimestampMixin):
    """Auditable execution record for every agent invocation."""

    __tablename__ = "agent_runs"

    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    agent_key: Mapped[str] = mapped_column(String(64), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    triggered_by_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="started")
    input_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    output_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(nullable=True)
    token_usage: Mapped[dict] = mapped_column(JSON, default=dict)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Conversation(Base, IdMixin, TimestampMixin):
    __tablename__ = "conversations"

    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    agent_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel: Mapped[str] = mapped_column(String(32), default="api")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)