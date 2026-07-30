"""
app/harness/budget/guard.py
===========================
Gatekeeper logic that enforces resource limits before executing expensive operations.
"""

from datetime import datetime

from app.domain import ExecutionMetrics
from app.harness.budget.models import ExecutionBudget
from app.harness.exceptions import BudgetExhaustedError
from app.utils.time import elapsed_seconds


class BudgetGuard:
    """Enforces execution constraints against a defined ExecutionBudget."""

    def __init__(self, budget: ExecutionBudget) -> None:
        self.budget = budget

    def check_all(self, metrics: ExecutionMetrics, started_at: datetime) -> None:
        """
        Validates all execution metrics against budget boundaries.

        Args:
            metrics: The accumulated metrics so far.
            started_at: Timestamp when execution started.

        Raises:
            BudgetExhaustedError: If any resource limit has been exceeded.
        """
        self.check_duration(started_at)
        self.check_calls(metrics)
        self.check_tokens(metrics)
        self.check_cost(metrics)

    def check_duration(self, started_at: datetime) -> None:
        """Checks if the elapsed execution time exceeds the maximum allowed duration."""
        elapsed = elapsed_seconds(started_at)
        if elapsed > self.budget.max_duration_seconds:
            raise BudgetExhaustedError(
                message=f"Maximum duration exceeded: {elapsed:.1f}s elapsed (Limit: {self.budget.max_duration_seconds}s).",
                limit_type="duration",
            )

    def check_calls(self, metrics: ExecutionMetrics) -> None:
        """Validates LLM and tool call counts."""
        if metrics.total_llm_calls > self.budget.max_llm_calls:
            raise BudgetExhaustedError(
                message=f"LLM call budget exhausted: {metrics.total_llm_calls} calls made (Limit: {self.budget.max_llm_calls}).",
                limit_type="llm_calls",
            )

        if metrics.total_tool_calls > self.budget.max_tool_calls:
            raise BudgetExhaustedError(
                message=f"Tool call budget exhausted: {metrics.total_tool_calls} calls made (Limit: {self.budget.max_tool_calls}).",
                limit_type="tool_calls",
            )

    def check_tokens(self, metrics: ExecutionMetrics) -> None:
        """Validates prompt and completion token counts."""
        token_usage = metrics.token_usage

        if token_usage.prompt_tokens > self.budget.max_input_tokens:
            raise BudgetExhaustedError(
                message=f"Input token budget exhausted: {token_usage.prompt_tokens} tokens (Limit: {self.budget.max_input_tokens}).",
                limit_type="input_tokens",
            )

        if token_usage.completion_tokens > self.budget.max_output_tokens:
            raise BudgetExhaustedError(
                message=f"Output token budget exhausted: {token_usage.completion_tokens} tokens (Limit: {self.budget.max_output_tokens}).",
                limit_type="output_tokens",
            )

    def check_cost(self, metrics: ExecutionMetrics) -> None:
        """Validates accumulated API costs."""
        cost = metrics.token_usage.estimated_cost_usd
        if cost > self.budget.max_cost_usd:
            raise BudgetExhaustedError(
                message=f"Financial budget exhausted: ${cost:.4f} spent (Limit: ${self.budget.max_cost_usd:.2f}).",
                limit_type="financial_cost",
            )
