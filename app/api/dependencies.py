"""FastAPI dependency wiring for starter services and in-memory run storage."""

from __future__ import annotations

from app.config.settings import get_settings
from app.domain.execution import ResearchRun
from app.harness.runner import AgentRunner
from app.services.research_service import ResearchService
from app.services.run_service import RunService

_RUN_STORE: dict[str, ResearchRun] = {}


def get_run_store() -> dict[str, ResearchRun]:
    return _RUN_STORE


def get_agent_runner() -> AgentRunner:
    return AgentRunner(get_settings())


def get_research_service() -> ResearchService:
    return ResearchService(runner=get_agent_runner(), store=get_run_store())


def get_run_service() -> RunService:
    return RunService(store=get_run_store())


__all__ = [
    "get_agent_runner",
    "get_research_service",
    "get_run_service",
    "get_run_store",
]
