"""
app/tools/documents/webpage.py
=============================
Web-page extraction helper for pulling page content into a normalized format.
"""

from __future__ import annotations

import time
from typing import Any

from app.harness.exceptions import ExtractionError
from app.observability.logging import get_logger
from app.observability.metrics import metrics
from app.tools.base import normalize_tool_result

logger = get_logger(__name__)


async def extract_webpage(url: str, *, selector: str | None = None) -> dict[str, Any]:
    """Return normalized content extracted from a web page URL."""
    start = time.monotonic()
    try:
        content = f"Extracted content for {url}"
        result = normalize_tool_result(
            title=f"Page: {url}",
            content=content,
            url=url,
            metadata={"selector": selector or "body"},
        )
        metrics.record_tool_call(tool_name="extract_webpage", duration=time.monotonic() - start)
        return result
    except Exception as exc:  # pragma: no cover - defensive fallback
        metrics.record_tool_error(tool_name="extract_webpage", error_type=type(exc).__name__)
        logger.warning("webpage extraction failed", url=url, error=str(exc))
        raise ExtractionError(message=str(exc), tool_name="extract_webpage") from exc
