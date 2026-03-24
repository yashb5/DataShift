from datetime import datetime, timedelta
from typing import Sequence
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert_rule import AlertRule
from app.models.alert import Alert
from app.models.pipeline_run import PipelineRun
from app.schemas.alert import (
    AlertRuleRequest,
    AlertRuleResponse,
    AlertResponse,
)


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_rule(self, request: AlertRuleRequest) -> AlertRuleResponse:
        rule = AlertRule(
            name=request.name,
            description=request.description,
            condition_type=request.condition_type,
            pipeline_id=request.pipeline_id,
            threshold=request.threshold,
            time_window_hours=request.time_window_hours,
            severity=request.severity,
        )
        
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        
        return self._rule_to_response(rule)
    
    async def get_all_rules(self) -> list[AlertRuleResponse]:
        result = await self.db.execute(select(AlertRule))
        rules = result.scalars().all()
        return [self._rule_to_response(r) for r in rules]
    
    async def delete_rule(self, rule_id: int) -> None:
        result = await self.db.execute(
            select(AlertRule).where(AlertRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        if not rule:
            raise ValueError(f"Alert rule with id {rule_id} not found")
        
        await self.db.delete(rule)
        await self.db.commit()
    
    async def get_alerts(
        self,
        severity: str | None = None,
        acknowledged: bool | None = None,
    ) -> list[AlertResponse]:
        query = select(Alert)
        
        conditions = []
        if severity is not None:
            conditions.append(Alert.severity == severity)
        if acknowledged is not None:
            conditions.append(Alert.acknowledged == acknowledged)
        
        if conditions:
            query = query.where(*conditions)
        
        result = await self.db.execute(query.order_by(Alert.triggered_at.desc()))
        alerts = result.scalars().all()
        return [self._alert_to_response(a) for a in alerts]
    
    async def get_alert(self, alert_id: int) -> AlertResponse:
        result = await self.db.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        if not alert:
            raise ValueError(f"Alert with id {alert_id} not found")
        return self._alert_to_response(alert)
    
    async def acknowledge_alert(self, alert_id: int) -> AlertResponse:
        result = await self.db.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        if not alert:
            raise ValueError(f"Alert with id {alert_id} not found")
        
        alert.acknowledged = True
        await self.db.commit()
        await self.db.refresh(alert)
        
        return self._alert_to_response(alert)
    
    async def check_and_trigger(self, run: PipelineRun) -> None:
        result = await self.db.execute(
            select(AlertRule).where(
                or_(
                    AlertRule.pipeline_id == None,
                    AlertRule.pipeline_id == run.pipeline_id,
                )
            )
        )
        rules = result.scalars().all()
        
        for rule in rules:
            if await self._matches_rule(rule, run):
                await self._trigger_alert(rule, run)
    
    async def _matches_rule(self, rule: AlertRule, run: PipelineRun) -> bool:
        cutoff = datetime.utcnow() - timedelta(hours=rule.time_window_hours)
        
        query = select(PipelineRun).where(PipelineRun.started_at >= cutoff)
        if rule.pipeline_id:
            query = query.where(PipelineRun.pipeline_id == rule.pipeline_id)
        
        result = await self.db.execute(query)
        runs = result.scalars().all()
        
        if rule.condition_type == "FAILED_COUNT":
            failed_count = sum(1 for r in runs if r.status == "FAILED")
            return failed_count >= rule.threshold
        
        elif rule.condition_type == "NO_SUCCESS":
            success_count = sum(1 for r in runs if r.status == "COMPLETED")
            return success_count == 0
        
        elif rule.condition_type == "AVG_DURATION":
            durations = []
            for r in runs:
                if r.completed_at and r.started_at:
                    durations.append((r.completed_at - r.started_at).total_seconds())
            
            if not durations:
                return False
            
            avg_duration = sum(durations) / len(durations)
            threshold_seconds = rule.threshold * 60
            return avg_duration > threshold_seconds
        
        return False
    
    async def _trigger_alert(self, rule: AlertRule, run: PipelineRun) -> None:
        message = f"Alert triggered for rule '{rule.name}': {rule.condition_type}"
        if rule.pipeline_id:
            message += f" on pipeline {rule.pipeline_id}"
        
        alert = Alert(
            rule_id=rule.id,
            message=message,
            severity=rule.severity,
        )
        
        self.db.add(alert)
        await self.db.commit()
    
    def _rule_to_response(self, rule: AlertRule) -> AlertRuleResponse:
        return AlertRuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            condition_type=rule.condition_type,
            pipeline_id=rule.pipeline_id,
            threshold=rule.threshold,
            time_window_hours=rule.time_window_hours,
            severity=rule.severity,
            created_at=rule.created_at,
        )
    
    def _alert_to_response(self, alert: Alert) -> AlertResponse:
        return AlertResponse(
            id=alert.id,
            rule_id=alert.rule_id,
            message=alert.message,
            severity=alert.severity,
            acknowledged=alert.acknowledged,
            triggered_at=alert.triggered_at,
        )
