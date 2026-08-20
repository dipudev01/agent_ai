from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: str | None = None


class ToolSpec(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class LLMRequest(BaseModel):
    model: str
    provider: str
    messages: list[ChatMessage]
    tools: list[ToolSpec] = Field(default_factory=list)
    temperature: float = 0.2
    max_tokens: int = 2048
    json_mode: bool = False
    tenant_id: str | None = None


class LLMResponse(BaseModel):
    text: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    model: str
    provider: str
    usage: dict[str, int] = Field(default_factory=dict)
    finish_reason: str = "stop"