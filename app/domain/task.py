"""
app/domain/task.py
===================
Models representing individual, prioritized research tasks within a plan.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums import TaskStatus
from app.domain.evidence import Finding
from app.utils.ids import new_task_id
from app.utils.time import utcnow


class ResearchTask(BaseModel):
    """An atomic research task to be executed by the Researcher."""

    task_id: str = Field(
        default_factory=new_task_id,
        description="Unique identifier for this task.",
    )
    parent_run_id: str = Field(..., description="ID of the research run this task belongs to.")
    query: str = Field(..., description="The search query or target question for this task.")
    rationale: str = Field(default="", description="Planner's reasoning for creating this task.")
    priority: int = Field(default=5, ge=1, le=10, description="Priority rating (1=lowest, 10=highest).")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Execution status of the task.")
    max_sources: int = Field(default=5, ge=1, description="Max sources to query for this specific task.")
    findings: list[Finding] = Field(default_factory=list, description="Findings generated during this task.")
    error: str | None = Field(default=None, description="Error message if task execution failed.")
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = Field(default=None, description="Timestamp when task status became final.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary execution context.")
