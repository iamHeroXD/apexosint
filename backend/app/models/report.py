"""Intelligence report model."""

from typing import Optional, Dict, Any
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    classification: Mapped[str] = mapped_column(
        String(64), default="CONFIDENTIAL / FOR INTERNAL INVESTIGATION ONLY"
    )
    format: Mapped[str] = mapped_column(String(32), default="markdown")  # markdown, html, json, pdf
    content_markdown: Mapped[Text] = mapped_column(Text, nullable=False)
    content_html: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    summary_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="reports")
