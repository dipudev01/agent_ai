"""Dependency container — the single place services resolve their collaborators.

All services receive dependencies through this container (or FastAPI DI).
No service constructs its own clients. This keeps services unit-testable and
prevents the app from being a distributed monolith of leaked imports.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import check_database
from app.events.broker import EventBroker, KafkaEventBroker, LocalEventBroker
from app.gateway.llm import LLMGateway
from app.rag.vectorstore import InMemoryVectorStore, VectorStore


class Container:
    """Holds shared infrastructure dependencies."""

    def __init__(self) -> None:
        self._llm: LLMGateway | None = None
        self._events: EventBroker | None = None
        self._vector: VectorStore | None = None
        self._redis = None

    def llm(self) -> LLMGateway:
        if self._llm is None:
            from app.gateway.factory import build_llm_gateway

            self._llm = build_llm_gateway(settings)
        return self._llm

    def events(self) -> EventBroker:
        if self._events is None:
            if settings.app_env == "production":
                self._events = KafkaEventBroker(settings)
            else:
                self._events = LocalEventBroker()
        return self._events

    def vector(self) -> VectorStore:
        if self._vector is None:
            if settings.vector_store == "opensearch":
                from app.rag.vectorstore import OpenSearchVectorStore

                self._vector = OpenSearchVectorStore(settings)
            else:
                self._vector = InMemoryVectorStore()
        return self._vector

    def redis(self):
        if self._redis is None:
            from redis.asyncio import Redis

            self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def readiness(self) -> dict[str, bool]:
        checks = {"database": False, "redis": False, "events": False}
        try:
            await check_database()
            checks["database"] = True
        except Exception:
            pass
        try:
            await self.redis().ping()
            checks["redis"] = True
        except Exception:
            pass
        if settings.app_env == "production":
            checks["events"] = self._events is not None and self._events.started
        else:
            checks["events"] = True
        return checks

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        await self.events().start()
        try:
            yield
        finally:
            await self.events().stop()
            if self._redis is not None:
                await self._redis.aclose()


container = Container()
