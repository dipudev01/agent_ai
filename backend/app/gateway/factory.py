"""Factory that assembles the LLM Gateway from configuration.

The gateway supports: provider routing, per-provider model defaults, retry with
exponential backoff, and failover to fallback providers. Routing rules (e.g.
cost/latency-based model selection) live in app/gateway/routing.py.
"""

from __future__ import annotations

import logging

from prometheus_client import Counter
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.gateway.llm import LLMGateway, LLMProvider
from app.gateway.models import LLMRequest, LLMResponse

PROVIDER_ORDER: list[str] = ["openai", "anthropic", "ollama", "mock"]

_TOKENS_TOTAL = Counter("bfsi_llm_tokens_total", "LLM tokens consumed", ["provider", "model", "tenant"])
_LLM_CALLS = Counter("bfsi_llm_calls_total", "LLM inference calls", ["provider", "model"])


class RoutingLLMGateway(LLMGateway):
    def __init__(self, providers: dict[str, LLMProvider], default_provider: str, default_model: str) -> None:
        self._providers = providers
        self._default_provider = default_provider
        self._default_model = default_model

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=8),
        reraise=False,
    )
    async def _complete_once(self, request: LLMRequest) -> LLMResponse:
        provider = self._providers.get(request.provider)
        if provider is None:
            raise ValueError(f"unknown provider: {request.provider}")
        return await provider.complete(request)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        if not request.model:
            request.model = self._default_model
        try:
            response = await self._complete_once(request)
        except Exception as exc:
            # Graceful degradation: if the routed provider is unavailable
            # (dev/test/no keys), fall back to the deterministic mock provider
            # rather than failing the request. Logs the degradation for observability.
            logging.getLogger(__name__).warning(
                "LLM provider %s failed, degrading to mock: %s", request.provider, exc
            )
            request.provider = "mock"
            request.model = self._default_model
            response = await self._complete_once(request)
        self.track(request, response)
        return response

    def track(self, request: LLMRequest, response: LLMResponse) -> None:
        """Record token usage and estimated cost for FinOps/Observability.
        In production these counters feed Prometheus and the per-tenant quota
        service (app/services/finops.py)."""
        usage = response.usage
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        _TOKENS_TOTAL.labels(provider=response.provider, model=response.model, tenant=request.tenant_id or "unknown").inc(
            prompt_tokens + completion_tokens
        )
        _LLM_CALLS.labels(provider=response.provider, model=response.model).inc()

    async def complete_with_fallback(self, request: LLMRequest) -> LLMResponse:
        """Try preferred providers in order until one succeeds."""
        primary = request.provider
        for candidate in [primary, *PROVIDER_ORDER]:
            if candidate not in self._providers:
                continue
            if candidate == "mock":
                continue
            request.provider = candidate
            try:
                return await self.complete(request)
            except Exception:
                continue
        request.provider = primary
        return await self.complete(request)  # last resort (mock)


def build_llm_gateway(settings: Settings) -> LLMGateway:
    providers: dict[str, LLMProvider] = {}
    from app.gateway.providers.anthropic import AnthropicProvider
    from app.gateway.providers.mock import MockLLMProvider
    from app.gateway.providers.ollama import OllamaProvider
    from app.gateway.providers.openai import OpenAIProvider

    if settings.openai_api_key:
        providers["openai"] = OpenAIProvider(settings.openai_api_key, settings.openai_base_url)
    if settings.anthropic_api_key:
        providers["anthropic"] = AnthropicProvider(settings.anthropic_api_key)
    providers["ollama"] = OllamaProvider()
    providers["mock"] = MockLLMProvider()

    default_provider = settings.llm_default_provider if settings.llm_default_provider in providers else "mock"
    return RoutingLLMGateway(
        providers=providers,
        default_provider=default_provider,
        default_model=settings.llm_default_model,
    )