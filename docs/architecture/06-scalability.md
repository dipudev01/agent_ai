# Scalability Architecture

## 1. Scale Targets

| Milestone | Users | Peak RPS | Notes |
|---|---|---|---|
| S1 | 100 | ~5 | single node, dev deploy |
| S2 | 10,000 | ~500 | 3+ replicas, managed infra |
| S3 | 1,000,000 | ~20,000+ | multi-AZ, multi-region, HPA, sharded stores |

## 2. Stateless Services

All services are stateless; state lives in Redis/Postgres/Kafka. Instances can
be added/removed freely. Agent runs, tool calls, and sessions are safe to
relocate because they hold no in-memory state (memory is in the memory service).

## 3. Scaling Levers

| Layer | Mechanism |
|---|---|
| API/agent services | HPA (CPU/memory), Cluster Autoscaler |
| Queue | Kafka partitions per tenant; consumer groups scale consumers |
| Postgres | read replicas; partitioning; write scaling via schema design |
| Redis | cluster mode, shards |
| Kafka | partition count × broker count; tenant-keyed partitioning |
| OpenSearch | shards; warm/cold tiers |
| Object storage | natively elastic |
| Vector store | shard by tenant group; replica shards |
| GPU pool | node pool autoscaling |

## 4. Bottlenecks & Mitigations

| Bottleneck | Symptom | Strategy |
|---|---|---|
| DB writes (audit, runs) | latency spike at peak | async write path via Kafka; batch persistence; partitioning |
| LLM provider quota | 429s | quota budgeting, request coalescing, model downgrade |
| Token budget | cost explosion | per-tenant token budgets, semantic cache, prompt compression |
| Agent orchestration CPU | routing latency | in-process routing, cached specs, supervisor fast path |
| Redis hot keys (per-tenant limiter) | tail latency | local token buckets + periodic sync |
| GPU cold start | first-token spike | pre-warmed pools, warm-up, spot+on-demand mix |
| Cross-region replication | RPO breach | synchronous within region, async across regions |

## 5. Multi-Region Deployment

- **Active-active** for stateless read paths (API, RAG retrieval, cache); writes pin to home region for data residency.
- **Active-passive** for DB (primary region + standby) with promoted writes on failover.
- **Global traffic management**: DNS-based geo routing (Route 53/Cloud DNS); API gateway region affinity.
- Tenants are pinned to a region by `data_residency` (never silently moved).

## 6. Scaling Strategy Decisions

> **Decision → Reason → Alternatives → Trade-offs → Failure Modes → Scaling → Security → Cost**

**Partitioned audit/runs in Postgres**: Reason — unbounded growth kills index performance. Alternatives — TimescaleDB, archive-only. Trade-off — partition maintenance complexity. Failure — partition gaps → archiver job monitors. Scaling — monthly partitions + prune after retention. Security — partition ACLs by tenant hash to avoid cross-tenant table scans. Cost — storage grows linearly; use compressed column storage for archive.

**Kafka for async load leveling**: Reason — peak ingestion (transactions, events) must never block API. Alternatives — SQS/Kinesis. Trade-off — Kafka ops complexity. Failure — consumer lag → lag alerting + autoscale consumers. Scaling — partitions scale with brokers. Security — topic ACLs + TLS. Cost — broker instances are the largest infra cost; use tiered storage for older events.