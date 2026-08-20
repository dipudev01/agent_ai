# FinOps & Cost Control

## 1. Cost Centers

| Cost | Biggest levers |
|---|---|
| LLM usage | tiered routing, semantic cache, prompt compression, quota |
| GPU | node autoscaling, quantization, batch, spot mix |
| Database | partitioning, compression, read replicas sizing, archive |
| Storage | lifecycle policies, tiering (hot→cold→glacier) |
| Network | egress minimization, regional affinity |
| Kubernetes | node autoscaler, right-sizing requests, bin-packing |
| Observability | metric cardinality control, log sampling, retention |

## 2. Controls

- **Per-tenant quotas**: token budget/month, LLM spend budget, storage quota, API call quota.
- **Per-agent budgets**: per-agent token caps; superusers exempt with approval.
- **Model routing based on cost**: fast tier for high-volume intents; strong tier only for low-volume complex tasks (`gateway/routing.py`).
- **Usage dashboards**: per-tenant, per-agent, per-model spend (Grafana FinOps dashboard).
- **Cost alerts**: budget burn alerts at 70/90/100%; auto-pause non-critical agents at cap.
- **Chargeback/showback**: per-tenant cost attribution → billing line items for institutions.

## 3. Cost Attribution

Every LLM call records `tenant_id` + `agent_key` + `model` + token counts
(`bfsi_llm_tokens_total{tenant}`). Attribution pipeline aggregates nightly to a
cost ledger (object storage) consumed by billing and FinOps.

## 4. Optimization Loops

1. Monitor spend by tier → shift intents to cheaper tiers.
2. Cache hit ratio → tune semantic cache.
3. Context size → prompt compression + conversation trimming.
4. GPU utilization → batch size, quantization, node sizing.

## 5. Failure Mode

A runaway loop in an agent can burn budget fast. Mitigations: per-agent token
cap (hard), tool-round cap (6), circuit breaker on repeated tool failures,
budget alerting, and `agent.executed.v1` events feeding real-time cost meters.