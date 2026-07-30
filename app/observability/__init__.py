"""
app.observability
=================
Centralized logging, tracing, and metrics configuration.
"""

from app.observability.logging import configure_logging, get_logger

__all__ = ["configure_logging", "get_logger"]
