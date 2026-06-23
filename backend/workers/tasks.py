import os
import sys
os.environ.setdefault("GRPC_DNS_RESOLVER", "native")
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "packages"))

import asyncio
import json
import logging
import time
from datetime import datetime, timezone

from arq.connections import RedisSettings
from arq.worker import func

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
WORKFLOW_STEP_CONCURRENCY = int(os.getenv("WORKFLOW_STEP_CONCURRENCY", "3"))
WORKFLOW_CANCEL_REQUESTED_STATUSES = {"cancelling", "cancelled"}
WORKFLOW_CANCELLED_MESSAGE = "用户已停止生成"
WORKFLOW_CANCELLED_STEP_MESSAGE = "__workflow_cancelled__"


class WorkflowCancelled(RuntimeError):
    """Raised when a workflow has been cancelled by the user."""


async def _get_workflow_status(session_factory, workflow_id: str) -> str | None:
    from sqlalchemy import select
    from models.workflow import Workflow

    async with session_factory() as db:
        result = await db.execute(
            select(Workflow.status).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()


async def _is_workflow_cancel_requested(session_factory, workflow_id: str) -> bool:
    status = await _get_workflow_status(session_factory, workflow_id)
    return status in WORKFLOW_CANCEL_REQUESTED_STATUSES


async def _raise_if_workflow_cancelled(session_factory, workflow_id: str) -> None:
    if await _is_workflow_cancel_requested(session_factory, workflow_id):
        raise WorkflowCancelled(WORKFLOW_CANCELLED_MESSAGE)


async def _mark_workflow_cancelled(
    session_factory,
    workflow_id: str,
    message: str = WORKFLOW_CANCELLED_MESSAGE,
) -> None:
    from sqlalchemy import select
    from models.feature import Feature
    from models.workflow import Workflow

    async with session_factory() as db:
        wf = await db.get(Workflow, workflow_id)
        if not wf:
            return

        if wf.status not in {"completed", "partial"}:
            wf.status = "cancelled"
            wf.error_message = message
            wf.finished_at = datetime.now(timezone.utc)

        result = await db.execute(
            select(Feature).where(
                Feature.workflow_id == workflow_id,
                Feature.status.in_(["pending", "processing"]),
            )
        )
        for feat in result.scalars().all():
            feat.status = "cancelled"
            feat.error_message = message
            feat.finished_at = datetime.now(timezone.utc)

        await db.commit()


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
                import config as _config
                llm_cfg = await _resolve_llm()
                if llm_cfg:
                    ak, bu, md = llm_cfg
                    economy = await _config.is_easy_task_llm_configured()
                    logger.info(f"[{file_name}] step 2.5: generating summaries for {len(segments)} segments (model={md}, economy={economy})")
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
        "Briefly describe this image in English. Focus on:\n"
        "1. The image's main subject and content.\n"
        "2. Key visual elements such as chart data, visible text, objects, or scenes.\n"
        "Use 50-100 English words."
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


def _build_workflow_execution_layers(feature_items: list[dict]) -> list[list[dict]]:
    """Build DAG execution layers from feature custom_config step_id/depends_on."""
    by_step_id: dict[str, dict] = {}
    errors: list[str] = []
    for item in feature_items:
        step_id = item.get("step_id")
        if not step_id:
            errors.append(f"feature {item.get('id')} is missing step_id")
            continue
        if step_id in by_step_id:
            errors.append(f"duplicate step_id: {step_id}")
            continue
        by_step_id[step_id] = item

    for item in feature_items:
        step_id = item.get("step_id")
        if not step_id:
            continue
        for dep_id in item.get("depends_on") or []:
            dep = by_step_id.get(dep_id)
            if not dep:
                errors.append(f"step {step_id!r} depends on unknown step_id {dep_id!r}")

    if errors:
        raise RuntimeError("; ".join(errors))

    layers: dict[str, int] = {}
    visiting: set[str] = set()

    def layer_of(step_id: str) -> int:
        if step_id in layers:
            return layers[step_id]
        if step_id in visiting:
            raise RuntimeError(f"dependency cycle detected at step_id {step_id!r}")
        visiting.add(step_id)
        item = by_step_id[step_id]
        deps = item.get("depends_on") or []
        layer = 0 if not deps else max(layer_of(dep_id) for dep_id in deps) + 1
        visiting.remove(step_id)
        layers[step_id] = layer
        return layer

    for step_id in by_step_id:
        layer_of(step_id)

    grouped: dict[int, list[dict]] = {}
    for item in feature_items:
        grouped.setdefault(layers[item["step_id"]], []).append(item)

    return [
        sorted(grouped[layer], key=lambda item: item["order_index"])
        for layer in sorted(grouped.keys())
    ]


def _build_workflow_dependency_ancestors(feature_items: list[dict]) -> dict[str, list[str]]:
    """Return all transitive upstream dependency step_ids for each step, in display order."""
    by_step_id = {
        item["step_id"]: item
        for item in feature_items
        if item.get("step_id")
    }
    order_index = {
        step_id: item["order_index"]
        for step_id, item in by_step_id.items()
    }
    ancestors: dict[str, set[str]] = {}
    visiting: set[str] = set()

    def collect(step_id: str) -> set[str]:
        if step_id in ancestors:
            return ancestors[step_id]
        if step_id in visiting:
            raise RuntimeError(f"dependency cycle detected at step_id {step_id!r}")
        visiting.add(step_id)
        item = by_step_id[step_id]
        result: set[str] = set()
        for dep_id in item.get("depends_on") or []:
            if dep_id not in by_step_id:
                raise RuntimeError(f"step {step_id!r} depends on unknown step_id {dep_id!r}")
            result.add(dep_id)
            result.update(collect(dep_id))
        visiting.remove(step_id)
        ancestors[step_id] = result
        return result

    return {
        step_id: sorted(collect(step_id), key=lambda dep_id: order_index.get(dep_id, 0))
        for step_id in by_step_id
    }


async def generate_workflow_task(
    ctx: dict,
    workflow_id: str,
    output_language: str | None = None,
) -> dict:
    """规划 + 逐栏目生成一份报告。"""
    from datetime import datetime, timezone

    from agent.feature_agent import FeatureAgent
    from agent.capabilities import DEFAULT_FEATURE_TYPE
    from agent.tools.query_knowledge_base import CitationState
    from models.feature import Feature
    from models.workflow import Workflow
    from services.workflow_citations import (
        convert_local_feature_to_workflow,
        finalize_workflow_citations,
    )
    from services.workflow_planner import generate_workflow_title, plan_workflow
    from services.workflow_titles import ensure_unique_workflow_title

    session_factory = ctx["session_factory"]
    workflow_started_at = time.perf_counter()
    output_language = (output_language or "").strip()

    # 1) 载入 workflow，置 processing
    async with session_factory() as db:
        from sqlalchemy import update as sa_update

        wf = await db.get(Workflow, workflow_id)
        if not wf:
            logger.error(f"generate_workflow_task: workflow {workflow_id} not found")
            return {"status": "error", "reason": "workflow not found"}
        if wf.status in WORKFLOW_CANCEL_REQUESTED_STATUSES:
            wf.status = "cancelled"
            wf.error_message = wf.error_message or WORKFLOW_CANCELLED_MESSAGE
            wf.finished_at = datetime.now(timezone.utc)
            await db.commit()
            logger.info("[workflow] cancelled before start workflow_id=%s", workflow_id)
            return {"status": "cancelled", "workflow_id": workflow_id}
        project_id = wf.project_id
        workflow_type = wf.workflow_type
        custom_prompt = wf.custom_prompt or ""
        file_ids = wf.get_file_ids()
        user_title = wf.title
        started_at = datetime.now(timezone.utc)
        result = await db.execute(
            sa_update(Workflow)
            .where(
                Workflow.id == workflow_id,
                Workflow.status.notin_(WORKFLOW_CANCEL_REQUESTED_STATUSES),
            )
            .values(status="processing", started_at=started_at)
        )
        await db.commit()
        if result.rowcount == 0:
            logger.info("[workflow] cancelled before processing claim workflow_id=%s", workflow_id)
            await _mark_workflow_cancelled(session_factory, workflow_id)
            return {"status": "cancelled", "workflow_id": workflow_id}

    logger.info(
        "[workflow] start workflow_id=%s project_id=%s type=%s title=%r "
        "file_ids=%s custom_prompt_chars=%d custom_prompt_preview=%r",
        workflow_id,
        project_id,
        workflow_type,
        user_title,
        file_ids,
        len(custom_prompt),
        custom_prompt[:200],
    )

    try:
        if not output_language:
            raise ValueError("缺少输出语言")

        await _raise_if_workflow_cancelled(session_factory, workflow_id)

        # 2) 未传标题时，先根据用户要求生成标题，再进入规划
        if not user_title:
            await _raise_if_workflow_cancelled(session_factory, workflow_id)
            user_title = await generate_workflow_title(
                custom_prompt,
                project_id=project_id,
                file_ids=file_ids,
                output_language=output_language,
                cancellation_check=lambda: _raise_if_workflow_cancelled(
                    session_factory,
                    workflow_id,
                ),
            )
            await _raise_if_workflow_cancelled(session_factory, workflow_id)
            async with session_factory() as db:
                wf = await db.get(Workflow, workflow_id)
                if wf:
                    if wf.status in WORKFLOW_CANCEL_REQUESTED_STATUSES:
                        raise WorkflowCancelled(WORKFLOW_CANCELLED_MESSAGE)
                    if wf.title:
                        user_title = wf.title
                    else:
                        user_title = await ensure_unique_workflow_title(
                            db,
                            project_id,
                            user_title,
                            exclude_workflow_id=workflow_id,
                        )
                        wf.title = user_title
                        await db.commit()
            logger.info(
                "[workflow] generated title workflow_id=%s title=%r",
                workflow_id,
                user_title,
            )

        # 3) 规划栏目
        await _raise_if_workflow_cancelled(session_factory, workflow_id)
        plan = await plan_workflow(
            project_id=project_id,
            custom_prompt=custom_prompt,
            file_ids=file_ids,
            report_title=user_title or "",
            output_language=output_language,
            cancellation_check=lambda: _raise_if_workflow_cancelled(
                session_factory,
                workflow_id,
            ),
        )
        await _raise_if_workflow_cancelled(session_factory, workflow_id)
        steps = plan["steps"]
        plan_title = user_title or ""
        logger.info(
            "[workflow] plan workflow_id=%s:\n%s",
            workflow_id,
            json.dumps(plan, ensure_ascii=False, indent=2),
        )

        # 4) 落 plan + 建 feature 行
        async with session_factory() as db:
            wf = await db.get(Workflow, workflow_id)
            if wf and wf.status in WORKFLOW_CANCEL_REQUESTED_STATUSES:
                raise WorkflowCancelled(WORKFLOW_CANCELLED_MESSAGE)
            wf.plan_json = json.dumps(plan, ensure_ascii=False)
            if not wf.title:
                plan_title = await ensure_unique_workflow_title(
                    db,
                    project_id,
                    plan_title,
                    exclude_workflow_id=workflow_id,
                )
                wf.title = plan_title
            for idx, step in enumerate(steps):
                feat = Feature(
                    project_id=project_id,
                    workflow_id=workflow_id,
                    feature_type=DEFAULT_FEATURE_TYPE,
                    step_index=idx,
                    step_name=step["step_name"],
                    title=step["step_name"],
                    status="pending",
                )
                feat.set_custom_config({
                    "prompt": custom_prompt,
                    "file_ids": file_ids,
                    "step_id": step.get("step_id"),
                    "depends_on": step.get("depends_on", []),
                    "instruction": step.get("instruction", ""),
                })
                db.add(feat)
            await db.commit()
    except WorkflowCancelled:
        logger.info("[workflow] cancelled during planning workflow_id=%s", workflow_id)
        await _mark_workflow_cancelled(session_factory, workflow_id)
        return {"status": "cancelled", "workflow_id": workflow_id}
    except Exception as exc:
        logger.exception(f"workflow {workflow_id} planning failed: {exc}")
        async with session_factory() as db:
            wf = await db.get(Workflow, workflow_id)
            if wf:
                wf.status = "failed"
                wf.error_message = f"规划失败: {exc}"
                wf.finished_at = datetime.now(timezone.utc)
                await db.commit()
        raise

    # 4) 按 planner 依赖图分层并发生成；每个栏目使用独立 CitationState。
    from sqlalchemy import select

    if await _is_workflow_cancel_requested(session_factory, workflow_id):
        logger.info("[workflow] cancelled before generation workflow_id=%s", workflow_id)
        await _mark_workflow_cancelled(session_factory, workflow_id)
        return {"status": "cancelled", "workflow_id": workflow_id}

    async with session_factory() as db:
        wf = await db.get(Workflow, workflow_id)
        result = await db.execute(
            select(Feature).where(Feature.workflow_id == workflow_id).order_by(Feature.step_index)
        )
        features = list(result.scalars().all())
        feature_items = []
        for feature in features:
            cfg = feature.get_custom_config()
            depends_on = cfg.get("depends_on") or []
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            feature_items.append({
                "id": feature.id,
                "order_index": feature.step_index,
                "step_id": cfg.get("step_id"),
                "depends_on": depends_on,
                "step_name": feature.step_name,
                "feature_type": feature.feature_type,
            })
        execution_layers = _build_workflow_execution_layers(feature_items)
        dependency_ancestors = _build_workflow_dependency_ancestors(feature_items)
        report_title = wf.title or plan_title
    total_steps = len(feature_items)
    logger.info(
        "[workflow] generation begin workflow_id=%s report_title=%r total_steps=%d layers=%d concurrency=%d",
        workflow_id,
        report_title,
        total_steps,
        len(execution_layers),
        WORKFLOW_STEP_CONCURRENCY,
    )

    agent = FeatureAgent()
    completed = 0
    failed = 0
    failed_step_ids: dict[str, str] = {}

    async def mark_feature_failed(item: dict, message: str) -> None:
        async with session_factory() as db:
            feat = await db.get(Feature, item["id"])
            if feat:
                feat.status = "failed"
                feat.error_message = message
                feat.finished_at = datetime.now(timezone.utc)
                await db.commit()

    async def mark_feature_cancelled(item: dict, message: str = WORKFLOW_CANCELLED_MESSAGE) -> None:
        async with session_factory() as db:
            feat = await db.get(Feature, item["id"])
            if feat and feat.status in {"pending", "processing"}:
                feat.status = "cancelled"
                feat.error_message = message
                feat.finished_at = datetime.now(timezone.utc)
                await db.commit()

    async def run_feature(item: dict) -> tuple[str, bool, str]:
        step_started_at = time.perf_counter()
        feat_id = item["id"]
        step_id = item["step_id"]
        step_index = item["order_index"]
        step_name = item["step_name"]
        feature_type = item["feature_type"] or DEFAULT_FEATURE_TYPE

        await _raise_if_workflow_cancelled(session_factory, workflow_id)

        async with session_factory() as db:
            feat = await db.get(Feature, feat_id)
            if not feat:
                return step_id, False, "feature not found"
            if feat.status == "cancelled":
                raise WorkflowCancelled(WORKFLOW_CANCELLED_MESSAGE)
            feat.status = "processing"
            feat.started_at = datetime.now(timezone.utc)
            feat.error_message = None
            await db.commit()
            custom_config = feat.get_custom_config()
            instruction = custom_config.get("instruction", "")
            depends_on = custom_config.get("depends_on") or []
            accessible_dependencies = dependency_ancestors.get(step_id, [])

        logger.info(
            "[workflow] step start workflow_id=%s step=%d/%d step_id=%s feature_id=%s type=%s "
            "name=%r depends_on=%s accessible_dependencies=%s instruction_chars=%d instruction_preview=%r",
            workflow_id,
            step_index + 1,
            total_steps,
            step_id,
            feat_id,
            feature_type,
            step_name,
            depends_on,
            accessible_dependencies,
            len(instruction),
            instruction[:240],
        )

        try:
            citation_state = CitationState()
            citation_state.project_id = project_id
            citation_state.file_ids = file_ids or None
            citation_state.workflow_id = workflow_id
            citation_state.current_step_id = step_id
            citation_state.current_feature_id = feat_id
            citation_state.depends_on = list(accessible_dependencies or [])

            blocks, local_citations, _ = await agent.generate(
                report_title=report_title,
                step_name=step_name,
                instruction=instruction,
                feature_type=feature_type,
                custom_prompt=custom_prompt,
                citation_state=citation_state,
                start_display_num=1,
                cancellation_check=lambda: _raise_if_workflow_cancelled(
                    session_factory,
                    workflow_id,
                ),
            )
            await _raise_if_workflow_cancelled(session_factory, workflow_id)
            workflow_blocks, workflow_citations = convert_local_feature_to_workflow(
                blocks,
                local_citations,
                step_id,
            )
            async with session_factory() as db:
                feat = await db.get(Feature, feat_id)
                feat.set_blocks(workflow_blocks)
                feat.set_citations(workflow_citations)
                feat.status = "completed"
                feat.finished_at = datetime.now(timezone.utc)
                await db.commit()
            logger.info(
                "[workflow] step done workflow_id=%s step=%d/%d step_id=%s feature_id=%s name=%r "
                "blocks=%d local_citations=%d workflow_citations=%d elapsed=%.2fs",
                workflow_id,
                step_index + 1,
                total_steps,
                step_id,
                feat_id,
                step_name,
                len(workflow_blocks),
                len(local_citations or {}),
                len(workflow_citations or {}),
                time.perf_counter() - step_started_at,
            )
            return step_id, True, ""
        except WorkflowCancelled:
            logger.info(
                "[workflow] step cancelled workflow_id=%s step=%d/%d step_id=%s feature_id=%s name=%r "
                "elapsed=%.2fs",
                workflow_id,
                step_index + 1,
                total_steps,
                step_id,
                feat_id,
                step_name,
                time.perf_counter() - step_started_at,
            )
            await mark_feature_cancelled(item)
            return step_id, False, WORKFLOW_CANCELLED_STEP_MESSAGE
        except Exception as exc:
            logger.exception(
                "[workflow] step failed workflow_id=%s step=%d/%d step_id=%s feature_id=%s name=%r "
                "elapsed=%.2fs error=%s",
                workflow_id,
                step_index + 1,
                total_steps,
                step_id,
                feat_id,
                step_name,
                time.perf_counter() - step_started_at,
                exc,
            )
            await mark_feature_failed(item, str(exc))
            return step_id, False, str(exc)

    for layer_index, layer in enumerate(execution_layers, start=1):
        if await _is_workflow_cancel_requested(session_factory, workflow_id):
            logger.info(
                "[workflow] cancelled before layer workflow_id=%s layer=%d/%d",
                workflow_id,
                layer_index,
                len(execution_layers),
            )
            await _mark_workflow_cancelled(session_factory, workflow_id)
            return {"status": "cancelled", "workflow_id": workflow_id}

        logger.info(
            "[workflow] layer start workflow_id=%s layer=%d/%d steps=%s",
            workflow_id,
            layer_index,
            len(execution_layers),
            [item["step_id"] for item in layer],
        )
        skipped = []
        runnable = []
        for item in layer:
            failed_deps = [
                dep_id for dep_id in (item.get("depends_on") or [])
                if dep_id in failed_step_ids
            ]
            if failed_deps:
                message = f"dependency failed: {', '.join(failed_deps)}"
                await mark_feature_failed(item, message)
                failed_step_ids[item["step_id"]] = message
                skipped.append(item["step_id"])
                failed += 1
            else:
                runnable.append(item)

        semaphore = asyncio.Semaphore(WORKFLOW_STEP_CONCURRENCY)

        async def run_with_limit(item: dict) -> tuple[str, bool, str]:
            async with semaphore:
                await _raise_if_workflow_cancelled(session_factory, workflow_id)
                return await run_feature(item)

        results = await asyncio.gather(
            *(run_with_limit(item) for item in runnable),
            return_exceptions=True,
        )
        for item, result in zip(runnable, results):
            if isinstance(result, WorkflowCancelled):
                await mark_feature_cancelled(item)
                await _mark_workflow_cancelled(session_factory, workflow_id)
                logger.info("[workflow] cancelled during layer workflow_id=%s", workflow_id)
                return {"status": "cancelled", "workflow_id": workflow_id}
            if isinstance(result, Exception):
                message = str(result)
                await mark_feature_failed(item, message)
                failed_step_ids[item["step_id"]] = message
                failed += 1
                continue
            step_id, ok, message = result
            if ok:
                completed += 1
            else:
                if message == WORKFLOW_CANCELLED_STEP_MESSAGE:
                    await _mark_workflow_cancelled(session_factory, workflow_id)
                    logger.info("[workflow] cancelled during feature workflow_id=%s", workflow_id)
                    return {"status": "cancelled", "workflow_id": workflow_id}
                failed_step_ids[step_id] = message
                failed += 1

        if await _is_workflow_cancel_requested(session_factory, workflow_id):
            logger.info("[workflow] cancelled after layer workflow_id=%s", workflow_id)
            await _mark_workflow_cancelled(session_factory, workflow_id)
            return {"status": "cancelled", "workflow_id": workflow_id}

        async with session_factory() as db:
            await finalize_workflow_citations(db, workflow_id)
            await db.commit()

        logger.info(
            "[workflow] layer done workflow_id=%s layer=%d/%d completed=%d failed=%d skipped=%s",
            workflow_id,
            layer_index,
            len(execution_layers),
            completed,
            failed,
            skipped,
        )

    # 5) 汇总 workflow 状态
    if await _is_workflow_cancel_requested(session_factory, workflow_id):
        logger.info("[workflow] cancelled before finalizing workflow_id=%s", workflow_id)
        await _mark_workflow_cancelled(session_factory, workflow_id)
        return {"status": "cancelled", "workflow_id": workflow_id}

    if completed == 0:
        final_status = "failed"
    elif failed > 0:
        final_status = "partial"
    else:
        final_status = "completed"

    async with session_factory() as db:
        wf = await db.get(Workflow, workflow_id)
        wf.status = final_status
        wf.finished_at = datetime.now(timezone.utc)
        await db.commit()

    logger.info(
        "[workflow] finished workflow_id=%s status=%s completed=%d failed=%d elapsed=%.2fs",
        workflow_id,
        final_status,
        completed,
        failed,
        time.perf_counter() - workflow_started_at,
    )
    return {"status": final_status, "workflow_id": workflow_id, "completed": completed, "failed": failed}


class WorkerSettings:
    functions = [
        parse_file_task,
        # Workflow generation is not idempotent yet; avoid ARQ replay appending duplicate steps.
        func(generate_workflow_task, max_tries=1),
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
    max_jobs = int(os.getenv("WORKER_MAX_JOBS", "4"))
    job_timeout = int(os.getenv("WORKER_JOB_TIMEOUT", "3600"))
    max_tries = 3
    retry_jobs = True
    retry_delay = 1.0
    retry_backoff = True
