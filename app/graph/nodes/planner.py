"""
app/graph/nodes/planner.py
=========================
Planner node for decomposing research requests into tasks.
"""

from __future__ import annotations

from app.domain import ResearchPlan, ResearchTask, TaskStatus
from app.graph.state import ResearchState, emit_event
from app.observability.logging import get_logger

logger = get_logger(__name__)


async def planner_node(state: ResearchState) -> dict:
    request = state["request"]
    plan = ResearchPlan(
        run_id=request.run_id,
        original_query=request.query,
        tasks=[
            ResearchTask(
                parent_run_id=request.run_id,
                query=request.query,
                rationale="Initial broad investigation of the research question.",
                priority=5,
                status=TaskStatus.PENDING,
                max_sources=request.max_sources,
            )
        ],
        estimated_depth=request.depth,
        rationale="Break the question into a focused exploration path.",
    )

    event = emit_event(
        node="planner",
        event="plan_created",
        message="Research plan created and tasks initialized.",
        data={"task_count": len(plan.tasks)},
    )

    logger.info("planner generated plan", run_id=request.run_id, task_count=len(plan.tasks))
    return {
        "plan": plan,
        "tasks": plan.tasks,
        "status": "planning",
        "progress_events": [event],
    }
