"""
app/graph/workflow.py
====================
Minimal state graph workflow that composes the core research nodes.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.graph.nodes.critic import critic_node
from app.graph.nodes.planner import planner_node
from app.graph.nodes.researcher import researcher_node
from app.graph.nodes.writer import writer_node
from app.graph.state import ResearchState


def _should_continue_router(state: ResearchState) -> str:
    if state.get("should_continue_research"):
        return "researcher"
    return "writer"


workflow = StateGraph(ResearchState)
workflow.add_node("planner", planner_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("critic", critic_node)
workflow.add_node("writer", writer_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "researcher")
workflow.add_edge("researcher", "critic")
workflow.add_conditional_edges(
    "critic",
    _should_continue_router,
    {
        "researcher": "researcher",
        "writer": "writer",
    },
)
workflow.add_edge("writer", END)

compiled_workflow = workflow.compile()
