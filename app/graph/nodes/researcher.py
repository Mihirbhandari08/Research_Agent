"""
app/graph/nodes/researcher.py
============================
Researcher node for gathering findings and sources from tool executions.
"""

from __future__ import annotations

from app.domain import Finding, Source, SourceType
from app.graph.state import ResearchState, emit_event
from app.observability.logging import get_logger

logger = get_logger(__name__)


async def researcher_node(state: ResearchState) -> dict:
    request = state["request"]

    findings = [
        Finding(
            finding_id=f"finding_{request.run_id}_1",
            run_id=request.run_id,
            task_id="task-1",
            title="Initial research finding",
            summary=f"Explored the topic: {request.query}",
            evidence="Initial evidence placeholder acquired during the research phase.",
            confidence=0.7,
            source_ids=[],
            category="overview",
        )
    ]
    sources = [
        Source(
            source_id=f"source_{request.run_id}_1",
            run_id=request.run_id,
            title="Research source placeholder",
            url="https://example.com",
            source_type=SourceType.WEB_PAGE,
            snippet="Placeholder source for the current research workflow.",
            credibility_score=0.75,
        )
    ]

    event = emit_event(
        node="researcher",
        event="research_completed",
        message="Initial research pass completed and evidence gathered.",
        data={"finding_count": len(findings), "source_count": len(sources)},
    )

    logger.info("researcher gathered evidence", run_id=request.run_id, findings=len(findings))
    return {
        "findings": findings,
        "sources": sources,
        "status": "researching",
        "progress_events": [event],
    }
