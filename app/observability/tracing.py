"""
app/observability/tracing.py
============================
Distributed tracing setup using LangSmith and OpenTelemetry (OTEL).
Provides span decorators and context managers for instrumenting LLM calls and graph nodes.
"""

import functools
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Callable, Generator, TypeVar

from app.observability.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# ---------------------------------------------------------------------------
# LangSmith Setup
# ---------------------------------------------------------------------------


def configure_langsmith() -> bool:
    """
    Activates LangSmith tracing if credentials are configured.

    Returns:
        bool: True if LangSmith was successfully configured, False otherwise.
    """
    try:
        from app.config.settings import get_settings

        settings = get_settings()

        api_key = settings.langsmith.api_key.get_secret_value() if hasattr(settings.langsmith.api_key, "get_secret_value") else settings.langsmith.api_key
        if not api_key:
            logger.info("LangSmith tracing disabled: LANGSMITH_API_KEY not set.")
            return False

        if not settings.langsmith.tracing_enabled:
            logger.info("LangSmith tracing disabled via LANGSMITH_TRACING_ENABLED=false.")
            return False

        import os

        # LangSmith reads these from environment variables automatically
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith.project

        logger.info("LangSmith tracing enabled.", project=settings.langsmith.project)
        return True

    except Exception as exc:
        logger.warning("LangSmith configuration failed.", error=str(exc))
        return False


# ---------------------------------------------------------------------------
# OpenTelemetry Setup
# ---------------------------------------------------------------------------


def configure_otel() -> bool:
    """
    Configures OpenTelemetry tracing with an OTLP HTTP exporter.
    Exports spans to configured OTEL_EXPORTER_ENDPOINT (e.g., Jaeger, Tempo, Honeycomb).

    Returns:
        bool: True if OTEL was successfully configured, False otherwise.
    """
    try:
        from app.config.settings import get_settings

        settings = get_settings()

        if not settings.otel.exporter_endpoint:
            logger.info("OTEL tracing disabled: OTEL_EXPORTER_ENDPOINT not set.")
            return False

        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        existing = trace.get_tracer_provider()
        if not isinstance(existing, TracerProvider):
            resource = Resource.create({"service.name": settings.otel.service_name})
            provider = TracerProvider(resource=resource)
            exporter = OTLPSpanExporter(endpoint=settings.otel.exporter_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
        else:
            logger.info("OTEL tracer provider already configured; skipping re-registration.")

        logger.info(
            "OTEL tracing enabled.",
            service=settings.otel.service_name,
            endpoint=settings.otel.exporter_endpoint,
        )
        return True

    except ImportError:
        logger.warning("OTEL packages not installed. Install: opentelemetry-sdk opentelemetry-exporter-otlp.")
        return False
    except Exception as exc:
        logger.warning("OTEL configuration failed.", error=str(exc))
        return False


def configure_tracing() -> None:
    """
    Bootstrap all supported tracing backends at application startup.
    Called once from app/main.py during lifespan.
    """
    langsmith_ok = configure_langsmith()
    otel_ok = configure_otel()

    if not langsmith_ok and not otel_ok:
        logger.info("No distributed tracing configured. Running without trace export.")


# ---------------------------------------------------------------------------
# Span Helpers
# ---------------------------------------------------------------------------


@contextmanager
def node_span(node_name: str, run_id: str, **attributes: Any) -> Generator[None, None, None]:
    """
    Synchronous context manager that creates an OTEL span for a graph node.
    Falls back silently if OTEL is not configured.

    Usage:
        with node_span("planner", run_id=run_id, query="..."):
            ...
    """
    try:
        from opentelemetry import trace

        tracer = trace.get_tracer("research_agent")
        with tracer.start_as_current_span(f"node.{node_name}") as span:
            span.set_attribute("run_id", run_id)
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
            yield
    except Exception:
        # OTEL not configured or failed — continue silently
        yield


@asynccontextmanager
async def async_node_span(node_name: str, run_id: str, **attributes: Any) -> AsyncGenerator[None, None]:
    """
    Async context manager that creates an OTEL span for an async graph node.
    Falls back silently if OTEL is not configured.

    Usage:
        async with async_node_span("researcher", run_id=run_id):
            await do_research(...)
    """
    try:
        from opentelemetry import trace

        tracer = trace.get_tracer("research_agent")
        with tracer.start_as_current_span(f"node.{node_name}") as span:
            span.set_attribute("run_id", run_id)
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
            yield
    except Exception:
        yield


def traced_node(node_name: str) -> Callable[[F], F]:
    """
    Decorator that automatically wraps an async graph node function in an OTEL span.

    Usage:
        @traced_node("planner")
        async def planner_node(state: ResearchState, config: dict) -> dict:
            ...
    """
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract run_id from the first argument (state dict) if possible
            run_id = "unknown"
            if args and isinstance(args[0], dict):
                run_id = args[0].get("run_id", "unknown")

            async with async_node_span(node_name, run_id=run_id):
                return await fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
