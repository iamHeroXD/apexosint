"""Contradiction & conflict detection model."""

from typing import Optional, Dict, Any
from sqlalchemy import String, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Contradiction(Base, TimestampMixin):
    __tablename__ = "contradictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    attribute_name: Mapped[str] = mapped_column(String(128), nullable=False)
    
    # Source A
    source_a_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    source_a_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_a_claim: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Source B
    source_b_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    source_b_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_b_claim: Mapped[str] = mapped_column(Text, nullable=False)
    
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="contradictions")
