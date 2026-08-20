# Security Architecture

> **Design stance:** Security is first-class. The single most important rule:
> **an LLM never reaches a production financial system without an explicit
> authorization layer.** Every tool call is authorized by RBAC → ABAC → OPA →
> HITL before execution (`backend/app/tools/authz.py` is the only enforcement
> point).

## 1. Trust Boundary (Section 22)

```
Client
 → WAF (OWASP CRS, bot mgmt, DDoS)
 → API Gateway (TLS, rate limit, authn, routing)
 → AuthN (OIDC/JWT)
 → Policy Engine (RBAC + ABAC + OPA)
 → Agent Gateway (guardrails, prompt injection)
 → Agent Orchestrator (supervisor)
 → Tool Authorization (registry + RBAC + ABAC + OPA + HITL)
 → Tool
 → Core Banking / Fintech System
```

An agent cannot bypass any layer. Tool authorization is a distinct enforcement
point that agents cannot call around.

## 2. Zero Trust

- mTLS between services (service mesh or SPIFFE/SPIRE).
- Service-to-service tokens with short TTL and per-service scopes.
- Network policies (see `infra/kubernetes/security.yaml`) — deny-by-default egress.
- No trusted network segments; every request re-authenticated.

## 3. Identity & Access

- **AuthN**: OAuth2/OIDC with an enterprise IdP (Keycloak/Auth0/ADFS). JWT access tokens (15 min) + refresh tokens (7 days, revocable, hash-stored). MFA for staff.
- **RBAC**: role → permission matrix (`app/core/security/rbac.py`).
- **ABAC**: attribute conditions — tenant match, ownership, data sensitivity.
- **Fine-grained authorization**: per-resource grants for documents (document-level ACL), per-tool permissions, per-agent capabilities.

## 4. API Security

- TLS 1.2+ everywhere; HSTS; mTLS for internal.
- Rate limiting per (tenant, user, route) at gateway + in-app middleware.
- Request/response schema validation (Pydantic + OpenAPI).
- Idempotency keys for mutating endpoints.
- Correlation IDs; no secrets in logs (PII masking before logging).

## 5. Cryptography

| Layer | Mechanism |
|---|---|
| In transit | TLS 1.2+; mTLS internal |
| At rest | KMS-managed disk encryption (EBS/PD/DB) |
| Field-level | Fernet encryption for PII columns (`app/core/security/encryption.py`) |
| Tokenization | PAN → token via token vault; raw PAN never in app DB |
| Key rotation | KMS auto-rotation; Fernet key ring with rotation window |
| Secret rotation | Vault dynamic secrets; automated rotation jobs |

**Decision → Reason → Alternatives → Trade-offs → Failure Modes → Scaling → Security → Cost**

> Fernet for field-level encryption: simple, audited, symmetric, KMS-keyed.
> Alternatives: envelope encryption with per-field keys (stronger, heavier),
> tokenization (best for PAN but requires vault). Trade-off: Fernet adds a
> ciphertext-vs-plaintext size overhead and makes indexing encrypted columns
> impossible — encrypted PII columns are non-searchable (search uses masked
> copies or HMAC blind indexes). Failure: lost key = data loss → KMS recovery +
> key ring. Scaling: stateless; KMS is the bottleneck → KMS quota management.
> Security: fine. Cost: negligible CPU, KMS call per field batch.

## 6. PII & Data Loss Prevention

- PII detection at ingestion (regex + model classifiers).
- PII masking at every boundary: logs, traces, prompts, audit, agent tool output.
- DLP: exfiltration detection on model output (email/PAN/IPA patterns in replies), download anomaly detection, object-store leak prevention policies.

## 7. AI-Specific Security

| Threat | Control |
|---|---|
| Prompt injection | Guardrail detector + system-prompt hardening + model judges |
| Tool injection | Unregistered tool rejection; arguments schema-validated |
| Data exfiltration | Output guardrails; masked tool results; DLP monitors |
| Jailbreak | Output jailbreak detector; canary prompts; red-team tests |
| Model access control | Per-tenant/provider/model entitlement; quota |
| Model output validation | Structured validation; citation checks; decision cross-checks |
| Hallucination | RAG citation requirement; figure cross-check vs tool results; judge |
| Indirect injection via documents | Document content scanned for injection patterns before chunking |

## 8. Audit, Monitoring, SIEM

- Audit logs are **append-only, write-only** from the app; hash-chained and shipped to immutable S3 Object Lock (`COMPLIANCE` mode) for tamper-evidence.
- Immutable security logs stream to SIEM (Splunk/Sentinel/Elastic).
- Threat detection: anomaly on auth failures, rate-limit bursts, tool denials, large model output, cross-tenant attempts.
- Alerting: `security/` + `observability/prometheus/alerts.yml`.

## 9. Fail-Closed Guarantees

- Unknown tool → denied (`tool_not_found`).
- Unknown agent → refused.
- Sensitive tool without approval ticket → `approval_required`.
- Cross-tenant resource → `policy_denied` / `ownership_required`.
- Placeholder secrets → app refuses to start.

## 10. [NEEDS LEGAL VALIDATION] — Control Sign-off

The following require institution-specific validation before production:
- PCI DSS scope & SAQ determination for cardholder data flows.
- DPDP consent architecture (purpose limitation, consent records).
- GDPR Article 22 (automated decision-making) applicability to eligibility outcomes; rights to explanation/objection.
- RBI KYC/AML master direction details (UCC, reporting timelines, STR timelines).
- Cross-border data transfer mechanisms under India DPDP.
- Model risk governance alignment with RBI guidelines on AI/ML adoption.