# Testing Strategy

## 1. Test Pyramid

| Layer | Tooling | Coverage targets |
|---|---|---|
| Unit | pytest | engines, guardrails, pii, rbac, authz, providers |
| Integration | httpx ASGI + aiosqlite | API lifecycle, auth flows, RAG pipeline, event broker |
| Contract | Pact | partner/institution APIs |
| API | OpenAPI schema validation | request/response conformance |
| E2E | Playwright + running stack | customer journey, admin consoles |
| Load | Locust | throughput, latency budgets |
| Stress | Locust + chaos | degradation behavior, recovery |
| Chaos | Chaos Mesh / Gremlin | pod kill, latency injection, partition |
| Security | bandit, trivy, pip-audit, ZAP | SAST, container scan, dependency audit, DAST |
| Penetration | external pentest | OWASP API/LLM top-10, red team |
| AI eval | harness | hallucination, prompt injection, agent behavior |
| RAG eval | ragas | retrieval quality, citation integrity |

Implemented: `backend/tests/{unit,integration,security,load,ai_eval}`.

## 2. AI-Specific Testing

- **Prompt injection tests**: adversarial input suite must be rejected by guardrails.
- **Agent behavior tests**: routing/delegation/tool-call assertions with the scripted mock provider.
- **RAG evaluation**: MRR/nDCG on curated queries; citation-fidelity checks; ACL-leak tests (tenant B query never returns tenant A docs).
- **Hallucination tests**: response must cite or decline; financial figures must match tool output.
- **Model evaluation**: offline evals before promotion; shadow-mode comparisons; bias checks on score distributions.

## 3. Security Testing

- Unit: authz fail-closed matrix (unknown tool, insufficient permission, cross-tenant, missing approval).
- DAST: ZAP on staging; SAST: bandit in CI; container: trivy; deps: pip-audit.
- Fuzz: hypothesis on schemas/parsers (document ingestion).
- Regular external pentest + red-team (incl. LLM-specific attacks).

## 4. Load & Stress Targets

| Test | Profile | Pass criteria |
|---|---|---|
| Load | 1k–20k RPS on /chats | p95 end-to-end ≤ 3s (streamed), error < 0.1% |
| Stress | 2× peak | graceful 429/503, no crash, recovery ≤ 2 min |
| Chaos | kill 30% pods / inject latency | SLO preserved, circuit breakers engage |

## 5. CI Integration

Runs in `infra/ci/github-actions/ci.yml`; coverage gate ≥ 80% on decisioning +
authz modules (critical paths).