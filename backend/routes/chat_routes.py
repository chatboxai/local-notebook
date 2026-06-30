import json
import logging
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import get_current_user
from dependencies.database import get_db
from dependencies.permissions import require_session
from models.message import Message
from models.session import Session
from models.user import User
from schemas.chat import ChatRequest, EditMessageRequest

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("chat_routes")


async def _agent_sse(
    session: Session,
    user_id: str,
    user_message: str,
    file_ids: list[str],
    db: AsyncSession,
    enable_web_search: bool = False,
    user_msg_id: Optional[str] = None,
    workflow_redis=None,
    output_language: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    from datetime import datetime, timezone
    from agent.chat_agent import ChatAgent
    import json as _json

    agent = ChatAgent()

    conversation_history: list = []
    citation_counter = 0
    next_citation_display_num = 1
    last_total_tokens = None
    started_at = datetime.now(timezone.utc)

    try:
        async for event in agent.ask_stream(
            question=user_message,
            session_id=session.id,
            project_id=session.project_id,
            user_id=user_id,
            file_ids=file_ids or None,
            enable_web_search=enable_web_search,
            workflow_redis=workflow_redis,
            output_language=output_language,
        ):
            if event["type"] == "citations":
                conversation_history = event.get("conversation_history") or []
                citation_counter = event.get("citation_counter", 0)
                next_citation_display_num = event.get("next_citation_display_num", 1)
                last_total_tokens = event.get("last_total_tokens")

            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    except Exception as e:
        logger.exception("ChatAgent stream error")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        try:
            error_msg = Message(
                session_id=session.id,
                role="assistant",
                content=f"Generation failed: {str(e)}",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                _error=str(e),
            )
            db.add(error_msg)
            await db.commit()
        except Exception:
            logger.exception("Failed to persist error message")
        return

    finished_at = datetime.now(timezone.utc)

    if not conversation_history:
        return

    try:
        last_assistant_id = None
        last_assistant_msg: Optional[Message] = None
        for msg in conversation_history:
            role = msg.get("role")
            content = msg.get("content") or ""

            if role == "assistant":
                tool_calls_data = msg.get("tool_calls")
                tool_calls_json = _json.dumps(tool_calls_data, ensure_ascii=False) if tool_calls_data else None

                assistant_msg = Message(
                    session_id=session.id,
                    role="assistant",
                    content=content,
                    reasoning_content=msg.get("reasoning_content"),
                    tool_calls=tool_calls_json,
                    started_at=started_at,
                    finished_at=finished_at,
                )
                db.add(assistant_msg)
                last_assistant_msg = assistant_msg

            elif role == "tool":
                tool_meta = {
                    "tool_call_id": msg.get("tool_call_id"),
                    "name": msg.get("name"),
                }
                citations_data = msg.get("citations")
                citations_json = _json.dumps(citations_data, ensure_ascii=False) if citations_data else None

                db.add(Message(
                    session_id=session.id,
                    role="tool",
                    content=content,
                    tool_calls=_json.dumps(tool_meta, ensure_ascii=False),
                    citations=citations_json,
                ))

        await db.flush()
        last_assistant_id = last_assistant_msg.id if last_assistant_msg else None
        await db.commit()

        saved_count = len(conversation_history) + 1
        session.citation_counter = citation_counter
        session.next_citation_display_num = next_citation_display_num
        session.message_count += saved_count
        session.updated_at = finished_at
        if last_total_tokens is not None:
            session.last_total_tokens = last_total_tokens
        await db.commit()

        if user_msg_id and last_assistant_id:
            yield f"data: {json.dumps({'type': 'message_ids', 'user_message_id': user_msg_id, 'assistant_message_id': last_assistant_id}, ensure_ascii=False)}\n\n"

    except Exception:
        logger.exception("Failed to persist conversation history")


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    session = await require_session(db, body.session_id, current_user)

    import json as _json
    user_msg = Message(
        session_id=body.session_id,
        role="user",
        content=body.message,
        used_file_ids=_json.dumps(body.file_ids) if body.file_ids else None,
    )
    db.add(user_msg)
    await db.commit()

    return StreamingResponse(
        _agent_sse(session, current_user.id, body.message, body.file_ids, db, body.enable_web_search,
                   user_msg_id=user_msg.id,
                   workflow_redis=request.app.state.redis,
                   output_language=body.output_language),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/messages/{message_id}/edit")
async def edit_message_and_regenerate(
    session_id: str,
    message_id: str,
    body: EditMessageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    session = await require_session(db, session_id, current_user)

    original_msg = await db.get(Message, message_id)
    if not original_msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    if original_msg.session_id != session_id:
        raise HTTPException(status_code=400, detail="消息不属于此会话")
    if original_msg.role != "user":
        raise HTTPException(status_code=400, detail="只能编辑用户消息")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    await db.execute(
        update(Message)
        .where(Message.session_id == session_id)
        .where(Message.deleted_at.is_(None))
        .where(Message.created_at >= original_msg.created_at)
        .values(deleted_at=now)
    )
    await db.commit()
    logger.info(f"[edit_message] 软删除了 message_id={message_id} 及之后的消息")

    import json as _json
    new_user_msg = Message(
        session_id=session_id,
        role="user",
        content=body.content,
        used_file_ids=_json.dumps(body.file_ids) if body.file_ids else None,
        parent_message_id=message_id,
    )
    db.add(new_user_msg)

    if session.compact_trigger_message_id == message_id:
        session.compact_trigger_message_id = new_user_msg.id
        logger.info(f"[edit_message] 更新 compact_trigger_message_id: {message_id} -> {new_user_msg.id}")

    await db.commit()

    return StreamingResponse(
        _agent_sse(
            session, current_user.id, body.content, body.file_ids or [], db,
            enable_web_search=body.enable_web_search,
            user_msg_id=new_user_msg.id,
            workflow_redis=request.app.state.redis,
            output_language=body.output_language,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
