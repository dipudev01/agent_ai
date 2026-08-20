# Diagrams

Rendered in any Mermaid-compatible viewer (GitHub, VSCode Mermaid plugin,
Mermaid Live Editor). All diagrams are embedded in the associated section docs;
this file collects the canonical set.

## 1. System Context (section 02)

```mermaid
flowchart LR
  C[Customer] -->|chat| GW[API Gateway]
  O[Loan Officer] -->|review/approve| GW
  A[Admin/Compliance] -->|oversight| GW
  GW --> API[Agent Platform]
  API --> LLM[LLM Gateway]
  API --> ENG[Decision Engines]
  API --> RAG[Vector Store]
  API --> DB[(Postgres)]
  API --> EV[Event Stream]
  API --> AUD[Audit Vault]
  LLM --> P1[OpenAI]
  LLM --> P2[Anthropic]
  LLM --> P3[Self-hosted/vLLM]
  ENG --> BANK[Core Banking / Bureau]
```

## 2. Agent Architecture (section 01)

```mermaid
flowchart TB
  U[User] --> APIGW
  APIGW --> SUP[Supervisor Agent]
  SUP -->|route| AG1[Customer Support]
  SUP -->|route| AG2[Loan Eligibility]
  SUP -->|route| AG3[Fraud Detection]
  SUP -->|route| AG4[KYC/AML]
  SUP -->|route| AG5[Document]
  SUP -->|route| AG6[+ 12 more agents]
  AG1 & AG2 & AG3 & AG4 & AG5 --> REG[Agent Registry]
  REG --> TOOLS[Tool Registry]
  TOOLS --> AUTHZ[Authorization Boundary]
  AUTHZ --> TS[Tools: customer, document, compliance, financial, kyc]
  AUTHZ --> ENG[Deterministic Engines]
  AG2 --> MEM[(Memory: short/long/shared)]
```

## 3. Agent Lifecycle (section 01)

```mermaid
stateDiagram-v2
  [*] --> idle
  idle --> running: message received
  running --> waiting_tools: tool needed
  running --> waiting_hitl: sensitive action
  waiting_tools --> running: tool result
  waiting_hitl --> running: approval granted
  running --> completed: response sent
  running --> failed: guardrail/error
  completed --> idle
  failed --> idle
```

## 4. Security Trust Boundary (section 02)

```mermaid
flowchart LR
  subgraph Untrusted
    C[Client]
  end
  subgraph Perimeter
    GW[WAF + API Gateway]
  end
  subgraph Trusted
    API[Agent Platform]
    ENG[Decision Engines]
    DB[(Databases)]
  end
  C -->|TLS + token| GW -->|mTLS| API
  API -->|authz boundary| ENG
  API -->|tenant-scoped| DB
```

## 5. RAG Pipeline (section 09)

```mermaid
flowchart LR
  D[Document] --> SCAN[Malware Scan]
  SCAN --> PARSE[Parse/OCR]
  PARSE --> CLS[Classify type/sensitivity]
  CLS --> CHUNK[Chunk]
  CHUNK --> EMB[Embed]
  EMB --> VS[(Vector Store)]
  Q[Query] --> H[Hybrid Search]
  VS --> H
  H --> RR[Rerank]
  RR --> ACL[ACL Filter]
  ACL --> CTX[Validated Context]
  CTX --> LLM[LLM]
  LLM --> OUT[Cited Answer]
```

## 6. Loan Decision Flow (section 10 / 20)

```mermaid
sequenceDiagram
  participant C as Customer
  participant API as Agent Platform
  participant A as Loan Agent
  participant E as Eligibility Engine
  participant H as HITL
  C->>API: loan request
  API->>A: route
  A->>E: check_loan_eligibility (income, cibil, dti)
  E-->>A: score + max_amount + reasons + policy_version
  A->>H: sensitive offer -> approval ticket
  H-->>A: approved
  A-->>C: deterministic outcome + next steps
  API->>API: audit + events
```

## 7. Multi-Tenancy (section 15)

```mermaid
flowchart TB
  subgraph Tenant A
    A1[Users] --> A_DB[(DB rows tenant_a)]
    A1 --> A_RED[(Redis keys tenant_a)]
    A1 --> A_V[(Vector docs tenant_a)]
  end
  subgraph Tenant B
    B1[Users] --> B_DB[(DB rows tenant_b)]
    B1 --> B_RED[(Redis keys tenant_b)]
    B1 --> B_V[(Vector docs tenant_b)]
  end
  subgraph Platform
    GW[Gateway] -->|resolve tenant from token| T[Tenant Context]
    T --> A1
    T --> B1
  end
```

## 8. Event Architecture (section 12)

```mermaid
flowchart LR
  SVC1[Services] -->|events| K[Kafka]
  K -->|customer.*| C1[Customer Consumers]
  K -->|transaction.*| C2[Fraud/Monitoring]
  K -->|loan.*| C3[Loan Workflow]
  K -->|document.*| C4[Ingestion Worker]
  K -->|approval.*| C5[HITL Queue]
  K -->|dlq| DLQ[(Dead Letter)]
  C1 & C2 & C3 & C4 & C5 --> AUD[(Audit Vault)]
```

## 9. Observability (section 13)

```mermaid
flowchart LR
  API[API/Agents/Engines] -->|OTel| COL[OTel Collector]
  COL --> PR[Prometheus]
  COL --> TR[Jaeger/Tempo]
  COL --> LG[OpenSearch Logs]
  PR --> AL[Alertmanager]
  AL --> PD[PagerDuty/On-call]
  PR --> GR[Grafana Dashboards]
  TR --> GR
  LG --> GR
```

## 10. Deployment Topology (section 14)

```mermaid
flowchart TB
  ING[Ingress/WAF] --> SVC[Service]
  SVC --> DPL[Deployment - API]
  DPL --> HPA[HPA 3-50]
  DPL --> PDB[PDB minAvailable]
  DPL --> NET[NetworkPolicy deny-egress]
  DPL -->|read/write| PG[(Postgres)]
  DPL -->|cache| RD[(Redis HA)]
  DPL -->|events| KK[Kafka]
  DPL -->|search| OS[OpenSearch]
  GPU[GPU Node Pool - vLLM] -->|model calls| DPL
```

## 11. Multi-Region DR (section 07)

```mermaid
flowchart LR
  subgraph Region A
    AP1[API]
    PG1[(Postgres Primary)]
    KK1[Kafka]
  end
  subgraph Region B
    AP2[API reads]
    PG2[(Postgres Standby)]
    KK2[Kafka Mirror]
  end
  AP1 --> PG1
  PG1 -->|async WAL| PG2
  KK1 -->|mirror| KK2
  AP2 --> PG2
  GTM[Global Traffic Manager] --> AP1
  GTM --> AP2
  PG2 -.promote on failover.-> PG1
```

## 12. CI/CD Pipeline (section 14)

```mermaid
flowchart LR
  PR[Pull Request] --> CI[ruff + mypy + pytest + bandit + trivy]
  CI -->|main| BUILD[Build Image + SBOM]
  BUILD -->|tag| REG[Registry]
  REG --> STG[Deploy Staging]
  STG -->|tests pass| GATE[Prod Gate approval]
  GATE --> CANARY[Canary 5-25-100%]
  CANARY -->|SLO ok| FULL[Full rollout]
  CANARY -->|fail| RB[Rollback]
```

## 13. Fraud Decisioning (section 10)

```mermaid
flowchart TB
  TX[transaction.created.v1] --> FE[Fraud Engine]
  FE -->|signals + ML risk| SCORE[Score]
  SCORE -->|>= block_threshold| BLOCK[Block + HITL]
  SCORE -->|>= review_threshold| REVIEW[Review queue]
  SCORE -->|else| OK[Approve]
  BLOCK --> EV[fraud.detected.v1]
  REVIEW --> EV
  EV --> CMP[Compliance + Notification]
  EV --> AUD[Audit]
```

## 14. LLM Gateway Routing (section 08)

```mermaid
flowchart LR
  REQ[Request] --> R[Router]
  R -->|task type / budget / cache| CACHE{Semantic cache hit?}
  CACHE -->|yes| RESP[Return cached]
  CACHE -->|no| TIER{Route tier}
  TIER -->|fast| F[Fast model]
  TIER -->|balanced| B[Balanced model]
  TIER -->|strong| S[Strong model]
  F & B & S --> CB{Circuit breaker}
  CB -->|provider down| FAIL[Failover tier]
  FAIL --> MOCK[Mock fallback dev]
  CB --> OK[LLM response]
  OK --> COST[Track tokens + cost per tenant]
```

## 15. Compliance Evidence (section 03)

```mermaid
flowchart TB
  D[Decision] --> EP[Evidence Pack]
  EP --> AUD[Audit Log - append-only]
  AUD --> HC[Hash Chain Nightly]
  HC --> OL[S3 Object Lock - COMPLIANCE]
  OL --> EXP[Regulatory Export]
  C[Compliance Controls] --> MC[Control Matrix]
  MC --> VAL[Validation by counsel/auditor]
```

## 16. HITL Approval (section 20)

```mermaid
sequenceDiagram
  participant A as Agent
  participant T as Authz Boundary
  participant Q as Approval Queue
  participant O as Officer
  A->>T: sensitive tool call
  T->>Q: approval.requested.v1 (evidence pack)
  Q-->>O: review
  O-->>Q: approve / deny
  Q->>T: approval.resolved.v1
  T-->>A: proceed / blocked
  T->>AUD: audit record
```