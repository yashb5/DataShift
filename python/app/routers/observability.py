from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.pipeline_service import PipelineService
from app.schemas.pipeline import PipelineMetricsResponse, ExecutionTrendResponse

router = APIRouter(prefix="/api/v1/observability", tags=["Observability"])


@router.get("/pipelines/metrics", response_model=PipelineMetricsResponse)
async def get_global_metrics(db: AsyncSession = Depends(get_db)):
    service = PipelineService(db)
    return await service.get_global_metrics()


@router.get("/pipelines/{pipeline_id}/stats", response_model=PipelineMetricsResponse)
async def get_pipeline_stats(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    service = PipelineService(db)
    return await service.get_pipeline_metrics(pipeline_id)


@router.get("/system/health")
async def get_system_health():
    return {"status": "System is operational"}


@router.get("/trends", response_model=list[ExecutionTrendResponse])
async def get_execution_trends(
    granularity: str = Query("daily", regex="^(hourly|daily)$"),
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    service = PipelineService(db)
    return await service.get_execution_trends(granularity, days)
