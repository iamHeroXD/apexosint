"""Target entity input model."""

from typing import Optional, Dict, Any, List
from sqlalchemy import String, Text, Float, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Target(Base, TimestampMixin):
    __tablename__ = "targets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_input: Mapped[str] = mapped_column(Text, nullable=False)
    detected_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    normalized_value: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    hypotheses_json: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    parent_entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, analyzing, completed, failed

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="targets")
