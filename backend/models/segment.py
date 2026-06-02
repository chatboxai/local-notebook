import json
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[str] = mapped_column(String(200), primary_key=True)

    file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    pos_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pos_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    block_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def get_block_ids(self) -> list[str]:
        if not self.block_ids:
            return []
        if isinstance(self.block_ids, list):
            return self.block_ids
        return json.loads(self.block_ids)
