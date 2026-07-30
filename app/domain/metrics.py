"""
app/domain/metrics.py
===================
Models for tracking token consumption, API financial costs, and general execution metrics.
"""

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Tracks LLM token consumption and estimated cost."""

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)

    def add(self, other: TokenUsage) -> TokenUsage:
        """Accumulate token usage and costs."""
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            estimated_cost_usd=self.estimated_cost_usd + other.estimated_cost_usd,
        )

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return self.add(other)


class ExecutionMetrics(BaseModel):
    """Detailed execution telemetry for a research run or task."""

    elapsed_seconds: float = Field(default=0.0, ge=0.0)
    total_llm_calls: int = Field(default=0, ge=0)
    total_tool_calls: int = Field(default=0, ge=0)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
