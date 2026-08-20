"""API request/response schemas. Versioned under api.v1."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TokenPair(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access-token",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh-token",
        "token_type": "bearer",
        "expires_in": 900,
    }})

    access_token: str = Field(description="Short-lived JWT access token.")
    refresh_token: str = Field(description="Longer-lived JWT refresh token.")
    token_type: str = Field(default="bearer", examples=["bearer"])
    expires_in: int = Field(description="Access-token lifetime in seconds.", examples=[900])


class LoginRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "email": "customer@demo.com",
        "password": "demo1234",
    }})

    email: str = Field(examples=["customer@demo.com"])
    password: str = Field(examples=["demo1234"], min_length=1)


class LoginResponse(TokenPair):
    model_config = ConfigDict(json_schema_extra={"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access-token",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh-token",
        "token_type": "bearer",
        "expires_in": 900,
        "user_id": "user_7f4a2c10",
        "tenant_id": "t_axisdemo",
        "roles": ["customer"],
    }})

    user_id: str = Field(examples=["user_7f4a2c10"])
    tenant_id: str = Field(examples=["t_axisdemo"])
    roles: list[str] = Field(examples=[["customer"]])


class ChatRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "message": "What documents do I need for a home loan?",
        "conversation_id": "conv_01J8HOMELOAN",
        "agent_hint": "customer_support",
        "context": {"channel": "web"},
    }})

    message: str = Field(min_length=1, max_length=8000, examples=["What documents do I need for a home loan?"])
    conversation_id: str | None = Field(default=None, examples=["conv_01J8HOMELOAN"])
    agent_hint: str | None = Field(default=None, examples=["customer_support"])
    context: dict[str, Any] = Field(default_factory=dict, examples=[{"channel": "web"}])


class ChatResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "conversation_id": "conv_01J8HOMELOAN",
        "agent": "customer_support",
        "reply": "For a home loan, typically provide identity, income, address, and property documents.",
        "used_tools": [],
        "delegated_to": [],
        "needs_human_approval": False,
        "decision": None,
        "duration_ms": 842,
    }})

    conversation_id: str = Field(examples=["conv_01J8HOMELOAN"])
    agent: str = Field(examples=["customer_support"])
    reply: str = Field(examples=["For a home loan, typically provide identity, income, address, and property documents."])
    used_tools: list[str] = Field(default_factory=list, examples=[[]])
    delegated_to: list[str] = Field(default_factory=list, examples=[[]])
    needs_human_approval: bool = Field(default=False, examples=[False])
    decision: dict[str, Any] | None = Field(default=None, examples=[None])
    duration_ms: int = Field(default=0, examples=[842])


class AgentSpec(BaseModel):
    key: str = Field(examples=["customer_support"])
    name: str = Field(examples=["Customer Support"])
    description: str = Field(examples=["Answers customer service questions and explains account processes."])
    capabilities: list[str] = Field(examples=[["faq", "account_support"]])
    version: str = Field(examples=["1.0.0"])
    routing_priority: int = Field(examples=[50])


class AgentListResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "agents": [{
            "key": "customer_support",
            "name": "Customer Support",
            "description": "Answers customer service questions and explains account processes.",
            "capabilities": ["faq", "account_support"],
            "version": "1.0.0",
            "routing_priority": 50,
        }]
    }})

    agents: list[AgentSpec]


class ToolSpecResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "customer.lookup",
        "description": "Look up customer profile data for the current tenant.",
    }})

    name: str = Field(examples=["customer.lookup"])
    description: str = Field(examples=["Look up customer profile data for the current tenant."])


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "document_id": "doc_01J8DOCUMENT",
        "status": "indexed",
        "message": "document indexed",
    }})

    document_id: str = Field(examples=["doc_01J8DOCUMENT"])
    status: str = Field(examples=["indexed"])
    message: str = Field(examples=["document indexed"])


class RefreshResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access-token",
    }})

    access_token: str = Field(examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access-token"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok"}})

    status: str = Field(examples=["ok"])


class TenantCreatedResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"tenant_id": "t_01J8TENANT"}})

    tenant_id: str = Field(examples=["t_01J8TENANT"])


class UserCreatedResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "user_id": "user_01J8USER",
        "tenant_id": "t_01J8TENANT",
    }})

    user_id: str = Field(examples=["user_01J8USER"])
    tenant_id: str = Field(examples=["t_01J8TENANT"])


class InstitutionCreatedResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "institution_id": "inst_01J8INSTITUTION",
        "tenant_id": "t_01J8TENANT",
    }})

    institution_id: str = Field(examples=["inst_01J8INSTITUTION"])
    tenant_id: str = Field(examples=["t_01J8TENANT"])


class ErrorBody(BaseModel):
    detail: str
    code: str
    correlation_id: str | None = None
