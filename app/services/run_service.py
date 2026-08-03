"""Run lookup and status service."""

from __future__ import annotations

from app.domain.execution import ResearchRun


class RunService:
    """Read-only service for retrieving stored runs."""

    def __init__(self, store: dict[str, ResearchRun] | None = None) -> None:
        self.store = store or {}

    def get_run(self, run_id: str) -> ResearchRun:
        if run_id not in self.store:
            raise KeyError(run_id)
        return self.store[run_id]

    def list_runs(self) -> list[ResearchRun]:
        return list(self.store.values())
