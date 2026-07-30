"""
app/harness/retry/executor.py
=============================
Async execution wrapper that retries transient failures using exponential backoff and jitter.
"""

import asyncio
from app.observability.logging import get_logger
import random
from typing import Any, Callable, Coroutine, Sequence, Type, TypeVar

from app.harness.retry.policy import RetryPolicy

T = TypeVar("T")
logger = get_logger(__name__)


class RetryExecutor:
    """Wraps async calls with retry logic based on a RetryPolicy."""

    def __init__(self, policy: RetryPolicy) -> None:
        self.policy = policy

    async def execute(
        self,
        coro_fn: Callable[..., Coroutine[Any, Any, T]],
        retryable_exceptions: Sequence[Type[Exception]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Executes an async function, retrying on specified exceptions.

        Args:
            coro_fn: The target async function callable to run.
            retryable_exceptions: Tuple of exceptions that are safe to retry.
            args: Postional arguments passed to the function.
            kwargs: Keyword arguments passed to the function.

        Returns:
            The return value of coro_fn.

        Raises:
            Exception: The last exception caught if all retry attempts fail.
        """
        attempt = 1
        while True:
            try:
                # Execute the async target function
                return await coro_fn(*args, **kwargs)

            except Exception as exc:
                # If we caught an exception we are not configured to retry, or we've hit max attempts, raise
                is_retryable = any(isinstance(exc, exc_type) for exc_type in retryable_exceptions)
                if not is_retryable or attempt >= self.policy.max_attempts:
                    logger.warning(
                        f"Execution failed on attempt {attempt}/{self.policy.max_attempts}. "
                        f"Non-retryable error or attempts exhausted: {exc}"
                    )
                    raise exc

                # Calculate backoff delay: delay = initial_delay * (multiplier ** (attempt - 1))
                backoff = self.policy.initial_delay_seconds * (self.policy.backoff_multiplier ** (attempt - 1))
                delay = min(self.policy.max_delay_seconds, backoff)

                # Inject jitter: randomized delay between 0 and calculated backoff limit
                if self.policy.use_jitter:
                    delay = random.uniform(0, delay)

                logger.info(
                    f"Attempt {attempt}/{self.policy.max_attempts} failed with retryable error ({exc.__class__.__name__}). "
                    f"Retrying in {delay:.2f}s..."
                )

                await asyncio.sleep(delay)
                attempt += 1
