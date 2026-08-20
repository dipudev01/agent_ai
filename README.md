# BFSI AI Agent Platform

A production-grade, enterprise-scale, multi-tenant AI Agent Operating Platform for banks, NBFCs, insurance companies, payment companies, lending platforms, wealth-management firms, and financial institutions.

**Design stance:** This is an *AI operating platform*, not a chatbot. AI is used for conversation, reasoning, document understanding, and assisted workflows. Every regulated financial decision (credit, fraud, AML, eligibility) is executed by deterministic decision engines, rules, and models behind an explicit authorization layer. The LLM never directly touches production financial systems.

## Monorepo Layout

```
ai_agent/
├── backend/        # FastAPI services — API gateway, agent gateway, LLM gateway, RAG, decisioning
├── frontend/       # Next.js console (customer, ops, compliance, admin)
├── infra/          # Docker, Terraform, Kubernetes, Helm, CI/CD
├── security/       # OPA policies, guardrails, threat model inputs
├── observability/  # Prometheus, Grafana, OpenTelemetry, alerting
├── docs/           # Architecture, diagrams, threat model, roadmap
└── scripts/        # Dev/ops tooling
```

## Quick Start (local dev)

```bash
# 1. Backend (requires Python 3.12)
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# 2. Infrastructure (optional)
docker compose -f ../infra/docker/docker-compose.yml up -d postgres redis kafka opensearch

# 3. Tests
pytest
```

OpenAPI docs: `http://localhost:8000/docs`

## Key Documents

| Topic | Location |
|---|---|---|
| Architecture (22 sections) | `docs/architecture/00-overview.md` → `docs/architecture/20-request-flow.md` |
| Technology stack | `docs/architecture/technology-stack.md` |
| Mermaid diagrams (16) | `docs/architecture/diagrams.md` |
| Threat model (STRIDE) | `docs/threats/threat-model.md` |
| Implementation roadmap (7 phases) | `docs/roadmap/roadmap.md` |
| API spec | `backend/app/api/v1/openapi.json` (generated) |
| Event spec | `backend/app/events/schemas.py` |

## Non-Negotiable Design Rules

1. **No LLM → production system access without an authorization layer.** Every tool call is checked against a policy engine (OPA) and per-tenant ABAC rules.
2. **Deterministic decisioning for regulated decisions.** Loan approval, credit scoring, fraud, and AML decisions use rules/models with HITL approval; LLM output is advisory only.
3. **Fail closed** for sensitive operations.
4. **Strong tenant isolation** at API, service, DB, cache, object storage, vector store, search, events, and AI memory.
5. **No vendor lock-in.** All AI access goes through the LLM gateway provider abstraction.
6. **Full auditability.** Every agent execution, tool call, and decision is audited and explainable.
7. **Observable AI.** Token, cost, latency, hallucination, and retrieval-quality metrics are first-class.

## Compliance Notice

Architecture includes controls for RBI, PCI DSS, SOC 2, ISO 27001, GDPR, and India DPDP. Presence of a control is **not** an attestation of compliance — every control requiring institution-specific legal/compliance validation is marked **[NEEDS LEGAL VALIDATION]** in the docs. Engage counsel and an auditor before production sign-off.