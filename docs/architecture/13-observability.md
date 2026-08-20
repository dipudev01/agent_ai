# Observability Architecture

## 1. Pillars

- **Metrics**: Prometheus (API, DB, Redis, Kafka, LLM, agents, security, finops).
- **Logs**: centralized (Loki/OpenSearch), structured JSON, correlation IDs, PII-redacted.
- **Traces**: OpenTelemetry → OTLP collector → Jaeger/Tempo; spans tagged `tenant_id`, `user_id`, `agent_key`, `tool`, `model`.
- **AI observability**: token usage, model latency, model cost, agent success rate, tool failure rate, hallucination rate, RAG retrieval quality, guardrail rejections.

## 2. Instrumentation

- OTel SDK bootstrapped in `backend/app/core/telemetry.py`; FastAPI + httpx auto-instrumented.
- Custom metrics:
  - `bfsi_http_requests_total{status,route}`
  - `bfsi_llm_calls_total{provider,model}` / `bfsi_llm_tokens_total{provider,model,tenant}`
  - `bfsi_llm_latency_seconds` / `bfsi_llm_cost_estimate_total{tenant}`
  - `bfsi_agent_runs_total{agent,status}` / `bfsi_agent_success_rate`
  - `bfsi_tool_failures_total{tool}`
  - `bfsi_rag_retrieval_score` / `bfsi_rag_hits_total`
  - `bfsi_guardrail_rejections_total{type}`
  - `bfsi_security_denials_total{code}`
  - `bfsi_ratelimit_hits_total`
  - `bfsi_audit_sequence_timestamp` (compliance audit-stream health)
  - `bfsi_consumer_lag{consumer}`

## 3. Dashboards (per team)

| Team | Dashboard | Key panels |
|---|---|---|
| Engineering | latency, errors, saturation, traces | HTTP SLO burn, p95/p99, 5xx |
| Security | `security.json` | denials, guardrails, rate limits, audit progress |
| Compliance | audit integrity, approvals, retention | audit lag, HITL cycle time, evidence exports |
| AI/ML | `ai-ml.json` | model latency/cost, agent success, RAG quality, hallucination |
| Operations | infra health | pods, DB, Kafka, GPU pool, node autoscaler |
| Business | adoption, outcomes | conversations, completed decisions, approvals |

## 4. Alerting

Rules in `observability/prometheus/alerts.yml`: high error rate, LLM provider
degraded, token budget exceeded, agent success low, security denial spike,
audit stream hole, RAG quality low. Alertmanager → on-call (PagerDuty) +
security queue for security alerts.

## 5. SLO Monitoring

- Request latency SLO (p95 3s streamed) and availability SLO (99.9%) as Prometheus burn-rate alerts.
- Error budget tracking per tenant tier.