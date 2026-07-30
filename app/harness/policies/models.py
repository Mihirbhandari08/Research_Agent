"""
app/harness/policies/models.py
==============================
Models representing security policies governing what actions/tools an agent is allowed to execute.
"""

from pydantic import BaseModel, Field


class ActionPolicy(BaseModel):
    """Defines permission rules for tool execution and API actions."""

    allowed_actions: list[str] = Field(
        default_factory=list,
        description="Explicitly allowed actions/tool names (e.g., ['web_search', 'pdf_reader']).",
    )
    forbidden_actions: list[str] = Field(
        default_factory=list,
        description="Explicitly blocked actions/tool names (e.g., ['execute_shell_command']).",
    )
    require_approval_actions: list[str] = Field(
        default_factory=list,
        description="Actions/tool names that are paused and require user human-in-the-loop approval.",
    )
