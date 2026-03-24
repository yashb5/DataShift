from datetime import datetime
from pydantic import BaseModel, Field


class AlertRuleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    condition_type: str = Field(..., alias="conditionType")
    pipeline_id: int | None = Field(None, alias="pipelineId")
    threshold: float
    time_window_hours: int = Field(..., alias="timeWindowHours", gt=0)
    severity: str

    class Config:
        populate_by_name = True


class AlertRuleResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    condition_type: str = Field(..., alias="conditionType")
    pipeline_id: int | None = Field(None, alias="pipelineId")
    threshold: float
    time_window_hours: int = Field(..., alias="timeWindowHours")
    severity: str
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class AlertResponse(BaseModel):
    id: int
    rule_id: int = Field(..., alias="ruleId")
    message: str
    severity: str
    acknowledged: bool
    triggered_at: datetime = Field(..., alias="triggeredAt")

    class Config:
        from_attributes = True
        populate_by_name = True
