from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pipeline_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rows_extracted: Mapped[int] = mapped_column(Integer, default=0)
    rows_loaded: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    pipeline: Mapped["Pipeline"] = relationship(
        "Pipeline",
        back_populates="runs",
    )
    logs: Mapped[list["PipelineLog"]] = relationship(
        "PipelineLog",
        back_populates="pipeline_run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
