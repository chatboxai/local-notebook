import os
import sys
os.environ.setdefault("GRPC_DNS_RESOLVER", "native")
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "packages"))

import asyncio
import logging
from datetime import datetime, timezone

from arq.connections import RedisSettings

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


async def on_startup(ctx: dict) -> None:
    from database import AsyncSessionLocal, engine, Base
    import models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    ctx["session_factory"] = AsyncSessionLocal

    await _recover_stuck_files(AsyncSessionLocal)

    logger.info("ARQ worker started")


async def _recover_stuck_files(session_factory) -> None:
    from sqlalchemy import select, delete as sa_delete
    from models.file import File
    from models.segment import Segment
    from models.block import Block
    from models.image import Image
    from services.vector_service import delete_by_file

    async with session_factory() as db:
        result = await db.execute(
            select(File).where(File.status == "processing")
        )
        stuck = result.scalars().all()
        if not stuck:
            return

        logger.warning(f"Found {len(stuck)} file(s) stuck in 'processing', recovering...")
        arq_pool = await _get_arq_pool()

        for f in stuck:
            logger.info(f"Recovering file {f.id} ({f.file_name})")
            await db.execute(sa_delete(Segment).where(Segment.file_id == f.id))
            await db.execute(sa_delete(Block).where(Block.file_id == f.id))
            await db.execute(sa_delete(Image).where(Image.file_id == f.id))
            await asyncio.to_thread(delete_by_file, f.project_id, f.id)
            f.status = "pending"
            await db.flush()
            await arq_pool.enqueue_job("parse_file_task", f.id)
            logger.info(f"Re-enqueued file {f.id}")

        await db.commit()
        if arq_pool:
            await arq_pool.aclose()


async def _get_arq_pool():
    from arq import create_pool
    try:
        return await create_pool(RedisSettings.from_dsn(REDIS_URL))
    except Exception as e:
        logger.error(f"Cannot connect to Redis for re-enqueue: {e}")
        return None


async def on_shutdown(ctx: dict) -> None:
    from database import engine
    await engine.dispose()
    logger.info("ARQ worker stopped")


async def parse_file_task(ctx: dict, file_id: str) -> dict:
    from models.file import File

    session_factory = ctx["session_factory"]

    async with session_factory() as db:
        db_file = await db.get(File, file_id)
        if not db_file:
            logger.error(f"parse_file_task: file {file_id} not found")
            return {"status": "error", "reason": "file not found"}

        file_name = db_file.file_name
        file_type = db_file.file_type
        file_path = db_file.file_path
        project_id = db_file.project_id

        try:
            logger.info(f"Parsing file {file_id} ({file_name}, type={file_type})")

            from models.segment import Segment
            from models.block import Block
            from models.image import Image
            from sqlalchemy import delete as sa_delete
            await db.execute(sa_delete(Segment).where(Segment.file_id == file_id))
            await db.execute(sa_delete(Block).where(Block.file_id == file_id))
            await db.execute(sa_delete(Image).where(Image.file_id == file_id))
            from services.vector_service import delete_by_file
            await asyncio.to_thread(delete_by_file, project_id, file_id)

            db_file.status = "processing"
            await db.commit()

            import config
            _, emb_base_url, _, emb_api_key = await config.resolve_embedding_config()
            if not emb_base_url:
                raise RuntimeError(
                    "Embedding 服务地址未配置。请在「设置」页面配置后重新上传。"
                )
            emb_source = await config.get_setting("embedding_source", "bailian")
            if emb_source != "local" and not emb_api_key:
                raise RuntimeError(
                    "Embedding API Key 未配置。请在「设置」页面配置百炼 API Key 后重新上传。"
                )

            logger.info(f"[{file_name}] step 1/5: extracting text & creating blocks")
            text, blocks, raw_images = await _extract_text_and_blocks(
                file_type, file_path, file_id=file_id, db=db
            )
            logger.info(f"[{file_name}] extracted {len(text)} chars, {len(blocks)} blocks, {len(raw_images)} raw images")

            images_meta = await _describe_images(file_name, raw_images)

            if not blocks:
                logger.warning(f"[{file_name}] no blocks produced, marking ready")
                db_file.status = "ready"
                db_file.updated_at = datetime.now(timezone.utc)
                await db.commit()
                return {"status": "ok", "file_id": file_id, "segments": 0}

            logger.info(f"[{file_name}] step 2/5: segmenting from {len(blocks)} blocks")
            from services.segment_service import segment_service
            split_result = segment_service.split_text_with_warnings(text, blocks)
            segments = split_result.segments
            for w in split_result.warnings:
                logger.warning(f"[{file_name}] segment warning: {w}")

            if not segments:
                logger.warning(f"[{file_name}] no segments produced, marking ready")
                db_file.status = "ready"
                db_file.updated_at = datetime.now(timezone.utc)
                await db.commit()
                return {"status": "ok", "file_id": file_id, "segments": 0}

            logger.info(f"[{file_name}] {len(segments)} segments")

            segment_summaries: dict[int, str] = {}
            llm_cfg = None
            try:
                from services.summary_service import _resolve_llm, generate_segment_summaries
                llm_cfg = await _resolve_llm()
                if llm_cfg:
                    ak, bu, md = llm_cfg
                    logger.info(f"[{file_name}] step 2.5: generating summaries for {len(segments)} segments (model={md})")
                    seg_inputs = [{"segment_index": s.segment_index, "content": s.content} for s in segments]
                    segment_summaries = await generate_segment_summaries(seg_inputs, ak, bu, md)
                    logger.info(f"[{file_name}] summaries generated: {len(segment_summaries)}/{len(segments)}")
                else:
                    logger.info(f"[{file_name}] LLM not configured, skipping segment summaries")
            except Exception as e:
                logger.warning(f"[{file_name}] segment summary step failed, continuing: {e}")

            logger.info(f"[{file_name}] step 3: embedding {len(segments)} segments")
            from services.embedding_service import embed_texts
            contents = [s.content for s in segments]
            vectors = await embed_texts(contents)
            logger.info(f"[{file_name}] embedding done, dim={len(vectors[0])}")

            logger.info(f"[{file_name}] step 4/5: storing vectors, blocks, segments & images")
            from services.vector_service import (
                ensure_collection, upsert_chunks,
                ensure_image_collection, upsert_image_chunks
            )
            from models.block import Block
            from models.image import Image
            import json as _json

            dim = len(vectors[0])
            await asyncio.to_thread(ensure_collection, project_id, dim)

            await db.execute(sa_delete(Block).where(Block.file_id == file_id))
            await db.execute(sa_delete(Segment).where(Segment.file_id == file_id))
            await db.execute(sa_delete(Image).where(Image.file_id == file_id))

            db_blocks = [
                Block(
                    id=f"{file_id}_{b['id']}",
                    file_id=file_id,
                    block_id=b['id'],
                    block_index=i,
                    block_type=b['type'],
                    content=b['content'],
                    pos_start=b['position']['start'],
                    pos_end=b['position']['end'],
                    page=b.get('page', 0),
                    extra=_json.dumps(b.get('extra')) if b.get('extra') else None,
                )
                for i, b in enumerate(blocks)
            ]
            db.add_all(db_blocks)
            await db.flush()
            logger.info(f"[{file_name}] stored {len(db_blocks)} blocks")

            db_segments = [
                Segment(
                    id=f"{file_id}_s_{s.segment_index}",
                    file_id=file_id,
                    project_id=project_id,
                    segment_index=s.segment_index,
                    content=s.content,
                    summary=segment_summaries.get(s.segment_index),
                    pos_start=s.pos_start,
                    pos_end=s.pos_end,
                    block_ids=_json.dumps(s.block_ids) if s.block_ids else None,
                )
                for s in segments
            ]
            db.add_all(db_segments)
            await db.flush()

            db_image_count = 0
            if images_meta:
                db_images = [
                    Image(
                        id=f"{file_id}_img_{img['image_index']}",
                        file_id=file_id,
                        image_index=img["image_index"],
                        description=img["description"],
                        vlm_model=img.get("vlm_model"),
                    )
                    for img in images_meta
                ]
                db.add_all(db_images)
                db_image_count = len(db_images)
                await db.flush()

            await db.commit()
            logger.info(
                f"[{file_name}] committed {len(db_blocks)} blocks, "
                f"{len(db_segments)} segments, {db_image_count} images"
            )

            chunks = [
                {
                    "id":            f"{file_id}_s_{s.segment_index}",
                    "file_id":       file_id,
                    "file_name":     file_name,
                    "segment_index": s.segment_index,
                    "content":       s.content,
                    "summary":       segment_summaries.get(s.segment_index) or "",
                    "embedding":     vectors[i],
                }
                for i, s in enumerate(segments)
            ]
            await asyncio.to_thread(upsert_chunks, project_id, chunks)

            if images_meta:
                logger.info(f"[{file_name}] storing {len(images_meta)} images")
                await asyncio.to_thread(ensure_image_collection, project_id, dim)

                image_descriptions = [img["description"] for img in images_meta]
                image_vectors = await embed_texts(image_descriptions)

                image_chunks = [
                    {
                        "id":            f"{file_id}_img_{img['image_index']}",
                        "file_id":       file_id,
                        "file_name":     file_name,
                        "image_index":   img["image_index"],
                        "description":   img["description"],
                        "embedding":     image_vectors[i],
                    }
                    for i, img in enumerate(images_meta)
                ]
                await asyncio.to_thread(upsert_image_chunks, project_id, image_chunks)
                logger.info(f"[{file_name}] stored {len(images_meta)} images to vector db")

            try:
                if llm_cfg and segment_summaries:
                    from services.summary_service import generate_file_summary
                    ak, bu, md = llm_cfg

                    logger.info(f"[{file_name}] step 5.1: generating file summary")
                    ordered = [segment_summaries[s.segment_index]
                               for s in segments if s.segment_index in segment_summaries]
                    file_result = await generate_file_summary(file_name, ordered, ak, bu, md)
                    if file_result["summary"]:
                        db_file.summary = file_result["summary"]
                    if file_result["keywords"]:
                        db_file.keywords = _json.dumps(file_result["keywords"], ensure_ascii=False)
                    logger.info(f"[{file_name}] file summary done")
                else:
                    logger.info(f"[{file_name}] skipping file/project summaries (LLM not configured or no segment summaries)")
            except Exception as e:
                logger.warning(f"[{file_name}] file/project summary failed, continuing: {e}")

            db_file.status = "ready"
            db_file.updated_at = datetime.now(timezone.utc)
            await db.commit()

            try:
                if llm_cfg and segment_summaries:
                    ak, bu, md = llm_cfg
                    logger.info(f"[{file_name}] step 5.2: generating project summary")
                    await _update_project_summary(db, project_id, ak, bu, md)
            except Exception as e:
                logger.warning(f"[{file_name}] project summary failed, continuing: {e}")

            logger.info(f"[{file_name}] done: {len(blocks)} blocks, {len(segments)} segments, {len(images_meta)} images stored")
            return {"status": "ok", "file_id": file_id, "blocks": len(blocks), "segments": len(segments), "images": len(images_meta)}

        except Exception as exc:
            logger.exception(f"Failed to parse file {file_id}: {exc}")
            await db.rollback()
            db_file = await db.get(File, file_id)
            if not db_file:
                raise
            db_file.status = "failed"
            db_file.error_message = str(exc)
            db_file.updated_at = datetime.now(timezone.utc)
            await db.commit()
            raise


async def _update_project_summary(db, project_id: str, api_key: str, base_url: str, model: str) -> None:
    from sqlalchemy import select
    from models.file import File
    from models.project import Project
    from services.summary_service import generate_project_summary

    result = await db.execute(
        select(File).where(File.project_id == project_id, File.status == "ready", File.summary.isnot(None))
    )
    ready_files = result.scalars().all()

    project = await db.get(Project, project_id)
    if not project:
        await db.commit()
        return
    project_name = project.name

    file_summaries = [
        {"file_name": f.file_name, "summary": f.summary}
        for f in ready_files if f.summary
    ]

    await db.commit()

    if not file_summaries:
        return

    summary = await generate_project_summary(project_name, file_summaries, api_key, base_url, model)
    if summary:
        project = await db.get(Project, project_id)
        if not project:
            await db.commit()
            return
        project.summary = summary
        await db.commit()
        logger.info(f"Project {project_id} summary updated ({len(summary)} chars)")


async def _describe_images(file_name: str, raw_images: list) -> list:
    if not raw_images:
        return []

    from services.vlm_client import describe_image, resolve_vlm_config

    try:
        api_key, base_url, model = await resolve_vlm_config()
        if not api_key or not model:
            logger.warning(f"[{file_name}] VLM 未配置，跳过 {len(raw_images)} 张图片的描述")
            return []
    except Exception:
        logger.warning(f"[{file_name}] VLM 配置读取失败，跳过图片描述")
        return []

    logger.info(f"[{file_name}] step 1.5/5: VLM 描述 {len(raw_images)} 张图片（model={model}，并发=2）")

    PROMPT = (
        "请简洁描述这张图片的内容，重点关注：\n"
        "1. 图片主题和主要内容\n"
        "2. 关键视觉元素（图表数据、文字、物体等）\n"
        "用中文回答，100-200字。"
    )

    semaphore = asyncio.Semaphore(5)

    async def _describe_one(img: dict):
        async with semaphore:
            try:
                description, vlm_model = await describe_image(img["file_path"], prompt=PROMPT)
                logger.info(f"[{file_name}] 图片 {img['image_index']} 描述完成（{len(description)} 字）")
                return {**img, "description": description, "vlm_model": vlm_model}
            except Exception as exc:
                logger.warning(f"[{file_name}] 图片 {img['image_index']} VLM 描述失败，跳过: {exc}")
                return None

    results = await asyncio.gather(*[_describe_one(img) for img in raw_images])
    return [r for r in results if r is not None]


async def _extract_text_and_blocks(
    file_type: str | None, file_path: str,
    file_id: str | None = None, db=None,
) -> tuple[str, list, list]:
    from workers.parsers import get_parser_for_file

    if file_type in ("txt", "pdf", "docx", "epub"):
        parser = get_parser_for_file(file_path)
        if file_type == "pdf":
            result = await parser.parse(file_path, file_id=file_id, db=db)
        else:
            result = await parser.parse(file_path)

        blocks = [
            {
                "id": b.id,
                "type": b.type,
                "content": b.content,
                "position": b.position,
                "page": b.page,
                "extra": b.extra,
            }
            for b in result.blocks
        ]

        return result.text, blocks, result.images

    elif file_type in {"jpg", "jpeg", "png"}:
        parser = get_parser_for_file(file_path)
        result = await parser.parse(file_path)

        blocks = [
            {
                "id": b.id,
                "type": b.type,
                "content": b.content,
                "position": b.position,
                "page": b.page,
                "extra": b.extra,
            }
            for b in result.blocks
        ]

        return result.text, blocks, result.images

    logger.info(f"No text extractor for file_type={file_type!r}, skipping")
    return "", [], []


class WorkerSettings:
    functions = [parse_file_task]
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
    max_jobs = int(os.getenv("WORKER_MAX_JOBS", "4"))
    job_timeout = int(os.getenv("WORKER_JOB_TIMEOUT", "3600"))
    max_tries = 3
    retry_jobs = True
    retry_delay = 1.0
    retry_backoff = True
