from app.domain.execution import ResearchRun
from app.domain.metadata import RunMetadata
from app.domain.request import ResearchRequest
from app.storage.repositories.runs import RunRepository


def test_run_repository_add_and_list() -> None:
    repository = RunRepository()
    request = ResearchRequest(query="How do large language models work?", max_sources=3)
    metadata = RunMetadata(
        run_id="run-123",
        thread_id="thread-123",
        session_id="session-123",
        user_id="user-123",
        model_name="gemini/gemini-2.5-pro",
        max_critic_passes=2,
        max_tasks=6,
        max_sources_per_task=5,
        token_budget=100000,
        cost_budget_usd=1.0,
        timeout_seconds=300.0,
    )
    run = ResearchRun(run_id="run-123", request=request, metadata=metadata)

    repository.add(run)

    assert repository.get("run-123") == run
    assert repository.list() == [run]
