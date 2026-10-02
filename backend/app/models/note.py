"""Investigator notes model."""

from typing import Optional, List
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Note(Base, TimestampMixin):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=True, index=True
    )
    evidence_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evidence.id", ondelete="CASCADE"), nullable=True, index=True
    )
    author: Mapped[str] = mapped_column(String(128), default="Analyst")
    content: Mapped[Text] = mapped_column(Text, nullable=False)
    tags_json: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="notes")
    entity: Mapped[Optional["Entity"]] = relationship("Entity", back_populates="notes")
    evidence: Mapped[Optional["Evidence"]] = relationship("Evidence", back_populates="notes")
