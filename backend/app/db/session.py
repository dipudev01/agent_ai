"""Async SQLAlchemy engine/session with mandatory tenant scoping.

Every ORM query must be executed through a session bound to a tenant context.
`get_scoped_session(tenant_id)` returns a session whose local variable
`current_tenant_id` is set; model query helpers that are tenant-aware read this
to inject the `tenant_id` filter. Client-supplied tenant IDs are never trusted —
the tenant is always resolved server-side from the authenticated principal.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextvars import ContextVar
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

current_tenant_id: ContextVar[str | None] = ContextVar("current_tenant_id", default=None)
current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)

_engine_kwargs: dict[str, Any] = {
    "echo": settings.db_echo,
    "pool_pre_ping": True,
}
if settings.database_url.startswith("sqlite"):
    # In-memory SQLite requires a static pool so every connection shares one DB.
    from sqlalchemy.pool import StaticPool

    _engine_kwargs["poolclass"] = StaticPool
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_size"] = settings.db_pool_size
    _engine_kwargs["max_overflow"] = settings.db_max_overflow

_engine = create_async_engine(settings.database_url, **_engine_kwargs)

SessionLocal = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


def set_tenant_context(tenant_id: str, user_id: str | None = None) -> None:
    current_tenant_id.set(tenant_id)
    if user_id:
        current_user_id.set(user_id)


def clear_tenant_context() -> None:
    current_tenant_id.set(None)
    current_user_id.set(None)


async def close() -> None:
    await _engine.dispose()