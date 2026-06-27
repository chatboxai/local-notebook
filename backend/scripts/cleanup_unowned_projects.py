#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "packages"))


def _apply_local_data_defaults() -> None:
    data_dir = Path(
        os.getenv("LOCAL_NOTEBOOK_DATA_DIR", REPO_DIR / "local-notebook-data")
    )
    db_path = data_dir / "local_notebook.db"
    upload_dir = data_dir / "uploads"

    if "DATABASE_URL" not in os.environ and db_path.exists():
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    if "UPLOAD_DIR" not in os.environ and upload_dir.exists():
        os.environ["UPLOAD_DIR"] = str(upload_dir)


def _collection_names(project_id: str) -> tuple[str, str]:
    name = "p_" + project_id.replace("-", "_")
    return name, name + "_images"


async def _unowned_project_rows() -> list[tuple[str, str]]:
    import models  # noqa: F401
    from database import AsyncSessionLocal
    from models.project import Project
    from sqlalchemy import or_, select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Project.id, Project.name)
            .where(or_(Project.owner_user_id.is_(None), Project.owner_user_id == ""))
            .order_by(Project.created_at.asc())
        )
        return [(project_id, name) for project_id, name in result.all()]


async def _count_rows(project_ids: list[str]) -> dict[str, int]:
    import models  # noqa: F401
    from database import AsyncSessionLocal
    from models.block import Block
    from models.feature import Feature
    from models.file import File
    from models.image import Image
    from models.message import Message
    from models.segment import Segment
    from models.session import Session
    from models.workflow import Workflow
    from sqlalchemy import func, or_, select

    async with AsyncSessionLocal() as db:
        file_ids = (
            await db.execute(select(File.id).where(File.project_id.in_(project_ids)))
        ).scalars().all()
        session_ids = (
            await db.execute(select(Session.id).where(Session.project_id.in_(project_ids)))
        ).scalars().all()
        workflow_ids = (
            await db.execute(select(Workflow.id).where(Workflow.project_id.in_(project_ids)))
        ).scalars().all()

        async def count(model, condition) -> int:
            result = await db.execute(select(func.count()).select_from(model).where(condition))
            return result.scalar_one()

        counts = {
            "projects": len(project_ids),
            "files": await count(File, File.project_id.in_(project_ids)),
            "sessions": await count(Session, Session.project_id.in_(project_ids)),
            "workflows": await count(Workflow, Workflow.project_id.in_(project_ids)),
        }
        counts["messages"] = (
            await count(Message, Message.session_id.in_(session_ids)) if session_ids else 0
        )
        counts["features"] = await count(
            Feature,
            or_(
                Feature.project_id.in_(project_ids),
                Feature.workflow_id.in_(workflow_ids) if workflow_ids else False,
            ),
        )
        counts["segments"] = await count(
            Segment,
            or_(
                Segment.project_id.in_(project_ids),
                Segment.file_id.in_(file_ids) if file_ids else False,
            ),
        )
        counts["blocks"] = await count(Block, Block.file_id.in_(file_ids)) if file_ids else 0
        counts["images"] = await count(Image, Image.file_id.in_(file_ids)) if file_ids else 0
        return counts


async def _delete_db_rows(project_ids: list[str]) -> dict[str, int]:
    import models  # noqa: F401
    from database import AsyncSessionLocal
    from models.block import Block
    from models.feature import Feature
    from models.file import File
    from models.image import Image
    from models.message import Message
    from models.project import Project
    from models.segment import Segment
    from models.session import Session
    from models.workflow import Workflow
    from sqlalchemy import delete as sa_delete, or_, select

    async with AsyncSessionLocal() as db:
        file_ids = (
            await db.execute(select(File.id).where(File.project_id.in_(project_ids)))
        ).scalars().all()
        session_ids = (
            await db.execute(select(Session.id).where(Session.project_id.in_(project_ids)))
        ).scalars().all()
        workflow_ids = (
            await db.execute(select(Workflow.id).where(Workflow.project_id.in_(project_ids)))
        ).scalars().all()

        async def delete(key: str, stmt) -> tuple[str, int]:
            result = await db.execute(stmt)
            return key, result.rowcount or 0

        deleted: dict[str, int] = {}
        actions = []
        if session_ids:
            actions.append(("messages", sa_delete(Message).where(Message.session_id.in_(session_ids))))
        actions.append(
            (
                "features",
                sa_delete(Feature).where(
                    or_(
                        Feature.project_id.in_(project_ids),
                        Feature.workflow_id.in_(workflow_ids) if workflow_ids else False,
                    )
                ),
            )
        )
        if file_ids:
            actions.extend(
                [
                    (
                        "segments",
                        sa_delete(Segment).where(
                            or_(Segment.project_id.in_(project_ids), Segment.file_id.in_(file_ids))
                        ),
                    ),
                    ("blocks", sa_delete(Block).where(Block.file_id.in_(file_ids))),
                    ("images", sa_delete(Image).where(Image.file_id.in_(file_ids))),
                ]
            )
        else:
            actions.append(("segments", sa_delete(Segment).where(Segment.project_id.in_(project_ids))))
        actions.extend(
            [
                ("sessions", sa_delete(Session).where(Session.project_id.in_(project_ids))),
                ("workflows", sa_delete(Workflow).where(Workflow.project_id.in_(project_ids))),
                ("files", sa_delete(File).where(File.project_id.in_(project_ids))),
                ("projects", sa_delete(Project).where(Project.id.in_(project_ids))),
            ]
        )

        for key, stmt in actions:
            deleted_key, count = await delete(key, stmt)
            deleted[deleted_key] = count
        await db.commit()
        return deleted


def _delete_upload_dirs(project_ids: list[str], dry_run: bool) -> list[str]:
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    paths = [upload_dir / project_id for project_id in project_ids if (upload_dir / project_id).exists()]
    if not dry_run:
        for path in paths:
            shutil.rmtree(path, ignore_errors=True)
    return [str(path) for path in paths]


def _cleanup_milvus(project_ids: list[str], dry_run: bool) -> list[str]:
    try:
        from services.vector_service import MILVUS_URI
        from pymilvus import MilvusClient
    except Exception as exc:
        print(f"Milvus cleanup skipped: cannot import pymilvus ({exc})")
        return []

    try:
        client = MilvusClient(uri=MILVUS_URI)
    except Exception as exc:
        print(f"Milvus cleanup skipped: cannot connect ({exc})")
        return []

    existing = []
    for project_id in project_ids:
        for name in _collection_names(project_id):
            if client.has_collection(name):
                existing.append(name)

    if not dry_run:
        for name in existing:
            client.drop_collection(collection_name=name)
    return existing


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete projects with no owner_user_id and their local resources."
    )
    parser.add_argument("--yes", action="store_true", help="Delete the listed data.")
    args = parser.parse_args()
    dry_run = not args.yes

    _apply_local_data_defaults()
    projects = await _unowned_project_rows()
    project_ids = [project_id for project_id, _ in projects]

    print("Mode:", "dry-run" if dry_run else "delete")
    print("DATABASE_URL:", os.getenv("DATABASE_URL"))
    print("UPLOAD_DIR:", os.getenv("UPLOAD_DIR", "./uploads"))

    if not projects:
        print("\nNo unowned projects found.")
        return

    print("\nUnowned projects:")
    for project_id, name in projects:
        print(f"  {project_id}  {name}")

    counts = await _count_rows(project_ids)
    upload_dirs = _delete_upload_dirs(project_ids, dry_run=True)
    milvus_collections = _cleanup_milvus(project_ids, dry_run=True)

    print("\nRows:")
    for key, count in counts.items():
        print(f"  {key}: {count}")

    print("\nUpload dirs:")
    if upload_dirs:
        for path in upload_dirs:
            print(f"  {path}")
    else:
        print("  none")

    print("\nMilvus collections:")
    if milvus_collections:
        for name in milvus_collections:
            print(f"  {name}")
    else:
        print("  none")

    if dry_run:
        print("\nNo changes were made. Re-run with --yes to delete these projects.")
        return

    _cleanup_milvus(project_ids, dry_run=False)
    deleted = await _delete_db_rows(project_ids)
    deleted_dirs = _delete_upload_dirs(project_ids, dry_run=False)

    print("\nDeleted rows:")
    for key, count in deleted.items():
        print(f"  {key}: {count}")

    print("\nDeleted upload dirs:")
    if deleted_dirs:
        for path in deleted_dirs:
            print(f"  {path}")
    else:
        print("  none")


if __name__ == "__main__":
    asyncio.run(main())
