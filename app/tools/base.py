"""
app/tools/base.py
=================
Shared data structures and helper interfaces for all tool calls.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol


class ToolResult(Protocol):
    """Normalized return contract used by all tools."""

    title: str
    url: str | None
    content: str
    metadata: dict[str, Any]


class BaseTool(Protocol):
    """Minimal interface for tool adapters."""

    name: str

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        ...


def normalize_tool_result(
    *,
    title: str,
    content: str,
    url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "title": title,
        "url": url,
        "content": content,
        "metadata": metadata or {},
    }
