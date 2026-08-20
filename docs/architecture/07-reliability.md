# Reliability Architecture

## 1. Targets

| Metric | Value | Notes |
|---|---|---|
| SLO (availability) | 99.9% monthly | API platform |
| SLA | 99.9% (standard), 99.95% (premium tier) | contract-dependent |
| RTO | ≤ 1 hour | full-region failover |
| RPO | ≤ 15 minutes | WAL/stream replication |

## 2. Fault-Tolerance Patterns

| Pattern | Implementation |
|---|---|
| Circuit breaker | LLM providers, downstream core-banking adapters; open on repeated failure, half-open probe |
| Retries + exponential backoff | tenacity in LLM gateway; Jitter; idempotent retries |
| Timeouts | LLM (60s default), tool calls (bounded), DB (statement_timeout) |
| Bulkheads | per-tenant thread/task pools + connection pools; one noisy tenant can't starve others |
| Idempotency | `Idempotency-Key` header; consumers keyed by event `event_id` |
| Distributed locks | Redis Redlock for scheduled jobs (retention, reporting) |
| Dead-letter queues | Kafka DLQ topics + replay tooling |
| Backpressure | bounded queues + explicit rejection (429/503); streaming token backpressure |
| Graceful degradation | degrade LLM tier on outage (mock last resort), serve read-only degraded mode |
| Health checks | liveness/readiness/startup probes (k8s) |
| Multi-AZ | deployment across ≥3 AZs; PDB minAvailable |
| Multi-region failover | active-passive DB, GTM switch |

## 3. Idempotency Contract

- **API**: `Idempotency-Key` required on mutating endpoints; duplicate key returns the original result (Redis-backed).
- **Consumers**: at-least-once delivery; consumers dedupe by `event_id` (unique index). Exactly-once is approximated (at-least-once + idempotent processing), which is the accepted trade-off for Kafka.
- **Agent runs**: `run_id` unique — retried agent invocations never double-record.

## 4. Disaster Recovery

```
                  ┌───────────────────────────┐
                  │   Region A (primary)      │
                  │   API + Postgres + Kafka  │
                  └──────────┬────────────────┘
                             │ async replication (RPO ≤ 15m)
                  ┌──────────v────────────────┐
                  │   Region B (standby)      │
                  │   API (active reads)      │
                  │   Postgres standby        │
                  │   Kafka mirror (active)   │
                  └───────────────────────────┘
   Failover: GTM flip → promote DB → resume consumers (RTO ≤ 1h)
```

- Quarterly DR drills with measured RTO/RPO.
- Backup verification (restore drills), point-in-time recovery for data corruption.
- Object storage cross-region replication for audit/documents with lifecycle rules.

## 5. Runbooks (Docs/Operations)

- Incident severity matrix (SEV1 platform down / SEV2 degraded / SEV3 cosmetic).
- On-call rotation, escalation to senior engineer + security for security events.
- Playbooks: LLM provider outage, DB failover, consumer lag, token budget breach, security incident.