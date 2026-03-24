from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.alert_service import AlertService
from app.schemas.alert import (
    AlertRuleRequest,
    AlertRuleResponse,
    AlertResponse,
)

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


@router.post("/rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    request: AlertRuleRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AlertService(db)
    return await service.create_rule(request)


@router.get("/rules", response_model=list[AlertRuleResponse])
async def get_all_alert_rules(db: AsyncSession = Depends(get_db)):
    service = AlertService(db)
    return await service.get_all_rules()


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    service = AlertService(db)
    try:
        await service.delete_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("", response_model=list[AlertResponse])
async def get_alerts(
    severity: str | None = Query(None),
    acknowledged: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AlertService(db)
    return await service.get_alerts(severity, acknowledged)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    service = AlertService(db)
    try:
        return await service.get_alert(alert_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    service = AlertService(db)
    try:
        return await service.acknowledge_alert(alert_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
