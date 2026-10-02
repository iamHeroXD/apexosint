"""Relationship graph edge model."""

from typing import Optional, Dict, Any, List
from sqlalchemy import String, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Relationship(Base, TimestampMixin):
    __tablename__ = "relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # OWNS, MENTIONS, HOSTED_ON, RESOLVES_TO, AUTHORED, CONTRIBUTES_TO, LINKS_TO, ASSOCIATED_WITH, DISCOVERED_FROM, CERTIFICATE_FOR, SUBDOMAIN_OF
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    evidence_ids_json: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    is_ai_inferred: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="relationships")
    source_entity: Mapped["Entity"] = relationship("Entity", foreign_keys=[source_entity_id])
    target_entity: Mapped["Entity"] = relationship("Entity", foreign_keys=[target_entity_id])
