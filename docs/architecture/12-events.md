# Event Architecture

## 1. Event Catalog

| Event | Topic | Producer | Consumers |
|---|---|---|---|
| `customer.created.v1` | customer | customer service | analytics, risk, RAG |
| `customer.updated.v1` | customer | customer service | analytics |
| `kyc.completed.v1` | kyc | KYC workflow | compliance, notification |
| `kyc.rejected.v1` | kyc | KYC workflow | notification, HITL |
| `transaction.created.v1` | transaction | core banking adapter | fraud engine, monitoring |
| `transaction.flagged.v1` | transaction | monitoring | fraud engine, HITL |
| `fraud.detected.v1` | fraud | fraud engine | HITL, compliance, notification |
| `loan.application.created.v1` | loan | loan workflow | eligibility, risk |
| `loan.approved.v1` | loan | decision workflow | disbursement, notification |
| `loan.rejected.v1` | loan | decision workflow | notification |
| `loan.disbursed.v1` | loan | disbursement | reporting, analytics |
| `document.uploaded.v1` | document | API | ingestion worker |
| `document.indexed.v1` | document | ingestion | search-ready signal |
| `agent.executed.v1` | agent | agent runtime | observability, finops, evals |
| `approval.requested.v1` | approval | decision workflows | HITL queue |
| `approval.resolved.v1` | approval | HITL | resume workflows |
| `compliance.alert.created.v1` | compliance | AML | compliance queue |
| `sanctions.hit.v1` | compliance | sanctions screen | HITL, reporting |

Schemas in `backend/app/events/schemas.py`.

## 2. Schema Registry & Versioning

- Events carry `event_type` (versioned suffix `.v1`) + explicit `version` field.
- A schema registry (Confluent/APICurio) validates producer/consumer compatibility; backward-compatible changes only (additive), breaking changes → new `.v2` event type + migration.

## 3. Ordering & Partitioning

- **Partition key = `tenant_id`** → per-tenant ordering preserved; global ordering not required.
- Within a tenant, events from a single entity (e.g., one loan) use `entity_id` in the key for strict ordering where needed.
- Out-of-order tolerance documented per consumer (most consumers are order-insensitive or rekey).

## 4. Delivery Semantics

- **At-least-once** is the contract. Exactly-once is approximated as at-least-once + **idempotent consumers** (dedupe by `event_id` unique index; replay-safe processing).
- Producer idempotence enabled (Kafka `enable_idempotence=true`, `acks=all`).

## 5. Replay & DLQ

- **Replay**: topics retained 7 days + snapshots in object storage for long-range rebuild.
- **DLQ**: failed events (poison messages) → `<topic>.dlq` with original payload + error; alert on DLQ depth; replay tooling.
- Consumer lag alerting (`bfsi_consumer_lag` metric).

## 6. Consumer Idempotency Pattern

```
on message(event):
    if event.event_id in processed_events: return   # dedupe (redis/unique index)
    process(event)                                    # atomic with claim
    mark_processed(event.event_id)
```