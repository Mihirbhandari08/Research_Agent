"""
app/domain/critique.py
======================
Models representing the evaluations, gaps, and contradictions identified by the Critic.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import Severity
from app.utils.ids import new_contradiction_id, new_critique_id, new_gap_id
from app.utils.time import utcnow


class ResearchGap(BaseModel):
    """A missing piece of evidence or information identified by the Critic."""

    gap_id: str = Field(
        default_factory=new_gap_id,
        description="Unique identifier for this research gap.",
    )
    description: str = Field(..., description="Details on what evidence or information is missing.")
    related_task_ids: list[str] = Field(
        default_factory=list,
        description="Sub-tasks linked to the domain of this gap.",
    )
    severity: Severity = Field(default=Severity.MEDIUM, description="The criticality of resolving this gap.")
    suggested_query: str = Field(default="", description="Recommended search query to fill this gap.")
    created_at: datetime = Field(default_factory=utcnow)


class Contradiction(BaseModel):
    """An identified conflict between two separate findings."""

    contradiction_id: str = Field(
        default_factory=new_contradiction_id,
        description="Unique identifier for this contradiction.",
    )
    finding_id_a: str = Field(..., description="ID of the first conflicting finding.")
    finding_id_b: str = Field(..., description="ID of the second conflicting finding.")
    description: str = Field(..., description="Description of the discrepancy or conflict.")
    resolution: str = Field(
        default="",
        description="Instructions on how the Writer/Synthesizer should address this conflict.",
    )


class Critique(BaseModel):
    """The complete critique pass details produced by the Critic node."""

    critique_id: str = Field(
        default_factory=new_critique_id,
        description="Unique identifier for this critique pass.",
    )
    run_id: str = Field(..., description="ID of the associated research execution.")
    pass_number: int = Field(default=1, ge=1, description="Iteration pass counter.")
    gaps: list[ResearchGap] = Field(default_factory=list, description="Gaps identified during this pass.")
    contradictions: list[Contradiction] = Field(
        default_factory=list,
        description="Discrepancies identified during this pass.",
    )
    weak_sources: list[str] = Field(
        default_factory=list,
        description="Source URLs or IDs flagged as low credibility.",
    )
    overall_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Critic's rating of information completeness.",
    )
    sufficient: bool = Field(
        default=False,
        description="Whether findings are thorough enough to proceed to writing.",
    )
    reasoning: str = Field(default="", description="The Critic's explanation for their evaluation.")
    suggested_follow_up_queries: list[str] = Field(
        default_factory=list,
        description="Queries suggested to address gaps in the next iteration loop.",
    )
    created_at: datetime = Field(default_factory=utcnow)
