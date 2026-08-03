"""FastAPI dependency wiring for service and repository access."""

from __future__ import annotations

from app.config.settings import get_settings
from app.harness.runner import AgentRunner
from app.services.research_service import ResearchService
from app.services.run_service import RunService
from app.storage.repositories.runs import RunRepository

_RUN_REPOSITORY = RunRepository()


def get_run_repository() -> RunRepository:
    return _RUN_REPOSITORY


def get_agent_runner() -> AgentRunner:
    return AgentRunner(get_settings())


def get_research_service() -> ResearchService:
    return ResearchService(runner=get_agent_runner(), repository=get_run_repository())


def get_run_service() -> RunService:
    return RunService(repository=get_run_repository())


__all__ = [
    "get_agent_runner",
    "get_research_service",
    "get_run_repository",
    "get_run_service",
]
