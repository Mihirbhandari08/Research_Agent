"""
app/domain/metadata.py
===================
Models for tracking request context, user tags, and harness-injected execution parameters.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.utils.time import utcnow


class RequestMetadata(BaseModel):
    """Optional context metadata passed by the client initiating the research."""

    user_id: str | None = Field(default=None, description="The user initiating the request.")
    session_id: str | None = Field(default=None, description="The session grouping this query.")
    project_id: str | None = Field(default=None, description="A project identifier for billing or grouping.")
    custom_tags: list[str] = Field(default_factory=list, description="Arbitrary labels for categorizing runs.")
    extra: dict[str, Any] = Field(default_factory=dict, description="Any other unstructured data.")


class RunMetadata(BaseModel):
    """Runtime parameters and limits injected by the Agent Harness before executing a run."""

    run_id: str = Field(..., description="Unique ID for this specific execution attempt.")
    thread_id: str = Field(..., description="Durable workflow thread ID.")
    session_id: str | None = Field(default=None, description="Associated session ID.")
    user_id: str | None = Field(default=None, description="Owner of the execution.")

    started_at: datetime = Field(default_factory=utcnow, description="Time execution started.")
    deadline: datetime | None = Field(default=None, description="Target datetime for run completion.")

    model_name: str = Field(..., description="Default model targeted for standard nodes.")
    max_critic_passes: int = Field(default=2, ge=0)
    max_tasks: int = Field(default=10, ge=1)
    max_sources_per_task: int = Field(default=5, ge=1)

    token_budget: int = Field(default=100_000, ge=0)
    cost_budget_usd: float = Field(default=1.00, ge=0.0)
    timeout_seconds: float = Field(default=300.0, ge=0.0)
    retry_count: int = Field(default=0, ge=0)
