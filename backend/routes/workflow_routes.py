import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dependencies.auth import get_current_user
from dependencies.database import get_db
from models.feature import Feature
from models.project import Project
from models.workflow import Workflow
from services.workflow_titles import ensure_unique_workflow_title

logger = logging.getLogger("routes.workflow")

router = APIRouter(prefix="/workflows", tags=["workflows"])


# ---------- request bodies ----------

class WorkflowCustomConfig(BaseModel):
    prompt: Optional[str] = None
    file_ids: list[str] = []


class GenerateWorkflowRequest(BaseModel):
    project_id: str
    title: str = ""
    custom_config: Optional[WorkflowCustomConfig] = None


class StatusBatchRequest(BaseModel):
    workflow_ids: list[str] = []


class TitleUpdateRequest(BaseModel):
    title: str


# ---------- helpers ----------

async def _get_workflow_with_features(db: AsyncSession, workflow_id: str) -> Optional[Workflow]:
    result = await db.execute(
        select(Workflow)
        .options(selectinload(Workflow.features))
        .where(Workflow.id == workflow_id)
    )
    return result.scalar_one_or_none()


# ---------- routes (literal paths first) ----------

@router.post("/generate")
async def generate_workflow(
    body: GenerateWorkflowRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    project = await db.get(Project, body.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cfg = body.custom_config or WorkflowCustomConfig()
    if not cfg.file_ids:
        raise HTTPException(status_code=400, detail="请选择至少一个文件")
    custom_prompt = (cfg.prompt or "").strip()
    if not custom_prompt:
        raise HTTPException(status_code=400, detail="请输入工作流要求")

    requested_title = (body.title or "").strip()
    workflow_title = (
        await ensure_unique_workflow_title(db, body.project_id, requested_title)
        if requested_title
        else None
    )

    wf = Workflow(
        project_id=body.project_id,
        workflow_type="custom",
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

    await redis.enqueue_job("generate_workflow_task", wf.id)

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
    _: str = Depends(get_current_user),
) -> dict:
    if not body.workflow_ids:
        return {"workflows": {}}
    result = await db.execute(
        select(Workflow)
        .options(selectinload(Workflow.features))
        .where(Workflow.id.in_(body.workflow_ids))
    )
    workflows = {wf.id: wf.to_status_dict() for wf in result.scalars().all()}
    return {"workflows": workflows}


@router.get("/project/{project_id}")
async def list_project_workflows(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
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
    _: str = Depends(get_current_user),
) -> dict:
    wf = await _get_workflow_with_features(db, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf.to_status_dict()


@router.get("/{workflow_id}/content")
async def get_workflow_content(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    wf = await _get_workflow_with_features(db, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "workflow_id": wf.id,
        "citations": wf.get_citations(),
        "features": [f.to_content_dict() for f in wf.features],
    }


@router.get("/{workflow_id}")
async def get_workflow_detail(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    wf = await _get_workflow_with_features(db, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf.to_detail_dict()


@router.put("/{workflow_id}/title")
async def rename_workflow(
    workflow_id: str,
    body: TitleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    wf = await _get_workflow_with_features(db, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
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
    _: str = Depends(get_current_user),
) -> None:
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    # SQLite 默认不开 FK 级联，显式删除子 features 避免孤儿行
    await db.execute(sa_delete(Feature).where(Feature.workflow_id == workflow_id))
    await db.delete(wf)
    await db.commit()
