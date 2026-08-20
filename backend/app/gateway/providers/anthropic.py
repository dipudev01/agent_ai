"""Anthropic Claude provider."""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.gateway.llm import LLMProvider
from app.gateway.models import LLMRequest, LLMResponse

_ROLE_MAP = {"system": "user", "assistant": "assistant", "user": "user", "tool": "user"}


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str) -> None:
        self._client = httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            timeout=settings.llm_timeout_seconds,
        )

    async def complete(self, request: LLMRequest) -> LLMResponse:
        system = " ".join(m.content for m in request.messages if m.role == "system")
        messages = [
            {"role": _ROLE_MAP[m.role], "content": m.content}
            for m in request.messages
            if m.role != "system"
        ]
        payload: dict = {
            "model": request.model,
            "system": system,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        resp = await self._client.post("/v1/messages", json=payload)
        resp.raise_for_status()
        data = resp.json()
        text = "".join(
            b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
        )
        return LLMResponse(
            text=text,
            model=request.model,
            provider=self.name,
            usage={
                "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
            },
            finish_reason=data.get("stop_reason", "stop"),
        )