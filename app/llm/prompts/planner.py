"""Planner prompt template and helper for research task decomposition."""

from __future__ import annotations

from app.domain import ResearchRequest


def build_planner_prompt(request: ResearchRequest) -> str:
    """Build the planner system/user prompt for decomposing a research request."""
    return f"""
You are the Planner for a research agent.

Goal:
- Decompose the user request into a clear set of concrete research tasks.
- Keep the tasks actionable, atomic, and aligned with the selected research depth.
- Return only valid JSON that matches the expected schema.

User request:
- Query: {request.query}
- Depth: {request.depth.value}
- Max sources: {request.max_sources}
- Focus domains: {', '.join(request.focus_domains) if request.focus_domains else 'none'}
- Output format: {request.output_format.value}

Instructions:
1. Break the request into 2-8 targeted sub-tasks.
2. Each task must be specific and search-oriented.
3. Include rationale for each task and a priority score.
4. Capture the overall research strategy in a concise explanation.
5. Ensure the final JSON contains an array of tasks and a top-level rationale.

Return strict JSON with fields:
- plan_id (string)
- run_id (string)
- original_query (string)
- tasks (array of objects containing: task_id, query, rationale, priority, status, max_sources)
- estimated_depth (string)
- rationale (string)
""".strip()
