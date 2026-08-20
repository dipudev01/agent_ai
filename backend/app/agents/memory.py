"""Agent memory: short-term (conversation), long-term (durable facts), and
shared (cross-agent working memory). All scoped by tenant + user. In production
the backing store is Redis (short-term, TTL) + PostgreSQL (long-term) and
Kafka topics (shared event memory)."""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.gateway.models import ChatMessage

SHORT_TERM_TTL_SECONDS = 900


@dataclass
class MemoryRecord:
    tenant_id: str
    user_id: str
    key: str
    value: dict
    scope: str = "short"  # short | long | shared


class AgentMemory:
    def __init__(self) -> None:
        self._short: dict[str, list[ChatMessage]] = {}
        self._long: dict[str, dict] = {}
        self._shared: dict[str, dict] = {}

    # ---- short-term ----
    async def get_short_term(self, conversation_id: str | None, tenant_id: str, user_id: str) -> list[ChatMessage]:
        if not conversation_id:
            return []
        key = f"conv:{tenant_id}:{user_id}:{conversation_id}"
        return self._short.get(key, [])[-10:]

    async def append(self, inp, reply: str, used_tools: list[str]) -> None:
        if not inp.conversation_id:
            return
        key = f"conv:{inp.tenant_id}:{inp.user_id}:{inp.conversation_id}"
        msgs = self._short.setdefault(key, [])
        msgs.append(ChatMessage(role="user", content=inp.message))
        msgs.append(ChatMessage(role="assistant", content=reply))
        self._short[key] = msgs[-20:]

    # ---- long-term ----
    async def put_long_term(self, tenant_id: str, user_id: str, key: str, value: dict) -> None:
        self._long[f"{tenant_id}:{user_id}:{key}"] = value

    async def get_long_term(self, tenant_id: str, user_id: str, key: str) -> dict | None:
        return self._long.get(f"{tenant_id}:{user_id}:{key}")

    # ---- shared (agent-to-agent working memory) ----
    async def put_shared(self, key: str, value: dict) -> None:
        self._shared[key] = value

    async def get_shared(self, key: str) -> dict | None:
        return self._shared.get(key)

    def snapshot(self) -> str:
        return json.dumps(
            {"short": {k: [m.model_dump() for m in v] for k, v in self._short.items()}},
            default=str,
        )