"""Research request API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.research import ResearchRequestCreate, ResearchRunResponse
from app.services.research_service import ResearchService
from app.api.dependencies import get_research_service

router = APIRouter(prefix="/api/v1", tags=["research"])


@router.post("/research", response_model=ResearchRunResponse, status_code=status.HTTP_201_CREATED)
async def create_research(
    payload: ResearchRequestCreate,
    service: ResearchService = Depends(get_research_service),
) -> ResearchRunResponse:
    try:
        run = await service.create_run(payload.to_domain())
        return ResearchRunResponse.model_validate(run)
    except Exception as exc:  # pragma: no cover - defensive API layer
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
