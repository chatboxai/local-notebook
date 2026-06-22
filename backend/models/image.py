from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from utils.time import utc_isoformat


class Image(Base):
    __tablename__ = "images"

    id: Mapped[str] = mapped_column(String(200), primary_key=True)

    file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True
    )

    image_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    vlm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "image_index": self.image_index,
            "description": self.description,
            "vlm_model": self.vlm_model,
            "created_at": utc_isoformat(self.created_at),
        }
