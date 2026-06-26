import asyncio
import os
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse as FastAPIFileResponse
from pydantic import BaseModel
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import get_current_user, get_current_user_query_or_header
from dependencies.database import get_db
from models.file import File
from models.project import Project
from schemas.file import FileResponse

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_CHUNK_SIZE = 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".epub", ".jpg", ".jpeg", ".png", ".wav", ".mp3", ".m4a"}

router = APIRouter(prefix="/projects/{project_id}/files", tags=["files"])


def _file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext in {"pdf", "docx", "doc", "txt", "epub", "jpg", "jpeg", "png", "wav", "mp3", "m4a"}:
        return ext
    return "unknown"


def _get_pdf_page_count_sync(file_path: str) -> int:
    try:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        return len(reader.pages)
    except Exception:
        return 0


async def _get_file_or_404(
    db: AsyncSession, file_id: str, project_id: str | None = None
) -> File:
    db_file = await db.get(File, file_id)
    if not db_file or (project_id is not None and db_file.project_id != project_id):
        raise HTTPException(status_code=404, detail="File not found")
    return db_file


async def _delete_file(db: AsyncSession, db_file: File) -> None:
    from models.segment import Segment
    from models.block import Block
    from models.image import Image

    try:
        Path(db_file.file_path).unlink(missing_ok=True)
    except Exception:
        pass

    try:
        from services.vector_service import delete_by_file
        await asyncio.wait_for(
            asyncio.to_thread(delete_by_file, db_file.project_id, db_file.id),
            timeout=5.0,
        )
    except Exception:
        pass

    await db.execute(sa_delete(Segment).where(Segment.file_id == db_file.id))
    await db.execute(sa_delete(Block).where(Block.file_id == db_file.id))
    await db.execute(sa_delete(Image).where(Image.file_id == db_file.id))
    await db.delete(db_file)
    await db.commit()


@router.get("", response_model=list[FileResponse])
async def list_files(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[FileResponse]:
    result = await db.execute(
        select(File)
        .where(File.project_id == project_id)
        .order_by(File.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    project_id: str,
    file: UploadFile,
    request: Request,
    output_language: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> FileResponse:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File type '{ext}' not supported.",
        )

    project_dir = UPLOAD_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    dest = project_dir / file.filename

    file_size = 0
    async with aiofiles.open(dest, "wb") as f:
        while chunk := await file.read(UPLOAD_CHUNK_SIZE):
            file_size += len(chunk)
            await f.write(chunk)

    db_file = File(
        project_id=project_id,
        file_name=file.filename,
        file_path=str(dest),
        file_type=_file_type(file.filename or ""),
        file_size=file_size,
        status="pending",
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)

    redis = request.app.state.redis
    if redis is None:
        await db.refresh(db_file)
        return db_file

    job = await redis.enqueue_job("parse_file_task", db_file.id, output_language)
    db_file.job_id = job.job_id
    await db.commit()
    await db.refresh(db_file)

    return db_file


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    project_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> None:
    db_file = await _get_file_or_404(db, file_id, project_id)
    await _delete_file(db, db_file)


file_router = APIRouter(prefix="/files", tags=["files"])


class FileUpdateRequest(BaseModel):
    file_name: str


@file_router.put("/{file_id}")
async def update_file(
    file_id: str,
    body: FileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    db_file = await _get_file_or_404(db, file_id)
    db_file.file_name = body.file_name
    await db.commit()
    await db.refresh(db_file)
    return {
        "id": db_file.id,
        "file_name": db_file.file_name,
        "status": db_file.status,
    }


@file_router.post("/status/batch")
async def get_files_status_batch(
    file_ids: list[str] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    if not file_ids:
        return {"files": []}
    result = await db.execute(
        select(File.id, File.status, File.error_message).where(File.id.in_(file_ids))
    )
    files = [
        {"id": row.id, "status": row.status, "error_message": row.error_message}
        for row in result.all()
    ]
    return {"files": files}


@file_router.get("/{file_id}", response_model=FileResponse)
async def get_file_by_id(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> FileResponse:
    return await _get_file_or_404(db, file_id)


@file_router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_by_id(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> None:
    db_file = await _get_file_or_404(db, file_id)
    await _delete_file(db, db_file)


@file_router.get("/{file_id}/content")
async def get_file_content(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    from models.segment import Segment
    from models.block import Block
    from sqlalchemy import select, asc
    import json

    db_file = await _get_file_or_404(db, file_id)

    if db_file.status != "ready":
        raise HTTPException(status_code=400, detail="文件尚未处理完成")

    result = await db.execute(
        select(Block)
        .where(Block.file_id == file_id)
        .order_by(asc(Block.block_index))
    )
    blocks = result.scalars().all()

    result = await db.execute(
        select(Segment)
        .where(Segment.file_id == file_id)
        .order_by(asc(Segment.segment_index))
    )
    segments_raw = result.scalars().all()
    segments = [
        {
            "segment_id": s.id,
            "block_ids": json.loads(s.block_ids) if s.block_ids else [],
            "summary": "",
        }
        for s in segments_raw
    ]

    return {
        "file_id": file_id,
        "file_name": db_file.file_name,
        "summary": "",
        "keywords": [],
        "blocks": [
            {
                "block_id": b.block_id,
                "block_type": b.block_type,
                "content": b.content,
                "page": b.page,
                "extra": b.get_extra(),
            }
            for b in blocks
        ],
        "segments": segments
    }


@file_router.get("/{file_id}/content/pages")
async def get_file_pages(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    from models.segment import Segment
    from models.block import Block
    from sqlalchemy import select, asc, func
    import json

    db_file = await _get_file_or_404(db, file_id)

    if db_file.status != "ready":
        raise HTTPException(status_code=400, detail="文件尚未处理完成")

    result = await db.execute(
        select(func.count())
        .select_from(Block)
        .where(Block.file_id == file_id, Block.page > 0)
    )
    has_page_info = (result.scalar() or 0) > 0

    is_pdf = db_file.file_type == "pdf"
    has_pages = has_page_info or is_pdf

    if not has_pages:
        return {
            "file_id": file_id,
            "file_name": db_file.file_name,
            "file_type": db_file.file_type,
            "has_pages": False,
            "total_pages": 0,
            "pages": [],
            "segments": []
        }

    result = await db.execute(
        select(Block.page, func.count().label("block_count"))
        .where(Block.file_id == file_id, Block.page > 0)
        .group_by(Block.page)
        .order_by(asc(Block.page))
    )
    page_list = [{"page": row.page, "block_count": row.block_count} for row in result.all()]

    result = await db.execute(
        select(func.max(Block.page))
        .where(Block.file_id == file_id)
    )
    total_pages = result.scalar() or 0

    if is_pdf and total_pages == 0:
        result = await db.execute(
            select(func.count()).select_from(Block).where(Block.file_id == file_id)
        )
        block_count = result.scalar() or 0

        total_pages = await asyncio.to_thread(_get_pdf_page_count_sync, db_file.file_path)
        if total_pages == 0:
            total_pages = 1

        if total_pages > 0 and not page_list:
            page_list = [{"page": 1, "block_count": block_count}]

    if total_pages == 0:
        result = await db.execute(
            select(func.count()).select_from(Block).where(Block.file_id == file_id)
        )
        block_count = result.scalar() or 0
        if block_count > 0:
            total_pages = 1
            page_list = [{"page": 1, "block_count": block_count}]

    result = await db.execute(
        select(Segment)
        .where(Segment.file_id == file_id)
        .order_by(asc(Segment.segment_index))
    )
    segments_raw = result.scalars().all()
    segments = [
        {
            "segment_id": s.id,
            "block_ids": json.loads(s.block_ids) if s.block_ids else [],
            "summary": "",
        }
        for s in segments_raw
    ]

    return {
        "file_id": file_id,
        "file_name": db_file.file_name,
        "file_type": db_file.file_type,
        "has_pages": True,
        "total_pages": total_pages,
        "pages": page_list,
        "segments": segments
    }


@file_router.get("/{file_id}/raw")
async def get_file_raw(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    db_file = await _get_file_or_404(db, file_id)

    file_path = Path(db_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    content_type = "application/octet-stream"
    if db_file.file_type == "pdf":
        content_type = "application/pdf"
    elif db_file.file_type == "docx":
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif db_file.file_type == "txt":
        content_type = "text/plain; charset=utf-8"

    from urllib.parse import quote

    encoded_filename = quote(db_file.file_name, safe="")

    return FastAPIFileResponse(
        path=str(file_path),
        media_type=content_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
        }
    )


@file_router.get("/{file_id}/preview")
async def preview_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_query_or_header),
):
    from fastapi.responses import FileResponse

    db_file = await _get_file_or_404(db, file_id)

    file_path = Path(db_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    mime_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }
    if db_file.file_type in mime_types:
        media_type = mime_types[db_file.file_type]
        return FileResponse(str(file_path), media_type=media_type)

    raise HTTPException(status_code=400, detail="Preview only available for image files")


@file_router.post("/{file_id}/blocks/bbox")
async def get_blocks_bbox(
    file_id: str,
    block_ids: list[str] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    from models.block import Block
    from sqlalchemy import select

    db_file = await _get_file_or_404(db, file_id)

    if not block_ids:
        return {
            "file_id": file_id,
            "file_type": db_file.file_type,
            "blocks": {}
        }

    result = await db.execute(
        select(Block.block_id, Block.page, Block.extra)
        .where(Block.file_id == file_id, Block.block_id.in_(block_ids))
    )
    blocks = result.all()

    blocks_info = {}
    for row in blocks:
        bbox = None
        if row.extra:
            try:
                import json
                extra = json.loads(row.extra) if isinstance(row.extra, str) else row.extra
                bbox = extra.get("bbox")
            except (json.JSONDecodeError, AttributeError):
                pass

        blocks_info[row.block_id] = {
            "page": row.page or 0,
            "bbox": bbox
        }

    return {
        "file_id": file_id,
        "file_type": db_file.file_type,
        "blocks": blocks_info
    }


@file_router.post("/{file_id}/blocks/find-by-position")
async def find_block_by_position(
    file_id: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    from models.block import Block
    from sqlalchemy import select, and_
    import json

    db_file = await _get_file_or_404(db, file_id)

    page = data.get("page")
    x = data.get("x")
    y = data.get("y")

    if page is None or x is None or y is None:
        raise HTTPException(status_code=400, detail="Missing required parameters: page, x, y")

    result = await db.execute(
        select(Block)
        .where(
            and_(
                Block.file_id == file_id,
                Block.page == page
            )
        )
    )
    blocks = result.scalars().all()

    for block in blocks:
        if not block.extra:
            continue

        try:
            extra = json.loads(block.extra) if isinstance(block.extra, str) else block.extra
            bbox = extra.get("bbox")
            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = bbox
            if x1 <= x <= x2 and y1 <= y <= y2:
                return {
                    "found": True,
                    "block": {
                        "block_id": block.block_id,
                        "content": block.content[:500] if block.content else "",
                        "page": block.page,
                        "bbox": bbox
                    }
                }
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue

    return {"found": False, "block": None}


@file_router.post("/{file_id}/blocks/location")
async def get_blocks_location(
    file_id: str,
    block_ids: list[str] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    from models.block import Block
    from sqlalchemy import select

    db_file = await _get_file_or_404(db, file_id)

    if not block_ids:
        return {
            "file_id": file_id,
            "blocks": {}
        }

    result = await db.execute(
        select(Block.block_id, Block.page, Block.block_index)
        .where(Block.file_id == file_id, Block.block_id.in_(block_ids))
    )
    blocks = result.all()

    blocks_info = {}
    for row in blocks:
        blocks_info[row.block_id] = {
            "page": row.page or 0,
            "block_index": row.block_index or 0,
            "exists": True
        }

    for bid in block_ids:
        if bid not in blocks_info:
            blocks_info[bid] = {"page": 0, "block_index": 0, "exists": False}

    return {
        "file_id": file_id,
        "blocks": blocks_info
    }


@file_router.get("/{file_id}/image-info")
async def get_image_info(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    from models.image import Image
    from sqlalchemy import select, asc

    db_file = await _get_file_or_404(db, file_id)

    IMAGE_TYPES = {"jpg", "jpeg", "png"}
    if db_file.file_type not in IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Not an image file")

    if db_file.status != "ready":
        raise HTTPException(status_code=400, detail="文件尚未处理完成")

    result = await db.execute(
        select(Image)
        .where(Image.file_id == file_id)
        .order_by(asc(Image.image_index))
    )
    images = result.scalars().all()

    return {
        "file_id": file_id,
        "file_name": db_file.file_name,
        "file_type": db_file.file_type,
        "images": [img.to_dict() for img in images],
    }
