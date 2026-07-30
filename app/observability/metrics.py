"""
app/observability/metrics.py
============================
Prometheus metrics definitions for real-time Grafana dashboards.
Tracks research run lifecycle, LLM gateway performance, and tool usage patterns.
"""

from typing import Any

from app.observability.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lazy Import Helpers
# ---------------------------------------------------------------------------

def _get_prometheus():
    """Lazy import of prometheus_client to avoid hard dependency at startup."""
    try:
        import prometheus_client
        return prometheus_client
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Metric Definitions
# ---------------------------------------------------------------------------


class ResearchAgentMetrics:
    """
    Prometheus metrics registry for the research agent system.
    Initializes counters and histograms lazily to allow graceful degradation
    when prometheus_client is not installed.
    """

    def __init__(self) -> None:
        self._initialized = False
        self._prom = _get_prometheus()

        if self._prom:
            self._init_metrics()
        else:
            logger.warning("prometheus_client not installed. Metrics collection disabled.")

    def _init_metrics(self) -> None:
        """Initialize all Prometheus metric instruments."""
        prom = self._prom

        # ── Research Run Counters ──────────────────────────────────────────
        self.runs_started = prom.Counter(
            "research_runs_started_total",
            "Total number of research runs that have started.",
            ["depth"],
        )
        self.runs_completed = prom.Counter(
            "research_runs_completed_total",
            "Total number of research runs that completed successfully.",
            ["depth"],
        )
        self.runs_failed = prom.Counter(
            "research_runs_failed_total",
            "Total number of research runs that failed.",
            ["reason"],
        )
        self.runs_cancelled = prom.Counter(
            "research_runs_cancelled_total",
            "Total number of research runs cancelled by the client.",
        )

        # ── Run Duration Histogram ─────────────────────────────────────────
        self.run_duration_seconds = prom.Histogram(
            "research_run_duration_seconds",
            "End-to-end duration of a completed research run in seconds.",
            ["depth"],
            buckets=[10, 30, 60, 120, 180, 300, 600],
        )

        # ── LLM Gateway Metrics ────────────────────────────────────────────
        self.llm_calls_total = prom.Counter(
            "llm_calls_total",
            "Total number of LLM API calls made.",
            ["model", "node"],
        )
        self.llm_call_duration_seconds = prom.Histogram(
            "llm_call_duration_seconds",
            "Duration of individual LLM API calls in seconds.",
            ["model", "node"],
            buckets=[0.5, 1, 2, 5, 10, 20, 30, 60],
        )
        self.llm_tokens_total = prom.Counter(
            "llm_tokens_total",
            "Total tokens consumed from LLM APIs.",
            ["model", "token_type"],  # token_type: prompt | completion
        )
        self.llm_cost_usd_total = prom.Counter(
            "llm_cost_usd_total",
            "Cumulative estimated LLM API costs in USD.",
            ["model"],
        )

        # ── Tool Execution Metrics ─────────────────────────────────────────
        self.tool_calls_total = prom.Counter(
            "tool_calls_total",
            "Total number of tool executions by the Researcher node.",
            ["tool_name"],
        )
        self.tool_errors_total = prom.Counter(
            "tool_errors_total",
            "Total number of tool execution failures.",
            ["tool_name", "error_type"],
        )
        self.tool_duration_seconds = prom.Histogram(
            "tool_duration_seconds",
            "Duration of individual tool executions in seconds.",
            ["tool_name"],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
        )

        # ── Critic Loop Metrics ────────────────────────────────────────────
        self.critic_passes_total = prom.Counter(
            "critic_passes_total",
            "Total number of research critique passes performed.",
        )
        self.critic_gaps_found_total = prom.Counter(
            "critic_gaps_found_total",
            "Total number of research gaps identified by the Critic.",
            ["severity"],
        )

        self._initialized = True
        logger.info("Prometheus metrics initialized.")

    # ── Emission Helpers ───────────────────────────────────────────────────

    def record_run_started(self, depth: str) -> None:
        if self._initialized:
            self.runs_started.labels(depth=depth).inc()

    def record_run_completed(self, depth: str, duration: float) -> None:
        if self._initialized:
            self.runs_completed.labels(depth=depth).inc()
            self.run_duration_seconds.labels(depth=depth).observe(duration)

    def record_run_failed(self, reason: str) -> None:
        if self._initialized:
            self.runs_failed.labels(reason=reason).inc()

    def record_run_cancelled(self) -> None:
        if self._initialized:
            self.runs_cancelled.inc()

    def record_llm_call(
        self,
        model: str,
        node: str,
        duration: float,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
    ) -> None:
        if self._initialized:
            self.llm_calls_total.labels(model=model, node=node).inc()
            self.llm_call_duration_seconds.labels(model=model, node=node).observe(duration)
            self.llm_tokens_total.labels(model=model, token_type="prompt").inc(prompt_tokens)
            self.llm_tokens_total.labels(model=model, token_type="completion").inc(completion_tokens)
            self.llm_cost_usd_total.labels(model=model).inc(cost)

    def record_tool_call(self, tool_name: str, duration: float) -> None:
        if self._initialized:
            self.tool_calls_total.labels(tool_name=tool_name).inc()
            self.tool_duration_seconds.labels(tool_name=tool_name).observe(duration)

    def record_tool_error(self, tool_name: str, error_type: str) -> None:
        if self._initialized:
            self.tool_errors_total.labels(tool_name=tool_name, error_type=error_type).inc()

    def record_critic_pass(self, gaps: int, severity_counts: dict[str, int]) -> None:
        if self._initialized:
            self.critic_passes_total.inc()
            for severity, count in severity_counts.items():
                self.critic_gaps_found_total.labels(severity=severity).inc(count)


# Global singleton metric registry
metrics = ResearchAgentMetrics()
