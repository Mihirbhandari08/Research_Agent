"""
app/observability/logging.py
============================
Centralized structured logging configuration using structlog.
Supports JSON output for production and pretty console output for development.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.config.settings import get_settings


def _add_run_context(logger: Any, method: str, event_dict: EventDict) -> EventDict:
    """
    Processor that injects run_id, node, and thread_id into every log entry
    if they exist in the bound context.
    """
    # These are set via structlog.contextvars.bind_contextvars() per request
    return event_dict


def _drop_color_message_key(logger: Any, method: str, event_dict: EventDict) -> EventDict:
    """
    Remove uvicorn's color_message key from log entries to avoid duplicate messages.
    """
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging() -> None:
    """
    Configures structlog and standard library logging for the entire application.

    - In development: Pretty-printed colored console output with timestamps.
    - In production: JSON structured output suitable for Loki, Datadog, or CloudWatch.
    """
    settings = get_settings()
    is_dev = settings.app.app_env == "development"

    # ── Shared Processors ──────────────────────────────────────────────────
    # These are applied to every log record in both dev and prod
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        _drop_color_message_key,
        _add_run_context,
    ]

    # ── Configure Structlog ────────────────────────────────────────────────
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # ── Choose Formatter ───────────────────────────────────────────────────
    if is_dev:
        # Human-readable, color-highlighted console output for local development
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
        )
    else:
        # JSON structured logs for production observability tools
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
        )

    # ── Configure Root Handler ─────────────────────────────────────────────
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(settings.app.log_level.upper())

    # ── Silence Noisy Libraries ────────────────────────────────────────────
    for noisy_module in ("httpx", "httpcore", "hpack", "asyncio"):
        logging.getLogger(noisy_module).setLevel(logging.WARNING)

    structlog.get_logger(__name__).info(
        "Logging configured",
        env=settings.app.app_env,
        log_level=settings.app.log_level,
        format="console" if is_dev else "json",
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Returns a pre-configured structlog bound logger.

    Usage:
        from app.observability.logging import get_logger
        logger = get_logger(__name__)
        logger.info("task_started", task_id="task_abc123", query="some query")

    Args:
        name: The module name (pass __name__ from the calling module).

    Returns:
        A BoundLogger instance with structured logging capabilities.
    """
    return structlog.get_logger(name)
