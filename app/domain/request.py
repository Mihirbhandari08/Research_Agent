"""
app/domain/request.py
===================
Input schemas for validating and defining a research request.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import OutputFormat, ResearchDepth
from app.domain.metadata import RequestMetadata
from app.utils.ids import new_run_id
from app.utils.time import utcnow


class ResearchRequest(BaseModel):
    """The structured representation of a user's initial research request."""

    run_id: str = Field(
        default_factory=new_run_id,
        description="Unique identifier for this specific research run.",
    )
    query: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="The research question or topic to investigate.",
    )
    depth: ResearchDepth = Field(
        default=ResearchDepth.STANDARD,
        description="Research thoroughness. quick=fast/fewer sources, deep=slow/many sources.",
    )
    max_sources: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum total sources to search across all tasks.",
    )
    focus_domains: list[str] = Field(
        default_factory=list,
        description="Optional list of domains to focus search toward (e.g. ['arxiv.org', 'nature.com']).",
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="Desired final document format.",
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        description="Datetime the request was created.",
    )
    metadata: RequestMetadata = Field(
        default_factory=RequestMetadata,
        description="Optional client-provided tracking information.",
    )

    @property
    def depth_config(self) -> dict[str, int]:
        """Returns runtime parameters mapping to the chosen research depth."""
        configs = {
            ResearchDepth.QUICK: {
                "max_tasks": 3,
                "max_critic_passes": 1,
                "max_sources_per_task": 3,
            },
            ResearchDepth.STANDARD: {
                "max_tasks": 6,
                "max_critic_passes": 2,
                "max_sources_per_task": 5,
            },
            ResearchDepth.DEEP: {
                "max_tasks": 12,
                "max_critic_passes": 3,
                "max_sources_per_task": 8,
            },
        }
        return configs[self.depth]
