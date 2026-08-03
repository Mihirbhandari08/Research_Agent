"""Repository for persisted research payloads and report artifacts."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any


class ResearchRepository:
    """Simple in-memory repository for research payloads and supports future DB backends."""

    def __init__(self, initial: MutableMapping[str, Any] | None = None) -> None:
        self._items: dict[str, Any] = dict(initial or {})

    def add(self, key: str, value: Any) -> Any:
        self._items[key] = value
        return value

    def get(self, key: str) -> Any:
        if key not in self._items:
            raise KeyError(key)
        return self._items[key]

    def list(self) -> list[Any]:
        return list(self._items.values())

    def delete(self, key: str) -> None:
        if key in self._items:
            del self._items[key]


__all__ = ["ResearchRepository"]
