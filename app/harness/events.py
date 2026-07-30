"""
app/harness/events.py
=====================
Thread-safe event publishing and subscription router for real-time run progress streaming (SSE).
"""

import asyncio
from collections import defaultdict
from app.observability.logging import get_logger
from typing import AsyncGenerator

from app.graph import ProgressEvent

logger = get_logger(__name__)


class RunEventPublisher:
    """Manages real-time streaming subscriptions for executing research runs."""

    def __init__(self) -> None:
        # Maps run_id -> set of active client queues
        self._listeners: dict[str, set[asyncio.Queue[ProgressEvent]]] = defaultdict(set)
        # Lock to ensure thread-safe listener updates
        self._lock = asyncio.Lock()

    async def subscribe(self, run_id: str) -> AsyncGenerator[ProgressEvent, None]:
        """
        Creates a subscriber queue for a specific run and yields events as they arrive.

        Args:
            run_id: The ID of the research run to follow.

        Yields:
            ProgressEvent: Serializable progress events.
        """
        queue: asyncio.Queue[ProgressEvent] = asyncio.Queue()

        async with self._lock:
            self._listeners[run_id].add(queue)
            logger.info(f"Client subscribed to stream for run_id: {run_id} (active listeners: {len(self._listeners[run_id])})")

        try:
            while True:
                # Retrieve the next event and yield it to the async stream
                event = await queue.get()
                yield event
                queue.task_done()
        except asyncio.CancelledError:
            # Handle client disconnect gracefully
            pass
        finally:
            async with self._lock:
                if run_id in self._listeners:
                    self._listeners[run_id].discard(queue)
                    if not self._listeners[run_id]:
                        del self._listeners[run_id]
                    logger.info(f"Client unsubscribed from run_id: {run_id}")

    async def publish(self, run_id: str, event: ProgressEvent) -> None:
        """
        Broadcasts a progress event to all active subscribers of a run.

        Args:
            run_id: The run ID triggering the progress event.
            event: The formatted ProgressEvent payload.
        """
        async with self._lock:
            queues = self._listeners.get(run_id)
            if not queues:
                return

            for queue in queues:
                await queue.put(event)


# Global singleton instance for app-wide event distribution
event_publisher = RunEventPublisher()
