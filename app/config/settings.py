"""
app/config/settings.py
======================
Single source of truth for all application configuration.

Uses Pydantic Settings v2 — values are read from environment variables
or a .env file. Every field has a sensible default so the app starts
without a fully configured environment (useful for tests and local dev).

Usage:
    from app.config.settings import get_settings
    settings = get_settings()
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration for the research agent.
    Grouped by concern for readability.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",        # silently ignore unknown env vars
    )

    # ── Application ────────────────────────────────────────────────────────
    app_name: str = Field(default="research-agent")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development"
    )
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )

    # ── API Server ─────────────────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_workers: int = Field(default=1)
    api_reload: bool = Field(default=True)  # auto-reload in dev
    cors_origins: list[str] = Field(default=["*"])

    # ── LLM — Gemini ───────────────────────────────────────────────────────
    gemini_api_key: SecretStr = Field(default=SecretStr(""))
    gemini_default_model: str = Field(default="gemini/gemini-2.5-pro")
    gemini_fallback_model: str = Field(default="gemini/gemini-2.0-flash")

    # ── LLM — OpenAI (optional fallback) ──────────────────────────────────
    openai_api_key: SecretStr = Field(default=SecretStr(""))
    openai_default_model: str = Field(default="gpt-4o")

    # ── LLM — Anthropic (optional fallback) ───────────────────────────────
    anthropic_api_key: SecretStr = Field(default=SecretStr(""))
    anthropic_default_model: str = Field(default="claude-sonnet-4-5")

    # ── LiteLLM ────────────────────────────────────────────────────────────
    litellm_verbose: bool = Field(default=False)
    litellm_cache: bool = Field(default=False)

    # ── Search Tools ───────────────────────────────────────────────────────
    tavily_api_key: SecretStr = Field(default=SecretStr(""))
    tavily_max_results: int = Field(default=5)

    serper_api_key: SecretStr = Field(default=SecretStr(""))
    serper_max_results: int = Field(default=5)

    # Primary search provider — first available is used
    search_provider: Literal["tavily", "serper"] = Field(default="tavily")

    # ── Database — PostgreSQL ──────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/research_agent"
    )
    database_pool_size: int = Field(default=10)
    database_max_overflow: int = Field(default=20)
    database_echo: bool = Field(default=False)  # log SQL in dev

    # ── pgvector ───────────────────────────────────────────────────────────
    vector_embedding_model: str = Field(default="text-embedding-3-small")
    vector_dimensions: int = Field(default=1536)

    # ── Execution Budgets (defaults, overridable per-request) ──────────────
    default_max_duration_seconds: float = Field(default=300.0)   # 5 minutes
    default_max_iterations: int = Field(default=3)
    default_max_llm_calls: int = Field(default=30)
    default_max_tool_calls: int = Field(default=50)
    default_max_input_tokens: int = Field(default=100_000)
    default_max_output_tokens: int = Field(default=30_000)
    default_max_cost_usd: float = Field(default=1.00)

    # ── Timeouts (seconds) ─────────────────────────────────────────────────
    timeout_node_seconds: float = Field(default=30.0)
    timeout_llm_seconds: float = Field(default=20.0)
    timeout_tool_seconds: float = Field(default=10.0)

    # ── Retry ──────────────────────────────────────────────────────────────
    retry_max_attempts: int = Field(default=3)
    retry_initial_delay_seconds: float = Field(default=1.0)
    retry_max_delay_seconds: float = Field(default=30.0)
    retry_backoff_multiplier: float = Field(default=2.0)
    retry_jitter: bool = Field(default=True)

    # ── Observability ──────────────────────────────────────────────────────
    langsmith_api_key: SecretStr = Field(default=SecretStr(""))
    langsmith_project: str = Field(default="research-agent")
    langsmith_tracing_enabled: bool = Field(default=False)

    otel_exporter_endpoint: str = Field(default="")
    otel_service_name: str = Field(default="research-agent")

    # ── Checkpointing ──────────────────────────────────────────────────────
    # "memory" = in-process (dev), "postgres" = durable (production)
    checkpoint_backend: Literal["memory", "postgres"] = Field(default="memory")

    # ── Field Validators ───────────────────────────────────────────────────

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Allow CORS_ORIGINS to be a comma-separated string in .env."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ── Computed Properties ────────────────────────────────────────────────

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def active_llm_model(self) -> str:
        """The primary model used for all LLM calls."""
        return self.gemini_default_model

    @property
    def database_url_sync(self) -> str:
        """Synchronous database URL for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached Settings instance.

    Using lru_cache means the .env file is read exactly once
    per process lifetime — not on every import.

    In tests, call get_settings.cache_clear() to reset.
    """
    return Settings()
