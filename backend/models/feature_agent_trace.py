import gzip
import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class FeatureAgentTrace(Base):
    """Compressed while-loop trace for one workflow feature generation phase."""

    __tablename__ = "feature_agent_traces"
    __table_args__ = (
        UniqueConstraint("feature_id", "phase", name="uq_feature_agent_trace_feature_phase"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    workflow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    feature_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("features.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phase: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    payload: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
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

    @staticmethod
    def pack_payload(data: dict[str, Any]) -> bytes:
        raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return gzip.compress(raw)

    @staticmethod
    def unpack_payload(payload: bytes) -> dict[str, Any]:
        if not payload:
            return {}
        raw = gzip.decompress(payload).decode("utf-8")
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}

    def get_payload(self) -> dict[str, Any]:
        try:
            return self.unpack_payload(self.payload)
        except Exception:
            return {}

    def set_payload(self, data: dict[str, Any]) -> None:
        self.payload = self.pack_payload(data)
