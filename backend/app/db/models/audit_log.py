from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class AuditLog(Base, IdMixin, TimestampMixin):
    """Append-only audit trail. In production this table is WRITE-ONLY from the
    app's perspective: rows are shipped to an immutable, hash-chained store
    (e.g. S3 object-lock + hash chain) by a nightly job and never UPDATEd here."""

    __tablename__ = "audit_logs"

    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)
    actor_type: Mapped[str] = mapped_column(String(32), default="user")  # user|agent|system
    actor_id: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(128), index=True)
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str] = mapped_column(String(64))
    outcome: Mapped[str] = mapped_column(String(32))  # success|denied|error
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    hash_chain_prev: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hash_chain_current: Mapped[str | None] = mapped_column(String(128), nullable=True)