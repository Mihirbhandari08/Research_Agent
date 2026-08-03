"""Service layer for creating and managing research runs."""

from __future__ import annotations

from app.domain import ResearchRequest
from app.domain.execution import ResearchRun
from app.harness.runner import AgentRunner


class ResearchService:
    """Coordinates research execution and stores run records in memory."""

    def __init__(self, runner: AgentRunner, store: dict[str, ResearchRun] | None = None) -> None:
        self.runner = runner
        self.store = store or {}

    async def create_run(self, request: ResearchRequest) -> ResearchRun:
        run = await self.runner.run(request)
        self.store[run.run_id] = run
        return run

    def get_run(self, run_id: str) -> ResearchRun:
        if run_id not in self.store:
            raise KeyError(run_id)
        return self.store[run_id]
