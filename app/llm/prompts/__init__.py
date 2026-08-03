"""
app.llm.prompts
===============
Prompt templates used by the LLM gateway for each node in the research graph.
"""

from app.llm.prompts.critic import build_critic_prompt
from app.llm.prompts.planner import build_planner_prompt
from app.llm.prompts.researcher import build_researcher_prompt
from app.llm.prompts.writer import build_writer_prompt

__all__ = [
    "build_planner_prompt",
    "build_researcher_prompt",
    "build_critic_prompt",
    "build_writer_prompt",
]
