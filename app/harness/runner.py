"""
app/harness/runner.py
=====================
The core AgentRunner that sets up the execution context, budget limits,
and streams the compiled LangGraph workflow.
"""

import asyncio
from app.observability.logging import get_logger
from typing import Any

from app.config.settings import Settings
from app.domain import (
    ExecutionMetrics,
    ResearchRequest,
    ResearchRun,
    ResearchStatus,
    TokenUsage,
)
from app.graph import create_initial_state
from app.harness.budget import BudgetGuard, ExecutionBudget
from app.harness.cancellation import CancellationToken
from app.harness.context import RunContext
from app.harness.events import event_publisher
from app.harness.lifecycle import LifecycleManager
from app.harness.policies import ActionPolicy, PolicyEvaluator
from app.utils.ids import new_thread_id
from app.utils.time import deadline_from_now, utcnow

logger = get_logger(__name__)


class AgentRunner:
    """Orchestrates runtime configuration, guards, and workflow execution for research runs."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def run(
        self,
        request: ResearchRequest,
        cancellation_token: CancellationToken | None = None,
    ) -> ResearchRun:
        """
        Executes a research request end-to-end within the harness limits.

        Args:
            request: The validated user request configuration.
            cancellation_token: Optional token for canceling the run.

        Returns:
            ResearchRun: The final execution state report.
        """
        # 1. Establish identities
        run_id = request.run_id
        thread_id = new_thread_id()
        cancellation_token = cancellation_token or CancellationToken()

        # 2. Build Budget and Guard
        budget = ExecutionBudget(
            max_duration_seconds=request.depth_config.get("max_tasks", 6) * self.settings.timeouts.node_seconds,
            max_iterations=request.depth_config.get("max_critic_passes", 2),
            max_llm_calls=self.settings.budgets.default_max_llm_calls,
            max_tool_calls=self.settings.budgets.default_max_tool_calls,
            max_input_tokens=self.settings.budgets.default_max_input_tokens,
            max_output_tokens=self.settings.budgets.default_max_output_tokens,
            max_cost_usd=self.settings.budgets.default_max_cost_usd,
        )
        budget_guard = BudgetGuard(budget)

        # 3. Build Security Policies
        # (By default whitelisting tavily/serper search and web extraction tools)
        policy = ActionPolicy(
            allowed_actions=["web_search", "web_extract", "pdf_extract"],
            forbidden_actions=["execute_shell_command", "file_delete"],
        )
        policy_evaluator = PolicyEvaluator(policy)

        # 4. Build Timing and Context
        deadline = deadline_from_now(budget.max_duration_seconds)
        run_context = RunContext(
            run_id=run_id,
            thread_id=thread_id,
            budget_guard=budget_guard,
            policy_evaluator=policy_evaluator,
            cancellation_token=cancellation_token,
            session_id=request.metadata.session_id,
            user_id=request.metadata.user_id,
            started_at=utcnow(),
            deadline=deadline,
        )

        # 5. Build Lifecycle and Tracking record
        lifecycle = LifecycleManager(run_id)
        run_record = ResearchRun(
            run_id=run_id,
            status=ResearchStatus.QUEUED,
            request=request,
            metadata=run_context.to_metadata(self.settings.llm.gemini_default_model),
            metrics=run_context.metrics,
        )

        # 6. Initialize State and config dictionary
        state = create_initial_state(request, run_record.metadata)
        config = {
            "configurable": {
                "context": run_context,
            },
            "recursion_limit": 100,
        }

        # 7. Import graph workflow dynamically to avoid premature module load issues
        from app.graph.workflow import workflow

        # Transition status to PLANNING
        start_event = lifecycle.transition(ResearchStatus.PLANNING, "Starting research request planning stage.")
        await event_publisher.publish(run_id, start_event)
        run_record.update_status(ResearchStatus.PLANNING)

        try:
            # Stream graph updates node-by-node
            async for chunk in workflow.astream(state, config=config, stream_mode="updates"):
                # verify timeout and cancellation on every node step transition
                run_context.verify_guards()

                for node_name, state_update in chunk.items():
                    # Stream progress events to subscribers
                    events = state_update.get("progress_events", [])
                    for event in events:
                        await event_publisher.publish(run_id, event)

                    # Accumulate metrics
                    run_record.metrics = run_context.metrics

                    # Capture updates to status, plan, and final report
                    if "status" in state_update:
                        run_record.update_status(state_update["status"])
                    if "plan" in state_update:
                        run_record.plan = state_update["plan"]
                    if "final_report" in state_update:
                        run_record.latest_report = state_update["final_report"]

            # Complete execution
            if run_record.status not in (ResearchStatus.FAILED, ResearchStatus.CANCELLED):
                run_record.update_status(ResearchStatus.COMPLETE)
                completion_event = lifecycle.transition(ResearchStatus.COMPLETE, "Research run completed successfully.")
                await event_publisher.publish(run_id, completion_event)

        except Exception as exc:
            # Translate exception and update state
            updates = lifecycle.handle_error(exc, node_name="runner")
            run_record.update_status(updates["status"])
            run_record.error = updates["error"]

            # Broadcast failure events
            for event in updates.get("progress_events", []):
                await event_publisher.publish(run_id, event)

        return run_record
