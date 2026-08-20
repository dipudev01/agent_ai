# Financial Decisioning Architecture

> **The core principle:** separate **LLM reasoning** from **deterministic
> financial decision logic**. Critical financial decisions (loan approval,
> credit scoring, fraud, AML, underwriting, segmentation) are produced by
> deterministic rules/models with configurable approval workflows. **The LLM
> narrates and assists; it never decides.**

## 1. Decision Engines

| Engine | Module | Output | HITL |
|---|---|---|---|
| Loan eligibility | `decisioning/eligibility.py` | eligible + score + max_amount + reasons | pre-approved offers need sign-off |
| Credit risk | credit-risk model (ML) | PD/score tiers | high exposure |
| Fraud | `decisioning/fraud.py` | approve/review/block + signals | block/review |
| Transaction risk | monitoring rules + model | risk score | freeze |
| AML alert | rules + model | alert + STR evidence | report |
| Insurance underwriting | underwriting rules | premium/accept-decline | high sum insured |
| Segmentation | clustering | segment id | none |

## 2. Deterministic vs Probabilistic Boundary

| Capability | Probabilistic (LLM) | Deterministic (Engine) |
|---|---|---|
| Understanding intent | ✔ | — |
| Extracting loan params from chat | ✔ (validated) | — |
| Eligibility decision | ✘ (never) | ✔ (engine) |
| Max loan amount | ✘ (never invents) | ✔ (engine) |
| Fraud verdict | ✘ (never) | ✔ (engine) |
| KYC sanctions result | ✘ (never) | ✔ (tool/service) |
| Regulatory narrative | ✔ (assist, cited) | — |

**Enforcement in code:**
- Eligibility tool returns a `decision` object with `policy_version`; the agent
  relays it verbatim (`loan_eligibility` agent's system prompt forbids computing
  scores itself).
- The eligibility tool is `sensitive=True` → requires an approval ticket for
  any presented offer.
- Fraud verdicts come from `score_transaction()`; agents only explain signals.

## 3. Loan Decision Flow (Section 27 trace)

```
Customer: "Can I get a ₹10 lakh personal loan?"
  → API /chats → authN → authZ (RBAC customer) → rate limit
  → Agent Gateway (guardrail on input)
  → Supervisor → route → loan_eligibility agent
  → Tool: get_customer_profile (masked)     [deterministic service data]
  → Tool: get_credit_report (masked)        [bureau]
  → Tool: check_loan_eligibility            [DETERMINISTIC ENGINE]
        ├─ eligibility rules (income, CIBIL, obligation ratio, DTI)
        ├─ score, max_amount, reasons[], policy_version
        └─ sensitive → approval_required for offer presentation
  → LLM narrates decision (never computes)  [probabilistic layer]
  → Response Guardrail (no invented figures)
  → Audit: agent run + decision + tool calls
  → Reply to user with deterministic outcome + next steps
```

## 4. Explainability

- Every decision returns structured `reasons` (rule name + pass/fail + detail).
- `policy_version`/`model_version` on every decision for governance.
- RAG answers require citations.
- HITL evidence packs bundle decision + inputs + masked context.

## 5. Configuration & Versioning

- Thresholds are configuration (per-institution override via tenant settings),
  gated by policy version.
- Changing a threshold = new policy version → audit + governance approval.
- No drift: engines are pure functions of inputs; no hidden state.