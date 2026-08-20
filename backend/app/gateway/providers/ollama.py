"""Ollama provider for self-hosted / private / open-source models."""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.gateway.llm import LLMProvider
from app.gateway.models import LLMRequest, LLMResponse


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str | None = None) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url or settings.ollama_base_url,
            timeout=settings.llm_timeout_seconds,
        )

    async def complete(self, request: LLMRequest) -> LLMResponse:
        payload: dict = {
            "model": request.model,
            "messages": [m.model_dump(exclude_none=True) for m in request.messages],
            "stream": False,
            "options": {"temperature": request.temperature, "num_predict": request.max_tokens},
        }
        if request.tools:
            payload["tools"] = [t.model_dump() for t in request.tools]
        resp = await self._client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("message", {})
        return LLMResponse(
            text=msg.get("content") or "",
            model=request.model,
            provider=self.name,
            usage=data.get("eval_count") and {
                "completion_tokens": data["eval_count"],
                "prompt_tokens": data.get("prompt_eval_count", 0),
            }
            or {},
            finish_reason=data.get("done_reason", "stop"),
        )