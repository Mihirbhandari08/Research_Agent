from app.domain.execution import ResearchRun
from app.domain.request import ResearchRequest
from app.storage.repositories.runs import RunRepository


def test_run_repository_add_and_list() -> None:
    repository = RunRepository()
    request = ResearchRequest(query="How do large language models work?", max_sources=3)
    run = ResearchRun(run_id="run-123", request=request, metadata=request.metadata)

    repository.add(run)

    assert repository.get("run-123") == run
    assert repository.list() == [run]
