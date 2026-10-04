"""Evidence provenance record model with advanced epistemic and reliability attributes."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Text, Float, Boolean, Integer, JSON, DateTime, ForeignKey
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
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    # Advanced Epistemic & Reliability Attributes (Phase 3 & Phase 7)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source_reliability: Mapped[float] = mapped_column(Float, default=0.90)  # 0.0 - 1.0 based on authoritative tier
    epistemic_label: Mapped[str] = mapped_column(
        String(32), default="OBSERVED", index=True
    )  # OBSERVED, CORROBORATED, CONFLICTED, INFERRED, UNVERIFIED, STALE
    corroboration_count: Mapped[int] = mapped_column(Integer, default=0)
    independent_source_count: Mapped[int] = mapped_column(Integer, default=1)
    module_version: Mapped[str] = mapped_column(String(32), default="1.0.0")

    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    related_entity_ids_json: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    hash_signature: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="evidence")
    timeline_events: Mapped[List["TimelineEvent"]] = relationship(
        "TimelineEvent", back_populates="evidence", cascade="all, delete-orphan"
    )
    notes: Mapped[List["Note"]] = relationship("Note", back_populates="evidence", cascade="all, delete-orphan")
