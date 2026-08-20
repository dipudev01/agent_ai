# End-to-End Request Flows

## 1. Chat / Agent Run Flow

```
Client
  │  POST /api/v1/chats {message}   (X-Correlation-ID, Bearer token)
  ▼
Edge/API Gateway ── rate limit (token bucket per tenant/user) ── WAF ── TLS
  ▼
API service
  ├─ authN: verify JWT (local verify) → principal (tenant_id, user_id, roles)
  ├─ authZ: RBAC (endpoint permission) + ABAC (tenant match)
  ├─ correlation id + otel span start
  ▼
Agent Gateway (guardrail: input scan — PII, injection, PII-confidentiality)
  ▼
Supervisor Agent
  ├─ intent detection (fast tier model)
  └─ route → specialized agent (e.g., loan_eligibility)
        ▼
   Agent loop (max 6 tool rounds)
     ├─ tool: get_customer_profile  → repository → DB (tenant-scoped) → masked
     ├─ tool: get_credit_report     → bureau adapter (masked)
     ├─ tool: check_loan_eligibility → DETERMINISTIC engine (decision + reasons + policy_version)
     │     └─ sensitive → approval required (HITL ticket) for offer
     ├─ LLM narrates decision (strong tier, cited)  [never computes]
     └─ tool round guard: cap reached → fallback response
  ▼
Response Guardrail: output validation (no invented figures, no PII, no tools-called leakage)
  ▼
Audit: agent run record + tool calls + decision + events (agent.executed.v1)
  ▼
Streamed reply (SSE) → client
```

## 2. Document Upload → RAG Ingestion Flow

```
POST /api/v1/documents (multipart, ACL-validated)
  → malware scan (fail closed)
  → event document.uploaded.v1
  → ingestion worker:
       parse → OCR → classify (type/sensitivity/retention) → chunk
       → prompt-injection scan → embed → vector upsert (tenant + ACL tags)
  → event document.indexed.v1 → search-ready
Retrieval path: query → hybrid search (dense+BM25) → tenant + ACL filter
  → rerank → validated context → LLM (FinancialDocumentAgent) → cited answer
```

## 3. Fraud Decision Flow

```
transaction.created.v1 → Fraud Engine (deterministic signals + ML risk score)
  → verdict: approve | review | block   (+ signals, evidence)
  → if block: HITL approval ticket; if review: queue
  → event fraud.detected.v1 → compliance + notification
  → verdict recorded with policy/model version → audit
Agents can explain the verdict; they cannot change it.
```

## 4. Approval / HITL Flow

```
sensitive action requested → approval.requested.v1 → ticket (role-scoped)
  → officer reviews (evidence pack: decision + masked inputs + versions)
  → approval.resolved.v1 → resume/block workflow → audit record
```

## 5. Cross-Cutting on Every Request

- Correlation ID propagated (header → logs → spans → events).
- Tenant context resolved server-side; fail closed if absent.
- PII masked in logs/prompts/tool outputs.
- Rate limit + quota check before heavy work.
- Response validated by Pydantic + guardrails.