"""LLMGateway — the only interface the application talks to for LLM access.

The application is NEVER coupled to a provider SDK. Model routing, provider
failover, retries, token/cost tracking, and quotas all happen behind this
interface. Provider SDKs live only in app/gateway/providers/*.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.gateway.models import LLMRequest, LLMResponse


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse: ...


class LLMGateway(ABC):
    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse: ...

    @abstractmethod
    async def complete_with_fallback(self, request: LLMRequest) -> LLMResponse: ...

    @abstractmethod
    def track(self, request: LLMRequest, response: LLMResponse) -> None: ...