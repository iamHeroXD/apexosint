"""Telemetry and execution status for OSINT module runs."""

from typing import Optional, Dict, Any
from sqlalchemy import String, Text, Integer, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class ModuleRun(Base, TimestampMixin):
    __tablename__ = "module_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    module_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="pending"
    )  # pending, running, completed, error, skipped
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metrics_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="module_runs")
