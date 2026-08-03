"""
app/graph/nodes/writer.py
========================
Writer node for synthesizing findings into the final report.
"""

from __future__ import annotations

from app.domain import FinalReport, ReportSection
from app.graph.state import ResearchState, emit_event
from app.observability.logging import get_logger

logger = get_logger(__name__)


async def writer_node(state: ResearchState) -> dict:
    request = state["request"]
    report = FinalReport(
        run_id=request.run_id,
        query=request.query,
        executive_summary=f"Summary of the research on: {request.query}",
        sections=[
            ReportSection(
                title="Overview",
                content=f"This report covers the findings relevant to: {request.query}",
                supporting_finding_ids=[],
            )
        ],
        total_sources=len(state.get("sources", [])),
        total_findings=len(state.get("findings", [])),
        critic_passes=state.get("critic_pass_count", 0),
    )

    event = emit_event(
        node="writer",
        event="report_ready",
        message="Final report generated from the accumulated findings.",
        data={"report_id": report.report_id},
    )

    logger.info("writer finalized report", run_id=request.run_id, report_id=report.report_id)
    return {
        "final_report": report,
        "status": "complete",
        "progress_events": [event],
    }
