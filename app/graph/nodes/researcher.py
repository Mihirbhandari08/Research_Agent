"""
app/graph/nodes/researcher.py
============================
Researcher node for gathering findings and sources from tool executions.
"""

from __future__ import annotations

from app.domain import Finding, Source, SourceType
from app.graph.state import ResearchState, emit_event
from app.observability.logging import get_logger
from app.tools.search.web_search import web_search

logger = get_logger(__name__)


async def researcher_node(state: ResearchState) -> dict:
    request = state["request"]

    search_results = await web_search(
        request.query,
        max_results=min(request.max_sources, 5),
        provider="tavily",
    )

    sources: list[Source] = []
    findings: list[Finding] = []

    for index, result in enumerate(search_results, start=1):
        source = Source(
            title=result.get("title", f"Search result {index}"),
            url=result.get("url") or f"https://example.com/search/{index}",
            source_type=SourceType.WEB_PAGE,
            snippet=result.get("content") or result.get("url") or "Search result excerpt",
            credibility_score=0.75,
            metadata={"query": request.query, "provider": "tavily"},
        )
        sources.append(source)

        findings.append(
            Finding(
                task_id=f"task-{request.run_id}-{index}",
                content=result.get("content") or result.get("title") or "Search result content unavailable.",
                summary=result.get("title", "Search result summary"),
                sources=[source],
                confidence=0.75,
                tags=["search_result"],
                metadata={"query": request.query, "source_url": source.url},
            )
        )

    if not findings:
        findings.append(
            Finding(
                task_id=f"task-{request.run_id}-1",
                content=f"No direct search result was available for: {request.query}",
                summary="Search returned no usable evidence.",
                confidence=0.1,
                tags=["missing_evidence"],
                metadata={"query": request.query},
            )
        )

    event = emit_event(
        node="researcher",
        event="research_completed",
        message="Initial research pass completed and evidence gathered.",
        data={"finding_count": len(findings), "source_count": len(sources)},
    )

    logger.info("researcher gathered evidence", run_id=request.run_id, findings=len(findings), sources=len(sources))
    return {
        "findings": findings,
        "sources": sources,
        "status": "researching",
        "progress_events": [event],
    }
