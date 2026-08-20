# Data Architecture

## 1. Data Platform Layers

```
   OLTP (Postgres) ── system of record: tenants, users, agents, audit, approvals
        │ CDC (Debezium) ──┐
        ▼                  ▼
   Event Stream (Kafka) ──► Data Lake (S3/object storage, Iceberg)
                              │
                              ▼
   Feature Store (online/offline) ─► Models
   Warehouse (Trino/Snowflake) ─► Reporting, Regulatory
   OpenSearch ─► Search + Vector + Log analytics
   Vector DB ─► RAG embeddings
```

## 2. 360 Views

| View | Composition |
|---|---|
| Customer 360 | Profile + accounts + loans + transactions + interactions + risk segments |
| Risk 360 | Credit risk + fraud signals + AML alerts + exposure |
| Transaction 360 | Transaction + context (device/geo) + fraud verdict + AML flags + audit |

Built via event streaming + periodic aggregation into the warehouse; served
online via read replicas + cache for agent tool access.

## 3. Ownership, Schemas, Partitioning

- **Ownership**: bounded-context ownership — each service owns its tables; cross-context reads via events/APIs (no shared tables).
- **Schemas**: versioned (JSON schema registry for events); DB migrations via Alembic expand/contract.
- **Partitioning**:
  - `transactions` — partitioned by month (transaction date).
  - `audit_logs` — partitioned by month, archived quarterly.
  - `agent_runs` — partitioned by month.
  - `events` — Kafka topics partitioned by `tenant_id` (per-tenant ordering).
- **Indexing**: indexes on `(tenant_id, resource_id)`, `(tenant_id, created_at)`, hot-path lookups (user by email, run by correlation). Partial indexes for active rows.

## 4. Retention & Archival

| Data | Retention | Archive |
|---|---|---|
| Audit | 7 years | S3 Object Lock (COMPLIANCE), hash-chained |
| Transactions | 10 years | Warehouse + object storage |
| KYC docs | per RBI + policy | Encrypted object storage, classified |
| Raw documents | classified (high 7y / low 5y) | Encrypted object storage |
| Conversations | 180 days (masked) | Warehouse |
| Model artifacts | per governance | Object storage |

## 5. Encryption, Backup, DR

- Encryption at rest (KMS), field-level PII encryption, object-store SSE.
- Backups: Postgres PITR (WAL archiving, 35-day), nightly snapshots to object storage, Kafka topic mirroring.
- DR: RPO ≤ 15 min (WAL), RTO ≤ 1 hour (active-passive multi-region); recovery drill quarterly.

## 6. Database Selection (Section 16)

| Workload | Chosen | Why | Alternatives | Trade-off |
|---|---|---|---|---|
| System of record, relational integrity | **PostgreSQL** | ACID, JSONB, pgvector, maturity, async driver | MySQL | Postgres better for JSON + extensions; MySQL faster for pure OLTP reads |
| Session/rate-limit/semantic cache, locks | **Redis** | sub-ms, TTL, pub/sub | Memcached | Memcached lacks data structures + pub/sub; Redis single-threaded → shard |
| Full-text + log + vector search | **OpenSearch** | KNN, analyzers, opensearch pipelines | Elasticsearch | Feature-identical forks; ES has more tooling |
| Vector store | **OpenSearch (kNN)** or pgvector | reuse infra / fewer moving parts | Pinecone, Qdrant, Milvus | OpenSearch kNN accuracy vs HNSW libs; start pgvector for simplicity |
| Event streaming | **Kafka/Pulsar** | durability, ordering, replay, ecosystem | RabbitMQ, NATS | Kafka heavier ops; RabbitMQ simpler but weaker replay/ordering |
| Document/vector heavy (alt) | **MongoDB** (if schema-flexible at scale) | document model | Postgres JSONB | Mongo adds a second DB family — avoid unless needed |
| Key-value at extreme scale (alt) | **DynamoDB/Cassandra** | horizontal KV scale | Redis cluster | No relational joins; only for specific high-volume stores |
| Data lake / warehouse | **Object storage + Iceberg + Trino** | cost-efficient lakehouse | Snowflake/BigQuery | Lakehouse = more engineering; managed = faster but pricier |
| Object storage | **S3/GCS** | durable, cheap, lifecycle rules | Azure Blob | region pinning |

**Decision → Reason → Alternatives → Trade-offs → Failure Modes → Scaling → Security → Cost**

> Single source of truth = Postgres. Redis for hot paths. Kafka for async. 
> OpenSearch for search+vectors+logs. Object storage for documents/archive.
> No database introduced for technology diversity — each serves a distinct
> workload class (relational/ACID, cache, stream, search/vector, blob).