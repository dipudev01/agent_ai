# BFSI Compliance Architecture

> **Critical caveat:** presence of a control is **not** an attestation of
> compliance. Controls marked **[NEEDS LEGAL VALIDATION]** must be validated by
> institution counsel and an auditor before production sign-off.

## 1. Regulatory Coverage

| Regulation | Scope | Status |
|---|---|---|
| RBI KYC/AML Master Direction | KYC/AML/CFT, STR/CTR reporting | Controls built; **[NEEDS LEGAL VALIDATION]** |
| RBI AI/ML adoption guidance | Model governance, fairness, oversight | Controls built; **[NEEDS LEGAL VALIDATION]** |
| PCI DSS | Cardholder data | Architecture supports; scope TBD |
| SOC 2 | Trust services criteria | Controls map to SOC 2 Type II |
| ISO 27001 | ISMS | Controls map to Annex A |
| GDPR | EU data subjects | Controls built; DPA + SAR flows **[NEEDS LEGAL VALIDATION]** |
| India DPDP | Consent, purpose, data principal rights | Controls built; final rules **[NEEDS LEGAL VALIDATION]** |
| Model risk governance (SR 11-7 style) | Model inventory, validation, monitoring | Framework provided |

## 2. Compliance Subsystems

### KYC / AML / CFT
1. Onboarding workflow (KycAmlAgent): document collection → identity verification → sanctions screening → risk rating → approval.
2. Sanctions screening against OFAC/UN/EU lists (dedup/fuzzy + PEP flags).
3. AML: transaction monitoring rules + ML risk scoring; STR generation with evidence pack; CTR thresholds.
4. CDD/EDD tiers by risk rating; ongoing monitoring.

### Transaction Monitoring
- Rule set (velocity, structuring, geography, cash) + anomaly models.
- Flagged transactions → `transaction.flagged.v1` → Fraud Engine verdict → HITL for block/review.

### Fraud Detection
- Deterministic scoring engine (`backend/app/decisioning/fraud.py`) — approve/review/block.
- Verdicts recorded with evidence (signals list) for explainability and regulator queries.

### Regulatory Reporting
- Reporting service consumes domain events → forms reports (STR/CTR, liquidity, NPA).
- Reports are versioned, signed, and archived with full evidence linkage.

### Data Retention & Residency
- Retention classes: audit (7y), KYC records (per RBI), transaction (10y), raw documents (classified), model artifacts (per governance).
- Residency: tenant-scoped region affinity; residency enforced at storage; encryption keys in-residence region.

### Consent & Privacy
- Consent registry: purpose, scope, duration, withdraw flows (DPDP).
- Privacy rights: access, correction, erasure (with lawful-hold exceptions), portability.
- SAR automation via Compliance Agent + audit/evidence retrieval.

### Explainability & Model Governance
- Every decision returns reasons (rule evidence) and a `policy_version`/`model_version`.
- Model inventory, validation reports, monitoring (drift, performance), approval gates, retirement.
- Deterministic engines are versioned as policies; changes require governance approval.

### Auditability & Regulatory Evidence
- Hash-chained audit logs (immutable).
- Evidence packs = decision + inputs + masked context + model/policy version + approver.
- Regulatory export service generates a complete evidence pack for a given transaction/decision.

## 3. Controls Matrix

| Control ID | Control | Artifact | Validated? |
|---|---|---|---|
| C-01 | Sanctions screening on every onboarding | sanctions_screen tool, evidence log | **[NEEDS LEGAL VALIDATION]** |
| C-02 | Deterministic eligibility (no LLM authority) | decisioning/eligibility.py | ✔ |
| C-03 | HITL for high-risk actions | approval tickets | ✔ |
| C-04 | Audit immutability + hash chain | audit service + S3 object lock | ✔ |
| C-05 | PII masking in logs/prompts | pii.py | ✔ |
| C-06 | Data retention enforcement | retention jobs + classification | **[NEEDS LEGAL VALIDATION]** |
| C-07 | Consent records for processing | consent registry | **[NEEDS LEGAL VALIDATION]** |
| C-08 | Model inventory + validation | model registry | ✔ (framework) |
| C-09 | STR/CTR reporting | reporting service | **[NEEDS LEGAL VALIDATION]** |
| C-10 | Fair-lending fairness checks | bias monitoring on scores | **[NEEDS LEGAL VALIDATION]** |

## 4. Compliance by Design in Code

- `AuditLog` table is append-only; nightly job hash-chains and ships to S3 Object Lock.
- Decision engines carry `policy_version`; changing thresholds = new policy version + audit.
- Every agent run records `model_version` + `token_usage` + latency for model governance and FinOps.
- PII never stored raw in audit/prompt/log surfaces (`pii.mask_payload`).