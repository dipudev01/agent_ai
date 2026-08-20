# Threat Model (STRIDE)

Scope: the BFSI Agent Platform across all deployment targets. STRIDE per
asset class; mitigations map to controls in sections 02/03/15.

## Assets

- A1 Customer PII / financial data (transactions, balances, KYC docs)
- A2 Decision outputs (eligibility, fraud, credit, AML verdicts)
- A3 Model & prompt artifacts, embeddings, RAG corpus
- A4 Audit / evidence chain (integrity is a compliance requirement)
- A5 API tokens, session, encryption keys, secrets
- A6 Tenant configuration & isolation boundary
- A7 Event streams & consumer state
- A8 LLM provider credentials & spend budget

## Threats by Asset

### A1 Customer PII / financial data

| # | Threat | STRIDE | Entry | Mitigation |
|---|---|---|---|---|
| T01 | Cross-tenant data read | Info disclosure | API/DB/cache/vector | tenant scoping (15), ACL filters (09), tests |
| T02 | SQL injection | Tampering | query params | ORM params + no raw SQL, bandit |
| T03 | PII in logs/prompts | Info disclosure | logging, LLM context | pii.mask_payload (02) |
| T04 | Broken object-level auth | Info disclosure | document/tool API | resource ownership check in authz.py |
| T05 | Object storage misconfig | Info disclosure | S3/GCS | bucket policy tests, IAM least-privilege |

### A2 Decision outputs

| # | Threat | STRIDE | Entry | Mitigation |
|---|---|---|---|---|
| T06 | LLM fabricates decision numbers | Tampering/Repudiation | agent reply | deterministic engine authority (10), output guardrail |
| T07 | Tampered thresholds | Tampering | config/DB | policy versioning + audit + write authz |
| T08 | Decision reversal/replay | Spoofing | API retry | idempotency keys, event_id dedupe |

### A3 Model & RAG corpus

| # | Threat | STRIDE | Entry | Mitigation |
|---|---|---|---|---|
| T09 | Indirect prompt injection via documents | Tampering | ingestion | content injection-pattern scan (09), guardrails |
| T10 | Prompt injection in chat | Tampering | chat input | input guardrail + confidentiality rules (02) |
| T11 | RAG poisoning (bad docs) | Tampering | ingestion | malware scan, classification, ACL, provenance |

### A4 Audit / evidence

| # | Threat | STRIDE | Entry | Mitigation |
|---|---|---|---|---|
| T12 | Audit log tampering | Tampering/Repudiation | DB writes | append-only + hash chain + object-lock (03) |
| T13 | Audit stream hole (lost event) | DoS | event pipeline | seq monitoring, DLQ, retention replay |

### A5 Tokens, keys, secrets

| # | Threat | STRIDE | Entry | Mitigation |
|---|---|---|---|---|
| T14 | Secret leakage in repo/logs | Info disclosure | CI/logs | secret scanning, boot rejection of change-me, vault/KMS |
| T15 | Key exfiltration | Info disclosure | memory/copy | KMS envelope, no raw keys in app, rotation |

### A6 Tenant isolation

| # | Threat | STRIDE | Entry | Mitigation |
|---|---|---|---|---|
| T16 | Tenant spoofing | Spoofing | token | JWT signed + issuer/aud verified; tenant from principal only |
| T17 | Cache/vector key collision | Info disclosure | cache/search | namespaced keys, fail-closed ACL |

### A7 Events

| # | Threat | STRIDE | Entry | Mitigation |
|---|---|---|---|---|
| T18 | Event injection / spoofed event | Spoofing/Tampering | Kafka | mTLS + ACL, producer idempotence, schema validation |

### A8 LLM cost/credential

| # | Threat | STRIDE | Entry | Mitigation |
|---|---|---|---|---|
| T19 | API key abuse / spend abuse | DoS | gateway | per-tenant quotas, secret storage, circuit breaker |
| T20 | Prompt-injection-driven tool abuse | Elevation | agent loop | authz boundary mandatory (authz.py), HITL on sensitive tools |

## LLM-Specific Threats

- Jailbreak → tool action: blocked by tool authz (tool calls require permission regardless of model).
- Confidential data exfiltration via model: PII masked pre-context; prompt firewall; eval suite.
- Model hallucination in regulatory facts: retrieval-cited answers; guardrail rejects uncited financial claims.
- Data poisoning of fine-tunes: no training on production data; eval gating.

## Summary of Top Risks & Priority

1. **Cross-tenant leakage** (T01, T04, T17) — highest severity; mitigated by
   enforcement + test suite.
2. **LLM action authority** (T06, T20) — mitigated by deterministic boundary +
   authz + HITL.
3. **Audit integrity** (T12) — compliance-critical; hash chain + object lock.
4. **Injection via documents** (T09, T11) — ingest controls + guardrails.

## Residual Risk & Validation

- **[NEEDS LEGAL VALIDATION]** controls in 03 (sanctions, retention, consent,
  reporting) reduce legal risk only after auditor sign-off.
- Regular red-team including LLM-specific attacks; annual pentest; DPIA for
  PII processing.