from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    citations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tool_calls: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    used_file_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    reasoning_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    agent_role: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    parent_message_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    _error: Mapped[Optional[str]] = mapped_column("error", Text, nullable=True)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    session: Mapped["Session"] = relationship("Session", back_populates="messages")
