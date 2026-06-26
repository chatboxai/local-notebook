"""Feature while-loop agent：为报告的单个栏目生成内容。

形态复刻 chat_agent 的 kosong.step 循环，但运行在后台任务里、不向客户端流式：
拿到栏目要求 → 用工具取证 → 产出带 [citation_X] 的 markdown → 转成 blocks。

整份 workflow 共享一个 CitationState（引用编号全局连续）。
"""

import logging
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

logger = logging.getLogger("feature_agent")

MAX_ITERATIONS = 12
MAX_OUTPUT_TOKENS = 8192


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

        final_text = ""

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
                step_result = await kosong.step(
                    chat_provider=chat_provider,
                    system_prompt=self.system_prompt,
                    toolset=toolset,
                    history=history,
                )
            except ChatProviderError as e:
                raise RuntimeError(f"LLM 调用失败: {e}") from e

            if cancellation_check:
                await cancellation_check()

            if step_result.tool_calls and not is_final:
                history.append(step_result.message)
                tool_results = await step_result.tool_results()
                if cancellation_check:
                    await cancellation_check()
                for tc, tr in zip(step_result.tool_calls, tool_results):
                    output = tr.output if hasattr(tr, "output") else str(tr)
                    if isinstance(output, str):
                        output_str = output
                    elif hasattr(output, "text"):
                        output_str = output.text
                    else:
                        output_str = str(output)
                    history.append(Message(
                        role="tool",
                        content=output_str,
                        tool_call_id=tc.id,
                    ))
                continue

            final_text = _extract_text(step_result.message)
            break

        final_text = (final_text or "").strip()
        if not final_text:
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

        logger.info(
            f"[feature_agent] step={step_name!r} blocks={len(blocks)} "
            f"citations={len(citations_snapshot)} next_display_num={next_display_num}"
        )
        return blocks, citations_snapshot, next_display_num
