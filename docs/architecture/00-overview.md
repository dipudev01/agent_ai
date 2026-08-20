# BFSI AI Agent Platform — Architecture Overview

## 1. Executive Summary

The BFSI AI Agent Platform is a **multi-tenant AI operating platform** for financial institutions. It is not a chatbot. It is a control plane that lets institutions run specialized AI agents (support, loans, fraud, KYC/AML, compliance, wealth, collections, ops) over their own data, within strict authorization, audit, and compliance boundaries.

The platform draws a hard line between:

- **Probabilistic AI** (LLM reasoning, conversation, summarization, extraction) — never authoritative for regulated decisions.
- **Deterministic decisioning** (rules, statistical models, policy engines) — the sole authority for credit, fraud, AML, and eligibility decisions, with human-in-the-loop for high-risk actions.

## 2. Architecture Principles (Quality Rules)

| Rule | Meaning |
|---|---|
| Security by design | Security controls are architectural, not bolted on. |
| Privacy by design | PII is masked/encrypted by default; retention enforced by policy. |
| Least privilege | Every call path resolves tenant + user + permissions before touching data. |
| Zero trust | No implicit trust inside the network; every call authenticated and authorized. |
| Defense in depth | WAF → gateway → auth → policy → tool authz → guardrails → audit. |
| Fail closed | Sensitive operations deny by default; explicit grant required. |
| Deterministic decisioning | Regulated financial decisions never depend on LLM output. |
| HITL for high-risk actions | Freezes, reversals, disbursements, write-offs require human approval. |
| No SPOF | Multi-AZ, multi-region, circuit breakers, DLQs. |
| No vendor lock-in | LLM gateway provider abstraction; infra is code. |
| Stateless services | Horizontal scale; state in Redis/Postgres/Kafka. |
| Async for long tasks | Agent runs, ingestion, decisioning are event-driven. |
| Strong tenant isolation | At every layer: API, DB, cache, object store, vector store, search, events, memory. |
| Full auditability | Every mutation, tool call, decision, and agent run is audited. |
| Explainable decisions | Decision engines return reasons; RAG returns citations. |
| Observable AI | Tokens, cost, latency, hallucination, retrieval quality are metrics. |
| Secure-by-default config | Placeholder secrets rejected at startup; production requires KMS. |

## 3. High-Level Architecture

```
                  +---------------------+
  Web / Mobile /  |  CDN + WAF          |    DDoS protection, bot mgmt, TLS
  API Clients     +----------+----------+
                             |
                  +----------v----------+
                  |  API Gateway        |   authn, rate limit, routing, versioning
                  +----------+----------+
                             |
                  +----------v----------+
                  |  AuthN/AuthZ        |   OIDC IdP, JWT, RBAC+ABAC, policy engine
                  +----------+----------+
                             |
                  +----------v----------+
                  |  Agent Gateway      |   guardrails, prompt injection, routing
                  +----------+----------+
                             |
                  +----------v----------+
                  |  Agent Orchestrator |   supervisor, delegation, workflows
                  +----------+----------+
                             |
                  +----------v----------+
                  |  Tool Authorization |   registry + RBAC + ABAC + OPA + HITL
                  +----------+----------+
                             |
                  +----------v----------+
                  |  Tools -> Decision Engines -> Core Banking / Fintech Systems
                  +----------+----------+
                             |
              +--------------+--------------+
              |                            |
    +---------v---------+       +----------v---------+
    | LLM Gateway       |       | RAG Pipeline       |
    | (routing, failover|       | (ingest → vector)  |
    |  cost, quotas)    |       +----------+---------+
    +-------------------+                  |
                                           v
                                  +--------+--------+
                                  | Vector Store     |
                                  +------------------+

   Cross-cutting: Events (Kafka) | Cache (Redis) | Postgres | Object Storage
                 Observability (OTel/Prom/Grafana) | Secrets (Vault/KMS) | Audit
```

## 4. Component Responsibilities & Communication

| Component | Responsibility | Communication |
|---|---|---|
| **WAF** | Block OWASP attacks, bot traffic, DDoS at edge | Inline, HTTP |
| **API Gateway** | AuthN, rate limiting, routing, versioning, correlation IDs | HTTP/REST + gRPC |
| **Identity Provider** | OIDC/OAuth2, MFA, federation with institution IdPs | OIDC |
| **AuthZ Policy Engine** | RBAC + ABAC + OPA decisions | REST to OPA / in-process |
| **Agent Gateway** | Input/output guardrails, prompt injection detection, routing to supervisor | In-process + events |
| **Agent Orchestrator** | Supervisor agent, delegation graph, workflow state, retries | In-process + Kafka |
| **Agent Runtime** | Executes agents, tool-call loop, memory, guardrails | In-process |
| **Agent Registry** | Register/discover agents, versioning, capabilities | DB |
| **Tool Registry** | Register/discover tools, schemas | DB |
| **Workflow Engine** | Durable multi-step workflows (KYC, loan, HITL) | Temporal/Airflow-style |
| **LLM Gateway** | Provider routing, failover, retry, token/cost tracking, quotas | gRPC/HTTPS to providers |
| **Model Router** | Tiered routing (fast/balanced/strong) by task | In-process |
| **RAG Pipeline** | Scan → parse → OCR → classify → chunk → embed → index | Async events |
| **Vector DB** | Semantic retrieval with tenant+doc ACL | gRPC/HTTPS |
| **Knowledge Graph** | Entity relationships (customer, account, transaction) | Graph DB (read) |
| **Feature Store** | Feature engineering + online/offline serving for models | gRPC |
| **Rules/Decision Engine** | Deterministic eligibility, policy rules | In-process, audited |
| **Fraud Engine** | Risk scoring, verdicts (approve/review/block) | Async + synchronous |
| **Risk Engine** | Credit risk, portfolio risk aggregation | Batch + sync |
| **Notification Service** | Email/SMS/push to customers | Kafka consumer |
| **Audit Service** | Append-only audit records, hash-chaining | Kafka consumer + DB |
| **Compliance Service** | Sanctions screening, regulatory reporting, evidence packs | Kafka + RAG |
| **HITL Service** | Approval tickets, resolver queues, timeout escalation | DB + events |
| **Event Bus (Kafka)** | Async decoupling, load leveling, replay | Kafka |
| **Cache (Redis)** | Sessions, rate limits, semantic cache, distributed locks | Redis protocol |
| **Postgres** | System of record: tenants, users, agents, runs, audit, approvals | SQL |
| **NoSQL (OpenSearch)** | Search, log analytics, vector index | REST |
| **Object Storage** | Documents (encrypted), model artifacts, audit archive | S3 API |
| **Secrets/KMS** | Keys, secrets, certificates, rotation | KMS/Vault |
| **Observability** | OTel traces, metrics, logs, dashboards, alerting | OTLP/Prometheus |

## 5. Design Decision Framework

Every decision in this document uses this template:

> **Decision** → **Reason** → **Alternatives** → **Trade-offs** → **Failure Modes** → **Scaling Strategy** → **Security Implications** → **Cost Implications**

Where a decision has no meaningful dimension, it is marked N/A rather than skipped.

## 6. Repository Map (implemented)

| Path | Contents |
|---|---|
| `backend/app/core` | Config, container, security (auth/pii/encryption/guardrails/rbac), telemetry |
| `backend/app/api` | v1 REST API: auth, chats, agents, tenants, documents, health |
| `backend/app/agents` | Base agent + lifecycle, registry, router, memory, supervisor, 17 specialists |
| `backend/app/gateway` | LLM gateway (providers: openai/anthropic/ollama/mock), routing |
| `backend/app/tools` | Registry, authz (RBAC+ABAC+OPA+HITL), financial tools |
| `backend/app/rag` | Pipeline (scan→embed→index), vector stores |
| `backend/app/decisioning` | Deterministic eligibility + fraud engines |
| `backend/app/events` | Domain event schemas, Kafka/local broker |
| `backend/app/services` | Audit, agent orchestration |
| `backend/app/db` | Models (tenant, user, agent, audit), async session w/ tenant scoping, Alembic |
| `infra/` | Docker, Terraform (aws/gcp/onprem), Kubernetes, Helm, CI/CD |
| `observability/` | Prometheus rules, Grafana dashboards |
| `security/` | OPA policies, guardrail policies |
| `frontend/` | Next.js console |

## 7. Cross-Cutting Concerns

- **Correlation IDs** propagate from WAF → gateway → services → events → logs → traces.
- **Idempotency keys** for all mutating APIs; consumers are idempotent.
- **Error standards**: RFC 9457 problem+json with stable `code` + `correlation_id`.
- **Retention**: audit 7 years (configurable), raw documents per classification, PII per DPDP/GDPR.
- **Data residency**: tenant-scoped region affinity; residency enforced at storage layer.