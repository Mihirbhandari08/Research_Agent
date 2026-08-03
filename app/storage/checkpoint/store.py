"""Simple checkpoint storage for graph state snapshots during long-running workflows."""

from __future__ import annotations

from typing import Any


class CheckpointStore:
    """Stores intermediate graph state checkpoints keyed by run ID."""

    def __init__(self, initial: dict[str, dict[str, Any]] | None = None) -> None:
        self._items: dict[str, dict[str, Any]] = dict(initial or {})

    def save(self, run_id: str, checkpoint: dict[str, Any]) -> dict[str, Any]:
        self._items[run_id] = checkpoint
        return checkpoint

    def get(self, run_id: str) -> dict[str, Any]:
        if run_id not in self._items:
            raise KeyError(run_id)
        return self._items[run_id]

    def list(self) -> list[dict[str, Any]]:
        return list(self._items.values())

    def delete(self, run_id: str) -> None:
        if run_id in self._items:
            del self._items[run_id]


__all__ = ["CheckpointStore"]
