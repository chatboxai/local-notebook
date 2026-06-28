#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import os
import re
import shutil
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "packages"))

COLLECTION_RE = re.compile(
    r"^p_([0-9a-f]{8}_[0-9a-f]{4}_[0-9a-f]{4}_[0-9a-f]{4}_[0-9a-f]{12})(?:_images)?$"
)


def _project_id_from_collection(name: str) -> str | None:
    match = COLLECTION_RE.match(name)
    if not match:
        return None
    return match.group(1).replace("_", "-")


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


async def _cleanup_db(dry_run: bool) -> dict[str, int]:
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
    from sqlalchemy import and_, delete as sa_delete, select

    project_ids = select(Project.id)
    file_ids = select(File.id)
    orphan_file_ids = select(File.id).where(File.project_id.not_in(project_ids))
    session_ids = select(Session.id)
    orphan_session_ids = select(Session.id).where(Session.project_id.not_in(project_ids))
    workflow_ids = select(Workflow.id)
    orphan_workflow_ids = select(Workflow.id).where(Workflow.project_id.not_in(project_ids))

    actions = [
        (
            "messages_in_orphan_sessions",
            sa_delete(Message).where(Message.session_id.in_(orphan_session_ids)),
        ),
        (
            "messages_without_session",
            sa_delete(Message).where(Message.session_id.not_in(session_ids)),
        ),
        (
            "features_in_orphan_projects",
            sa_delete(Feature).where(Feature.project_id.not_in(project_ids)),
        ),
        (
            "features_in_orphan_workflows",
            sa_delete(Feature).where(
                and_(
                    Feature.workflow_id.is_not(None),
                    Feature.workflow_id.in_(orphan_workflow_ids),
                )
            ),
        ),
        (
            "features_without_workflow",
            sa_delete(Feature).where(
                and_(
                    Feature.workflow_id.is_not(None),
                    Feature.workflow_id.not_in(workflow_ids),
                )
            ),
        ),
        (
            "segments_in_orphan_projects",
            sa_delete(Segment).where(Segment.project_id.not_in(project_ids)),
        ),
        (
            "segments_in_orphan_files",
            sa_delete(Segment).where(Segment.file_id.in_(orphan_file_ids)),
        ),
        (
            "segments_without_file",
            sa_delete(Segment).where(Segment.file_id.not_in(file_ids)),
        ),
        (
            "blocks_in_orphan_files",
            sa_delete(Block).where(Block.file_id.in_(orphan_file_ids)),
        ),
        ("blocks_without_file", sa_delete(Block).where(Block.file_id.not_in(file_ids))),
        (
            "images_in_orphan_files",
            sa_delete(Image).where(Image.file_id.in_(orphan_file_ids)),
        ),
        ("images_without_file", sa_delete(Image).where(Image.file_id.not_in(file_ids))),
        (
            "sessions_in_orphan_projects",
            sa_delete(Session).where(Session.project_id.not_in(project_ids)),
        ),
        (
            "workflows_in_orphan_projects",
            sa_delete(Workflow).where(Workflow.project_id.not_in(project_ids)),
        ),
        (
            "files_in_orphan_projects",
            sa_delete(File).where(File.project_id.not_in(project_ids)),
        ),
    ]

    counts: dict[str, int] = {}
    async with AsyncSessionLocal() as db:
        for key, stmt in actions:
            result = await db.execute(stmt)
            counts[key] = result.rowcount or 0
        if dry_run:
            await db.rollback()
        else:
            await db.commit()
    return counts


async def _active_project_ids() -> set[str]:
    import models  # noqa: F401
    from database import AsyncSessionLocal
    from models.project import Project
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Project.id))
        return set(result.scalars().all())


def _cleanup_uploads(active_project_ids: set[str], dry_run: bool) -> list[str]:
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    if not upload_dir.exists():
        return []

    orphan_dirs = [
        path
        for path in upload_dir.iterdir()
        if path.is_dir() and path.name not in active_project_ids
    ]
    if not dry_run:
        for path in orphan_dirs:
            shutil.rmtree(path, ignore_errors=True)
    return [str(path) for path in orphan_dirs]


def _cleanup_milvus(active_project_ids: set[str], dry_run: bool) -> list[str]:
    try:
        from services.vector_service import (
            MILVUS_URI,
            delete_vectors_not_in_projects,
            shared_collection_names,
        )
        from pymilvus import MilvusClient
    except Exception as exc:
        print(f"Milvus cleanup skipped: cannot import pymilvus ({exc})")
        return []

    try:
        client = MilvusClient(uri=MILVUS_URI)
        collections = client.list_collections()
    except Exception as exc:
        print(f"Milvus cleanup skipped: cannot connect ({exc})")
        return []

    orphan_collections = []
    for name in collections:
        project_id = _project_id_from_collection(name)
        if project_id and project_id not in active_project_ids:
            orphan_collections.append(name)

    shared_cleanup = [
        f"{name}: project_id not in active SQL projects ({len(active_project_ids)} kept)"
        for name in shared_collection_names()
        if name in collections
    ]

    if not dry_run:
        for name in orphan_collections:
            client.drop_collection(collection_name=name)
        delete_vectors_not_in_projects(active_project_ids)
    legacy_cleanup = [f"{name} (legacy collection)" for name in orphan_collections]
    return legacy_cleanup + shared_cleanup


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean orphan project data while preserving settings and valid projects."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Actually delete orphan SQL rows, upload dirs, and Milvus vectors.",
    )
    args = parser.parse_args()
    dry_run = not args.yes
    _apply_local_data_defaults()

    print("Mode:", "dry-run" if dry_run else "delete")
    print(
        "DATABASE_URL:",
        os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./local_notebook.db"),
    )
    print("UPLOAD_DIR:", os.getenv("UPLOAD_DIR", "./uploads"))

    db_counts = await _cleanup_db(dry_run=dry_run)
    active_project_ids = await _active_project_ids()
    upload_dirs = _cleanup_uploads(active_project_ids, dry_run=dry_run)
    milvus_collections = _cleanup_milvus(active_project_ids, dry_run=dry_run)

    print("\nSQL orphan rows:")
    for key, count in db_counts.items():
        if count:
            print(f"  {key}: {count}")
    if not any(db_counts.values()):
        print("  none")

    print("\nUpload dirs:")
    if upload_dirs:
        for path in upload_dirs:
            print(f"  {path}")
    else:
        print("  none")

    print("\nMilvus vectors / legacy collections:")
    if milvus_collections:
        for name in milvus_collections:
            print(f"  {name}")
    else:
        print("  none")

    if dry_run:
        print("\nNo changes were made. Re-run with --yes to delete these orphan records.")


if __name__ == "__main__":
    asyncio.run(main())
