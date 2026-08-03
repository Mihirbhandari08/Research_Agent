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
    findings = state.get("findings", [])
    sources = state.get("sources", [])

    if findings:
        average_confidence = sum(f.confidence for f in findings) / len(findings)
        evidence_density = len(findings) >= 2 and len(sources) >= 1
        sufficient = average_confidence >= 0.6 and evidence_density
    else:
        average_confidence = 0.0
        sufficient = False

    pass_number = state.get("critic_pass_count", 0) + 1
    gaps: list[ResearchGap] = []
    suggested_follow_up_queries: list[str] = []

    if not sufficient:
        gaps.append(
            ResearchGap(
                description="The current evidence is too thin or too low-confidence to support a final answer with confidence.",
                related_task_ids=[],
                severity=Severity.MEDIUM,
                suggested_query=request.query,
            )
        )
        suggested_follow_up_queries.append(f"{request.query} evidence and examples")

    critique = Critique(
        run_id=request.run_id,
        pass_number=pass_number,
        gaps=gaps,
        contradictions=[],
        weak_sources=[],
        overall_confidence=average_confidence,
        sufficient=sufficient,
        reasoning=(
            "The evidence set was assessed for breadth, confidence, and source coverage before synthesis."
            if sufficient
            else "The evidence set is still too weak or sparse; another research pass should gather stronger support."
        ),
        suggested_follow_up_queries=suggested_follow_up_queries,
    )

    should_continue_research = not sufficient and pass_number < request.metadata.max_critic_passes

    event = emit_event(
        node="critic",
        event="critique_ready",
        message="Critique pass completed and evidence sufficiency evaluated.",
        data={"sufficient": critique.sufficient, "should_continue_research": should_continue_research},
    )

    logger.info(
        "critic completed pass",
        run_id=request.run_id,
        sufficient=critique.sufficient,
        should_continue_research=should_continue_research,
    )
    return {
        "current_critique": critique,
        "critiques": [critique],
        "gaps": critique.gaps,
        "critic_pass_count": pass_number,
        "should_continue_research": should_continue_research,
        "status": "critiquing",
        "progress_events": [event],
    }
