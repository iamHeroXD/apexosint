"""Chronological timeline event model."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid, utcnow


class TimelineEvent(Base, TimestampMixin):
    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    evidence_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # REGISTRATION, CERTIFICATE_ISSUED, REPOSITORY_COMMIT, PROFILE_CREATED, DNS_CHANGE, EXPOSURE_DETECTED, OBSERVED
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Text] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="timeline_events")
    entity: Mapped[Optional["Entity"]] = relationship("Entity")
    evidence: Mapped[Optional["Evidence"]] = relationship("Evidence", back_populates="timeline_events")
