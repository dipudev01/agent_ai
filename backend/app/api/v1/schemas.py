"""API request/response schemas. Versioned under api.v1."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(TokenPair):
    user_id: str
    tenant_id: str
    roles: list[str]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = None
    agent_hint: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    conversation_id: str
    agent: str
    reply: str
    used_tools: list[str] = Field(default_factory=list)
    delegated_to: list[str] = Field(default_factory=list)
    needs_human_approval: bool = False
    decision: dict[str, Any] | None = None
    duration_ms: int = 0


class AgentSpec(BaseModel):
    key: str
    name: str
    description: str
    capabilities: list[str]
    version: str
    routing_priority: int


class AgentListResponse(BaseModel):
    agents: list[AgentSpec]


class ToolSpecResponse(BaseModel):
    name: str
    description: str


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    message: str


class ErrorBody(BaseModel):
    detail: str
    code: str
    correlation_id: str | None = None