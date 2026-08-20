"""OpenAI-compatible provider (also serves Azure OpenAI, vLLM, Together, etc.)."""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.gateway.llm import LLMProvider
from app.gateway.models import LLMRequest, LLMResponse


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        self._api_key = api_key
        self._base_url = base_url or "https://api.openai.com/v1"
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=settings.llm_timeout_seconds,
        )

    async def complete(self, request: LLMRequest) -> LLMResponse:
        payload: dict = {
            "model": request.model,
            "messages": [m.model_dump(exclude_none=True) for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.tools:
            payload["tools"] = [
                {"type": "function", "function": t.model_dump()} for t in request.tools
            ]
        if request.json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = await self._client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()["choices"][0]
        msg = data["message"]
        return LLMResponse(
            text=msg.get("content") or "",
            tool_calls=[
                {"id": c["id"], "name": c["function"]["name"], "arguments": c["function"].get("arguments") or {}}
                for c in msg.get("tool_calls", [])
            ],
            model=request.model,
            provider=self.name,
            usage=resp.json().get("usage") or {},
            finish_reason=data.get("finish_reason", "stop"),
        )