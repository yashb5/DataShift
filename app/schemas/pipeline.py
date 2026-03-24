from datetime import datetime
from pydantic import BaseModel, Field


class PipelineRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_connection_id: int = Field(..., alias="sourceConnectionId", gt=0)
    target_connection_id: int = Field(..., alias="targetConnectionId", gt=0)
    source_table: str = Field(..., min_length=1, max_length=255, alias="sourceTable")
    target_table: str = Field(..., min_length=1, max_length=255, alias="targetTable")
    mapping_config: str | None = Field(None, alias="mappingConfig")

    class Config:
        populate_by_name = True


class PipelineResponse(BaseModel):
    id: int
    name: str
    source_connection_id: int = Field(..., alias="sourceConnectionId")
    target_connection_id: int = Field(..., alias="targetConnectionId")
    source_table: str = Field(..., alias="sourceTable")
    target_table: str = Field(..., alias="targetTable")
    mapping_config: str | None = Field(None, alias="mappingConfig")
    active: bool
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class PipelineRunResponse(BaseModel):
    id: int
    pipeline_id: int = Field(..., alias="pipelineId")
    started_at: datetime = Field(..., alias="startedAt")
    completed_at: datetime | None = Field(None, alias="completedAt")
    rows_extracted: int = Field(..., alias="rowsExtracted")
    rows_loaded: int = Field(..., alias="rowsLoaded")
    status: str
    error_message: str | None = Field(None, alias="errorMessage")

    class Config:
        from_attributes = True
        populate_by_name = True


class PipelineLogResponse(BaseModel):
    id: int
    pipeline_run_id: int = Field(..., alias="pipelineRunId")
    timestamp: datetime
    log_level: str = Field(..., alias="logLevel")
    message: str

    class Config:
        from_attributes = True
        populate_by_name = True


class PipelineMetricsResponse(BaseModel):
    total_runs: int = Field(..., alias="totalRuns")
    successful_runs: int = Field(..., alias="successfulRuns")
    failed_runs: int = Field(..., alias="failedRuns")
    total_rows_transferred: int = Field(..., alias="totalRowsTransferred")
    average_duration_seconds: float = Field(..., alias="averageDurationSeconds")
    success_rate: float = Field(..., alias="successRate")

    class Config:
        populate_by_name = True


class ExecutionTrendResponse(BaseModel):
    time_bucket: str = Field(..., alias="timeBucket")
    run_count: int = Field(..., alias="runCount")
    success_count: int = Field(..., alias="successCount")
    failed_count: int = Field(..., alias="failedCount")
    average_duration_seconds: float = Field(..., alias="averageDurationSeconds")

    class Config:
        populate_by_name = True
