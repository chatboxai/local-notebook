import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dependencies.auth import get_current_user
from dependencies.database import get_db
from dependencies.permissions import require_project, require_workflow
from models.feature import Feature
from models.file import File
from models.project import Project
from models.user import User
from models.workflow import Workflow
from services.workflow_titles import ensure_unique_workflow_title

logger = logging.getLogger("routes.workflow")

router = APIRouter(prefix="/workflows", tags=["workflows"])


# ---------- request bodies ----------

class WorkflowCustomConfig(BaseModel):
    prompt: Optional[str] = None
    file_ids: list[str] = []
    preset_key: Optional[str] = None
    output_language: Optional[str] = None


class GenerateWorkflowRequest(BaseModel):
    project_id: str
    title: str = ""
    custom_config: Optional[WorkflowCustomConfig] = None


class StatusBatchRequest(BaseModel):
    workflow_ids: list[str] = []


class TitleUpdateRequest(BaseModel):
    title: str


WORKFLOW_TERMINAL_STATUSES = {"completed", "failed", "partial", "cancelled"}
WORKFLOW_CANCELLED_MESSAGE = "用户已停止生成"


# ---------- routes (literal paths first) ----------

@router.post("/generate")
async def generate_workflow(
    body: GenerateWorkflowRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await require_project(db, body.project_id, current_user)

    cfg = body.custom_config or WorkflowCustomConfig()
    if not cfg.file_ids:
        raise HTTPException(status_code=400, detail="请选择至少一个文件")
    custom_prompt = (cfg.prompt or "").strip()
    if not custom_prompt:
        raise HTTPException(status_code=400, detail="请输入工作流要求")
    workflow_type = (cfg.preset_key or "").strip()
    if not workflow_type:
        raise HTTPException(status_code=400, detail="缺少工作流类型")
    output_language = (cfg.output_language or "").strip()
    if not output_language:
        raise HTTPException(status_code=400, detail="缺少输出语言")
    result = await db.execute(
        select(File.id).where(
            File.project_id == body.project_id,
            File.id.in_(cfg.file_ids),
        )
    )
    accessible_file_ids = set(result.scalars().all())
    if accessible_file_ids != set(cfg.file_ids):
        raise HTTPException(status_code=404, detail="File not found")

    requested_title = (body.title or "").strip()
    workflow_title = (
        await ensure_unique_workflow_title(db, body.project_id, requested_title)
        if requested_title
        else None
    )

    wf = Workflow(
        project_id=body.project_id,
        workflow_type=workflow_type,
        title=workflow_title,
        status="pending",
        custom_prompt=custom_prompt,
        file_ids_json=json.dumps(cfg.file_ids, ensure_ascii=False),
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)

    redis = request.app.state.redis
    if redis is None:
        wf.status = "failed"
        wf.error_message = "后台任务服务(Redis)不可用，无法生成报告"
        await db.commit()
        raise HTTPException(status_code=503, detail="后台任务服务不可用，无法生成报告")

    await redis.enqueue_job("generate_workflow_task", wf.id, output_language)

    return {
        "workflow_id": wf.id,
        "workflow_type": wf.workflow_type,
        "display_name": wf.title or wf.workflow_type or "工作流",
        "status": wf.status,
        "steps_count": 0,
        "is_finalized": wf.is_finalized,
    }


@router.post("/status/batch")
async def get_workflows_status_batch(
    body: StatusBatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if not body.workflow_ids:
        return {"workflows": {}}
    result = await db.execute(
        select(Workflow)
        .options(selectinload(Workflow.features))
        .join(Project, Workflow.project_id == Project.id)
        .where(Workflow.id.in_(body.workflow_ids), Project.owner_user_id == current_user.id)
    )
    workflows = {wf.id: wf.to_status_dict() for wf in result.scalars().all()}
    return {"workflows": workflows}


@router.get("/project/{project_id}")
async def list_project_workflows(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await require_project(db, project_id, current_user)
    result = await db.execute(
        select(Workflow)
        .options(selectinload(Workflow.features))
        .where(Workflow.project_id == project_id)
        .order_by(Workflow.created_at.desc())
    )
    return {"workflows": [wf.to_list_dict() for wf in result.scalars().all()]}


@router.get("/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    wf = await require_workflow(db, workflow_id, current_user, with_features=True)
    return wf.to_status_dict()


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    wf = await require_workflow(db, workflow_id, current_user, with_features=True)

    if wf.status in WORKFLOW_TERMINAL_STATUSES:
        return wf.to_status_dict()

    if wf.status == "pending":
        wf.status = "cancelled"
        wf.error_message = WORKFLOW_CANCELLED_MESSAGE
        wf.finished_at = datetime.now(timezone.utc)
        for feature in wf.features or []:
            if feature.status in {"pending", "processing"}:
                feature.status = "cancelled"
                feature.error_message = WORKFLOW_CANCELLED_MESSAGE
                feature.finished_at = datetime.now(timezone.utc)
    else:
        wf.status = "cancelling"
        wf.error_message = WORKFLOW_CANCELLED_MESSAGE
        for feature in wf.features or []:
            if feature.status == "pending":
                feature.status = "cancelled"
                feature.error_message = WORKFLOW_CANCELLED_MESSAGE
                feature.finished_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(wf)
    logger.info("[workflow] cancel requested workflow_id=%s status=%s", workflow_id, wf.status)
    return wf.to_status_dict()


@router.get("/{workflow_id}/content")
async def get_workflow_content(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    wf = await require_workflow(db, workflow_id, current_user, with_features=True)
    return {
        "workflow_id": wf.id,
        "citations": wf.get_citations(),
        "features": [f.to_content_dict() for f in wf.features],
    }


@router.get("/{workflow_id}")
async def get_workflow_detail(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    wf = await require_workflow(db, workflow_id, current_user, with_features=True)
    return wf.to_detail_dict()


@router.put("/{workflow_id}/title")
async def rename_workflow(
    workflow_id: str,
    body: TitleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    wf = await require_workflow(db, workflow_id, current_user, with_features=True)
    new_title = body.title.strip()
    if new_title:
        wf.title = await ensure_unique_workflow_title(
            db,
            wf.project_id,
            new_title,
            exclude_workflow_id=workflow_id,
        )
    await db.commit()
    return wf.to_list_dict()


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    wf = await require_workflow(db, workflow_id, current_user)
    # SQLite 默认不开 FK 级联，显式删除子 features 避免孤儿行
    await db.execute(sa_delete(Feature).where(Feature.workflow_id == workflow_id))
    await db.delete(wf)
    await db.commit()
