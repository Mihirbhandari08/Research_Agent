"""
app.domain
==========
Public domain models re-exported for easy imports across the entire system.
"""

from app.domain.enums import (
    ConfidenceLevel,
    OutputFormat,
    ResearchDepth,
    ResearchStatus,
    Severity,
    SourceType,
    TaskStatus,
)
from app.domain.metadata import RequestMetadata, RunMetadata
from app.domain.metrics import ExecutionMetrics, TokenUsage
from app.domain.request import ResearchRequest
from app.domain.evidence import Finding, Source
from app.domain.task import ResearchTask
from app.domain.planning import ResearchPlan
from app.domain.knowledge import ConsolidatedFact, KnowledgeBase
from app.domain.critique import Contradiction, ResearchGap, Critique
from app.domain.citation import Citation
from app.domain.report import FinalReport, ReportSection
from app.domain.execution import ResearchRun

__all__ = [
    # Enums
    "ConfidenceLevel",
    "OutputFormat",
    "ResearchDepth",
    "ResearchStatus",
    "Severity",
    "SourceType",
    "TaskStatus",
    # Metadata & Metrics
    "RequestMetadata",
    "RunMetadata",
    "ExecutionMetrics",
    "TokenUsage",
    # Input Request
    "ResearchRequest",
    # Evidence & Tasks
    "Finding",
    "Source",
    "ResearchTask",
    "ResearchPlan",
    # Knowledge Deduplication
    "ConsolidatedFact",
    "KnowledgeBase",
    # Critique & Gaps
    "Contradiction",
    "ResearchGap",
    "Critique",
    # Citations & Output Reports
    "Citation",
    "FinalReport",
    "ReportSection",
    # Execution run history records
    "ResearchRun",
]
