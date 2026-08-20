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

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
| ------ | ---------- |
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
