# Roadmap

Seven phases toward an autonomous BFSI agent platform. Each phase is gated by
security/compliance sign-off and measurable SLOs.

## Phase 0 — Foundation (Weeks 0-2)
- [x] Monorepo scaffold, FastAPI + agent framework + gateway + RAG + tools +
      decision engines
- [x] Tests (53), ruff, mypy, Docker, compose, K8s, Terraform, Helm, CI/CD,
      OPA, observability, docs (all 22 architecture sections + threat model)
- [ ] Vault/KMS secrets wiring, real OpenSearch/Redis/Kafka in compose
- **Gate**: CI green, security review of authz boundary

## Phase 1 — Core Platform (Weeks 2-6)
- [ ] Real auth flows (SSO/OIDC, MFA) for staff
- [ ] API hardening (throttling, rate-limit tiers, error taxonomy)
- [ ] Audit evidence packs + regulatory export service
- [ ] Production infra on one cloud (Terraform apply)
- **Gate**: load test (p95 latency), DR drill, pen-test (non-LLM scope)

## Phase 2 — AI Agents GA (Weeks 6-10)
- [ ] Frontend console (login, chat, admin) — scaffold exists
- [ ] Real LLM wiring (OpenAI/Anthropic/self-hosted), tiered routing tuned
- [ ] Agent eval harness + hallucination gates for every agent
- [ ] HITL workflow UI for officers
- **Gate**: eval scores meet thresholds; guardrail rejection rate audited

## Phase 3 — BFSI Intelligence (Weeks 10-16)
- [ ] Core-banking adapters (loan origination, payments, ledger) via events
- [ ] Fraud + credit models trained on anonymized tenant data
- [ ] RAG on regulatory + policy + product corpus at scale
- [ ] Fairness/bias monitoring on decision engines
- **Gate**: decision engines validated by model risk team; explainability reports

## Phase 4 — Enterprise Security & Compliance (Weeks 16-22)
- [ ] ISO 27001 + SOC 2 audit readiness program
- [ ] GDPR / DPDP: consent registry, SAR automation, DPA
- [ ] OPA policy expansion (full ABAC + attribute governance)
- [ ] External pen-test + red team (LLM-specific)
- **Gate**: audit attestation; residual risk accepted by CISO

## Phase 5 — Multi-Region Scale (Weeks 22-30)
- [ ] Active-passive DR, GTM failover, residency-aware routing
- [ ] Scale to 1M users: partitioning, sharding, GPU autoscaling, FinOps
- [ ] Chaotic drills + SLO SRE practice
- **Gate**: scale + DR acceptance; FinOps unit economics

## Phase 6 — Autonomous Agent Platform (Weeks 30+)
- [ ] Agent self-improvement loop (evals → prompt/model tuning) with governance
- [ ] Cross-domain agent workflows (loan → KYC → fraud → disbursement)
- [ ] Advanced memory, personalization (privacy-preserving)
- [ ] Multilingual agents (Indic languages), voice channel
- **Gate**: autonomous workflows with full audit + human override at every decision

## Continuous (all phases)
- Threat model review each release; dependency + container scanning in CI.
- Cost optimization loops (FinOps) after each phase.
- Legal validation of all `[NEEDS LEGAL VALIDATION]` controls.