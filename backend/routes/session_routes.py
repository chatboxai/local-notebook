import json
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select, asc
from sqlalchemy.ext.asyncio import AsyncSession

from agent.citation_parser import CitationParser
from dependencies.auth import get_current_user
from dependencies.database import get_db
from dependencies.permissions import require_project, require_session
from models.message import Message
from models.session import Session
from models.user import User
from schemas.session import SessionCreate, SessionResponse
from utils.time import utc_isoformat

logger = logging.getLogger("session_routes")
router = APIRouter(tags=["sessions"])


class SessionTitleUpdate(BaseModel):
    title: Optional[str] = None


def _safe_json(raw: Optional[str]):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _brief_message(m: Message) -> dict:
    return {
        "id": m.id,
        "role": m.role,
        "created_at": utc_isoformat(m.created_at),
        "parent_message_id": m.parent_message_id,
    }


def _full_message(m: Message) -> dict:
    msg_data = {
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "created_at": utc_isoformat(m.created_at),
        "started_at": utc_isoformat(m.started_at),
        "finished_at": utc_isoformat(m.finished_at),
        "reasoning_content": m.reasoning_content,
        "agent_role": m.agent_role,
        "parent_message_id": m.parent_message_id,
    }
    citations = _safe_json(m.citations)
    if citations is not None:
        msg_data["citations"] = citations
    tool_calls = _safe_json(m.tool_calls)
    if tool_calls is not None:
        msg_data["tool_calls"] = tool_calls
    used_file_ids = _safe_json(m.used_file_ids)
    if used_file_ids is not None:
        msg_data["used_file_ids"] = used_file_ids
    return msg_data


@router.get("/projects/{project_id}/sessions")
async def list_sessions(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await require_project(db, project_id, current_user)
    total_result = await db.execute(
        select(func.count()).select_from(Session).where(Session.project_id == project_id)
    )
    total = total_result.scalar_one()

    result = await db.execute(
        select(Session)
        .where(Session.project_id == project_id)
        .order_by(Session.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()
    return {
        "sessions": [SessionResponse.model_validate(s).model_dump() for s in sessions],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/projects/{project_id}/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(
    project_id: str,
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await require_project(db, project_id, current_user)

    result = await db.execute(
        select(Session)
        .where(Session.project_id == project_id)
        .where(
            ~select(func.count())
            .select_from(Message)
            .where(Message.session_id == Session.id)
            .where(Message.deleted_at.is_(None))
            .correlate(Session)
            .exists()
        )
        .order_by(Session.created_at.desc())
        .limit(1)
    )
    empty_session = result.scalar_one_or_none()

    if empty_session:
        return {
            "id": empty_session.id,
            "project_id": project_id,
            "title": empty_session.title,
            "created_at": utc_isoformat(empty_session.created_at),
            "updated_at": utc_isoformat(empty_session.updated_at),
            "reused": True
        }

    session = Session(project_id=project_id, title=body.title or "\u65b0\u5bf9\u8bdd")
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return {
        "id": session.id,
        "project_id": project_id,
        "title": session.title,
        "created_at": utc_isoformat(session.created_at),
        "updated_at": utc_isoformat(session.updated_at),
        "reused": False
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    brief: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    session = await require_session(db, session_id, current_user)

    has_compact = bool(session.compact_summary and session.compact_message_id)

    total_result = await db.execute(
        select(func.count()).select_from(Message).where(Message.session_id == session_id).where(Message.deleted_at.is_(None))
    )
    total_messages = total_result.scalar_one()

    subquery = (
        select(Message.id)
        .where(Message.session_id == session_id)
        .where(Message.deleted_at.is_(None))
        .order_by(Message.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).subquery()
    result = await db.execute(
        select(Message)
        .where(Message.id.in_(select(subquery.c.id)))
        .order_by(asc(Message.created_at))
    )
    messages = list(result.scalars().all())

    while messages and messages[0].role not in ("user", ):
        messages.pop(0)

    processed_messages = []

    if brief:
        processed_messages = [_brief_message(m) for m in messages]
    else:
        raw_messages = []
        divider_inserted = False
        trigger_id = session.compact_trigger_message_id if has_compact else None
        for m in messages:
            if trigger_id and not divider_inserted and m.id == trigger_id:
                raw_messages.append({
                    "id": "compact_divider",
                    "role": "compact_divider",
                    "content": "\u4ee5\u4e0a\u5bf9\u8bdd\u5df2\u538b\u7f29",
                })
                divider_inserted = True

            raw_messages.append(_full_message(m))

        processed_messages = _process_messages_citations(raw_messages)
        for i, pm in enumerate(processed_messages):
            if pm.get("role") == "compact_divider":
                logger.info(f"[get_session] divider at processed[{i}]/{len(processed_messages)}")
                break

    raw_fetched = len(messages)
    return {
        "id": session.id,
        "project_id": session.project_id,
        "title": session.title,
        "created_at": utc_isoformat(session.created_at),
        "updated_at": utc_isoformat(session.updated_at),
        "messages": processed_messages,
        "total_messages": total_messages,
        "raw_fetched": raw_fetched,
        "messages_limit": limit,
        "messages_offset": offset,
    }


TOOL_DISPLAY_NAMES = {
    "query_knowledge_base": "\u6b63\u5728\u68c0\u7d22\u77e5\u8bc6\u5e93...",
    "read_segments": "\u6b63\u5728\u8bfb\u53d6\u539f\u6587...",
    "list_files": "\u6b63\u5728\u5217\u51fa\u6587\u4ef6...",
    "get_file_meta": "\u6b63\u5728\u83b7\u53d6\u6587\u4ef6\u4fe1\u606f...",
    "ask_image": "\u6b63\u5728\u5206\u6790\u56fe\u7247...",
}


def _process_messages_citations(messages: list) -> list:
    citations_map: dict = {}
    for m in messages:
        if m.get("role") == "tool" and m.get("citations"):
            citations = m["citations"]
            if isinstance(citations, dict):
                citations_map.update(citations)

    max_display_num = 0
    for metadata in citations_map.values():
        dn = metadata.get("display_num", 0)
        if dn > max_display_num:
            max_display_num = dn
    next_display_num = max_display_num + 1 if max_display_num > 0 else 1

    parser = CitationParser(citation_map=citations_map, start_display_num=next_display_num)
    processed_messages: list = []

    current_assistant_msg: dict | None = None
    current_parts: list = []

    def _flush_assistant():
        nonlocal current_assistant_msg, current_parts
        if current_assistant_msg is not None:
            if current_parts:
                current_assistant_msg["content_parts"] = current_parts
            processed_messages.append(current_assistant_msg)
            current_assistant_msg = None
            current_parts = []

    def _extract_parts(m: dict) -> list:
        parts: list = []

        if m.get("reasoning_content") and str(m["reasoning_content"]).strip():
            reasoning_text = str(m["reasoning_content"])
            processed_reasoning = ""
            for event in parser.feed(reasoning_text):
                if event["type"] == "text":
                    processed_reasoning += event["content"]
                elif event["type"] == "citation_ref":
                    processed_reasoning += f"{{{{CITE:{event['display_num']}}}}}"
            for event in parser.flush():
                if event["type"] == "text":
                    processed_reasoning += event["content"]
            parts.append({"type": "reasoning", "content": processed_reasoning})

        tool_calls = m.get("tool_calls")
        if isinstance(tool_calls, list):
            for tc in tool_calls:
                name = tc.get("function", {}).get("name", "") if isinstance(tc, dict) else ""
                if name:
                    parts.append({
                        "type": "tool_status",
                        "display": TOOL_DISPLAY_NAMES.get(name, f"\u6b63\u5728\u6267\u884c {name}..."),
                    })

        content = m.get("content") or ""
        if content:
            for event in parser.feed(content):
                if event["type"] == "text":
                    parts.append({"type": "text", "content": event["content"]})
                elif event["type"] == "citation_ref":
                    ref_item: dict = {
                        "type": "citation_ref",
                        "display_num": event["display_num"],
                    }
                    citation_type = event.get("citation_type")
                    if citation_type == "image":
                        ref_item["citation_type"] = "image"
                        ref_item["file_id"] = event.get("file_id", "")
                        ref_item["file_name"] = event.get("file_name", "")
                        if event.get("image_name"):
                            ref_item["image_name"] = event.get("image_name", "")
                        if event.get("image_index") is not None:
                            ref_item["image_index"] = event.get("image_index")
                        if event.get("page") is not None:
                            ref_item["page"] = event.get("page")
                    elif citation_type == "web":
                        ref_item["citation_type"] = "web"
                        ref_item["title"] = event.get("title", "")
                        ref_item["url"] = event.get("url", "")
                        ref_item["snippet"] = event.get("snippet", "")
                        ref_item["source"] = event.get("source", "")
                        ref_item["published_date"] = event.get("published_date", "")
                        ref_item["favicon"] = event.get("favicon", "")
                    elif citation_type == "audio":
                        ref_item["citation_type"] = "audio"
                        ref_item["file_name"] = event.get("file_name", "")
                        ref_item["segment_id"] = event.get("segment_id", "")
                        ref_item["summary"] = event.get("summary", "")
                        ref_item["time_start"] = event.get("time_start")
                        ref_item["time_end"] = event.get("time_end")
                        ref_item["time_range"] = event.get("time_range", "")
                    else:
                        ref_item["file_name"] = event.get("file_name", "")
                        ref_item["segment_id"] = event.get("segment_id", "")
                        ref_item["summary"] = event.get("summary", "")
                    parts.append(ref_item)

            for event in parser.flush():
                if event["type"] == "text":
                    parts.append({"type": "text", "content": event["content"]})

        return parts

    for m in messages:
        role = m.get("role")

        if role == "compact_divider":
            _flush_assistant()
            processed_messages.append(m.copy())

        elif role == "user":
            _flush_assistant()
            processed_messages.append(m.copy())

        elif role == "assistant":
            if current_assistant_msg is None:
                current_assistant_msg = m.copy()
                current_assistant_msg.pop("content", None)
                current_assistant_msg.pop("tool_calls", None)
                current_assistant_msg.pop("reasoning_content", None)

            current_parts.extend(_extract_parts(m))

    _flush_assistant()

    return processed_messages


@router.put("/sessions/{session_id}", response_model=SessionResponse)
@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    body: SessionTitleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    session = await require_session(db, session_id, current_user)
    if body.title is not None:
        session.title = body.title
    await db.commit()
    await db.refresh(session)
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    session = await require_session(db, session_id, current_user)
    await db.delete(session)
    await db.commit()


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    brief: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    session = await require_session(db, session_id, current_user)

    total_result = await db.execute(
        select(func.count()).select_from(Message).where(Message.session_id == session_id).where(Message.deleted_at.is_(None))
    )
    total = total_result.scalar_one()

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .where(Message.deleted_at.is_(None))
        .order_by(asc(Message.created_at))
        .limit(limit)
        .offset(offset)
    )
    messages = result.scalars().all()

    if brief:
        processed_messages = [_brief_message(m) for m in messages]
    else:
        raw_messages = [_full_message(m) for m in messages]
        processed_messages = _process_messages_citations(raw_messages)

    raw_fetched = len(messages)
    return {
        "session_id": session_id,
        "messages": processed_messages,
        "total": total,
        "raw_fetched": raw_fetched,
        "limit": limit,
        "offset": offset,
    }


class ExportRequest(BaseModel):
    user_message_ids: Optional[List[str]] = None
    include_citations: bool = True


@router.post("/sessions/{session_id}/export")
async def export_session(
    session_id: str,
    body: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from services.export_service import export_service

    session = await require_session(db, session_id, current_user)

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .where(Message.deleted_at.is_(None))
        .order_by(asc(Message.created_at))
    )
    messages = result.scalars().all()

    all_messages = []
    for m in messages:
        msg_data = {
            "id": m.id,
            "role": m.role,
            "content": m.content or "",
            "agent_role": m.agent_role,
        }
        if m.role == "tool":
            citations = _safe_json(m.citations)
            if citations is not None:
                msg_data["citations"] = citations
        all_messages.append(msg_data)

    try:
        docx_stream, filename = export_service.export_session_to_docx(
            session_title=session.title or "\u5bf9\u8bdd\u5bfc\u51fa",
            all_messages=all_messages,
            user_message_ids=body.user_message_ids,
            include_citations=body.include_citations,
        )

        from urllib.parse import quote
        encoded_filename = quote(filename)

        return StreamingResponse(
            docx_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("\u5bfc\u51fa\u5931\u8d25")
        raise HTTPException(status_code=500, detail="\u5bfc\u51fa\u5931\u8d25\uff0c\u8bf7\u91cd\u8bd5")
