"""Run status and history API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_run_service
from app.api.schemas.research import ResearchRunResponse
from app.services.run_service import RunService

router = APIRouter(prefix="/api/v1", tags=["runs"])


@router.get("/runs", response_model=list[ResearchRunResponse])
async def list_runs(service: RunService = Depends(get_run_service)) -> list[ResearchRunResponse]:
    return [ResearchRunResponse.model_validate(run) for run in service.list_runs()]


@router.get("/runs/{run_id}", response_model=ResearchRunResponse)
async def get_run(run_id: str, service: RunService = Depends(get_run_service)) -> ResearchRunResponse:
    try:
        run = service.get_run(run_id)
        return ResearchRunResponse.model_validate(run)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' was not found.") from exc
