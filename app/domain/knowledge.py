"""
app/domain/knowledge.py
======================
Models representing synthesized, consolidated factual knowledge derived from raw findings.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.evidence import Source
from app.utils.time import utcnow


class ConsolidatedFact(BaseModel):
    """A synthesized, deduplicated fact that aggregates multiple raw findings."""

    fact_id: str = Field(..., description="Unique identifier for this consolidated fact.")
    summary: str = Field(..., description="The high-level summary statement of the fact.")
    detailed_explanation: str = Field(default="", description="Deep-dive context of this fact.")
    raw_finding_ids: list[str] = Field(
        default_factory=list,
        description="IDs of raw findings that support or consolidate into this fact.",
    )
    supporting_sources: list[Source] = Field(
        default_factory=list,
        description="Consolidated sources backing this fact.",
    )
    consensus_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Degree of agreement among raw findings (1.0 = perfect consensus).",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Aggregated confidence rating.",
    )
    created_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeBase(BaseModel):
    """The complete aggregated factual database built during a research run."""

    run_id: str = Field(..., description="The execution run this knowledge base belongs to.")
    facts: list[ConsolidatedFact] = Field(
        default_factory=list,
        description="Unique, consolidated facts extracted during research.",
    )
    all_sources: list[Source] = Field(
        default_factory=list,
        description="Flat index of all unique sources crawled or read.",
    )

    @property
    def total_facts(self) -> int:
        return len(self.facts)

    @property
    def total_sources(self) -> int:
        return len(self.all_sources)
