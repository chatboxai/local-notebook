from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.workflow import Workflow


MAX_WORKFLOW_TITLE_LENGTH = 500


def make_unique_workflow_title(desired_title: str, existing_titles: Iterable[str]) -> str:
    """Return a project-local unique workflow title by appending （1）, （2）, ... when needed."""
    base = desired_title.strip()[:MAX_WORKFLOW_TITLE_LENGTH]
    if not base:
        return base

    existing = {title for title in existing_titles if title}
    if base not in existing:
        return base

    index = 1
    while True:
        suffix = f"（{index}）"
        prefix = base[: MAX_WORKFLOW_TITLE_LENGTH - len(suffix)]
        candidate = f"{prefix}{suffix}"
        if candidate not in existing:
            return candidate
        index += 1


async def ensure_unique_workflow_title(
    db: AsyncSession,
    project_id: str,
    desired_title: str,
    *,
    exclude_workflow_id: Optional[str] = None,
) -> str:
    title = desired_title.strip()
    if not title:
        return title

    query = select(Workflow.title).where(
        Workflow.project_id == project_id,
        Workflow.title.is_not(None),
    )
    if exclude_workflow_id:
        query = query.where(Workflow.id != exclude_workflow_id)

    result = await db.execute(query)
    return make_unique_workflow_title(title, result.scalars().all())
