"""Critic prompt template and helper for evidence evaluation."""

from __future__ import annotations

from app.domain import ResearchRequest


def build_critic_prompt(request: ResearchRequest, findings_summary: str) -> str:
    """Build the critic rubric prompt for evaluating sufficiency and gaps."""
    return f"""
You are the Critic for a research agent.

Goal:
- Judge whether the current evidence is sufficient to answer the user request.
- Highlight missing evidence and contradictions.
- Decide whether additional research is necessary.

User request:
- Query: {request.query}
- Depth: {request.depth.value}

Evidence collected:
{findings_summary}

Instructions:
1. Determine if the evidence is sufficient and explain why.
2. Identify missing information as concrete research gaps.
3. Flag contradictions or weak sources with severity levels.
4. Recommend the next follow-up query if more research is needed.

Return strict JSON with fields:
- pass_number (int)
- gaps (array with description, related_task_ids, severity, suggested_query)
- contradictions (array)
- weak_sources (array)
- overall_confidence (float)
- sufficient (bool)
- reasoning (string)
- suggested_follow_up_queries (array of strings)
""".strip()
