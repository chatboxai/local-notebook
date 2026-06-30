"""Feature while-loop agent：为报告的单个栏目生成内容。

形态复刻 chat_agent 的 kosong.step 循环，但运行在后台任务里、不向客户端流式：
拿到栏目要求 → 用工具取证 → 产出带 [citation_X] 的 markdown → 转成 blocks。

整份 workflow 共享一个 CitationState（引用编号全局连续）。
"""

import asyncio
import logging
import os
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import config
from agent.blocks_builder import markdown_to_blocks
from agent.capabilities import (
    TOOL_WEB_SEARCH,
    TOOL_CLASS_BY_NAME,
    get_capability,
)
from agent.prompts import FEATURE_AGENT_SYSTEM_PROMPT, build_feature_task_prompt
from agent.tools.query_knowledge_base import CitationState

import kosong
from kosong.chat_provider import ChatProviderError
from kosong.message import Message, TextPart
from kosong.tooling.simple import SimpleToolset
from services.llm_provider import create_llm_chat_provider
from services.feature_agent_trace_service import upsert_feature_agent_trace
from services.usage_service import record_model_usage

logger = logging.getLogger("feature_agent")

MAX_ITERATIONS = 12
MAX_OUTPUT_TOKENS = 8192
FEATURE_AGENT_LLM_STEP_TIMEOUT = int(os.getenv("FEATURE_AGENT_LLM_STEP_TIMEOUT", "600"))


def _extract_text(message: Message) -> str:
    text = ""
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for part in content:
            if isinstance(part, TextPart):
                text += part.text
            elif isinstance(part, str):
                text += part
    return text


def _message_to_trace(message: Message) -> Dict[str, Any]:
    return message.model_dump(mode="json", exclude_none=True)


def _usage_to_trace(usage: Any) -> Dict[str, Any] | None:
    if usage is None:
        return None
    if hasattr(usage, "model_dump"):
        return usage.model_dump(mode="json", exclude_none=True)
    return {
        "input_other": getattr(usage, "input_other", 0),
        "input_cache_read": getattr(usage, "input_cache_read", 0),
        "input_cache_creation": getattr(usage, "input_cache_creation", 0),
        "output": getattr(usage, "output", 0),
        "total": getattr(usage, "total", 0),
    }


def _citation_state_to_trace(state: CitationState) -> Dict[str, Any]:
    return {
        "citation_counter": state.citation_counter,
        "citations_map": state.citations_map,
        "segment_to_citation": state.segment_to_citation,
        "image_to_citation": state.image_to_citation,
        "workflow_citation_to_local": state.workflow_citation_to_local,
    }


def _tool_result_to_text(result: Any) -> str:
    return_value = getattr(result, "return_value", None)
    output = getattr(return_value, "output", None)

    if isinstance(output, str) and output:
        return output
    if isinstance(output, list):
        chunks = []
        for item in output:
            text = getattr(item, "text", None)
            chunks.append(text if isinstance(text, str) else str(item))
        return "".join(chunks)
    if output is not None and not isinstance(output, str):
        return str(output)

    message = getattr(return_value, "message", None)
    if isinstance(message, str) and message:
        return message
    return str(result)


def _exception_message(exc: BaseException) -> str:
    message = str(exc).strip()
    if message:
        return message
    return exc.__class__.__name__


async def _build_tools(
    tool_names: List[str],
    citation_state: CitationState,
    enable_web_search: bool,
):
    tools = []
    for name in tool_names:
        tool_cls = TOOL_CLASS_BY_NAME.get(name)
        if tool_cls is None:
            logger.warning(f"Unknown report tool skipped: {name}")
            continue
        if name == TOOL_WEB_SEARCH:
            if not enable_web_search:
                continue
            from agent.tools.web_search import WebSearchTool
            _, ws_key, ws_base_url = await config.resolve_web_search_config()
            tools.append(WebSearchTool(
                citation_state=citation_state,
                api_key=ws_key or "",
                base_url=ws_base_url or "",
            ))
        else:
            tools.append(tool_cls(citation_state=citation_state))
    return tools


class FeatureAgent:
    """生成一个栏目。"""

    def __init__(self):
        self.system_prompt = FEATURE_AGENT_SYSTEM_PROMPT

    async def generate(
        self,
        *,
        report_title: str,
        step_name: str,
        instruction: str,
        feature_type: str,
        custom_prompt: str,
        citation_state: CitationState,
        start_display_num: int,
        user_id: str | None = None,
        trace_phase: str = "draft",
        cancellation_check: Optional[Callable[[], Awaitable[None]]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], int]:
        """返回 (blocks, citations_snapshot, next_display_num)。

        失败时抛异常，由调用方标记该栏目 failed。
        """
        api_key, base_url, model, api_format = await config.resolve_llm_provider_config()
        if not api_key or not model:
            raise RuntimeError("LLM 未配置")

        chat_provider = create_llm_chat_provider(
            model=model,
            api_key=api_key,
            base_url=base_url,
            api_format=api_format,
            max_tokens=MAX_OUTPUT_TOKENS,
        )

        capability = get_capability(feature_type)
        # 联网工具仅在已配置时启用
        ws_enabled, _, _ = await config.resolve_web_search_config()
        tools = await _build_tools(capability.tools, citation_state, ws_enabled)
        toolset = SimpleToolset(tools)

        history: List[Message] = [
            Message(
                role="user",
                content=build_feature_task_prompt(
                    report_title,
                    step_name,
                    instruction,
                    custom_prompt,
                    citation_state.depends_on,
                ),
            )
        ]
        trace_iterations: List[Dict[str, Any]] = []

        async def save_trace(status: str, final_message: Message | None = None, error: str = "") -> None:
            workflow_id = citation_state.workflow_id
            feature_id = citation_state.current_feature_id
            if not workflow_id or not feature_id:
                return
            trace_history = [_message_to_trace(message) for message in history]
            if final_message is not None:
                trace_history.append(_message_to_trace(final_message))
            payload = {
                "phase": trace_phase,
                "status": status,
                "workflow_id": workflow_id,
                "feature_id": feature_id,
                "step_id": citation_state.current_step_id,
                "context": {
                    "report_title": report_title,
                    "step_name": step_name,
                    "instruction": instruction,
                    "feature_type": feature_type,
                    "custom_prompt": custom_prompt,
                    "depends_on": citation_state.depends_on,
                },
                "system_prompt": self.system_prompt,
                "history": trace_history,
                "iterations": trace_iterations,
                "citation_state": _citation_state_to_trace(citation_state),
            }
            if error:
                payload["error"] = error
            try:
                await upsert_feature_agent_trace(
                    workflow_id=workflow_id,
                    feature_id=feature_id,
                    phase=trace_phase,
                    status=status,
                    payload=payload,
                )
            except Exception as exc:
                logger.warning(
                    "[feature_agent] failed to save trace feature_id=%s phase=%s status=%s: %s",
                    feature_id,
                    trace_phase,
                    status,
                    exc,
                )

        await save_trace("running")

        final_text = ""
        final_message: Message | None = None

        for iteration in range(MAX_ITERATIONS):
            if cancellation_check:
                await cancellation_check()

            is_final = iteration == MAX_ITERATIONS - 1
            if is_final:
                history.append(Message(
                    role="user",
                    content=(
                        "[System notice] The tool-call limit has been reached. "
                        "Finish the current section immediately using the information already available, "
                        "and do not call any more tools. Output only the publishable section body; "
                        "do not include process notes, prefaces, separators, or afterwords."
                    ),
                ))

            try:
                step_coro = kosong.step(
                    chat_provider=chat_provider,
                    system_prompt=self.system_prompt,
                    toolset=toolset,
                    history=history,
                )
                if FEATURE_AGENT_LLM_STEP_TIMEOUT > 0:
                    step_result = await asyncio.wait_for(
                        step_coro,
                        timeout=FEATURE_AGENT_LLM_STEP_TIMEOUT,
                    )
                else:
                    step_result = await step_coro
            except asyncio.TimeoutError as e:
                message = f"LLM 单轮调用超时（{FEATURE_AGENT_LLM_STEP_TIMEOUT} 秒）"
                await save_trace("failed", error=message)
                raise RuntimeError(message) from e
            except asyncio.CancelledError:
                await asyncio.shield(save_trace("failed", error="栏目生成被取消或超时"))
                raise
            except ChatProviderError as e:
                message = _exception_message(e)
                await save_trace("failed", error=message)
                raise RuntimeError(f"LLM 调用失败: {message}") from e
            except Exception as e:
                message = _exception_message(e)
                await save_trace("failed", error=message)
                raise

            if cancellation_check:
                await cancellation_check()
            await record_model_usage(user_id=user_id, model=model, usage=step_result.usage)
            iteration_trace: Dict[str, Any] = {
                "iteration": iteration,
                "message_id": step_result.id,
                "assistant_message": _message_to_trace(step_result.message),
                "usage": _usage_to_trace(step_result.usage),
                "tool_results": [],
            }

            if step_result.tool_calls and not is_final:
                history.append(step_result.message)
                tool_results = await step_result.tool_results()
                if cancellation_check:
                    await cancellation_check()
                for tc, tr in zip(step_result.tool_calls, tool_results):
                    iteration_trace["tool_results"].append(
                        tr.model_dump(mode="json", exclude_none=True)
                    )
                    output_str = _tool_result_to_text(tr)
                    history.append(Message(
                        role="tool",
                        content=output_str,
                        tool_call_id=tc.id,
                    ))
                trace_iterations.append(iteration_trace)
                await save_trace("running")
                continue

            trace_iterations.append(iteration_trace)
            final_message = step_result.message
            final_text = _extract_text(final_message)
            await save_trace("completed", final_message=final_message)
            break

        final_text = (final_text or "").strip()
        if not final_text:
            await save_trace("failed", error="栏目生成结果为空")
            raise RuntimeError("栏目生成结果为空")

        blocks, next_display_num = markdown_to_blocks(
            final_text,
            citation_state.citations_map,
            start_display_num,
        )

        # 本栏目引用快照：取已分配 display_num 的引用，供前端按 citation_id 查找
        citations_snapshot: Dict[str, Any] = {
            cid: meta
            for cid, meta in citation_state.citations_map.items()
            if meta.get("display_num") is not None
        }
        await save_trace("completed", final_message=final_message)

        logger.info(
            f"[feature_agent] step={step_name!r} blocks={len(blocks)} "
            f"citations={len(citations_snapshot)} next_display_num={next_display_num}"
        )
        return blocks, citations_snapshot, next_display_num
