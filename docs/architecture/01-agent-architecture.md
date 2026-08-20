# Agent Architecture

## 1. Agent Inventory

| Key | Agent | Capabilities | Tools | Sensitive/HITL |
|---|---|---|---|---|
| `supervisor` | Supervisor/Orchestrator | orchestrate | — (delegates) | no |
| `customer_support` | Customer Support | support, general | get_customer_profile | no |
| `banking_assistant` | Banking Assistant | banking, product | get_customer_profile | no |
| `loan_eligibility` | Loan Eligibility | loan, eligibility, credit | profile, credit, eligibility | **HITL** |
| `credit_risk` | Credit Risk | credit, risk | credit, profile | no |
| `fraud_detection` | Fraud Detection | fraud | profile | **HITL** |
| `kyc_aml` | KYC/AML | kyc, aml, onboarding | sanctions_screen, kyc | **HITL** |
| `transaction_monitoring` | Transaction Monitoring | aml, transaction | profile | **HITL** |
| `financial_document` | Financial Document | document, rag | search_documents | no |
| `insurance` | Insurance | insurance | profile | no |
| `wealth` | Investment/Wealth | investment, wealth | profile | no (advisor-required for advice) |
| `collections` | Collections | collections, loan | profile | **HITL** (restructuring) |
| `compliance` | Compliance | compliance, regulatory | search_documents, sanctions | no |
| `regulatory_intelligence` | Regulatory Intelligence | regulatory | search_documents | no |
| `financial_research` | Financial Research | research, analysis | search_documents | no |
| `data_analysis` | Data Analysis | analysis, data | read-only query tool (prod) | no |
| `devops` | Developer/Operations | operations, devops | search_documents | no |

Implemented in `backend/app/agents/specialized/*`.

## 2. Agent Lifecycle

```
registered → discovered → routed → invoked → executed → evaluated → recorded → (versioned/rolled back)
```

1. **Registration** — agent registers with the `AgentRegistry` (key, capabilities, tools, version). Duplicate keys rejected.
2. **Discovery** — consoles and routers query `list_agents()` / `find_by_capability()`.
3. **Routing** — deterministic intent classification → capability matching → permission gate. The registry (not the model) picks the agent.
4. **Invocation** — `AgentInput` validated; prompt-injection guardrail runs first.
5. **Execution** — tool-call loop (max 6 rounds). Every tool call goes through `ToolAuthorization` (RBAC → ABAC → OPA → HITL).
6. **Evaluation** — post-hoc: outcome, tool success, latency, token cost, hallucination judge.
7. **Recording** — `AgentRun` row + audit event (idempotent on `run_id`).
8. **Versioning / rollback** — new versions are new registrations; rollback = repoint registry; runs always carry `model_version`.

## 3. Memory Architecture

| Memory | Backing store | Scope | TTL | Contents |
|---|---|---|---|---|
| Short-term | Redis | conversation+user | 15 min | recent turns |
| Long-term | Postgres | user | retention | durable facts, preferences, resolved intents |
| Shared | Kafka topics | agent run | run lifetime | inter-agent working memory (facts agreed by supervisor) |

Every memory key is namespaced `tenant_id:user_id:...`. No cross-tenant lookup is possible by construction.

## 4. Agent-to-Agent Communication

- Agents **do not hold references to each other**. The Supervisor delegates through the registry by key.
- Shared memory is written via the memory service; consumers read only what the supervisor grants.
- All delegation is recorded (`delegated_to`) and audited.

## 5. Tool Calling & Permission Model

1. Agent advertises tools via the LLM gateway tool schema.
2. LLM returns `tool_calls` → validated against the **Tool Registry** (unregistered tools rejected).
3. `authorize_tool_execution()` enforces, in order:
   - RBAC: required permission OR self-scoped equivalent for owned resources
   - ABAC: tenant match + ownership attributes
   - OPA: external policy for sensitive tools
   - HITL: approval ticket required for sensitive/high-risk tools
4. Tool runs inside the requesting user's tenant context. Result is PII-masked before it reaches the model.

## 6. Guardrails (both directions)

- **Input**: prompt-injection detector, tool-injection detector, size limits.
- **Output**: jailbreak detector, hallucination markers, structured-output validation, financial-figure cross-check against tool results.

## 7. Delegation, Evaluation, Rollback, Observability

- **Delegation**: Supervisor delegates by capability; a specialist can delegate to another specialist via shared memory + registry (supported, but recommended path is supervisor-mediated).
- **Evaluation**: per-run metrics (success, tools, tokens, latency, cost), offline evals (behavior, hallucination, RAG quality), regression suite.
- **Rollback**: agent version pinning; run history preserved.
- **Observability**: `agent_runs_total`, `agent_success_rate`, `tool_failure_rate`, token/cost per agent, traces per run.

## 8. Human Approval Workflows (HITL)

1. Sensitive tool executed → platform returns `needs_human_approval=true` + creates an approval ticket.
2. Ticket routes to the responsible role queue (compliance officer, fraud analyst, loan officer).
3. Resolver reviews evidence pack (decision object + reasons + masked context) and approves/denies with comment.
4. Outcome emitted as `approval.resolved.v1`; the original workflow resumes only on approval.
5. Timeout (`hitl_approval_timeout_hours`) escalates to a senior queue; never auto-approves.