from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class Tenant(Base, IdMixin, TimestampMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    plan: Mapped[str] = mapped_column(String(32), default="enterprise")
    data_residency: Mapped[str] = mapped_column(String(64), default="in")
    kms_key_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)


class Institution(Base, IdMixin, TimestampMixin):
    """Financial institution operating under a platform tenant."""

    __tablename__ = "institutions"

    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    rbi_license: Mapped[str | None] = mapped_column(String(64), nullable=True)
    compliance_tier: Mapped[str] = mapped_column(String(32), default="standard")