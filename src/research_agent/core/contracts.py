"""
Phase 1 — API Contracts
=======================
Request/Response schemas for the FastAPI layer.

These are deliberately separate from domain models (core/models.py) so that:
- API shapes can evolve independently of internal data structures.
- We can add/remove API fields without touching agent logic.
- Serialization concerns stay at the boundary layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from research_agent.core.models import (
    FinalReport,
    OutputFormat,
    ResearchDepth,
    ResearchStatus,
    TokenUsage,
)


# ---------------------------------------------------------------------------
# Request Contracts
# ---------------------------------------------------------------------------


class StartResearchRequest(BaseModel):
    """
    POST /research
    Body sent by the client to start a new research run.
    """

    query: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="The research question or topic to investigate.",
        examples=["What are the latest advances in quantum computing in 2024?"],
    )
    depth: ResearchDepth = Field(
        default=ResearchDepth.STANDARD,
        description="Research thoroughness. quick=fast/fewer sources, deep=slow/many sources.",
    )
    max_sources: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum total sources to gather across all tasks.",
    )
    focus_domains: list[str] = Field(
        default_factory=list,
        description="Optional list of domains to bias search toward (e.g. ['arxiv.org', 'nature.com']).",
        examples=[["arxiv.org", "nature.com"]],
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="Format of the final report.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary client metadata attached to this run.",
    )


# ---------------------------------------------------------------------------
# Response Contracts
# ---------------------------------------------------------------------------


class StartResearchResponse(BaseModel):
    """
    POST /research → 202 Accepted
    Returned immediately after a run is enqueued.
    """

    run_id: str = Field(description="Unique ID to poll or stream this run.")
    status: ResearchStatus = ResearchStatus.QUEUED
    stream_url: str = Field(description="SSE endpoint for live progress.")
    poll_url: str = Field(description="REST endpoint to poll for status/report.")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RunStatusResponse(BaseModel):
    """
    GET /research/{run_id}
    Full status of a research run, including the report if complete.
    """

    run_id: str
    status: ResearchStatus
    query: str
    depth: ResearchDepth
    report: FinalReport | None = None
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    elapsed_seconds: float = 0.0
    critic_passes: int = 0
    total_sources: int = 0
    total_findings: int = 0
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class RunListItem(BaseModel):
    """A summary row for GET /research (list all runs)."""

    run_id: str
    status: ResearchStatus
    query: str
    depth: ResearchDepth
    total_sources: int = 0
    overall_confidence: float = 0.0
    created_at: datetime
    elapsed_seconds: float = 0.0


class RunListResponse(BaseModel):
    """GET /research → paginated list of runs."""

    items: list[RunListItem]
    total: int
    page: int = 1
    page_size: int = 20


class ReportListItem(BaseModel):
    """A summary row for GET /reports."""

    report_id: str
    run_id: str
    query: str
    overall_confidence: float
    total_sources: int
    created_at: datetime


class ReportListResponse(BaseModel):
    """GET /reports → paginated list of reports."""

    items: list[ReportListItem]
    total: int
    page: int = 1
    page_size: int = 20


# ---------------------------------------------------------------------------
# Streaming Contracts
# ---------------------------------------------------------------------------


class StreamEvent(BaseModel):
    """
    GET /research/{run_id}/stream → SSE event payload.
    Each event is JSON-serialized and sent as SSE data.
    """

    event: str = Field(description="Event type identifier.")
    run_id: str
    message: str = Field(description="Human-readable progress message.")
    node: str = Field(description="Which graph node emitted this event.")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Error Contracts
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Standard error envelope returned on 4xx / 5xx responses."""

    error: str
    detail: str = ""
    run_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """GET /health"""

    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: dict[str, str] = Field(
        default_factory=dict,
        description="Status of each component (db, llm, search, etc.)",
        examples=[{"db": "ok", "llm": "ok", "search": "ok"}],
    )
