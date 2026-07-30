"""
app/harness/lifecycle.py
========================
Lifecycle transition logic and error translators for research runs.
"""

from app.observability.logging import get_logger
from typing import Any

from app.domain import ResearchStatus
from app.graph import ProgressEvent, emit_event
from app.harness.exceptions import CancellationError, ResearchAgentError, TimeoutError

logger = get_logger(__name__)


class LifecycleManager:
    """Manages execution status updates and formats progress events for a run."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id

    def transition(self, new_status: ResearchStatus, message: str, node_name: str = "harness") -> ProgressEvent:
        """
        Transition status and log the step change.

        Args:
            new_status: The target ResearchStatus to transition to.
            message: Explanation for the lifecycle change.
            node_name: Node triggering the transition.

        Returns:
            ProgressEvent: Serializable event to append to graph/streaming state.
        """
        logger.info(f"[run={self.run_id}][status={new_status.value}] {message}")
        return emit_event(
            node=node_name,
            event=f"status_{new_status.value}",
            message=message,
            data={"status": new_status.value},
        )

    def handle_error(self, exc: Exception, node_name: str = "harness") -> dict[str, Any]:
        """
        Translates a caught exception into proper state mutations (error fields, final status, events).

        Args:
            exc: The raised exception to handle.
            node_name: The graph node that failed.

        Returns:
            dict: Partial state updates to be merged into ResearchState.
        """
        error_msg = str(exc)

        # 1. Translate CancellationErrors
        if isinstance(exc, CancellationError):
            logger.warning(f"[run={self.run_id}] Execution was cancelled at node '{node_name}': {error_msg}")
            event = emit_event(
                node=node_name,
                event="run_cancelled",
                message="Research execution was cancelled.",
                data={"error": error_msg},
            )
            return {
                "status": ResearchStatus.CANCELLED,
                "error": error_msg,
                "error_node": node_name,
                "progress_events": [event],
            }

        # 2. Translate TimeoutErrors
        if isinstance(exc, TimeoutError):
            logger.error(f"[run={self.run_id}] Execution timed out at node '{node_name}': {error_msg}")
            event = emit_event(
                node=node_name,
                event="run_timed_out",
                message="Research execution timed out.",
                data={"error": error_msg},
            )
            return {
                "status": ResearchStatus.FAILED,
                "error": error_msg,
                "error_node": node_name,
                "progress_events": [event],
            }

        # 3. Handle standard/system errors
        logger.error(f"[run={self.run_id}] Execution failed at node '{node_name}': {error_msg}", exc_info=True)
        event = emit_event(
            node=node_name,
            event="run_failed",
            message=f"Research execution failed: {error_msg}",
            data={"error": error_msg},
        )
        return {
            "status": ResearchStatus.FAILED,
            "error": error_msg,
            "error_node": node_name,
            "progress_events": [event],
        }
