"""
app/tools/documents/pdf.py
=========================
PDF extraction helper placeholder for reading and normalizing document text.
"""

from __future__ import annotations

import time
from typing import Any

from app.harness.exceptions import DocumentReadError
from app.observability.logging import get_logger
from app.observability.metrics import metrics
from app.tools.base import normalize_tool_result

logger = get_logger(__name__)


async def extract_pdf(path: str) -> dict[str, Any]:
    """Return normalized content extracted from a PDF file path."""
    start = time.monotonic()
    try:
        content = f"Extracted PDF text from {path}"
        result = normalize_tool_result(
            title=f"PDF: {path}",
            content=content,
            url=None,
            metadata={"path": path},
        )
        metrics.record_tool_call(tool_name="extract_pdf", duration=time.monotonic() - start)
        return result
    except Exception as exc:  # pragma: no cover - defensive fallback
        metrics.record_tool_error(tool_name="extract_pdf", error_type=type(exc).__name__)
        logger.warning("pdf extraction failed", path=path, error=str(exc))
        raise DocumentReadError(message=str(exc), tool_name="extract_pdf") from exc
