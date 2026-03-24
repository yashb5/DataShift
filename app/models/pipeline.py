from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Pipeline(Base):
    __tablename__ = "pipelines"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source_connection_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("connections.id", ondelete="CASCADE"), nullable=False
    )
    target_connection_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("connections.id", ondelete="CASCADE"), nullable=False
    )
    source_table: Mapped[str] = mapped_column(String(255), nullable=False)
    target_table: Mapped[str] = mapped_column(String(255), nullable=False)
    mapping_config: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    source_connection: Mapped["Connection"] = relationship(
        "Connection",
        back_populates="source_pipelines",
        foreign_keys=[source_connection_id],
    )
    target_connection: Mapped["Connection"] = relationship(
        "Connection",
        back_populates="target_pipelines",
        foreign_keys=[target_connection_id],
    )
    runs: Mapped[list["PipelineRun"]] = relationship(
        "PipelineRun",
        back_populates="pipeline",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
