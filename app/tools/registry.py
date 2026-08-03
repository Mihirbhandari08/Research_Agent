"""
app/tools/registry.py
====================
Registry for tool discovery and invocation.
"""

from __future__ import annotations

from typing import Any, Callable

from app.tools.documents.pdf import extract_pdf
from app.tools.documents.webpage import extract_webpage
from app.tools.search.web_search import web_search


class ToolRegistry:
    """Simple name-to-callable registry for graph tool execution."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> None:
        self._tools[name] = func

    def get(self, name: str) -> Callable[..., Any]:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools[name]

    def list(self) -> list[str]:
        return sorted(self._tools.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._tools


def build_default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("web_search", web_search)
    registry.register("extract_webpage", extract_webpage)
    registry.register("extract_pdf", extract_pdf)
    return registry
