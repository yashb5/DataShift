from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PipelineLog(Base):
    __tablename__ = "pipeline_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pipeline_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    log_level: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    pipeline_run: Mapped["PipelineRun"] = relationship(
        "PipelineRun",
        back_populates="logs",
    )
