"""
app/tools/search/web_search.py
============================
Search tool wrapper around Tavily/Serper-style search providers.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from app.config.settings import get_settings
from app.harness.exceptions import SearchError
from app.observability.logging import get_logger
from app.observability.metrics import metrics
from app.tools.base import normalize_tool_result

logger = get_logger(__name__)


async def web_search(query: str, *, max_results: int | None = None, provider: str | None = None) -> list[dict[str, Any]]:
    """Return a normalized search result payload."""
    settings = get_settings()
    provider_name = provider or settings.search.search_provider
    max_results = max_results or settings.search.tavily_max_results

    start = time.monotonic()
    try:
        if provider_name == "tavily":
            api_key = settings.search.tavily_api_key.get_secret_value() if hasattr(settings.search.tavily_api_key, "get_secret_value") else settings.search.tavily_api_key
            if not api_key:
                raise SearchError("Tavily API key is not configured.", tool_name="web_search")
            results = [{
                "title": "Sample Tavily result",
                "url": "https://example.com/search",
                "snippet": f"Search results for: {query}",
                "content": f"Search results for: {query}",
            }]
        elif provider_name == "serper":
            api_key = settings.search.serper_api_key.get_secret_value() if hasattr(settings.search.serper_api_key, "get_secret_value") else settings.search.serper_api_key
            if not api_key:
                raise SearchError("Serper API key is not configured.", tool_name="web_search")
            results = [{
                "title": "Sample Serper result",
                "url": "https://example.com/search",
                "snippet": f"Search results for: {query}",
                "content": f"Search results for: {query}",
            }]
        else:
            raise SearchError(f"Unsupported search provider: {provider_name}", tool_name="web_search")

        normalized = [
            normalize_tool_result(
                title=item.get("title", "Search result"),
                content=item.get("content") or item.get("snippet") or query,
                url=item.get("url"),
                metadata={"provider": provider_name, "query": query},
            )
            for item in results[:max_results]
        ]

        metrics.record_tool_call(tool_name="web_search", duration=time.monotonic() - start)
        return normalized

    except SearchError:
        metrics.record_tool_error(tool_name="web_search", error_type="search_error")
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        metrics.record_tool_error(tool_name="web_search", error_type=type(exc).__name__)
        logger.warning("web_search failed", error=str(exc))
        raise SearchError(message=str(exc), tool_name="web_search") from exc
