"""Audit service — the only sanctioned way to write audit records and agent runs.

Records are append-only. In production a nightly job ships rows to immutable,
hash-chained storage (S3 object-lock) for tamper-evident evidence.
"""

from __future__ import annotations

from app.core.security import pii
from app.events.broker import new_event
from app.events.schemas import EventType


async def record(
    *,
    tenant_id: str,
    correlation_id: str,
    actor_type: str,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    outcome: str,
    detail: dict | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:

    # Mask PII before persistence so raw PII never lands in the audit store.
    safe_detail = pii.mask_payload(detail or {})
    from app.db.models.audit_log import AuditLog
    from app.db.session import SessionLocal

    async with SessionLocal() as session:
        session.add(
            AuditLog(
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                actor_type=actor_type,
                actor_id=actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                outcome=outcome,
                detail=safe_detail,
                ip=ip,
                user_agent=user_agent,
            )
        )
        await session.commit()


async def record_agent_run(
    *,
    tenant_id: str,
    run_id: str,
    agent_key: str,
    conversation_id: str | None,
    user_id: str | None,
    status: str,
    input_schema: dict,
    output_schema: dict,
    latency_ms: int | None,
    token_usage: dict,
    model_version: str | None,
) -> None:
    from app.db.models.agent import AgentRun
    from app.db.session import SessionLocal

    async with SessionLocal() as session:
        session.add(
            AgentRun(
                tenant_id=tenant_id,
                run_id=run_id,
                agent_key=agent_key,
                conversation_id=conversation_id,
                triggered_by_user_id=user_id,
                status=status,
                input_schema=pii.mask_payload(input_schema),
                output_schema=pii.mask_payload(output_schema),
                latency_ms=latency_ms,
                token_usage=token_usage,
                model_version=model_version,
            )
        )
        await session.commit()


def emit_domain_event(
    *,
    event_type: EventType,
    tenant_id: str,
    correlation_id: str,
    producer: str,
    institution_id: str | None = None,
    payload: dict | None = None,
) -> None:
    from app.core.container import container

    event = new_event(
        event_type,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        producer=producer,
        institution_id=institution_id,
        payload=pii.mask_payload(payload or {}),
    )
    import asyncio

    asyncio.create_task(container.events().publish(event))