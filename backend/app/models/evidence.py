"""Evidence provenance record model."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Text, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid, utcnow


class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    collection_method: Mapped[str] = mapped_column(String(64), default="DIRECT_QUERY")
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    epistemic_label: Mapped[str] = mapped_column(
        String(32), default="OBSERVED"
    )  # OBSERVED, CORROBORATED, AI_INFERENCE, UNVERIFIED
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    related_entity_ids_json: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    hash_signature: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="evidence")
    timeline_events: Mapped[List["TimelineEvent"]] = relationship(
        "TimelineEvent", back_populates="evidence", cascade="all, delete-orphan"
    )
    notes: Mapped[List["Note"]] = relationship("Note", back_populates="evidence", cascade="all, delete-orphan")
