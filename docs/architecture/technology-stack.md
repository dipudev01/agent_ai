# Technology Stack

## 1. Backend

| Concern | Technology | Rationale |
|---|---|---|
| Language/Runtime | Python 3.12 + asyncio | async, rich AI ecosystem |
| Framework | FastAPI | typed, OpenAPI-native, async |
| ORM | SQLAlchemy 2.0 (async) | typed async ORM + Alembic |
| Migrations | Alembic | expand/contract |
| DB | PostgreSQL (+pgvector) | ACID + JSONB + vectors |
| Cache | Redis | TTL, data structures, pub/sub |
| Search/Vector | OpenSearch | kNN + BM25 + logs |
| Streaming | Kafka | durability, ordering, replay |
| LLM gateway | `app/gateway` | provider-agnostic, routing, failover |
| Task queue | Kafka consumers / Celery (backfill) | async processing |
| Config | pydantic-settings | typed env config |
| Validation | Pydantic v2 | schemas, contracts |

## 2. Frontend

| Concern | Technology |
|---|---|
| Framework | Next.js (App Router) |
| Language | TypeScript |
| UI | React + Tailwind |
| State | SWR/React Query |
| Streaming | SSE for agent replies |
| Charts | Recharts (dashboards) |

## 3. Observability

| Concern | Technology |
|---|---|
| Metrics | Prometheus |
| Logs | OpenSearch / Loki |
| Traces | OpenTelemetry → Jaeger/Tempo |
| Alerting | Alertmanager → PagerDuty |
| Dashboards | Grafana |

## 4. AI/ML

| Concern | Technology |
|---|---|
| LLM providers | OpenAI, Anthropic, Ollama, self-hosted (vLLM) |
| Embeddings | self-hosted (BGE/E5) / API |
| Rerank | Cohere/BGE |
| ML serving | SKLearn/GPU serving for fraud/credit |
| Feature store | Feast (offline/online) |
| Eval | custom harness + ragas |

## 5. Security

| Concern | Technology |
|---|---|
| Secrets | Vault / KMS + External Secrets Operator |
| Encryption | Fernet field-level + envelope KMS |
| Policy | OPA/Rego (`security/opa`) |
| SAST/DAST | bandit, trivy, ZAP |
| Network | mTLS (Istio at scale), NetworkPolicies |

## 6. Infrastructure

| Concern | Technology |
|---|---|
| Containers | Docker |
| Orchestration | Kubernetes (EKS/GKE/AKS) |
| IaC | Terraform (aws/gcp/onprem) |
| Packaging | Helm |
| GitOps | ArgoCD |
| CI/CD | GitHub Actions |
| Cloud | AWS, GCP, on-prem (hybrid) |

## 7. Frontend Tooling Notes

- Node 20+; pnpm; ESLint + Prettier; Vitest + Playwright (E2E).
- The scaffold in `frontend/` is the starting console: login → chat with the
  Supervisor, with API base from `NEXT_PUBLIC_API_URL`.