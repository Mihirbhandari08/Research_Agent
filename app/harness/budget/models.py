"""
app/harness/budget/models.py
============================
Data models representing execution limits and constraints for the budget enforcement system.
"""

from pydantic import BaseModel, Field


class ExecutionBudget(BaseModel):
    """Defines the maximum allowed resources a research run can consume."""

    max_duration_seconds: float = Field(
        default=300.0,
        ge=0.0,
        description="Max execution time for the entire run.",
    )
    max_iterations: int = Field(
        default=3,
        ge=1,
        description="Max planning/critique loops allowed.",
    )
    max_llm_calls: int = Field(
        default=30,
        ge=1,
        description="Max total LLM gateway calls permitted.",
    )
    max_tool_calls: int = Field(
        default=50,
        ge=1,
        description="Max total tool invocations permitted.",
    )
    max_input_tokens: int = Field(
        default=100_000,
        ge=1,
        description="Max cumulative prompt tokens allowed.",
    )
    max_output_tokens: int = Field(
        default=30_000,
        ge=1,
        description="Max cumulative completion tokens allowed.",
    )
    max_cost_usd: float = Field(
        default=1.00,
        ge=0.0,
        description="Max estimated financial API cost in USD.",
    )
