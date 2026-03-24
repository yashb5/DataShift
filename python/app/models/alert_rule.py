from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition_type: Mapped[str] = mapped_column(String(50), nullable=False)
    pipeline_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    time_window_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="rule",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
