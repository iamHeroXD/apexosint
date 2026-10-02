"""Workspace model for grouping cases and investigations."""

from typing import Optional, List
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags_json: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Relationships
    investigations: Mapped[List["Investigation"]] = relationship(
        "Investigation",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
