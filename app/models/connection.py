from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Connection(Base):
    __tablename__ = "connections"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    database_name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    source_pipelines: Mapped[list["Pipeline"]] = relationship(
        "Pipeline",
        back_populates="source_connection",
        foreign_keys="Pipeline.source_connection_id",
        cascade="all, delete-orphan",
    )
    target_pipelines: Mapped[list["Pipeline"]] = relationship(
        "Pipeline",
        back_populates="target_connection",
        foreign_keys="Pipeline.target_connection_id",
        cascade="all, delete-orphan",
    )
