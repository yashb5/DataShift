from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response

router = APIRouter(tags=["Metrics"])

pipeline_runs_total = Counter(
    "pipelines_runs_total",
    "Total number of pipeline runs",
    ["pipeline", "pipeline_id"],
)

pipeline_runs_success = Counter(
    "pipelines_runs_success",
    "Number of successful pipeline runs",
    ["pipeline", "pipeline_id"],
)

pipeline_runs_failed = Counter(
    "pipelines_runs_failed",
    "Number of failed pipeline runs",
    ["pipeline", "pipeline_id"],
)

pipeline_execution_duration = Histogram(
    "pipelines_execution_duration_seconds",
    "Pipeline execution duration in seconds",
    ["pipeline", "pipeline_id"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)

pipeline_rows_transferred = Counter(
    "pipelines_rows_transferred",
    "Total number of rows transferred",
    ["pipeline", "pipeline_id"],
)

active_pipeline_runs = Gauge(
    "pipelines_active_runs",
    "Number of currently running pipelines",
)


def record_pipeline_run_start(pipeline_name: str, pipeline_id: int):
    pipeline_runs_total.labels(pipeline=pipeline_name, pipeline_id=str(pipeline_id)).inc()
    active_pipeline_runs.inc()


def record_pipeline_run_success(pipeline_name: str, pipeline_id: int, duration_seconds: float, rows: int):
    pipeline_runs_success.labels(pipeline=pipeline_name, pipeline_id=str(pipeline_id)).inc()
    pipeline_execution_duration.labels(pipeline=pipeline_name, pipeline_id=str(pipeline_id)).observe(duration_seconds)
    pipeline_rows_transferred.labels(pipeline=pipeline_name, pipeline_id=str(pipeline_id)).inc(rows)
    active_pipeline_runs.dec()


def record_pipeline_run_failure(pipeline_name: str, pipeline_id: int, duration_seconds: float):
    pipeline_runs_failed.labels(pipeline=pipeline_name, pipeline_id=str(pipeline_id)).inc()
    pipeline_execution_duration.labels(pipeline=pipeline_name, pipeline_id=str(pipeline_id)).observe(duration_seconds)
    active_pipeline_runs.dec()


@router.get("/metrics")
async def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
