# AGENTS.md

## Commands

- Lint: `cd backend && ruff check app tests`
- Type check: `cd backend && mypy app`
- Tests: `cd backend && pytest`
- Run API: `cd backend && uvicorn app.main:app --reload --port 8000`
- Format: `cd backend && ruff format app tests`

## Conventions

- Backend is Python 3.12 + FastAPI + async (asyncio) + SQLAlchemy 2.0 async.
- Do NOT use sync DB/redis calls inside request handlers or agents.
- Every dependency is injected via `app.core.container` (dependency container) or FastAPI DI.
- Every mutating operation publishes an event and writes an audit record.
- Never import provider SDKs outside `app/gateway/providers/*`. App code talks to `LLMGateway` interface only.
- Never let an agent call a tool that isn't registered in `app/tools/registry.py` and authorized by `app/tools/authz.py`.
- Multi-tenant: every query filters by `tenant_id` via `app/db/session.py` tenant scoping; never trust client-supplied tenant id.
- No secrets in code. All config via `app/core/config.py` + env.
- No comments unless they explain a non-obvious security or correctness invariant.
- Follow DDD bounded contexts under `app/services/`; infrastructure lives in `app/infra-like` modules (db, events, gateway, vector).
- SQLAlchemy models in `app/db/models/`, Alembic migrations in `app/db/migrations/`.

## Security Rules

- AuthZ: every request must resolve tenant + user + permissions before touching data.
- PII: mask/log-redact via `app/core/security/pii.py`; field-level encryption via `app/core/security/encryption.py`.
- Tool authorization: `require_permission()` before tool execution; OPA policy check for sensitive tools.
- Secrets: use vault/KMS in prod; never log tokens or keys.
- Rate limit every public endpoint; correlation ID on every request.