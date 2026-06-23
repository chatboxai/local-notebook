import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Feature(Base):
    """报告中的一个栏目(sub-report)。

    隶属于某个 Workflow(step)，由 while-loop agent 生成内容并落成 blocks。
    生成路径中应绑定 workflow_id；nullable 仅用于兼容历史数据。
    """

    __tablename__ = "features"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workflow_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=True, index=True
    )

    feature_type: Mapped[str] = mapped_column(String(50), nullable=False, default="text_section")
    step_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 栏目名(同时作为标题展示)
    step_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # pending / processing / completed / failed / cancelled
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    blocks_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citations_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generation_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow: Mapped[Optional["Workflow"]] = relationship("Workflow", back_populates="features")

    # --- JSON helpers ---

    def get_blocks(self) -> List[Dict[str, Any]]:
        if not self.blocks_json:
            return []
        try:
            data = json.loads(self.blocks_json)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def set_blocks(self, blocks: List[Dict[str, Any]]) -> None:
        self.blocks_json = json.dumps(blocks, ensure_ascii=False) if blocks else None

    def get_citations(self) -> Dict[str, Any]:
        if not self.citations_json:
            return {}
        try:
            data = json.loads(self.citations_json)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def set_citations(self, data: Dict[str, Any]) -> None:
        self.citations_json = json.dumps(data, ensure_ascii=False) if data else None

    def get_custom_config(self) -> Dict[str, Any]:
        if not self.custom_config_json:
            return {}
        try:
            data = json.loads(self.custom_config_json)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def set_custom_config(self, data: Dict[str, Any]) -> None:
        self.custom_config_json = json.dumps(data, ensure_ascii=False) if data else None

    # --- view helpers ---

    def to_content_dict(self) -> Dict[str, Any]:
        """前端 WorkflowContentFeature / Feature 形状。"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "feature_type": self.feature_type,
            "step_index": self.step_index,
            "step_name": self.step_name,
            "title": self.title or self.step_name,
            "status": self.status,
            "error_message": self.error_message,
            "blocks": self.get_blocks(),
            "citations": self.get_citations(),
            "generation_report": self.generation_report or "",
        }
