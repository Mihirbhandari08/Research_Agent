"""
app/domain/execution.py
======================
Models representing the overall execution records and logs for a research run.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import ResearchStatus
from app.domain.metadata import RunMetadata
from app.domain.metrics import ExecutionMetrics
from app.domain.planning import ResearchPlan
from app.domain.report import FinalReport
from app.domain.request import ResearchRequest
from app.utils.time import utcnow


class ResearchRun(BaseModel):
    """The complete historical and runtime state record of a single research execution."""

    run_id: str = Field(..., description="Unique ID for this research run.")
    status: ResearchStatus = Field(default=ResearchStatus.QUEUED, description="Lifecycle status of the run.")
    request: ResearchRequest = Field(..., description="The original request input.")
    metadata: RunMetadata = Field(..., description="Context parameters injected by the harness.")
    metrics: ExecutionMetrics = Field(
        default_factory=ExecutionMetrics,
        description="Accumulated resources consumed during execution.",
    )
    plan: ResearchPlan | None = Field(default=None, description="Decomposed tasks (once planning completes).")
    latest_report: FinalReport | None = Field(default=None, description="The final generated report (once complete).")
    error: str | None = Field(default=None, description="Error details if the run failed.")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    def update_status(self, new_status: ResearchStatus) -> None:
        """Helper to transition status and update modified timestamp."""
        self.status = new_status
        self.updated_at = utcnow()
