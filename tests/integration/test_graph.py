import asyncio

from app.domain import ResearchRequest
from app.graph.nodes.researcher import researcher_node


def test_researcher_node_collects_real_search_results(monkeypatch):
    async def fake_web_search(query: str, *, max_results: int | None = None, provider: str | None = None):
        assert query == "Benefits of renewable energy"
        assert max_results == 3
        return [
            {
                "title": "Renewable energy overview",
                "url": "https://example.com/renewable-energy",
                "content": "Renewable energy reduces emissions and improves resilience.",
                "metadata": {"provider": "tavily"},
            }
        ]

    monkeypatch.setattr("app.graph.nodes.researcher.web_search", fake_web_search)

    request = ResearchRequest(
        query="Benefits of renewable energy",
        max_sources=3,
    )

    result = asyncio.run(researcher_node({"request": request}))

    assert result["sources"]
    assert result["sources"][0].url == "https://example.com/renewable-energy"
    assert result["findings"]
    assert result["findings"][0].content == "Renewable energy reduces emissions and improves resilience."
