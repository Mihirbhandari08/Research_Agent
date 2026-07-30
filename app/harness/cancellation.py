"""
app/harness/cancellation.py
===========================
Thread-safe cancellation token implementation using asyncio.Event.
Allows runs to be stopped midway, preventing orphaned jobs and cost overrun.
"""

import asyncio
from typing import Any, Coroutine, TypeVar

from app.harness.exceptions import CancellationError

T = TypeVar("T")


class CancellationToken:
    """A thread-safe cancellation token wrapper around asyncio.Event."""

    def __init__(self) -> None:
        self._event = asyncio.Event()

    @property
    def is_cancelled(self) -> bool:
        """Returns True if the cancellation signal was triggered."""
        return self._event.is_set()

    def cancel(self) -> None:
        """Triggers the cancellation signal."""
        self._event.set()

    def raise_if_cancelled(self) -> None:
        """Raises CancellationError if cancellation was triggered."""
        if self.is_cancelled:
            raise CancellationError("Execution was cancelled by the user or system.")

    async def wait_or_complete(self, coro: Coroutine[Any, Any, T]) -> T:
        """
        Executes a coroutine, but aborts instantly if cancellation is triggered.

        Args:
            coro: The target async operation to execute.

        Returns:
            The output of the coroutine if it finishes before cancellation.

        Raises:
            CancellationError: If the token is cancelled before completion.
        """
        # If already cancelled, do not start execution
        self.raise_if_cancelled()

        task = asyncio.ensure_future(coro)
        cancel_waiter = asyncio.ensure_future(self._event.wait())

        # Wait for either the task to complete or the cancellation event to trigger
        done, pending = await asyncio.wait(
            [task, cancel_waiter],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Clean up tasks
        for p in pending:
            p.cancel()

        if cancel_waiter in done:
            # The cancellation event triggered first
            if not task.done():
                task.cancel()
            raise CancellationError("Execution cancelled during asynchronous operation.")

        # The coroutine finished successfully
        return await task
