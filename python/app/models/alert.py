from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    rule: Mapped["AlertRule"] = relationship(
        "AlertRule",
        back_populates="alerts",
    )
