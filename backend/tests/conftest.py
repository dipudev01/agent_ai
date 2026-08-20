"""Test fixtures: in-memory SQLite, local event broker, in-memory stores.
Env vars are set BEFORE any app module import so the cached settings/engine
pick them up."""

from __future__ import annotations

import asyncio
import os
import tempfile

_DB_FILE = os.path.join(tempfile.gettempdir(), "bfsi_test.db")
if os.path.exists(_DB_FILE):
    os.remove(_DB_FILE)

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_FILE}"
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET"] = "test-secret-key-that-is-long-enough"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-derivation"
os.environ["LLM_DEFAULT_PROVIDER"] = "mock"
os.environ["VECTOR_STORE"] = "memory"

import pytest

from app.db.base import Base
from app.db.session import SessionLocal, _engine

# Ensure all models are registered on Base.metadata before create_all.
from app.db.models import agent, audit_log, tenant, user  # noqa: F401, E402


@pytest.fixture(scope="session", autouse=True)
def _db():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _setup():
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    loop.run_until_complete(_setup())
    yield
    loop.run_until_complete(_teardown())


async def _teardown():
    from app.db.session import close

    await close()