import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from utils.time import utc_isoformat


class Workflow(Base):
    """一次「一键生成报告」任务。

    Plan 总模型为它规划出若干栏目(steps)，每个栏目对应一个 Feature。
    """

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 展示来源类型；仅用于前端区分内置 prompt / 自定义入口。
    workflow_type: Mapped[str] = mapped_column(String(50), nullable=False, default="custom")
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # pending / processing / cancelling / completed / partial / failed / cancelled
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    # Plan 模型产出的结构化规划(steps 列表)
    plan_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 用户自定义描述
    custom_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 参与生成的文件 id 列表
    file_ids_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 跨栏目共享、聚合后的引用表 {citation_id: metadata}
    citations_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_citation_display_num: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    is_finalized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    features: Mapped[List["Feature"]] = relationship(
        "Feature",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="Feature.step_index",
    )

    # --- JSON helpers ---

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

    def get_file_ids(self) -> List[str]:
        if not self.file_ids_json:
            return []
        try:
            data = json.loads(self.file_ids_json)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def get_plan(self) -> Dict[str, Any]:
        if not self.plan_json:
            return {}
        try:
            data = json.loads(self.plan_json)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    # --- view helpers ---

    def progress(self) -> Dict[str, Any]:
        feats = list(self.features or [])
        total = len(feats)
        completed = sum(1 for f in feats if f.status == "completed")
        failed = sum(1 for f in feats if f.status == "failed")
        cancelled = sum(1 for f in feats if f.status == "cancelled")
        current = next((f.step_name for f in feats if f.status == "processing"), None)
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "current_step": current,
        }

    def to_status_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "progress": self.progress(),
        }

    def to_list_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow_type": self.workflow_type,
            "display_name": self.title or self.workflow_type,
            "title": self.title,
            "status": self.status,
            "progress": self.progress(),
            "is_finalized": self.is_finalized,
            "created_at": utc_isoformat(self.created_at),
            "finished_at": utc_isoformat(self.finished_at),
        }

    def to_detail_dict(self) -> Dict[str, Any]:
        steps = [
            {
                "step_index": f.step_index,
                "step_id": f.get_step_id(),
                "depends_on": f.get_depends_on(),
                "step_name": f.step_name,
                "feature_id": f.id,
                "feature_type": f.feature_type,
                "display_name": f.step_name,
                "status": f.status,
                "title": f.title,
                "error_message": f.error_message,
            }
            for f in (self.features or [])
        ]
        return {
            "id": self.id,
            "workflow_type": self.workflow_type,
            "display_name": self.title or self.workflow_type,
            "title": self.title,
            "status": self.status,
            "progress": self.progress(),
            "steps": steps,
            "is_finalized": self.is_finalized,
            "created_at": utc_isoformat(self.created_at),
            "finished_at": utc_isoformat(self.finished_at),
        }
