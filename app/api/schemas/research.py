"""Pydantic schemas for the research API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain import ResearchRequest, ResearchStatus
from app.domain.execution import ResearchRun
from app.domain.metadata import RequestMetadata


class ResearchRequestCreate(BaseModel):
    """API input for creating a research workload."""

    query: str = Field(..., min_length=10, max_length=2000)
    depth: str = Field(default="standard")
    max_sources: int = Field(default=10, ge=1, le=50)
    focus_domains: list[str] = Field(default_factory=list)
    output_format: str = Field(default="markdown")
    metadata: RequestMetadata = Field(default_factory=RequestMetadata)

    def to_domain(self) -> ResearchRequest:
        return ResearchRequest(
            query=self.query,
            depth=self.depth,  # type: ignore[arg-type]
            max_sources=self.max_sources,
            focus_domains=self.focus_domains,
            output_format=self.output_format,  # type: ignore[arg-type]
            metadata=self.metadata,
        )


class ResearchRunResponse(BaseModel):
    """API response for a run status or record."""

    run_id: str
    status: ResearchStatus
    request: ResearchRequest
    metadata: object
    metrics: object | None = None
    plan: object | None = None
    latest_report: object | None = None
    error: str | None = None

    @classmethod
    def model_validate(cls, obj: ResearchRun) -> "ResearchRunResponse":
        return cls(
            run_id=obj.run_id,
            status=obj.status,
            request=obj.request,
            metadata=obj.metadata,
            metrics=obj.metrics,
            plan=obj.plan,
            latest_report=obj.latest_report,
            error=obj.error,
        )
