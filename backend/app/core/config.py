"""Application configuration via pydantic-settings.

All configuration derives from environment variables. No secrets in code.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "bfsi-ai-agent"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    correlation_header: str = "X-Correlation-ID"
    cors_allowed_origins: list[str] = []

    # Security
    jwt_secret: str = Field(default="", repr=False)
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7
    encryption_key: str = Field(default="", repr=False)

    # Database
    database_url: str = "postgresql+asyncpg://bfsi:bfsi@localhost:5432/bfsi_ai"
    db_pool_size: int = 20
    db_max_overflow: int = 40
    db_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl_seconds: int = 900

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "bfsi-ai-agent"

    # LLM Gateway
    llm_default_provider: str = "mock"
    llm_default_model: str = "bfsi-mock"
    openai_api_key: str = Field(default="", repr=False)
    openai_base_url: str | None = None
    anthropic_api_key: str = Field(default="", repr=False)
    ollama_base_url: str = "http://localhost:11434"
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 3
    llm_rate_limit_rpm: int = 600

    # RAG / Vector
    vector_store: str = "opensearch"
    opensearch_url: str = "http://localhost:9200"
    embedding_model: str = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
    embedding_dim: int = 384
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Observability
    otel_exporter_otlp_endpoint: str = "http://localhost:4318"
    otel_service_name: str = "bfsi-agent-api"
    log_level: str = "INFO"

    # Storage
    object_storage_endpoint: str = "http://localhost:9000"
    object_storage_bucket: str = "bfsi-documents"

    # HITL / Compliance
    hitl_approval_timeout_hours: int = 72
    audit_retention_days: int = 2555

    # Decisioning
    eligibility_min_score: int = 550
    fraud_max_risk_score: float = 65.0

    # Agent orchestration: "classic" (built-in loop) or "langgraph" (StateGraph).
    agent_orchestrator: str = "classic"

    @field_validator("jwt_secret", "encryption_key")
    @classmethod
    def reject_placeholder_secrets(cls, v: str, info) -> str:
        if v and v.startswith("change-me"):
            raise ValueError(f"{info.field_name} must not be the placeholder value")
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env in {"production", "staging"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
