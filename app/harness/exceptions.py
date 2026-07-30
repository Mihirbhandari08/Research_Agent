"""
app/harness/exceptions.py
=========================
Custom exceptions used across the agent harness, tools, and LLM gateway.
Allows fine-grained error catching and graceful degradation.
"""


class ResearchAgentError(Exception):
    """Base exception for all errors in the research agent system."""

    def __init__(self, message: str, run_id: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.run_id = run_id

    def __str__(self) -> str:
        if self.run_id:
            return f"[run={self.run_id}] {self.message}"
        return self.message


# ── Planning Errors ────────────────────────────────────────────────────────


class PlanningError(ResearchAgentError):
    """Raised when the Planner node fails to decompose the research request."""


class InvalidQueryError(PlanningError):
    """Raised when the research query is empty, malformed, or inappropriate."""


# ── LLM Gateway Errors ─────────────────────────────────────────────────────


class LLMError(ResearchAgentError):
    """Base error for LLM interactions."""

    def __init__(self, message: str, model_name: str | None = None, run_id: str | None = None) -> None:
        super().__init__(message, run_id)
        self.model_name = model_name

    def __str__(self) -> str:
        base = f"LLM error: {self.message}"
        if self.model_name:
            base = f"[{self.model_name}] {base}"
        if self.run_id:
            base = f"[run={self.run_id}] {base}"
        return base


class LLMRateLimitError(LLMError):
    """Raised when the LLM provider rate limits requests (HTTP 429)."""


class LLMContextLimitError(LLMError):
    """Raised when the input context exceeds the model's window limits."""


class LLMOutputParseError(LLMError):
    """Raised when the LLM returns structured JSON that violates the target schema."""


# ── Tool Execution Errors ──────────────────────────────────────────────────


class ToolError(ResearchAgentError):
    """Base error for all tools executed by the Researcher."""

    def __init__(self, message: str, tool_name: str, run_id: str | None = None) -> None:
        super().__init__(message, run_id)
        self.tool_name = tool_name

    def __str__(self) -> str:
        base = f"Tool '{self.tool_name}' failed: {self.message}"
        if self.run_id:
            return f"[run={self.run_id}] {base}"
        return base


class SearchError(ToolError):
    """Raised when search tools (Tavily, Serper) encounter API or network failures."""


class DocumentReadError(ToolError):
    """Raised when parsing local or fetched PDF/text files fails."""


class ExtractionError(ToolError):
    """Raised when scrapers fail to extract text from a target web page URL."""


# ── Harness Runtime & Policies ─────────────────────────────────────────────


class PolicyViolationError(ResearchAgentError):
    """Raised when a node attempts an action forbidden by security policies."""

    def __init__(self, message: str, action: str, run_id: str | None = None) -> None:
        super().__init__(message, run_id)
        self.action = action


class BudgetExhaustedError(ResearchAgentError):
    """Raised immediately when token, cost, or task budgets are exceeded."""

    def __init__(self, message: str, limit_type: str, run_id: str | None = None) -> None:
        super().__init__(message, run_id)
        self.limit_type = limit_type


class TimeoutError(ResearchAgentError):
    """Raised when a run, node, or gateway operation exceeds its deadline."""


class CancellationError(ResearchAgentError):
    """Raised when an operation checks the cancellation token and finds it triggered."""


# ── Database & Storage Errors ──────────────────────────────────────────────


class StorageError(ResearchAgentError):
    """Base exception for database failures."""


class RunNotFoundError(StorageError):
    """Raised when retrieving a non-existent run ID from storage."""


class ReportNotFoundError(StorageError):
    """Raised when retrieving a non-existent report ID from storage."""
