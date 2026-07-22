"""
Phase 4 — State Design
======================
The shared LangGraph graph state.

This is the single source of truth that flows through every node in the graph.
Each node reads from it and returns a partial update — LangGraph merges them.

Key design principles:
- All fields are Optional so nodes only update what they touch.
- Lists use Annotated with operator.add so updates append, not replace.
- Metadata and error fields give the harness layer full visibility.
"""

from __future__ import annotations

import operator
from datetime import datetime
from typing import Annotated, Any

from typing_extensions import TypedDict

from research_agent.core.models import (
    Critique,
    FinalReport,
    Finding,
    ResearchDepth,
    ResearchGap,
    ResearchPlan,
    ResearchRequest,
    ResearchStatus,
    ResearchTask,
    Source,
    TokenUsage,
)


# ---------------------------------------------------------------------------
# Progress Event — emitted to the streaming layer
# ---------------------------------------------------------------------------


class ProgressEvent(TypedDict, total=False):
    """A single progress event emitted during graph execution."""

    event: str          # e.g. "task_started", "finding_found", "critique_ready"
    message: str        # human-readable description
    node: str           # which graph node emitted this
    timestamp: str      # ISO datetime string
    data: dict[str, Any]  # arbitrary payload


# ---------------------------------------------------------------------------
# Run Metadata — managed by the harness
# ---------------------------------------------------------------------------


class RunMetadata(TypedDict, total=False):
    """Runtime metadata injected by the Agent Harness."""

    run_id: str
    thread_id: str
    started_at: str       # ISO datetime
    model_name: str
    max_critic_passes: int
    max_tasks: int
    max_sources_per_task: int
    token_budget: int
    cost_budget_usd: float
    timeout_seconds: float
    retry_count: int


# ---------------------------------------------------------------------------
# ResearchState — the shared graph state
# ---------------------------------------------------------------------------


class ResearchState(TypedDict, total=False):
    """
    The complete shared state for the research agent graph.

    LangGraph passes this between nodes. Each node receives the full state
    and returns only the fields it wants to update.

    Annotated[list, operator.add] fields append items on each update
    rather than replacing the entire list — safe for concurrent nodes.
    """

    # ── Input ──────────────────────────────────────────────────────────────
    request: ResearchRequest
    """The original user research request."""

    # ── Run Lifecycle ──────────────────────────────────────────────────────
    run_id: str
    """Unique identifier for this research run."""

    status: ResearchStatus
    """Current lifecycle status of the run."""

    run_metadata: RunMetadata
    """Harness-level metadata: budgets, timeouts, model config."""

    # ── Planning ───────────────────────────────────────────────────────────
    plan: ResearchPlan | None
    """The Planner's decomposition of the query into research tasks."""

    current_task_index: int
    """Which task the Researcher is currently working on."""

    # ── Research ───────────────────────────────────────────────────────────
    tasks: Annotated[list[ResearchTask], operator.add]
    """All research tasks (appended as the Planner creates them)."""

    findings: Annotated[list[Finding], operator.add]
    """All findings gathered across all tasks (appended incrementally)."""

    sources: Annotated[list[Source], operator.add]
    """All unique sources discovered across all tasks."""

    # ── Critique ───────────────────────────────────────────────────────────
    critiques: Annotated[list[Critique], operator.add]
    """All critique passes (one per iteration)."""

    current_critique: Critique | None
    """The most recent critique — used for routing decisions."""

    gaps: Annotated[list[ResearchGap], operator.add]
    """All research gaps identified across all critic passes."""

    critic_pass_count: int
    """How many critic passes have been completed."""

    # ── Loop Control ───────────────────────────────────────────────────────
    should_continue_research: bool
    """
    Set by the Critic. True → loop back to Researcher.
    False → proceed to Synthesizer.
    """

    follow_up_queries: Annotated[list[str], operator.add]
    """Additional queries the Critic wants the Researcher to address."""

    # ── Synthesis ──────────────────────────────────────────────────────────
    final_report: FinalReport | None
    """The Synthesizer's final output."""

    # ── Token / Cost Accounting ────────────────────────────────────────────
    token_usage: TokenUsage
    """Cumulative token usage across all LLM calls in this run."""

    # ── Streaming ──────────────────────────────────────────────────────────
    progress_events: Annotated[list[ProgressEvent], operator.add]
    """Stream of progress events emitted for the SSE layer."""

    # ── Error Handling ─────────────────────────────────────────────────────
    error: str | None
    """If set, the run has failed with this error message."""

    error_node: str | None
    """Which graph node raised the error."""

    # ── Timestamps ─────────────────────────────────────────────────────────
    created_at: str
    """ISO datetime when the run was created."""

    updated_at: str
    """ISO datetime of the last state update."""


# ---------------------------------------------------------------------------
# State Factory — creates a clean initial state
# ---------------------------------------------------------------------------


def create_initial_state(request: ResearchRequest, run_metadata: RunMetadata) -> ResearchState:
    """
    Build the initial ResearchState from a validated ResearchRequest.
    Called by the Agent Harness before invoking the graph.
    """
    now = datetime.utcnow().isoformat()

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
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# State Helpers
# ---------------------------------------------------------------------------


def get_all_findings(state: ResearchState) -> list[Finding]:
    """Return all findings across all tasks in insertion order."""
    return state.get("findings", [])


def get_pending_tasks(state: ResearchState) -> list[ResearchTask]:
    """Return tasks that have not yet been completed."""
    from research_agent.core.models import TaskStatus
    return [t for t in state.get("tasks", []) if t.status == TaskStatus.PENDING]


def get_latest_critique(state: ResearchState) -> Critique | None:
    """Return the most recent critique, or None if no critique has run yet."""
    return state.get("current_critique")


def emit_event(
    node: str,
    event: str,
    message: str,
    data: dict[str, Any] | None = None,
) -> ProgressEvent:
    """
    Helper for agent nodes to create a well-formed ProgressEvent.

    Usage inside a node:
        return {
            "progress_events": [emit_event("planner", "plan_ready", "Plan created with 5 tasks")]
        }
    """
    return ProgressEvent(
        event=event,
        message=message,
        node=node,
        timestamp=datetime.utcnow().isoformat(),
        data=data or {},
    )


def is_budget_exhausted(state: ResearchState) -> bool:
    """Check if the token budget has been exceeded."""
    metadata = state.get("run_metadata", {})
    token_budget = metadata.get("token_budget", float("inf"))
    usage = state.get("token_usage", TokenUsage())
    return usage.total_tokens >= token_budget


def should_stop_critic_loop(state: ResearchState) -> bool:
    """
    Returns True if the critic loop should stop, either because:
    - The critic marked the research as sufficient, OR
    - We've hit the maximum allowed critic passes.
    """
    metadata = state.get("run_metadata", {})
    max_passes = metadata.get("max_critic_passes", 2)
    pass_count = state.get("critic_pass_count", 0)
    critique = get_latest_critique(state)

    if critique and critique.sufficient:
        return True
    if pass_count >= max_passes:
        return True
    return False
