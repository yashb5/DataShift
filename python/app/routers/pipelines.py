from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.pipeline_service import PipelineService
from app.schemas.pipeline import (
    PipelineRequest,
    PipelineResponse,
    PipelineRunResponse,
    PipelineLogResponse,
)

router = APIRouter(prefix="/api/v1/pipelines", tags=["Pipelines"])


@router.post("", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    request: PipelineRequest,
    db: AsyncSession = Depends(get_db),
):
    service = PipelineService(db)
    try:
        return await service.create(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[PipelineResponse])
async def get_all_pipelines(db: AsyncSession = Depends(get_db)):
    service = PipelineService(db)
    return await service.get_all()


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    service = PipelineService(db)
    try:
        return await service.get_by_id(pipeline_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    service = PipelineService(db)
    try:
        await service.delete(pipeline_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{pipeline_id}/run", response_model=PipelineRunResponse)
async def run_pipeline(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    service = PipelineService(db)
    try:
        return await service.run_pipeline(pipeline_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{pipeline_id}/runs", response_model=list[PipelineRunResponse])
async def get_pipeline_runs(
    pipeline_id: int,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = PipelineService(db)
    return await service.get_runs(pipeline_id, page, size)


@router.get("/{pipeline_id}/runs/{run_id}/logs", response_model=list[PipelineLogResponse])
async def get_pipeline_run_logs(
    pipeline_id: int,
    run_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = PipelineService(db)
    return await service.get_run_logs(run_id)
