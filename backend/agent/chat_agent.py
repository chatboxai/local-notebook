import asyncio
import json
import logging
import re
from typing import AsyncGenerator

import config
from agent.citation_parser import CitationParser
from agent.prompts import CHAT_AGENT_SYSTEM_PROMPT
from agent.tools.query_knowledge_base import (
    CitationState,
    QueryKnowledgeBaseTool,
)
from agent.tools.read_segments import ReadSegmentsTool
from agent.tools.file_tools import ListFilesTool, GetFileMetaTool, AskImageTool

import kosong
from kosong.chat_provider import ChatProviderError, StreamedMessagePart
from kosong.contrib.chat_provider.openai_legacy import OpenAILegacy
from kosong.message import Message, TextPart, ThinkPart, ToolCall
from kosong.tooling import ToolResult
from kosong.tooling.simple import SimpleToolset

logger = logging.getLogger("chat_agent")

MAX_HISTORY_MESSAGES = 40
MAX_ITERATIONS = 20
COMPACT_TOKEN_THRESHOLD = 90_000
COMPACT_MIN_STEPS = 10
COMPACT_MIN_ROUNDS = 3


class ChatAgent:

    def __init__(self):
        self.system_prompt = CHAT_AGENT_SYSTEM_PROMPT

        self._citation_state = CitationState()
        self._next_display_num = 1

    @property
    def session_citation_counter(self) -> int:
        return self._citation_state.citation_counter

    @property
    def session_next_display_num(self) -> int:
        return self._next_display_num

    async def ask_stream(
        self,
        question: str,
        session_id: str,
        project_id: str,
        file_ids: list[str] | None = None,
        enable_web_search: bool = False,
    ) -> AsyncGenerator[dict, None]:
        api_key, base_url, model = await config.resolve_llm_config()

        if not api_key:
            yield {"type": "error", "message": "LLM API key 未配置，请前往「设置 → LLM」填写。"}
            return

        chat_provider = OpenAILegacy(
            model=model,
            api_key=api_key,
            base_url=base_url,
            reasoning_key="reasoning_content",
        ).with_generation_kwargs(max_tokens=4000)

        self._citation_state.project_id = project_id
        self._citation_state.file_ids = file_ids

        kb_tool = QueryKnowledgeBaseTool(citation_state=self._citation_state)
        read_tool = ReadSegmentsTool(citation_state=self._citation_state)
        list_files_tool = ListFilesTool(citation_state=self._citation_state)
        file_meta_tool = GetFileMetaTool(citation_state=self._citation_state)
        ask_image_tool = AskImageTool(citation_state=self._citation_state)
        tools = [kb_tool, read_tool, list_files_tool, file_meta_tool, ask_image_tool]

        if enable_web_search:
            from agent.tools.web_search import WebSearchTool
            _, ws_key, ws_base_url = await config.resolve_web_search_config()
            web_search_tool = WebSearchTool(
                citation_state=self._citation_state,
                api_key=ws_key or "",
                base_url=ws_base_url or "",
            )
            tools.append(web_search_tool)
            logger.info(f"联网搜索工具已加入 (configured={bool(ws_key)})")

        toolset = SimpleToolset(tools)

        history = await self._load_history(session_id)

        compact_needed = await self._should_compact(session_id, question)
        if compact_needed:
            yield {"type": "compacting"}
            try:
                await self._execute_compact(
                    session_id=session_id,
                    history=history,
                    chat_provider=chat_provider,
                )
                self._citation_state = CitationState()
                self._citation_state.project_id = project_id
                self._citation_state.file_ids = file_ids
                for tool in tools:
                    tool.state = self._citation_state
                history = await self._load_history(session_id)
                yield {"type": "compact_done"}
            except Exception as e:
                logger.exception("[compact] 执行失败，继续使用截断历史")
                yield {"type": "compact_failed", "message": str(e)}

        history.append(Message(role="user", content=question))

        citation_parser = CitationParser(
            citation_map=self._citation_state.citations_map,
            start_display_num=self._next_display_num,
        )

        logger.info(
            f"[LLM] model={model} base_url={base_url} "
            f"tools={[t.name for t in toolset.tools]} messages_count={len(history)}"
        )

        yield {"type": "start"}

        conversation_history: list[dict] = []
        last_total_tokens: int | None = None

        for iteration in range(MAX_ITERATIONS):
            is_final = iteration == MAX_ITERATIONS - 1

            current_toolset = toolset
            if is_final:
                history.append(Message(
                    role="user",
                    content="【系统提示】工具调用次数已达到上限，请立即根据已有信息回答，不要再调用任何工具。",
                ))

            part_queue: asyncio.Queue[StreamedMessagePart | None] = asyncio.Queue()

            async def on_message_part(part: StreamedMessagePart) -> None:
                await part_queue.put(part)

            def on_tool_result(result: ToolResult) -> None:
                logger.info(f"[tool_result] {result}")

            step_task = asyncio.create_task(
                kosong.step(
                    chat_provider=chat_provider,
                    system_prompt=self.system_prompt,
                    toolset=current_toolset,
                    history=history,
                    on_message_part=on_message_part,
                    on_tool_result=on_tool_result,
                )
            )

            full_content = ""
            raw_content = ""
            iteration_reasoning = ""
            tool_call_notified = False

            try:
                while True:
                    if step_task.done():
                        while not part_queue.empty():
                            part = part_queue.get_nowait()
                            if part is None:
                                break
                            if isinstance(part, TextPart):
                                raw_content += part.text
                            elif isinstance(part, ThinkPart):
                                iteration_reasoning += part.think
                            async for event in self._process_part(part, citation_parser):
                                if event["type"] == "text":
                                    full_content += event.get("content", "")
                                yield event
                        break

                    try:
                        part = await asyncio.wait_for(part_queue.get(), timeout=0.1)
                    except asyncio.TimeoutError:
                        continue

                    if part is None:
                        break

                    if isinstance(part, TextPart):
                        raw_content += part.text
                    elif isinstance(part, ThinkPart):
                        iteration_reasoning += part.think

                    if isinstance(part, (ToolCall,)) and not tool_call_notified:
                        tool_call_notified = True

                    async for event in self._process_part(part, citation_parser):
                        if event["type"] == "text":
                            full_content += event.get("content", "")
                        yield event

                step_result = await step_task

                if step_result.usage:
                    last_total_tokens = step_result.usage.total

            except ChatProviderError as e:
                yield {"type": "error", "message": str(e)}
                return
            except asyncio.CancelledError:
                step_task.cancel()
                logger.info("Stream cancelled")
                return
            except Exception as e:
                logger.exception("ChatAgent error")
                yield {"type": "error", "message": str(e)}
                return

            if step_result.tool_calls and not is_final:
                tools_display = [
                    {
                        "name": tc.function.name,
                        "display": self._tool_display_name(tc.function.name),
                    }
                    for tc in step_result.tool_calls
                ]
                yield {"type": "tool_executing", "tools": tools_display}

                tool_results = await step_result.tool_results()

                history.append(step_result.message)

                tool_outputs: list[tuple[str, str, str]] = []
                for tc, tr in zip(step_result.tool_calls, tool_results):
                    output = tr.output if hasattr(tr, "output") else str(tr)
                    if hasattr(output, "text") if hasattr(output, "__class__") else False:
                        output_str = output.text
                    elif isinstance(output, str):
                        output_str = output
                    else:
                        output_str = str(output)
                    history.append(Message(
                        role="tool",
                        content=output_str,
                        tool_call_id=tc.id,
                    ))
                    tool_outputs.append((output_str, tc.id, tc.function.name))

                for event in citation_parser.flush():
                    yield event
                self._sync_display_nums(citation_parser)

                conversation_history.append({
                    "role": "assistant",
                    "content": raw_content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments or "{}",
                            },
                        }
                        for tc in step_result.tool_calls
                    ],
                    "reasoning_content": iteration_reasoning or None,
                })
                for output_str, tc_id, tc_name in tool_outputs:
                    conversation_history.append({
                        "role": "tool",
                        "content": output_str,
                        "tool_call_id": tc_id,
                        "name": tc_name,
                        "citations": dict(self._citation_state.citations_map),
                    })

                citation_parser = CitationParser(
                    citation_map=self._citation_state.citations_map,
                    start_display_num=self._next_display_num,
                )
                continue

            for event in citation_parser.flush():
                yield event
            self._sync_display_nums(citation_parser)

            conversation_history.append({
                "role": "assistant",
                "content": raw_content,
                "reasoning_content": iteration_reasoning or None,
            })

            citation_summary = citation_parser.get_citation_summary()
            citations_result = self._extract_citations(full_content)

            yield {
                "type": "citations",
                "data": citations_result,
                "citation_summary": citation_summary,
                "citation_counter": self.session_citation_counter,
                "next_citation_display_num": self.session_next_display_num,
                "conversation_history": conversation_history,
                "last_total_tokens": last_total_tokens,
            }
            yield {"type": "done"}
            return

        yield {"type": "error", "message": "问题较为复杂，已达到处理步骤上限。请尝试简化提问。"}

    async def _process_part(
        self,
        part: StreamedMessagePart,
        citation_parser: CitationParser,
    ) -> AsyncGenerator[dict, None]:
        from kosong.message import ToolCallPart

        if isinstance(part, TextPart):
            for event in citation_parser.feed(part.text):
                yield event
        elif isinstance(part, ThinkPart):
            for event in citation_parser.feed(part.think):
                if event["type"] == "text":
                    yield {"type": "reasoning", "content": event["content"]}
                elif event["type"] == "citation_ref":
                    yield {"type": "reasoning_citation_ref", **{k: v for k, v in event.items() if k != "type"}}
        elif isinstance(part, (ToolCall, ToolCallPart)):
            pass

    async def _load_history(self, session_id: str) -> list[Message]:
        from database import AsyncSessionLocal
        from models.message import Message as DBMessage
        from models.session import Session as DBSession
        from sqlalchemy import select

        messages: list[Message] = []
        async with AsyncSessionLocal() as db:
            session_obj = await db.get(DBSession, session_id)
            if session_obj:
                self._citation_state.citation_counter = session_obj.citation_counter or 0
                self._next_display_num = session_obj.next_citation_display_num or 1

            has_compact = session_obj and session_obj.compact_summary

            if has_compact:
                if session_obj.compact_citations_json:
                    try:
                        snapshot = json.loads(session_obj.compact_citations_json)
                        if isinstance(snapshot, dict):
                            self._citation_state.citations_map.update(snapshot)
                    except json.JSONDecodeError:
                        logger.warning("[load_history] compact_citations_json 解析失败")

                messages.append(Message(
                    role="user",
                    content=f"[对话上下文摘要]\n{session_obj.compact_summary}",
                ))
                messages.append(Message(
                    role="assistant",
                    content="好的，我已了解之前的对话内容。请继续。",
                ))

                if session_obj.compact_message_id:
                    boundary_msg = await db.get(DBMessage, session_obj.compact_message_id)
                    if boundary_msg:
                        query = (
                            select(DBMessage)
                            .where(DBMessage.session_id == session_id)
                            .where(DBMessage.deleted_at.is_(None))
                            .where(DBMessage.created_at > boundary_msg.created_at)
                            .order_by(DBMessage.created_at.asc())
                        )
                    else:
                        query = (
                            select(DBMessage)
                            .where(DBMessage.session_id == session_id)
                            .where(DBMessage.deleted_at.is_(None))
                            .order_by(DBMessage.created_at.asc())
                            .limit(MAX_HISTORY_MESSAGES)
                        )
                else:
                    query = (
                        select(DBMessage)
                        .where(DBMessage.session_id == session_id)
                        .where(DBMessage.deleted_at.is_(None))
                        .order_by(DBMessage.created_at.asc())
                        .limit(MAX_HISTORY_MESSAGES)
                    )
            else:
                query = (
                    select(DBMessage)
                    .where(DBMessage.session_id == session_id)
                    .where(DBMessage.deleted_at.is_(None))
                    .order_by(DBMessage.created_at.asc())
                )

            result = await db.execute(query)
            db_rows = list(result.scalars().all())

            for msg in db_rows:
                content = msg.content or ""
                role = msg.role

                if msg._error and not content.startswith("⚠️"):
                    content = f"⚠️ 生成失败：{msg._error}"

                if role == "tool":
                    if msg.citations:
                        try:
                            citations_data = json.loads(msg.citations)
                            if isinstance(citations_data, dict):
                                self._citation_state.citations_map.update(citations_data)
                        except json.JSONDecodeError:
                            pass

                    tool_call_id = None
                    if msg.tool_calls:
                        try:
                            tc_data = json.loads(msg.tool_calls)
                            if isinstance(tc_data, dict):
                                tool_call_id = tc_data.get("tool_call_id")
                        except json.JSONDecodeError:
                            pass

                    messages.append(Message(
                        role="tool",
                        content=content,
                        tool_call_id=tool_call_id,
                    ))

                elif role == "assistant":
                    tool_calls_list = None
                    if msg.tool_calls:
                        try:
                            tc_data = json.loads(msg.tool_calls)
                            if isinstance(tc_data, list):
                                tool_calls_list = [
                                    ToolCall(
                                        id=tc.get("id", f"call_{i}"),
                                        function=ToolCall.FunctionBody(
                                            name=tc.get("function", {}).get("name", ""),
                                            arguments=tc.get("function", {}).get("arguments", "{}"),
                                        ),
                                    )
                                    for i, tc in enumerate(tc_data)
                                ]
                        except json.JSONDecodeError:
                            pass

                    msg_content: list = []
                    if msg.reasoning_content:
                        msg_content.append(ThinkPart(think=msg.reasoning_content))
                    if content:
                        msg_content.append(TextPart(text=content))

                    kwargs: dict = {"role": "assistant", "content": msg_content}
                    if tool_calls_list:
                        kwargs["tool_calls"] = tool_calls_list
                    messages.append(Message(**kwargs))

                else:
                    messages.append(Message(role=role, content=content))

        for cid, meta in self._citation_state.citations_map.items():
            ctype = meta.get("type", "segment")
            if ctype == "segment" and meta.get("segment_id"):
                self._citation_state.segment_to_citation[meta["segment_id"]] = cid
            elif ctype == "image" and meta.get("image_id"):
                self._citation_state.image_to_citation[meta["image_id"]] = cid

        logger.info(
            f"[load_history] session={session_id} messages={len(messages)} "
            f"citations={len(self._citation_state.citations_map)} "
            f"citation_counter={self._citation_state.citation_counter} "
            f"next_display_num={self._next_display_num} "
            f"compact={'yes' if has_compact else 'no'}"
        )
        return messages

    def _sync_display_nums(self, parser: CitationParser):
        for citation_id, display_num in parser.id_to_display.items():
            if citation_id in self._citation_state.citations_map:
                entry = self._citation_state.citations_map[citation_id]
                if entry.get("display_num") is None:
                    entry["display_num"] = display_num
        self._next_display_num = parser.display_num

    def _extract_citations(self, answer: str) -> dict:
        citation_nums: set[int] = set()
        for num in re.findall(r'\[citation_(\d+)\]', answer):
            citation_nums.add(int(num))
        for start, end in re.findall(r'\[citation_(\d+)-citation_(\d+)\]', answer):
            for n in range(int(start), int(end) + 1):
                citation_nums.add(n)

        citations = []
        for num in sorted(citation_nums):
            cid = f"citation_{num}"
            if cid in self._citation_state.citations_map:
                citations.append({"id": cid, **self._citation_state.citations_map[cid]})

        return {"answer": answer, "citations": citations}

    @staticmethod
    def _tool_display_name(name: str) -> str:
        return {
            "query_knowledge_base": "正在检索知识库...",
            "read_segments": "正在读取原文...",
            "list_files": "正在列出文件...",
            "get_file_meta": "正在获取文件信息...",
            "ask_image": "正在分析图片...",
        }.get(name, f"正在执行 {name}...")

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            return len(text) // 2

    async def _should_compact(self, session_id: str, new_question: str) -> bool:
        from database import AsyncSessionLocal
        from models.session import Session as DBSession

        async with AsyncSessionLocal() as db:
            session_obj = await db.get(DBSession, session_id)
            if not session_obj or session_obj.last_total_tokens is None:
                return False

            estimated = session_obj.last_total_tokens + self._estimate_tokens(new_question)
            should = estimated > COMPACT_TOKEN_THRESHOLD
            if should:
                logger.info(
                    f"[compact] 触发: last_total={session_obj.last_total_tokens} "
                    f"+ new_estimate={estimated - session_obj.last_total_tokens} "
                    f"= {estimated} > {COMPACT_TOKEN_THRESHOLD}"
                )
            return should

    async def _execute_compact(
        self,
        session_id: str,
        history: list[Message],
        chat_provider,
    ) -> None:
        from database import AsyncSessionLocal
        from models.message import Message as DBMessage
        from models.session import Session as DBSession
        from sqlalchemy import select

        if len(history) < COMPACT_MIN_STEPS + 2:
            logger.info("[compact] 历史消息太少，跳过")
            return

        boundary_idx = self._find_compact_boundary(history)
        if boundary_idx <= 2:
            logger.info("[compact] 保留区域覆盖了几乎所有消息，跳过")
            return

        messages_to_compact = history[:boundary_idx]
        logger.info(
            f"[compact] 压缩 {len(messages_to_compact)} 条消息，"
            f"保留 {len(history) - boundary_idx} 条"
        )

        compact_text = self._format_messages_for_compact(messages_to_compact)

        compact_system_prompt = (
            "你是一个文档问答系统的对话压缩模块。"
            "你的任务是将较长的对话历史压缩为结构化摘要，以便系统在后续对话中"
            "基于摘要继续回答用户问题，而不丢失关键上下文。\n\n"
            "你不是对话的参与者，因此，请以客观、简洁的第三人称视角进行总结。"
        )

        compact_prompt = (
            "请将以下对话历史压缩为结构化摘要，控制在 1000 字以内。\n\n"
            "## 输出要求\n"
            "1. **已完成的任务与关键发现**：总结用户提问和助手的核心回答。"
            "如果回答中引用了文档内容，保留对应的 [citation_X] 标记，格式不可修改\n"
            "2. **进行中的任务**：用户尚未得到完整回答的问题\n"
            "3. **用户偏好与关键上下文**：用户强调的要点、涉及的文件名/主题等\n\n"
            "## 注意事项\n"
            "- 只保留对后续对话有价值的信息，省略寒暄、重复和已纠正的错误\n"
            "- 不要杜撰 citation 标记，只保留对话中实际出现的\n"
            f"## 对话历史\n{compact_text}"
        )

        from kosong._generate import generate
        summary_result = await generate(
            chat_provider=chat_provider,
            system_prompt=compact_system_prompt,
            tools=None,
            history=[Message(role="user", content=compact_prompt)],
        )
        summary_text = ""
        for part in summary_result.message.content:
            if isinstance(part, TextPart):
                summary_text += part.text
            elif isinstance(part, str):
                summary_text += part

        if not summary_text.strip():
            raise ValueError("LLM 返回了空摘要")

        logger.info(f"[compact] 摘要生成完成，长度={len(summary_text)}")

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(DBMessage)
                .where(DBMessage.session_id == session_id)
                .where(DBMessage.deleted_at.is_(None))
                .order_by(DBMessage.created_at.asc())
            )
            db_messages = result.scalars().all()

            kept_count = len(history) - boundary_idx
            db_boundary_idx = len(db_messages) - kept_count

            session_obj = await db.get(DBSession, session_id)

            if db_boundary_idx <= 0 or db_boundary_idx > len(db_messages):
                raise ValueError(
                    f"compact boundary 计算异常: db_boundary_idx={db_boundary_idx}, "
                    f"db_messages={len(db_messages)}, kept={kept_count}"
                )

            boundary_message_id = db_messages[db_boundary_idx - 1].id

            trigger_result = await db.execute(
                select(DBMessage)
                .where(DBMessage.session_id == session_id)
                .where(DBMessage.deleted_at.is_(None))
                .where(DBMessage.role == "user")
                .order_by(DBMessage.created_at.desc())
                .limit(1)
            )
            trigger_msg = trigger_result.scalar_one_or_none()

            session_obj.compact_summary = summary_text
            session_obj.compact_citations_json = json.dumps(
                self._citation_state.citations_map, ensure_ascii=False
            )
            session_obj.compact_message_id = boundary_message_id
            session_obj.compact_trigger_message_id = trigger_msg.id if trigger_msg else None
            await db.commit()

        logger.info(
            f"[compact] 已保存: boundary_msg={boundary_message_id}, "
            f"trigger_msg={trigger_msg.id if trigger_msg else None}"
        )

    @staticmethod
    def _find_compact_boundary(history: list[Message]) -> int:
        total = len(history)

        round_count = 0
        round_boundary = total
        for i in range(total - 1, -1, -1):
            msg = history[i]
            role = msg.role if isinstance(msg.role, str) else str(msg.role)
            if role == "user":
                round_count += 1
                if round_count >= COMPACT_MIN_ROUNDS:
                    round_boundary = i
                    break

        step_boundary = max(0, total - COMPACT_MIN_STEPS)
        while step_boundary > 0:
            msg = history[step_boundary]
            role = msg.role if isinstance(msg.role, str) else str(msg.role)
            if role == "user":
                break
            step_boundary -= 1

        boundary = min(round_boundary, step_boundary)
        return boundary

    @staticmethod
    def _format_messages_for_compact(messages: list[Message]) -> str:
        lines = []
        for msg in messages:
            role = msg.role if isinstance(msg.role, str) else str(msg.role)
            content = ""
            if isinstance(msg.content, str):
                content = msg.content
            elif isinstance(msg.content, list):
                for part in msg.content:
                    if isinstance(part, TextPart):
                        content += part.text
                    elif isinstance(part, ThinkPart):
                        pass
                    elif isinstance(part, str):
                        content += part
            if role == "tool" and len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"[{role}]: {content}")
        return "\n\n".join(lines)
