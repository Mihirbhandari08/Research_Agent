"""
app/domain/enums.py
===================
Canonical enums representing the states, types, and levels used across the research system.
Using `str, Enum` allows easy JSON serialization and database storage.
"""

from enum import Enum


class ResearchDepth(str, Enum):
    """Controls how thorough the research run will be."""

    QUICK = "quick"        # 3–5 sources, 1 critic pass
    STANDARD = "standard"  # 8–12 sources, 2 critic passes
    DEEP = "deep"          # 15–25 sources, 3 critic passes


class ResearchStatus(str, Enum):
    """Lifecycle status of a research run."""

    QUEUED = "queued"
    PLANNING = "planning"
    RESEARCHING = "researching"
    CRITIQUING = "critiquing"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Status of an individual research task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"


class SourceType(str, Enum):
    """The type/origin of a source."""

    WEB_PAGE = "web_page"
    PDF = "pdf"
    NEWS = "news"
    ACADEMIC = "academic"
    VIDEO_TRANSCRIPT = "video_transcript"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """Human-readable confidence tier of findings or reports."""

    VERY_LOW = "very_low"    # < 0.2
    LOW = "low"              # 0.2 – 0.4
    MEDIUM = "medium"        # 0.4 – 0.6
    HIGH = "high"            # 0.6 – 0.8
    VERY_HIGH = "very_high"  # > 0.8


class Severity(str, Enum):
    """Severity of gaps identified by the Critic."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class OutputFormat(str, Enum):
    """Desired output format for the final report."""

    MARKDOWN = "markdown"
    JSON = "json"
