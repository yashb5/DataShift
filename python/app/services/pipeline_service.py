import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Sequence
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.connection import Connection
from app.models.pipeline import Pipeline
from app.models.pipeline_run import PipelineRun
from app.models.pipeline_log import PipelineLog
from app.schemas.pipeline import (
    PipelineRequest,
    PipelineResponse,
    PipelineRunResponse,
    PipelineLogResponse,
    PipelineMetricsResponse,
    ExecutionTrendResponse,
)
from app.services.encryption_service import encryption_service

logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, request: PipelineRequest) -> PipelineResponse:
        existing = await self.db.execute(
            select(Pipeline).where(Pipeline.name == request.name)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Pipeline with name '{request.name}' already exists")
        
        source_conn = await self._get_connection(request.source_connection_id)
        target_conn = await self._get_connection(request.target_connection_id)
        
        pipeline = Pipeline(
            name=request.name,
            source_connection_id=request.source_connection_id,
            target_connection_id=request.target_connection_id,
            source_table=request.source_table,
            target_table=request.target_table,
            mapping_config=request.mapping_config,
        )
        
        self.db.add(pipeline)
        await self.db.commit()
        await self.db.refresh(pipeline)
        
        return self._to_response(pipeline)
    
    async def get_all(self) -> list[PipelineResponse]:
        result = await self.db.execute(select(Pipeline))
        pipelines = result.scalars().all()
        return [self._to_response(p) for p in pipelines]
    
    async def get_by_id(self, pipeline_id: int) -> PipelineResponse:
        pipeline = await self._get_pipeline(pipeline_id)
        return self._to_response(pipeline)
    
    async def delete(self, pipeline_id: int) -> None:
        pipeline = await self._get_pipeline(pipeline_id)
        await self.db.delete(pipeline)
        await self.db.commit()
    
    async def run_pipeline(self, pipeline_id: int) -> PipelineRunResponse:
        pipeline = await self._get_pipeline(pipeline_id)
        
        run = PipelineRun(
            pipeline_id=pipeline_id,
            status="PENDING",
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        
        asyncio.create_task(self._execute_pipeline_async(run.id))
        
        return self._run_to_response(run)
    
    async def _execute_pipeline_async(self, run_id: int) -> None:
        from app.database import async_session_maker
        from app.services.alert_service import AlertService
        
        async with async_session_maker() as db:
            try:
                result = await db.execute(
                    select(PipelineRun)
                    .options(selectinload(PipelineRun.pipeline))
                    .where(PipelineRun.id == run_id)
                )
                run = result.scalar_one()
                
                run.status = "RUNNING"
                run.started_at = datetime.utcnow()
                await db.commit()
                
                await self._add_log(db, run.id, "INFO", f"Starting pipeline execution for {run.pipeline.name}")
                
                source_conn = await self._get_connection_by_id(db, run.pipeline.source_connection_id)
                target_conn = await self._get_connection_by_id(db, run.pipeline.target_connection_id)
                
                source_password = encryption_service.decrypt(source_conn.password)
                target_password = encryption_service.decrypt(target_conn.password)
                
                rows = await self._extract_rows(
                    source_conn.type, source_conn.host, source_conn.port,
                    source_conn.database_name, source_conn.username, source_password,
                    run.pipeline.source_table
                )
                
                run.rows_extracted = len(rows)
                await self._add_log(db, run.id, "INFO", f"Extracted {len(rows)} rows from source")
                await db.commit()
                
                if rows:
                    rows_loaded = await self._insert_rows(
                        target_conn.type, target_conn.host, target_conn.port,
                        target_conn.database_name, target_conn.username, target_password,
                        run.pipeline.target_table, rows
                    )
                    run.rows_loaded = rows_loaded
                    await self._add_log(db, run.id, "INFO", f"Loaded {rows_loaded} rows to target")
                
                run.status = "COMPLETED"
                run.completed_at = datetime.utcnow()
                await self._add_log(db, run.id, "INFO", "Pipeline execution completed successfully")
                await db.commit()
                
                alert_service = AlertService(db)
                await alert_service.check_and_trigger(run)
                
            except Exception as e:
                logger.error(f"Pipeline execution failed: {e}")
                run.status = "FAILED"
                run.error_message = str(e)
                run.completed_at = datetime.utcnow()
                await self._add_log(db, run.id, "ERROR", f"Pipeline execution failed: {e}")
                await db.commit()
                
                alert_service = AlertService(db)
                await alert_service.check_and_trigger(run)
    
    async def _add_log(self, db: AsyncSession, run_id: int, level: str, message: str) -> None:
        log = PipelineLog(
            pipeline_run_id=run_id,
            log_level=level,
            message=message,
        )
        db.add(log)
        await db.commit()
    
    async def get_runs(
        self, pipeline_id: int, page: int = 0, size: int = 20
    ) -> list[PipelineRunResponse]:
        result = await self.db.execute(
            select(PipelineRun)
            .where(PipelineRun.pipeline_id == pipeline_id)
            .order_by(PipelineRun.started_at.desc())
            .offset(page * size)
            .limit(size)
        )
        runs = result.scalars().all()
        return [self._run_to_response(r) for r in runs]
    
    async def get_run_logs(self, run_id: int) -> list[PipelineLogResponse]:
        result = await self.db.execute(
            select(PipelineLog)
            .where(PipelineLog.pipeline_run_id == run_id)
            .order_by(PipelineLog.timestamp.asc())
        )
        logs = result.scalars().all()
        return [self._log_to_response(log) for log in logs]
    
    async def get_global_metrics(self) -> PipelineMetricsResponse:
        result = await self.db.execute(select(PipelineRun))
        runs = result.scalars().all()
        
        total_runs = len(runs)
        successful_runs = sum(1 for r in runs if r.status == "COMPLETED")
        failed_runs = sum(1 for r in runs if r.status == "FAILED")
        total_rows = sum((r.rows_extracted or 0) + (r.rows_loaded or 0) for r in runs)
        
        durations = []
        for r in runs:
            if r.completed_at and r.started_at:
                durations.append((r.completed_at - r.started_at).total_seconds())
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        
        return PipelineMetricsResponse(
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            total_rows_transferred=total_rows,
            average_duration_seconds=avg_duration,
            success_rate=success_rate,
        )
    
    async def get_pipeline_metrics(self, pipeline_id: int) -> PipelineMetricsResponse:
        result = await self.db.execute(
            select(PipelineRun).where(PipelineRun.pipeline_id == pipeline_id)
        )
        runs = result.scalars().all()
        
        total_runs = len(runs)
        successful_runs = sum(1 for r in runs if r.status == "COMPLETED")
        failed_runs = sum(1 for r in runs if r.status == "FAILED")
        total_rows = sum((r.rows_extracted or 0) + (r.rows_loaded or 0) for r in runs)
        
        durations = []
        for r in runs:
            if r.completed_at and r.started_at:
                durations.append((r.completed_at - r.started_at).total_seconds())
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        
        return PipelineMetricsResponse(
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            total_rows_transferred=total_rows,
            average_duration_seconds=avg_duration,
            success_rate=success_rate,
        )
    
    async def get_execution_trends(
        self, granularity: str = "daily", days: int = 7
    ) -> list[ExecutionTrendResponse]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(PipelineRun).where(PipelineRun.started_at >= cutoff)
        )
        runs = result.scalars().all()
        
        buckets: dict[str, dict] = {}
        
        for run in runs:
            if granularity == "hourly":
                bucket = run.started_at.strftime("%Y-%m-%d %H:00")
            else:
                bucket = run.started_at.strftime("%Y-%m-%d")
            
            if bucket not in buckets:
                buckets[bucket] = {
                    "run_count": 0,
                    "success_count": 0,
                    "failed_count": 0,
                    "total_duration": 0,
                    "duration_count": 0,
                }
            
            buckets[bucket]["run_count"] += 1
            if run.status == "COMPLETED":
                buckets[bucket]["success_count"] += 1
            elif run.status == "FAILED":
                buckets[bucket]["failed_count"] += 1
            
            if run.completed_at and run.started_at:
                duration = (run.completed_at - run.started_at).total_seconds()
                buckets[bucket]["total_duration"] += duration
                buckets[bucket]["duration_count"] += 1
        
        trends = []
        for bucket, data in sorted(buckets.items()):
            avg_duration = (
                data["total_duration"] / data["duration_count"]
                if data["duration_count"] > 0
                else 0
            )
            trends.append(
                ExecutionTrendResponse(
                    time_bucket=bucket,
                    run_count=data["run_count"],
                    success_count=data["success_count"],
                    failed_count=data["failed_count"],
                    average_duration_seconds=avg_duration,
                )
            )
        
        return trends
    
    async def _get_pipeline(self, pipeline_id: int) -> Pipeline:
        result = await self.db.execute(
            select(Pipeline).where(Pipeline.id == pipeline_id)
        )
        pipeline = result.scalar_one_or_none()
        if not pipeline:
            raise ValueError(f"Pipeline with id {pipeline_id} not found")
        return pipeline
    
    async def _get_connection(self, connection_id: int) -> Connection:
        result = await self.db.execute(
            select(Connection).where(Connection.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        if not connection:
            raise ValueError(f"Connection with id {connection_id} not found")
        return connection
    
    async def _get_connection_by_id(self, db: AsyncSession, connection_id: int) -> Connection:
        result = await db.execute(
            select(Connection).where(Connection.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        if not connection:
            raise ValueError(f"Connection with id {connection_id} not found")
        return connection
    
    def _to_response(self, pipeline: Pipeline) -> PipelineResponse:
        return PipelineResponse(
            id=pipeline.id,
            name=pipeline.name,
            source_connection_id=pipeline.source_connection_id,
            target_connection_id=pipeline.target_connection_id,
            source_table=pipeline.source_table,
            target_table=pipeline.target_table,
            mapping_config=pipeline.mapping_config,
            active=pipeline.active,
            created_at=pipeline.created_at,
            updated_at=pipeline.updated_at,
        )
    
    def _run_to_response(self, run: PipelineRun) -> PipelineRunResponse:
        return PipelineRunResponse(
            id=run.id,
            pipeline_id=run.pipeline_id,
            started_at=run.started_at,
            completed_at=run.completed_at,
            rows_extracted=run.rows_extracted,
            rows_loaded=run.rows_loaded,
            status=run.status,
            error_message=run.error_message,
        )
    
    def _log_to_response(self, log: PipelineLog) -> PipelineLogResponse:
        return PipelineLogResponse(
            id=log.id,
            pipeline_run_id=log.pipeline_run_id,
            timestamp=log.timestamp,
            log_level=log.log_level,
            message=log.message,
        )
    
    async def _extract_rows(
        self,
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        table: str,
    ) -> list[dict]:
        db_type = db_type.lower()
        rows = []
        
        if db_type == "sqlite":
            import aiosqlite
            async with aiosqlite.connect(database) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(f"SELECT * FROM {table}")
                raw_rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                rows = [dict(zip(columns, row)) for row in raw_rows]
        
        elif db_type in ("mysql", "mariadb"):
            import aiomysql
            conn = await aiomysql.connect(
                host=host, port=port, user=username, password=password, db=database
            )
            try:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(f"SELECT * FROM {table}")
                    rows = await cursor.fetchall()
            finally:
                conn.close()
        
        elif db_type == "postgresql":
            import asyncpg
            conn = await asyncpg.connect(
                host=host, port=port, user=username, password=password, database=database
            )
            try:
                records = await conn.fetch(f"SELECT * FROM {table}")
                rows = [dict(record) for record in records]
            finally:
                await conn.close()
        
        return rows
    
    async def _insert_rows(
        self,
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        table: str,
        rows: list[dict],
    ) -> int:
        if not rows:
            return 0
        
        db_type = db_type.lower()
        columns = list(rows[0].keys())
        
        if db_type == "sqlite":
            import aiosqlite
            async with aiosqlite.connect(database) as conn:
                placeholders = ", ".join(["?" for _ in columns])
                col_names = ", ".join(columns)
                sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                
                for row in rows:
                    values = [row[col] for col in columns]
                    await conn.execute(sql, values)
                await conn.commit()
        
        elif db_type in ("mysql", "mariadb"):
            import aiomysql
            conn = await aiomysql.connect(
                host=host, port=port, user=username, password=password, db=database
            )
            try:
                async with conn.cursor() as cursor:
                    placeholders = ", ".join(["%s" for _ in columns])
                    col_names = ", ".join(columns)
                    sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                    
                    for row in rows:
                        values = [row[col] for col in columns]
                        await cursor.execute(sql, values)
                await conn.commit()
            finally:
                conn.close()
        
        elif db_type == "postgresql":
            import asyncpg
            conn = await asyncpg.connect(
                host=host, port=port, user=username, password=password, database=database
            )
            try:
                placeholders = ", ".join([f"${i+1}" for i in range(len(columns))])
                col_names = ", ".join(columns)
                sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                
                for row in rows:
                    values = [row[col] for col in columns]
                    await conn.execute(sql, *values)
            finally:
                await conn.close()
        
        return len(rows)
