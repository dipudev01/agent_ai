# AI / ML Layer

## 1. Model Portfolio

| Class | Examples | Hosting | Purpose |
|---|---|---|---|
| Frontier LLMs | GPT-4o, Claude Sonnet | Managed API | complex reasoning, synthesis |
| Mid LLMs | GPT-4o-mini, Claude Haiku | Managed API | extraction, classification, routing |
| Small open models | Qwen2.5, Llama 3.2 | Self-hosted (vLLM, GPU pool) | high-volume, low-latency, cost control |
| Embedding models | miniLM, BGE, E5 | Self-hosted / API | RAG embeddings |
| Rerankers | Cohere Rerank, BGE-reranker | API / self-hosted | retrieval quality |
| Classification | TF-IDF → XGBoost, transformers | ML serving | intent, doc type, sensitivity |
| Fraud models | Gradient boosting, NN | ML serving | fraud probability |
| Credit-risk models | Scorecards, LR, GBM | ML serving | PD/EAD/LGD |
| Forecasting | Prophet, LSTM, GBM | batch | cash flow, demand, collections |

## 2. LLM Gateway Capabilities

`backend/app/gateway/*` implements: model selection, cost optimization, latency
optimization, provider failover, token tracking, usage quotas, model fallback,
evaluation hooks, prompt/model versioning. The application only talks to the
`LLMGateway` interface — provider SDKs are confined to `providers/`.

- **No vendor lock-in**: swap/add providers behind the interface; self-hosted
  models (Ollama/vLLM) are first-class providers.
- **Token tracking**: every call records usage → FinOps counters + per-tenant
  budgets.
- **Fallback chain**: strong → balanced → fast → mock (dev); provider health
  tracked; circuit breaker.

## 3. Model Governance

| Governance element | Mechanism |
|---|---|
| Model inventory | registry (model id, version, provider, owner, status) |
| Validation | offline evals + shadow testing before promotion |
| Monitoring | drift, performance, bias, hallucination rate, cost per model |
| Approval | promotion requires model governance sign-off |
| Retirement | versioned rollout; deprecated models blocked at routing |

## 4. Embeddings & Reranking

- Embedding service (self-hosted, batch) → vector store upsert with tenant + doc ACL metadata.
- Hybrid retrieval: dense (kNN) + sparse (BM25) → fusion → rerank → top-k.
- Retrieval quality metric (`bfsi_rag_retrieval_score`) feeds observability.

## 5. Feature Store

- Online features (real-time signals: velocity, avg amount) served to fraud/credit models.
- Offline features for training; point-in-time correctness to avoid leakage.
- Feature ownership per domain; versioned definitions.

## 6. Model Serving & Routing Decisions

> **Decision → Reason → Alternatives → Trade-offs → Failure Modes → Scaling → Security → Cost**

**Self-hosted small models for high-volume tasks**: Reason — cost at 1M+ users; frontier APIs at $/1k tokens are 50–100× more expensive than self-hosted for high-frequency intents. Alternatives — fully managed APIs (simpler). Trade-off — GPU ops burden. Failure — GPU pool outage → route to managed + mock fallback. Scaling — node pool autoscaling, batch inference, quantization. Security — model access control, prompt filtering before self-hosted models (they may have weaker guardrails). Cost — GPU ~$1–2/hr vs API per-token; break-even around sustained volume.