"""Repository for persisted research run records."""

from __future__ import annotations

from app.domain.execution import ResearchRun


class RunRepository:
    """Simple in-memory repository used as the storage boundary for runs."""

    def __init__(self, initial: dict[str, ResearchRun] | None = None) -> None:
        self._items: dict[str, ResearchRun] = initial.copy() if initial else {}

    def add(self, run: ResearchRun) -> ResearchRun:
        self._items[run.run_id] = run
        return run

    def get(self, run_id: str) -> ResearchRun:
        if run_id not in self._items:
            raise KeyError(run_id)
        return self._items[run_id]

    def list(self) -> list[ResearchRun]:
        return list(self._items.values())

    def delete(self, run_id: str) -> None:
        if run_id in self._items:
            del self._items[run_id]


__all__ = ["RunRepository"]
