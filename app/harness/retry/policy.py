"""
app/harness/retry/policy.py
===========================
Configurable parameters for exponential backoff and jitter retry policies.
"""

from pydantic import BaseModel, Field


class RetryPolicy(BaseModel):
    """Configuration defining how to retry operations when transient failures occur."""

    max_attempts: int = Field(
        default=3,
        ge=1,
        description="Maximum number of execution attempts before raising the error.",
    )
    initial_delay_seconds: float = Field(
        default=1.0,
        ge=0.0,
        description="Starting delay time in seconds for the first retry backoff.",
    )
    max_delay_seconds: float = Field(
        default=30.0,
        ge=0.0,
        description="Ceiling cap to prevent backoff delays from growing indefinitely.",
    )
    backoff_multiplier: float = Field(
        default=2.0,
        ge=1.0,
        description="Multiplier by which the backoff delay increases each attempt.",
    )
    use_jitter: bool = Field(
        default=True,
        description="Toggle randomized jitter to prevent herd-request patterns on target APIs.",
    )
