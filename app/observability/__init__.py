"""
app.observability
=================
Centralized logging, distributed tracing, and Prometheus metrics configuration.
"""

from app.observability.logging import configure_logging, get_logger
from app.observability.tracing import (
    async_node_span,
    configure_tracing,
    node_span,
    traced_node,
)
from app.observability.metrics import ResearchAgentMetrics, metrics

__all__ = [
    # Logging
    "configure_logging",
    "get_logger",
    # Tracing
    "configure_tracing",
    "node_span",
    "async_node_span",
    "traced_node",
    # Metrics
    "ResearchAgentMetrics",
    "metrics",
]
