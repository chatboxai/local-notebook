import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Block(Base):
    __tablename__ = "blocks"

    id: Mapped[str] = mapped_column(String(200), primary_key=True)

    file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True
    )

    block_id: Mapped[str] = mapped_column(String(50), nullable=False)

    block_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    block_type: Mapped[str] = mapped_column(String(50), nullable=False, default="paragraph")

    content: Mapped[str] = mapped_column(Text, nullable=False)

    pos_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pos_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    page: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    extra: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def get_extra(self) -> Optional[Dict[str, Any]]:
        if not self.extra:
            return None
        if isinstance(self.extra, dict):
            return self.extra
        try:
            return json.loads(self.extra)
        except json.JSONDecodeError:
            return None

    def set_extra(self, data: Dict[str, Any]) -> None:
        self.extra = json.dumps(data, ensure_ascii=False) if data else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "content": self.content,
            "page": self.page,
            "pos_start": self.pos_start,
            "pos_end": self.pos_end,
            "extra": self.get_extra(),
        }
