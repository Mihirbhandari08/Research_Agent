"""
app/graph/state.py
==================
Shared state definition and helper functions for the LangGraph orchestrator.
"""

from datetime import datetime
import operator
from typing import Annotated, Any, TypedDict

from app.domain import (
    Critique,
    FinalReport,
    Finding,
    KnowledgeBase,
    ResearchGap,
    ResearchPlan,
    ResearchRequest,
    ResearchStatus,
    ResearchTask,
    RunMetadata,
    Source,
    TaskStatus,
    TokenUsage,
)
from app.utils.time import utcnow


class ProgressEvent(TypedDict, total=False):
    """A progress event emitted during graph execution for streaming."""

    event: str            # e.g., "task_started", "finding_found", "critique_ready"
    message: str          # Human-readable progress description
    node: str             # Which graph node emitted this
    timestamp: str        # ISO UTC datetime string
    data: dict[str, Any]  # Event payload


class ResearchState(TypedDict, total=False):
    """
    The master shared state for the research agent graph.

    Every field is optional so nodes can update only what they touch.
    Lists annotated with `operator.add` append items on updates.
    """

    # ── Input & Lifecycle ──────────────────────────────────────────────────
    request: ResearchRequest
    run_id: str
    status: ResearchStatus
    run_metadata: RunMetadata

    # ── Planning ───────────────────────────────────────────────────────────
    plan: ResearchPlan | None
    current_task_index: int

    # ── Accumulating Evidence & Tasks ──────────────────────────────────────
    tasks: Annotated[list[ResearchTask], operator.add]
    findings: Annotated[list[Finding], operator.add]
    sources: Annotated[list[Source], operator.add]

    # ── Unified Knowledge Base ─────────────────────────────────────────────
    knowledge_base: KnowledgeBase | None

    # ── Critique Loop ──────────────────────────────────────────────────────
    critiques: Annotated[list[Critique], operator.add]
    current_critique: Critique | None
    gaps: Annotated[list[ResearchGap], operator.add]
    critic_pass_count: int
    should_continue_research: bool
    follow_up_queries: Annotated[list[str], operator.add]

    # ── Final Output ───────────────────────────────────────────────────────
    final_report: FinalReport | None

    # ── Real-Time Metrics & Cost ───────────────────────────────────────────
    token_usage: TokenUsage

    # ── Streaming Events ───────────────────────────────────────────────────
    progress_events: Annotated[list[ProgressEvent], operator.add]

    # ── Error Logs ─────────────────────────────────────────────────────────
    error: str | None
    error_node: str | None

    # ── Timing ─────────────────────────────────────────────────────────────
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# State Initialization Factory
# ---------------------------------------------------------------------------


def create_initial_state(request: ResearchRequest, run_metadata: RunMetadata) -> ResearchState:
    """Creates a clean initial state dictionary for a research run."""
    now_iso = utcnow().isoformat()
    return ResearchState(
        request=request,
        run_id=request.run_id,
        status=ResearchStatus.QUEUED,
        run_metadata=run_metadata,
        plan=None,
        current_task_index=0,
        tasks=[],
        findings=[],
        sources=[],
        knowledge_base=None,
        critiques=[],
        current_critique=None,
        gaps=[],
        critic_pass_count=0,
        should_continue_research=True,
        follow_up_queries=[],
        final_report=None,
        token_usage=TokenUsage(),
        progress_events=[],
        error=None,
        error_node=None,
        created_at=now_iso,
        updated_at=now_iso,
    )


# ---------------------------------------------------------------------------
# State Helpers
# ---------------------------------------------------------------------------


def get_all_findings(state: ResearchState) -> list[Finding]:
    """Helper to return all findings collected so far."""
    return state.get("findings", [])


def get_pending_tasks(state: ResearchState) -> list[ResearchTask]:
    """Helper to retrieve tasks that haven't completed execution."""
    return [t for t in state.get("tasks", []) if t.status == TaskStatus.PENDING]


def get_latest_critique(state: ResearchState) -> Critique | None:
    """Helper to get the most recent critique evaluation."""
    return state.get("current_critique")


def emit_event(node: str, event: str, message: str, data: dict[str, Any] | None = None) -> ProgressEvent:
    """Generates a structured progress event for streaming."""
    return ProgressEvent(
        event=event,
        message=message,
        node=node,
        timestamp=utcnow().isoformat(),
        data=data or {},
    )


def is_budget_exhausted(state: ResearchState) -> bool:
    """Checks if the cumulative token budget has been exceeded."""
    metadata = state.get("run_metadata")
    if not metadata:
        return False
    usage = state.get("token_usage", TokenUsage())
    return usage.total_tokens >= metadata.token_budget


def should_stop_critic_loop(state: ResearchState) -> bool:
    """Determines if the research loop should terminate based on confidence or iterations."""
    metadata = state.get("run_metadata")
    if not metadata:
        return True

    latest_critique = get_latest_critique(state)
    if latest_critique and latest_critique.sufficient:
        return True

    pass_count = state.get("critic_pass_count", 0)
    if pass_count >= metadata.max_critic_passes:
        return True

    return False
