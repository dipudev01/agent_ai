# Development Architecture

## 1. Clean Architecture / DDD

Layers (dependency direction inward):

```
domain (decision engines, entities)  ← no infra imports
  ↑
application (services: agent_service, audit)  ← orchestration
  ↑
infrastructure (db, events, gateway, vector, providers)  ← imports domain+application
  ↑
presentation (api, middleware, main)
```

## 2. Bounded Contexts

| Context | Lives in | Owns |
|---|---|---|
| Identity & Tenancy | `app/services`, `app/db/models/tenant,user` | tenants, users, roles, sessions |
| Agent Platform | `app/agents`, `app/tools` | agents, runs, tools, memory, authz |
| AI Gateway | `app/gateway` | LLM providers, routing, models |
| RAG | `app/rag` | ingestion, vector, retrieval |
| Decisioning | `app/decisioning` | eligibility, fraud, risk engines |
| Compliance/Audit | `app/services`, `app/events` | audit trail, evidence, domain events |

Contexts communicate via events/APIs, never shared tables (no distributed monolith).

## 3. Repository & DI

- **Repository pattern**: data access through repositories; no SQL in services.
- **Dependency injection**: `app/core/container.py` provides LLMGateway, EventBroker, VectorStore; FastAPI DI for request-scoped deps.
- **Event-driven boundaries**: side effects emit events; consumers implement reactions.

## 4. Shared Libraries

| Library | Purpose |
|---|---|
| `app/core/security` | auth, pii, encryption, guardrails, rbac (importable everywhere) |
| `app/core/telemetry` | logging + OTel bootstrap |
| `app/events/schemas` | canonical event contracts (schema registry) |

## 5. Configuration Management

- pydantic-settings, env-driven, per-environment files (`values-*.yaml`, `.env.*`).
- Secrets via Vault/KMS; feature flags via config.
- No config drift: helm values are the source for runtime config; app config validated at boot.

## 6. API Contracts

- OpenAPI (generated) is the contract for REST; JSON schema registry for events.
- Contract tests protect consumers (Pact-style for partner APIs).

## 7. Anti-Patterns Avoided

- No global mutable state (except read-only registries).
- No service→service object references; registry/key lookup only.
- No sync I/O in async paths.
- No LLM SDK imports outside `app/gateway/providers`.