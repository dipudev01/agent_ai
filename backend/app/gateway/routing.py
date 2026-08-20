"""Model routing policies: select provider+model per request based on task,
cost, latency, tenant quota, and sensitivity. This is a cost/latency optimizer —
never a correctness authority. Sensitive/regulated decisions never depend on
these models for the final output (see decisioning/)."""

from __future__ import annotations

from dataclasses import dataclass

from app.gateway.models import LLMRequest

TIER_FAST = "fast"       # small, cheap, low-latency — summaries, classification
TIER_BALANCED = "balanced"
TIER_STRONG = "strong"   # large model — complex reasoning, doc extraction


@dataclass(frozen=True)
class Route:
    provider: str
    model: str
    tier: str
    est_cost_per_1k_in: float
    est_latency_ms: int


ROUTES: dict[str, Route] = {
    TIER_FAST: Route("ollama", "qwen2.5:1.5b-instruct", TIER_FAST, 0.0001, 300),
    TIER_BALANCED: Route("openai", "gpt-4o-mini", TIER_BALANCED, 0.00015, 700),
    TIER_STRONG: Route("openai", "gpt-4o", TIER_STRONG, 0.005, 2000),
}


def route_for(request: LLMRequest) -> Route:
    """Choose a route. Extend with tenant budgets, cache hits, and queue depth."""
    if request.tools:
        return ROUTES[TIER_STRONG]
    if request.json_mode:
        return ROUTES[TIER_BALANCED]
    return ROUTES[TIER_FAST]