"""
app/utils/time.py
=================
Time utilities used across the research agent.

Centralizing time operations here means:
- Tests can mock time in one place
- Timezone handling is consistent (always UTC)
- Duration formatting is uniform across logs and reports
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator


# ---------------------------------------------------------------------------
# UTC clock
# ---------------------------------------------------------------------------


def utcnow() -> datetime:
    """
    Return the current UTC datetime (timezone-aware).

    Always use this instead of datetime.utcnow() which returns
    a naive datetime without tzinfo — a common source of bugs.

    Example:
        >>> utcnow()
        datetime.datetime(2025, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc)
    """
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    """
    Return current UTC time as an ISO 8601 string.

    Example:
        >>> utcnow_iso()
        '2025-01-15T10:30:00.000000+00:00'
    """
    return utcnow().isoformat()


def utcnow_timestamp() -> float:
    """
    Return current UTC time as a UNIX timestamp (float seconds).

    Example:
        >>> utcnow_timestamp()
        1736937000.123456
    """
    return time.time()


# ---------------------------------------------------------------------------
# Deadline helpers
# ---------------------------------------------------------------------------


def deadline_from_now(seconds: float) -> datetime:
    """
    Return a UTC datetime that is `seconds` from now.

    Used by the harness to set run/node/llm deadlines.

    Example:
        >>> deadline = deadline_from_now(300)  # 5 minutes from now
    """
    from datetime import timedelta
    return utcnow() + timedelta(seconds=seconds)


def seconds_until(deadline: datetime) -> float:
    """
    Return how many seconds remain until the given UTC deadline.

    Returns 0.0 if the deadline has already passed.

    Example:
        >>> dl = deadline_from_now(60)
        >>> seconds_until(dl)  # ≈ 60.0
    """
    remaining = (deadline - utcnow()).total_seconds()
    return max(0.0, remaining)


def is_expired(deadline: datetime) -> bool:
    """
    Return True if the deadline has passed.

    Example:
        >>> dl = deadline_from_now(-1)  # 1 second in the past
        >>> is_expired(dl)
        True
    """
    return utcnow() >= deadline


# ---------------------------------------------------------------------------
# Duration formatting
# ---------------------------------------------------------------------------


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds into a human-readable string.

    Examples:
        >>> format_duration(0.45)
        '450ms'
        >>> format_duration(5.3)
        '5.3s'
        >>> format_duration(125.0)
        '2m 5s'
        >>> format_duration(3670.0)
        '1h 1m 10s'
    """
    if seconds < 1.0:
        return f"{int(seconds * 1000)}ms"

    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)

    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"

    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)
    return f"{hours}h {remaining_minutes}m {remaining_seconds}s"


def elapsed_seconds(start: datetime) -> float:
    """
    Return how many seconds have elapsed since `start` (UTC-aware).

    Example:
        >>> start = utcnow()
        >>> # ... do work ...
        >>> elapsed = elapsed_seconds(start)
        >>> print(f"Took {format_duration(elapsed)}")
    """
    return (utcnow() - start).total_seconds()


# ---------------------------------------------------------------------------
# Stopwatch context manager
# ---------------------------------------------------------------------------


@contextmanager
def stopwatch() -> Generator[dict[str, float], None, None]:
    """
    Context manager that measures elapsed time.

    Usage:
        with stopwatch() as timer:
            do_work()
        print(f"Elapsed: {timer['elapsed']:.2f}s")

    The dict is updated in-place when the context exits, so you can
    safely capture a reference before the block runs.
    """
    result: dict[str, float] = {"elapsed": 0.0}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["elapsed"] = time.perf_counter() - start
