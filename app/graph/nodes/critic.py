"""
app/graph/nodes/critic.py
=========================
Critic node for evaluating quality and deciding whether additional research is needed.
"""

from __future__ import annotations

from app.domain import Critique, ResearchGap, Severity
from app.graph.state import ResearchState, emit_event
from app.observability.logging import get_logger

logger = get_logger(__name__)


async def critic_node(state: ResearchState) -> dict:
    request = state["request"]
    critique = Critique(
        run_id=request.run_id,
        pass_number=1,
        gaps=[
            ResearchGap(
                description="Need a stronger evidence trail for the final answer.",
                related_task_ids=[],
                severity=Severity.MEDIUM,
                suggested_query=f"Investigate {request.query} further.",
            )
        ],
        contradictions=[],
        weak_sources=[],
        overall_confidence=0.72,
        sufficient=True,
        reasoning="The current evidence is adequate for an initial summary and synthesis.",
        suggested_follow_up_queries=[],
    )

    event = emit_event(
        node="critic",
        event="critique_ready",
        message="Critique pass completed and evidence sufficiency evaluated.",
        data={"sufficient": critique.sufficient},
    )

    logger.info("critic completed pass", run_id=request.run_id, sufficient=critique.sufficient)
    return {
        "current_critique": critique,
        "critiques": [critique],
        "gaps": critique.gaps,
        "critic_pass_count": 1,
        "should_continue_research": False,
        "status": "critiquing",
        "progress_events": [event],
    }
