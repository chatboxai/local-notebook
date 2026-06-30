import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import get_current_user
from dependencies.database import get_db
from dependencies.permissions import require_project
from models.feature import Feature
from models.file import File
from models.project import Project
from models.user import User

logger = logging.getLogger("routes.feature")

router = APIRouter(prefix="/features", tags=["features"])


class FeatureCustomConfig(BaseModel):
    prompt: Optional[str] = None
    title: Optional[str] = None
    file_ids: list[str] = Field(default_factory=list)
    output_language: Optional[str] = None


class GenerateFeatureRequest(BaseModel):
    project_id: str
    feature_type: str
    custom_config: Optional[FeatureCustomConfig] = None


class StatusBatchRequest(BaseModel):
    feature_ids: list[str] = Field(default_factory=list)


class ContentBatchRequest(BaseModel):
    feature_ids: list[str] = Field(default_factory=list)


class FeatureUpdateRequest(BaseModel):
    title: str


FEATURE_TYPE_LABELS = {
    "objective_positioning": ("定位分析", "Positioning analysis"),
    "audience_profile": ("受众画像", "Audience profile"),
    "comparative_analysis": ("同类分析", "Comparable analysis"),
    "content_summary": ("内容摘要", "Content summary"),
    "title_suggestion": ("标题生成", "Title suggestions"),
    "communication_copy": ("传播文案", "Communication copy"),
    "custom_feature": ("快捷工具", "Quick tool"),
    "text_section": ("快捷工具", "Quick tool"),
}


def _is_chinese_output(language: str | None) -> bool:
    return (language or "").strip().lower().startswith("chinese")


def feature_display_name(feature_type: str, output_language: str | None = None) -> str:
    zh, en = FEATURE_TYPE_LABELS.get(feature_type, (feature_type, feature_type))
    return zh if _is_chinese_output(output_language) else en


def _feature_to_list_dict(feature: Feature) -> dict:
    cfg = feature.get_custom_config()
    return {
        "id": feature.id,
        "feature_type": feature.feature_type,
        "display_name": feature.title or feature.step_name or feature.feature_type,
        "title": feature.title,
        "prompt": cfg.get("prompt"),
        "status": feature.status,
        "error_message": feature.error_message,
        "created_at": feature.created_at.isoformat(),
        "started_at": feature.started_at.isoformat() if feature.started_at else None,
        "finished_at": feature.finished_at.isoformat() if feature.finished_at else None,
    }


async def _require_feature(db: AsyncSession, feature_id: str, current_user: User) -> Feature:
    result = await db.execute(
        select(Feature)
        .join(Project, Feature.project_id == Project.id)
        .where(
            Feature.id == feature_id,
            Feature.workflow_id.is_(None),
            Project.owner_user_id == current_user.id,
        )
    )
    feature = result.scalar_one_or_none()
    if not feature:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature not found")
    return feature


@router.get("/project/{project_id}")
async def list_project_features(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await require_project(db, project_id, current_user)
    result = await db.execute(
        select(Feature)
        .where(Feature.project_id == project_id, Feature.workflow_id.is_(None))
        .order_by(Feature.created_at.desc())
    )
    return {"features": [_feature_to_list_dict(feature) for feature in result.scalars().all()]}


@router.post("/generate")
async def generate_feature(
    body: GenerateFeatureRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await require_project(db, body.project_id, current_user)

    feature_type = (body.feature_type or "").strip()
    if not feature_type:
        raise HTTPException(status_code=400, detail="缺少快捷工具类型")

    cfg = body.custom_config or FeatureCustomConfig()
    file_ids = [file_id for file_id in (cfg.file_ids or []) if file_id]
    if not file_ids:
        raise HTTPException(status_code=400, detail="请选择至少一个文件")

    result = await db.execute(
        select(File.id).where(
            File.project_id == body.project_id,
            File.status == "ready",
            File.id.in_(file_ids),
        )
    )
    accessible_file_ids = set(result.scalars().all())
    if accessible_file_ids != set(file_ids):
        raise HTTPException(status_code=404, detail="File not found or not ready")

    output_language = (cfg.output_language or "").strip() or "Chinese"
    display_name = feature_display_name(feature_type, output_language)
    title = (cfg.title or "").strip() or display_name

    feature = Feature(
        project_id=body.project_id,
        workflow_id=None,
        feature_type=feature_type,
        step_index=0,
        step_name=title,
        title=title,
        status="pending",
    )
    feature.set_custom_config({
        "prompt": (cfg.prompt or "").strip(),
        "title": (cfg.title or "").strip(),
        "file_ids": file_ids,
        "output_language": output_language,
    })
    db.add(feature)
    await db.commit()
    await db.refresh(feature)

    redis = request.app.state.redis
    if redis is None:
        feature.status = "failed"
        feature.error_message = "后台任务服务(Redis)不可用，无法生成快捷工具内容"
        feature.finished_at = datetime.now(timezone.utc)
        await db.commit()
        raise HTTPException(status_code=503, detail="后台任务服务不可用，无法生成快捷工具内容")

    await redis.enqueue_job("generate_feature_task", feature.id, output_language)

    return {
        "feature_id": feature.id,
        "status": feature.status,
        "display_name": display_name,
    }


@router.post("/status/batch")
async def get_features_status_batch(
    body: StatusBatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if not body.feature_ids:
        return {"features": {}}
    result = await db.execute(
        select(Feature)
        .join(Project, Feature.project_id == Project.id)
        .where(
            Feature.id.in_(body.feature_ids),
            Feature.workflow_id.is_(None),
            Project.owner_user_id == current_user.id,
        )
    )
    return {
        "features": {
            feature.id: _feature_to_list_dict(feature)
            for feature in result.scalars().all()
        }
    }


@router.post("/content/batch")
async def get_features_content_batch(
    body: ContentBatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if not body.feature_ids:
        return {"features": {}}
    result = await db.execute(
        select(Feature)
        .join(Project, Feature.project_id == Project.id)
        .where(
            Feature.id.in_(body.feature_ids),
            Feature.workflow_id.is_(None),
            Project.owner_user_id == current_user.id,
        )
    )
    return {
        "features": {
            feature.id: feature.to_content_dict()
            for feature in result.scalars().all()
        }
    }


@router.get("/{feature_id}")
async def get_feature(
    feature_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    feature = await _require_feature(db, feature_id, current_user)
    return feature.to_content_dict()


@router.put("/{feature_id}")
async def update_feature(
    feature_id: str,
    body: FeatureUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    feature = await _require_feature(db, feature_id, current_user)
    title = body.title.strip()
    if title:
        feature.title = title
        feature.step_name = title
    await db.commit()
    await db.refresh(feature)
    return {
        "id": feature.id,
        "title": feature.title,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.delete("/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature(
    feature_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    feature = await _require_feature(db, feature_id, current_user)
    await db.execute(sa_delete(Feature).where(Feature.id == feature.id))
    await db.commit()
