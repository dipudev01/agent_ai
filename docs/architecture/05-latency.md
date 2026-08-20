# Low-Latency Architecture

## 1. Latency Budgets

| Path | P95 Budget | Primary levers |
|---|---|---|
| API Gateway | ≤ 10 ms | stateless edge, in-memory routing, connection pooling |
| Authentication | ≤ 50 ms (token verify) | JWT local verify + Redis session check |
| Agent orchestration (routing + guardrails) | ≤ 80 ms | in-process routing, cached agent specs |
| Retrieval (RAG) | ≤ 120 ms | vector index + cache + prefetch |
| Tool execution (read tools) | ≤ 100 ms | read replicas + cache; write tools async |
| LLM inference (streamed first token) | ≤ 1.5 s (fast tier), ≤ 4 s (strong) | tiered routing, quantization, streaming |
| **End-to-end conversational reply (streamed)** | **≤ 3 s (fast), ≤ 6 s (strong)** | everything above + streaming |

## 2. Caching Strategy

| Cache | Key | TTL | Purpose |
|---|---|---|---|
| Session/auth | `sess:{tenant}:{user}` | 15 min | skip DB on hot path |
| Request cache | `req:{path}:{hash}` | 5 s | idempotent GETs |
| Semantic cache | `sem:{tenant}:{embedding_hash}` | 1 h | identical/vector-near queries reuse responses |
| Model response cache | `llm:{provider}:{model}:{prompt_hash}` | configurable | deterministic/regulatory facts |
| Agent registry cache | `agents:{tenant}` | 60 s | routing metadata |
| Decision cache (read-only) | `elig:{hash}` | 15 min | repeated eligibility lookups |

## 3. Async & Parallelism

- **Async I/O everywhere** (asyncio + asyncpg + aiohttp). No blocking calls in handlers/agents.
- **Parallel tool execution**: independent tools run concurrently with a bounded fan-out (asyncio.gather with semaphore).
- **Streaming responses**: token streaming to clients (SSE) so perceived latency < first-token latency.
- **Event-driven**: long tasks (doc ingestion, decision workflows) decouple to Kafka consumers.

## 4. Model Routing (small/large)

`backend/app/gateway/routing.py` — tiered routing:

| Tier | Model | Use | Est. cost/1k in | Latency |
|---|---|---|---|---|
| fast | qwen2.5:1.5b / small open model | classification, summarization, extraction | $0.0001 | ~300 ms |
| balanced | gpt-4o-mini / claude-haiku | JSON extraction, tool routing | $0.00015 | ~700 ms |
| strong | gpt-4o / claude-sonnet | complex reasoning, doc synthesis | $0.005 | ~2 s |

Routing inputs: task type, sensitivity, tenant budget, cache hit, queue depth.

## 5. Inference Optimization

- Quantization (INT8/FP8) and batch inference on self-hosted GPU nodes.
- GPU inference: vLLM/TGI with continuous batching; dedicated node pool (`inference` pool in Terraform).
- Token optimization: prompt compression, conversation trimming, structured outputs, intent-scoped prompts.
- Pre-computation: eligibility, feature aggregates, and embedding caches computed ahead of queries.

## 6. Database & Network

- Read replicas for tool/read paths; write path via primary.
- Targeted indexes; connection pooling (`pool_size`/`max_overflow` in config).
- CDN for static content; edge caching for public marketing endpoints only (never PII).

## 7. Latency Failure Modes

| Mode | Effect | Mitigation |
|---|---|---|
| LLM provider slow | Budget breach | circuit breaker + failover + fast-tier fallback |
| Cache miss storm | DB pressure | request coalescing, local caches, read replicas |
| Long tool chain | >budget | parallel execution, bounded rounds, timeout |
| Cold GPU node | First-token spike | pre-warmed pools, warm-up requests |
| Network to object store | Retrieval spike | local/edge caching of hot documents