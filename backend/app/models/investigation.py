"""Investigation case model."""

from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Investigation(Base, TimestampMixin):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="pending", index=True
    )  # pending, running, paused, completed, failed
    mode: Mapped[str] = mapped_column(
        String(32), default="standard"
    )  # quick, standard, deep, custom
    depth: Mapped[int] = mapped_column(Integer, default=1)
    budget_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        default=lambda: {
            "max_depth": 2,
            "max_requests": 150,
            "max_modules": 30,
            "max_runtime": 180,
            "max_ai_calls": 10,
        },
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    summary_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        default=lambda: {
            "entities_count": 0,
            "evidence_count": 0,
            "relationships_count": 0,
            "sources_count": 0,
            "high_confidence_count": 0,
            "contradictions_count": 0,
            "executive_summary": "",
        },
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="investigations")
    targets: Mapped[List["Target"]] = relationship(
        "Target", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    entities: Mapped[List["Entity"]] = relationship(
        "Entity", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    evidence: Mapped[List["Evidence"]] = relationship(
        "Evidence", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    relationships: Mapped[List["Relationship"]] = relationship(
        "Relationship", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    timeline_events: Mapped[List["TimelineEvent"]] = relationship(
        "TimelineEvent", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    contradictions: Mapped[List["Contradiction"]] = relationship(
        "Contradiction", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    notes: Mapped[List["Note"]] = relationship(
        "Note", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
    module_runs: Mapped[List["ModuleRun"]] = relationship(
        "ModuleRun", back_populates="investigation", cascade="all, delete-orphan", lazy="selectin"
    )
