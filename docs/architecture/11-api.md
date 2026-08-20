# API Architecture

## 1. REST Surface (v1)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/login` | — | password login → token pair |
| POST | `/api/v1/auth/refresh` | refresh | rotate access token |
| POST | `/api/v1/chats` | Bearer | run agent conversation |
| GET | `/api/v1/agents` | Bearer | agent registry discovery |
| GET | `/api/v1/agents/tools` | Bearer | tool catalog |
| POST | `/api/v1/tenants` | platform_admin | create tenant |
| POST | `/api/v1/tenants/{id}/users` | staff | create user |
| POST | `/api/v1/documents` | Bearer | upload → RAG ingestion |
| GET | `/api/v1/health/live` `/ready` | — | probes |

OpenAPI is generated from the FastAPI app (see `backend/app/api/v1`).

## 2. API Conventions

- **Versioning**: URL prefix `/api/v1`; breaking changes bump to `/api/v2`.
- **Idempotency**: `Idempotency-Key` header on mutating endpoints; stored result replayed.
- **Pagination**: cursor-based (`next_cursor`, `limit`) for list endpoints; offset only for small admin lists.
- **Filtering**: query params, whitelisted fields; tenant filter is never client-supplied.
- **Rate limiting**: gateway + in-app token bucket per (tenant, user, route); `Retry-After` on 429.
- **Request/response validation**: Pydantic schemas; strict `extra="forbid"` on event payloads.
- **Errors**: RFC 9457 `application/problem+json`: `{type, title, detail, code, correlation_id}`. Stable codes: `invalid_token`, `insufficient_permission`, `policy_denied`, `approval_required`, `rate_limited`, `tool_denied`, `guardrail_rejected`, `internal_error`.
- **Correlation IDs**: header `X-Correlation-ID` echo + propagation.
- **Distributed tracing**: OpenTelemetry; every span tagged `tenant_id`, `user_id`, `correlation_id`.

## 3. Internal gRPC

Use gRPC where beneficial (high-volume, typed, internal):
- Vector store (OpenSearch wrapper)
- LLM gateway (internal inference service)
- Decision engine service (risk scoring)
- Feature store lookups

REST for external + event-driven for async boundaries.

## 4. Security on API

- TLS everywhere; mTLS internal.
- OWASP API top-10 checklist enforced in review: broken object-level auth (tenant scoping), excessive data exposure (masking), mass assignment (Pydantic `extra=forbid`), rate limiting, injection, etc.

## 5. Response Validation

- Responses validated by Pydantic on the way out (`response_model`).
- Guardrail output validation before agent replies leave the platform.