import asyncio
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete as sa_delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import get_current_user
from dependencies.database import get_db
from dependencies.permissions import require_project
from models.file import File
from models.project import Project
from models.user import User
from schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

logger = logging.getLogger(__name__)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))

router = APIRouter(prefix="/projects", tags=["projects"])


def _project_response(project: Project, file_count: int = 0) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        user_id=project.owner_user_id,
        name=project.name,
        description=project.description,
        summary=project.summary,
        color=project.color,
        file_count=file_count,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


async def _get_project_file_count(db: AsyncSession, project_id: str) -> int:
    result = await db.execute(
        select(func.count(File.id)).where(File.project_id == project_id)
    )
    return result.scalar_one()


async def _drop_project_vectors(project_id: str) -> None:
    try:
        from services.vector_service import delete_project_collections

        await asyncio.wait_for(
            asyncio.to_thread(delete_project_collections, project_id),
            timeout=15.0,
        )
    except Exception as exc:
        logger.warning(
            "Failed to delete Milvus collections for project %s: %s",
            project_id,
            exc,
        )


async def _delete_project_upload_dir(project_id: str) -> None:
    project_dir = UPLOAD_DIR / project_id
    try:
        await asyncio.to_thread(shutil.rmtree, project_dir, ignore_errors=True)
    except Exception as exc:
        logger.warning(
            "Failed to delete upload dir for project %s: %s",
            project_id,
            exc,
        )


async def _delete_project_rows(db: AsyncSession, project_id: str, project: Project) -> None:
    from models.block import Block
    from models.feature import Feature
    from models.image import Image
    from models.message import Message
    from models.segment import Segment
    from models.session import Session
    from models.workflow import Workflow

    project_file_ids = set(
        (await db.execute(select(File.id).where(File.project_id == project_id)))
        .scalars()
        .all()
    )

    workflow_ids = set(
        (await db.execute(select(Workflow.id).where(Workflow.project_id == project_id)))
        .scalars()
        .all()
    )
    session_ids = set(
        (await db.execute(select(Session.id).where(Session.project_id == project_id)))
        .scalars()
        .all()
    )

    if session_ids:
        await db.execute(sa_delete(Message).where(Message.session_id.in_(session_ids)))
    await db.execute(sa_delete(Session).where(Session.project_id == project_id))

    feature_filters = [Feature.project_id == project_id]
    if workflow_ids:
        feature_filters.append(Feature.workflow_id.in_(workflow_ids))
    await db.execute(sa_delete(Feature).where(or_(*feature_filters)))
    await db.execute(sa_delete(Workflow).where(Workflow.project_id == project_id))

    segment_filters = [Segment.project_id == project_id]
    if project_file_ids:
        segment_filters.append(Segment.file_id.in_(project_file_ids))
        await db.execute(sa_delete(Block).where(Block.file_id.in_(project_file_ids)))
        await db.execute(sa_delete(Image).where(Image.file_id.in_(project_file_ids)))
    await db.execute(sa_delete(Segment).where(or_(*segment_filters)))

    await db.execute(sa_delete(File).where(File.project_id == project_id))

    await db.delete(project)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectResponse]:
    file_counts = (
        select(
            File.project_id,
            func.count(File.id).label("file_count"),
        )
        .group_by(File.project_id)
        .subquery()
    )
    result = await db.execute(
        select(
            Project,
            func.coalesce(file_counts.c.file_count, 0).label("file_count"),
        )
        .outerjoin(file_counts, Project.id == file_counts.c.project_id)
        .where(Project.owner_user_id == current_user.id)
        .order_by(Project.updated_at.desc())
    )
    return [_project_response(project, file_count) for project, file_count in result.all()]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    project = Project(
        name=body.name,
        description=body.description,
        owner_user_id=current_user.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return _project_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    project = await require_project(db, project_id, current_user)
    return _project_response(project, await _get_project_file_count(db, project_id))


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    project = await require_project(db, project_id, current_user)
    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    project.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(project)
    return _project_response(project, await _get_project_file_count(db, project_id))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    project = await require_project(db, project_id, current_user)

    await _drop_project_vectors(project_id)
    await _delete_project_rows(db, project_id, project)
    await db.commit()
    await _delete_project_upload_dir(project_id)
