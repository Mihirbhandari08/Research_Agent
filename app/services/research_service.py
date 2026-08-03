"""Service layer for creating and managing research runs."""

from __future__ import annotations

from app.domain import ResearchRequest
from app.domain.execution import ResearchRun
from app.harness.runner import AgentRunner
from app.storage.repositories.runs import RunRepository


class ResearchService:
    """Coordinates research execution and stores run records via repository abstraction."""

    def __init__(self, runner: AgentRunner, repository: RunRepository | None = None) -> None:
        self.runner = runner
        self.repository = repository or RunRepository()

    async def create_run(self, request: ResearchRequest) -> ResearchRun:
        run = await self.runner.run(request)
        self.repository.add(run)
        return run

    def get_run(self, run_id: str) -> ResearchRun:
        return self.repository.get(run_id)
