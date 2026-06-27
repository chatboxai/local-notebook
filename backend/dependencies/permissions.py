from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.file import File
from models.project import Project
from models.session import Session
from models.user import User
from models.workflow import Workflow


async def require_project(
    db: AsyncSession,
    project_id: str,
    current_user: User,
) -> Project:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_user_id == current_user.id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def require_file(
    db: AsyncSession,
    file_id: str,
    current_user: User,
    project_id: str | None = None,
) -> File:
    query = (
        select(File)
        .join(Project, File.project_id == Project.id)
        .where(File.id == file_id, Project.owner_user_id == current_user.id)
    )
    if project_id is not None:
        query = query.where(File.project_id == project_id)
    result = await db.execute(query)
    db_file = result.scalar_one_or_none()
    if not db_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return db_file


async def require_session(
    db: AsyncSession,
    session_id: str,
    current_user: User,
) -> Session:
    result = await db.execute(
        select(Session)
        .join(Project, Session.project_id == Project.id)
        .where(Session.id == session_id, Project.owner_user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


async def require_workflow(
    db: AsyncSession,
    workflow_id: str,
    current_user: User,
    *,
    with_features: bool = False,
) -> Workflow:
    query = (
        select(Workflow)
        .join(Project, Workflow.project_id == Project.id)
        .where(Workflow.id == workflow_id, Project.owner_user_id == current_user.id)
    )
    if with_features:
        query = query.options(selectinload(Workflow.features))
    result = await db.execute(query)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow
