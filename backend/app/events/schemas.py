"""Canonical domain event schemas.

Every event name is versioned (`v1`). Producers emit the current version;
consumers must handle schema evolution via the schema registry. Events are the
backbone of async, decoupled processing: audit, compliance, notifications,
analytics, and fraud engines subscribe to these topics.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventType(StrEnum):
    CUSTOMER_CREATED = "customer.created.v1"
    CUSTOMER_UPDATED = "customer.updated.v1"
    KYC_COMPLETED = "kyc.completed.v1"
    KYC_REJECTED = "kyc.rejected.v1"
    TRANSACTION_CREATED = "transaction.created.v1"
    TRANSACTION_FLAGGED = "transaction.flagged.v1"
    FRAUD_DETECTED = "fraud.detected.v1"
    LOAN_APPLICATION_CREATED = "loan.application.created.v1"
    LOAN_APPROVED = "loan.approved.v1"
    LOAN_REJECTED = "loan.rejected.v1"
    LOAN_DISBURSED = "loan.disbursed.v1"
    DOCUMENT_UPLOADED = "document.uploaded.v1"
    DOCUMENT_INDEXED = "document.indexed.v1"
    AGENT_EXECUTED = "agent.executed.v1"
    HUMAN_APPROVAL_REQUESTED = "approval.requested.v1"
    HUMAN_APPROVAL_RESOLVED = "approval.resolved.v1"
    COMPLIANCE_ALERT_CREATED = "compliance.alert.created.v1"
    SANCTIONS_HIT = "sanctions.hit.v1"


class DomainEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    version: int = 1
    tenant_id: str
    institution_id: str | None = None
    correlation_id: str
    producer: str
    occurred_at: str
    payload: dict[str, Any] = Field(default_factory=dict)

    @property
    def topic(self) -> str:
        return self.event_type.value.split(".")[0]