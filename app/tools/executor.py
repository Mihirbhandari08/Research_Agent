"""Execution helper for running registered tools with policy and metric tracking."""

from __future__ import annotations

from typing import Any, Callable

from app.harness.context import RunContext
from app.harness.exceptions import PolicyViolationError
from app.harness.policies import PolicyEvaluator
from app.tools.registry import ToolRegistry


class ToolExecutor:
    """Dispatches a registered tool through policy validation and runtime guards."""

    def __init__(self, registry: ToolRegistry, context: RunContext) -> None:
        self.registry = registry
        self.context = context

    async def execute(self, tool_name: str, *args: Any, **kwargs: Any) -> Any:
        if tool_name not in self.registry:
            raise KeyError(f"Tool '{tool_name}' is not registered.")

        evaluator: PolicyEvaluator = self.context.policy_evaluator
        decision = evaluator.evaluate(tool_name)
        if decision == "deny":
            raise PolicyViolationError(
                message=f"Action '{tool_name}' is forbidden by the current policy.",
                action=tool_name,
                run_id=self.context.run_id,
            )

        func: Callable[..., Any] = self.registry.get(tool_name)
        self.context.record_tool_call()
        return await func(*args, **kwargs)


__all__ = ["ToolExecutor"]
