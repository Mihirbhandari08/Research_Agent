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
    findings = state.get("findings", [])
    sources = state.get("sources", [])
    critique = state.get("current_critique")

    summary_points = [
        finding.summary or finding.content for finding in findings[:3]
    ]
    executive_summary = "\n".join(f"- {point}" for point in summary_points) or f"Research summary for: {request.query}"

    report_sections = []
    if findings:
        report_sections.append(
            ReportSection(
                title="Key findings",
                content="\n\n".join(
                    f"### {finding.summary or 'Finding'}\n{finding.content}" for finding in findings[:5]
                ),
                supporting_finding_ids=[finding.finding_id for finding in findings[:5]],
            )
        )

    report = FinalReport(
        run_id=request.run_id,
        query=request.query,
        executive_summary=executive_summary,
        sections=report_sections or [
            ReportSection(
                title="Overview",
                content=f"This report covers the topic: {request.query}",
                supporting_finding_ids=[],
            )
        ],
        total_sources=len(sources),
        total_findings=len(findings),
        critic_passes=state.get("critic_pass_count", 0),
        overall_confidence=critique.overall_confidence if critique else 0.5,
        gaps_acknowledged=critique.gaps if critique else [],
    )

    event = emit_event(
        node="writer",
        event="report_ready",
        message="Final report generated from the accumulated findings.",
        data={"report_id": report.report_id, "finding_count": len(findings)},
    )

    logger.info("writer finalized report", run_id=request.run_id, report_id=report.report_id)
    return {
        "final_report": report,
        "status": "complete",
        "progress_events": [event],
    }
