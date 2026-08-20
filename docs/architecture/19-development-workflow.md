# Development Workflow

## 1. Developer Setup

```bash
# backend
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # fill secrets
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# tests
pytest                            # 53 passing
ruff check app tests
mypy app
```

## 2. Git Workflow

- Trunk-based: short-lived feature branches → PR → CI (ruff + mypy + pytest + bandit) → merge to `main`.
- Semantic commit messages (`feat:`, `fix:`, `docs:`, `security:`).
- Protected `main`; required CI + review; no direct pushes.

## 3. Local Development Services

`docker-compose up` starts Postgres, Redis, Kafka, OpenSearch, MinIO, OTel,
Prometheus, Grafana. Dev default points at these; tests use SQLite.

## 4. Code Review Checklist

- [ ] Tenant scoping on every query; no client-supplied tenant id.
- [ ] PII masked before logging/LLM/tool output.
- [ ] Every mutating op publishes an event + audit record.
- [ ] No sync I/O in async handlers; no SDK imports outside providers.
- [ ] Tools registered in `app/tools/registry.py` + authz rule present.
- [ ] Decision thresholds go through policy versioning, not code edits.
- [ ] Provider SDKs only under `app/gateway/providers/*`.
- [ ] New config has no default secret value.

## 5. Feature Development Flow

```
feature spec → DDD context → models + migration (expand) → service + repository
→ event(s) → tool (if agent-facing) → authz rule → tests → agent wiring
→ docs → PR → CI → staging → promote
```

## 6. Environment Variables & Secrets

`.env.example` documents every var. Prod secrets come from Vault/KMS via
External Secrets Operator; never committed. `change-me*` values are rejected at
boot (fail-fast).