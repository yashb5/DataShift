from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, engine
from app.models.pipeline_run import PipelineRun

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    checks = {}
    overall_status = "UP"
    
    db_status = await check_database(db)
    checks["database"] = db_status
    if db_status["status"] != "UP":
        overall_status = "DOWN"
    
    pool_status = await check_connection_pool()
    checks["connectionPool"] = pool_status
    if pool_status["status"] == "DOWN":
        overall_status = "DOWN"
    
    pipeline_status = await check_pipelines(db)
    checks["pipelines"] = pipeline_status
    if pipeline_status["status"] == "DOWN":
        overall_status = "DOWN"
    
    return {
        "status": overall_status,
        "components": checks,
    }


@router.get("/health/liveness")
async def liveness_check():
    return {"status": "UP"}


@router.get("/health/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "UP"}
    except Exception:
        return {"status": "DOWN"}


async def check_database(db: AsyncSession) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "UP",
            "details": {"database": "Connected"},
        }
    except Exception as e:
        return {
            "status": "DOWN",
            "details": {"error": str(e)},
        }


async def check_connection_pool() -> dict:
    try:
        pool = engine.pool
        if hasattr(pool, "size") and hasattr(pool, "checkedout"):
            size = pool.size()
            checked_out = pool.checkedout()
            utilization = (checked_out / size * 100) if size > 0 else 0
            
            status = "DOWN" if utilization > 80 else "UP"
            return {
                "status": status,
                "details": {
                    "poolSize": size,
                    "activeConnections": checked_out,
                    "utilization": f"{utilization:.1f}%",
                },
            }
        return {
            "status": "UNKNOWN",
            "details": {"message": "Pool statistics not available"},
        }
    except Exception as e:
        return {
            "status": "UNKNOWN",
            "details": {"error": str(e)},
        }


async def check_pipelines(db: AsyncSession) -> dict:
    try:
        cutoff = datetime.utcnow() - timedelta(hours=24)
        result = await db.execute(
            select(PipelineRun).where(
                PipelineRun.started_at >= cutoff,
                PipelineRun.status == "FAILED",
            )
        )
        failed_runs = result.scalars().all()
        failed_count = len(failed_runs)
        
        status = "DOWN" if failed_count > 5 else "UP"
        return {
            "status": status,
            "details": {
                "failedRunsLast24Hours": failed_count,
                "threshold": 5,
            },
        }
    except Exception as e:
        return {
            "status": "UNKNOWN",
            "details": {"error": str(e)},
        }
