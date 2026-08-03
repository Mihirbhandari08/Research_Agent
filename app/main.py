"""Application bootstrap for the research agent API."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.research import router as research_router
from app.api.routes.runs import router as runs_router
from app.config.settings import get_settings
from app.observability.tracing import configure_tracing

settings = get_settings()

app = FastAPI(
    title=settings.app.app_name,
    version=settings.app.app_version,
    debug=settings.app.debug,
)

app.include_router(health_router)
app.include_router(research_router)
app.include_router(runs_router)


@app.on_event("startup")
async def startup_event() -> None:
    configure_tracing()


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": settings.app.app_name, "status": "ok"}
