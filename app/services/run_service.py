"""Run lookup and status service."""

from __future__ import annotations

from app.domain.execution import ResearchRun
from app.storage.repositories.runs import RunRepository


class RunService:
    """Read-only service for retrieving stored runs."""

    def __init__(self, repository: RunRepository | None = None) -> None:
        self.repository = repository or RunRepository()

    def get_run(self, run_id: str) -> ResearchRun:
        return self.repository.get(run_id)

    def list_runs(self) -> list[ResearchRun]:
        return self.repository.list()
