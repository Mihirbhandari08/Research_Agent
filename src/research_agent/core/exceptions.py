"""
Phase 1 — Custom Exceptions
============================
All domain-specific exceptions for the research agent.
Using a clear hierarchy allows the harness and API layer to
catch exceptions at the right level of specificity.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class ResearchAgentError(Exception):
    """Base exception for all research agent errors."""

    def __init__(self, message: str, run_id: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.run_id = run_id

    def __str__(self) -> str:
        if self.run_id:
            return f"[run={self.run_id}] {self.message}"
        return self.message


# ---------------------------------------------------------------------------
# Planning Errors
# ---------------------------------------------------------------------------


class PlanningError(ResearchAgentError):
    """Raised when the Planner fails to decompose the query."""


class InvalidQueryError(PlanningError):
    """Raised when the research query is malformed or unsupported."""


# ---------------------------------------------------------------------------
# Research Errors
# ---------------------------------------------------------------------------


class ResearchError(ResearchAgentError):
    """Raised when a research task fails during execution."""


class ToolError(ResearchError):
    """Raised when a tool (search, reader, extractor) fails."""

    def __init__(self, message: str, tool_name: str, run_id: str | None = None) -> None:
        super().__init__(message, run_id)
        self.tool_name = tool_name

    def __str__(self) -> str:
        base = f"[tool={self.tool_name}] {self.message}"
        if self.run_id:
            return f"[run={self.run_id}] {base}"
        return base


class SearchError(ToolError):
    """Raised when the web search tool fails."""


class DocumentReadError(ToolError):
    """Raised when the document reader fails to parse a source."""


class ExtractionError(ToolError):
    """Raised when the website extractor fails."""


# ---------------------------------------------------------------------------
# LLM Errors
# ---------------------------------------------------------------------------


class LLMError(ResearchAgentError):
    """Raised when an LLM call fails."""

    def __init__(
        self,
        message: str,
        model: str | None = None,
        run_id: str | None = None,
    ) -> None:
        super().__init__(message, run_id)
        self.model = model


class LLMRateLimitError(LLMError):
    """Raised when the LLM provider rate-limits us."""


class LLMContextLimitError(LLMError):
    """Raised when the input exceeds the model's context window."""


class LLMOutputParseError(LLMError):
    """Raised when the LLM response cannot be parsed into a Pydantic model."""


# ---------------------------------------------------------------------------
# Budget / Harness Errors
# ---------------------------------------------------------------------------


class BudgetExhaustedError(ResearchAgentError):
    """Raised when the token or cost budget is exceeded."""

    def __init__(
        self,
        message: str,
        budget_type: str = "token",
        run_id: str | None = None,
    ) -> None:
        super().__init__(message, run_id)
        self.budget_type = budget_type


class TimeoutError(ResearchAgentError):
    """Raised when a run or node exceeds its time limit."""


class CancellationError(ResearchAgentError):
    """Raised when a run is cancelled by the user or system."""


# ---------------------------------------------------------------------------
# Synthesis Errors
# ---------------------------------------------------------------------------


class SynthesisError(ResearchAgentError):
    """Raised when the Synthesizer fails to produce a final report."""


# ---------------------------------------------------------------------------
# Memory / Storage Errors
# ---------------------------------------------------------------------------


class StorageError(ResearchAgentError):
    """Raised when a database read or write fails."""


class RunNotFoundError(StorageError):
    """Raised when a requested run ID does not exist."""

    def __init__(self, run_id: str) -> None:
        super().__init__(f"Research run '{run_id}' not found.", run_id=run_id)


class ReportNotFoundError(StorageError):
    """Raised when a requested report ID does not exist."""
