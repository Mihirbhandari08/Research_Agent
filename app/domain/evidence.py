"""
app/domain/evidence.py
===================
Models representing discovered web/document sources and factual findings extracted from them.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import ConfidenceLevel, SourceType
from app.utils.ids import new_finding_id, new_source_id
from app.utils.time import utcnow


class Source(BaseModel):
    """An information source discovered by the Researcher."""

    source_id: str = Field(
        default_factory=new_source_id,
        description="Unique identifier for this source.",
    )
    url: str = Field(..., description="The URL of the source page or file.")
    title: str = Field(..., description="The title of the page/document.")
    snippet: str = Field(default="", description="Snippet or summary of content.")
    source_type: SourceType = Field(default=SourceType.UNKNOWN)
    domain: str = Field(default="", description="Base domain of the URL.")
    published_at: datetime | None = Field(default=None)
    fetched_at: datetime = Field(default_factory=utcnow)
    credibility_score: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("credibility_score")
    @classmethod
    def clamp_credibility(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class Finding(BaseModel):
    """A factual statement extracted from one or more sources."""

    finding_id: str = Field(
        default_factory=new_finding_id,
        description="Unique identifier for this finding.",
    )
    task_id: str = Field(..., description="ID of the ResearchTask that produced this finding.")
    content: str = Field(..., description="The factual text content.")
    summary: str = Field(default="", description="Brief summary of the finding.")
    sources: list[Source] = Field(default_factory=list, description="Sources supporting this finding.")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    contradicts: list[str] = Field(
        default_factory=list,
        description="List of other finding_ids that this finding directly contradicts.",
    )
    created_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Derive standard confidence tiers from numerical confidence."""
        if self.confidence < 0.2:
            return ConfidenceLevel.VERY_LOW
        elif self.confidence < 0.4:
            return ConfidenceLevel.LOW
        elif self.confidence < 0.6:
            return ConfidenceLevel.MEDIUM
        elif self.confidence < 0.8:
            return ConfidenceLevel.HIGH
        return ConfidenceLevel.VERY_HIGH
