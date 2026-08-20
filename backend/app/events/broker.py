"""Event broker abstraction with Kafka (prod) and in-process (dev/test) backends.

Publishing is fire-and-forget from the request path — consumers run as separate
services. This gives us load leveling and prevents agent runs from blocking on
downstream sinks. Topic partitioning key = tenant_id to preserve per-tenant
ordering.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime

from app.events.schemas import DomainEvent

_consumers: dict[str, list[Callable[[DomainEvent], None]]] = {}


def subscribe(topic: str):
    """Decorator to register an in-process consumer (dev/test only)."""

    def deco(fn: Callable[[DomainEvent], None]):
        _consumers.setdefault(topic, []).append(fn)
        return fn

    return deco


class EventBroker(ABC):
    started = False

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None: ...


class LocalEventBroker(EventBroker):
    """In-process broker. Used in development and tests."""

    def __init__(self) -> None:
        self._started = False

    async def start(self) -> None:
        self._started = True
        self.started = True

    async def stop(self) -> None:
        self._started = False
        self.started = False

    async def publish(self, event: DomainEvent) -> None:
        for fn in _consumers.get(event.topic, []):
            await asyncio.to_thread(fn, event)


class KafkaEventBroker(EventBroker):
    def __init__(self, settings) -> None:
        from aiokafka import AIOKafkaProducer

        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            enable_idempotence=True,
            acks="all",
            compression_type="lz4",
        )

    async def start(self) -> None:
        await self._producer.start()
        self.started = True

    async def stop(self) -> None:
        await self._producer.stop()
        self.started = False

    async def publish(self, event: DomainEvent) -> None:
        await self._producer.send(
            topic=event.topic,
            value=event.model_dump_json().encode(),
            key=event.tenant_id.encode(),  # per-tenant ordering
        )


def new_event(
    event_type,
    *,
    tenant_id: str,
    correlation_id: str,
    producer: str,
    institution_id: str | None = None,
    payload: dict | None = None,
) -> DomainEvent:
    return DomainEvent(
        event_type=event_type,
        tenant_id=tenant_id,
        institution_id=institution_id,
        correlation_id=correlation_id,
        producer=producer,
        occurred_at=datetime.now(UTC).isoformat(),
        payload=payload or {},
    )
