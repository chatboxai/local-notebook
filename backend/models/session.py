from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    citation_counter: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    next_citation_display_num: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    last_total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    compact_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    compact_citations_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    compact_message_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    compact_trigger_message_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="sessions")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
