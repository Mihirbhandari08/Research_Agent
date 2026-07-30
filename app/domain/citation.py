"""
app/domain/citation.py
======================
Models representing bibliography citations and mapping references within the final report.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.evidence import Source
from app.utils.ids import new_citation_id
from app.utils.time import utcnow


class Citation(BaseModel):
    """A formal bibliographic citation in the final report."""

    citation_id: str = Field(
        default_factory=new_citation_id,
        description="Unique identifier for this citation.",
    )
    source: Source = Field(..., description="The backing information source.")
    referenced_in: list[str] = Field(
        default_factory=list,
        description="Titles of report sections that reference this source.",
    )
    created_at: datetime = Field(default_factory=utcnow)
