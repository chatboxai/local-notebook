"""Plan 总模型：根据源材料 + 用户要求，动态规划报告栏目。

输出结构化的 steps 列表，交给后台任务逐栏目用 while-loop agent 生成。
"""

import json
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

from sqlalchemy import select

import config
import kosong
from agent.capabilities import (
    DEFAULT_FEATURE_TYPE,
    SECTION_TOOL_CLASSES,
    TOOL_CLASS_BY_NAME,
    TOOL_WEB_SEARCH,
    describe_capabilities_for_planner,
    get_capability,
)
from agent.tools.query_knowledge_base import CitationState
from kosong.contrib.chat_provider.openai_legacy import OpenAILegacy
from kosong.message import Message
from kosong.tooling.simple import SimpleToolset

logger = logging.getLogger("service.workflow_planner")

# 单次结构化规划调用；规划属复杂任务，用主 LLM。
_PLANNER_MAX_TOKENS = 2048
_TITLE_MAX_TOKENS = 1536
_PLANNER_RAW_LOG_LIMIT = 8000
_PLANNER_MAX_ATTEMPTS = 3
_TITLE_MAX_ATTEMPTS = 3
_PLANNER_MAX_ITERATIONS = 12

_PLAN_BASE_SYSTEM_PROMPT = """You are an expert report planner for Local Notebook.

Your job is to plan report sections from source materials and the user's requirements. Only plan the structure; do not write the report body.

You may use tools to inspect available files, search source material, read original segments, or inspect image evidence before planning. Use tools when the source overview is too thin, ambiguous, or when the user's requirements depend on specific source details.
"""

_PLAN_OUTPUT_REQUIREMENTS = """Planner output requirements:
1. Plan 4 to 9 sections in a logical order. Cover the user's requirements and the core source material without duplication.
2. For each section, provide a short `step_name` and a concrete, actionable `instruction`.
3. Each `instruction` must specify what evidence or information to extract from the source materials.
4. Choose `feature_type` only from the capability types listed above. Currently this should normally be `text_section`.
5. Use the downstream section generation agent contract and tools to make every `instruction` executable by that agent.
6. Determine the final report language and return it in `language` as a short English language name, such as "Chinese" or "English". If the user explicitly requests an output language, use that language; otherwise use the primary language of the user's requirements.
7. Write every `step_name` and every `instruction` in the final report language.
8. Return exactly one JSON object. Do not wrap it in Markdown or a code fence. Do not add a preface, explanation, or trailing text.
9. The first non-whitespace character of your final response must be `{`; the last non-whitespace character must be `}`.

Required JSON shape:
{"language": "Chinese", "steps": [{"feature_type": "text_section", "step_name": "Section name", "instruction": "What this section should cover"}]}
"""

_TITLE_SYSTEM_PROMPT = """You generate concise report titles for Local Notebook workflows.

Given the user's requirements and selected source files, write one clear report title.

Rules:
1. Use the same language as the user's requirements.
2. Output only the title text. Do not include quotes, Markdown, explanations, subtitles, or trailing punctuation unless it is part of the title.
3. Keep it concise: 4 to 18 Chinese characters for Chinese, or 3 to 10 words for English when possible.
4. Prefer source-specific topics, names, books, documents, people, or concepts when they are clear from the file list or summaries.
5. Avoid generic preset labels such as "Quick Read", "Core Deep Dive", "智能报告", or "内容速读" unless the source context is truly unavailable.
"""


def _log_planner_raw_response(raw: str | None, *, level: int = logging.INFO) -> None:
    if raw is None:
        logger.log(level, "[planner] raw model response: <none>")
        return

    if raw == "":
        logger.log(level, "[planner] raw model response: <empty string>")
        return

    preview = raw[:_PLANNER_RAW_LOG_LIMIT]
    truncated_note = "" if len(raw) <= _PLANNER_RAW_LOG_LIMIT else (
        f"\n...[truncated {len(raw) - _PLANNER_RAW_LOG_LIMIT} chars]"
    )
    logger.log(
        level,
        "[planner] raw model response (%s chars):\n%s%s",
        len(raw),
        preview,
        truncated_note,
    )


def _describe_generation_agent_for_planner() -> str:
    """Describe the downstream section writer so the planner can create executable steps."""
    from agent.prompts import FEATURE_AGENT_PROMPT

    lines = [
        "Downstream section generation agent prompt (output-format requirements omitted):",
        '"""',
        FEATURE_AGENT_PROMPT.strip(),
        '"""',
        "",
        "Downstream section generation agent tools (name: description):",
    ]
    for tool_cls in SECTION_TOOL_CLASSES:
        note = " (enabled only when web search is configured)" if tool_cls.name == TOOL_WEB_SEARCH else ""
        lines.append(f"- `{tool_cls.name}`{note}: {tool_cls.description}")
    return "\n".join(lines)


@lru_cache(maxsize=1)
def _planner_system_prompt() -> str:
    return "\n\n".join([
        _PLAN_BASE_SYSTEM_PROMPT.strip(),
        describe_capabilities_for_planner().strip(),
        _describe_generation_agent_for_planner().strip(),
        _PLAN_OUTPUT_REQUIREMENTS.strip(),
    ])


def _tool_output_to_text(result: Any) -> str:
    return_value = getattr(result, "return_value", result)
    output = getattr(return_value, "output", "")
    if isinstance(output, str):
        return output
    return str(output)


def _clean_generated_title(text: str) -> str:
    title = (text or "").strip()
    if not title:
        return ""
    if title.startswith("```"):
        lines = title.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        title = "\n".join(lines).strip()
    title = title.splitlines()[0].strip()
    title = title.strip(" \t\r\n\"'“”‘’`")
    return title[:100]


def _first_source_name_from_overview(source_overview: str) -> str:
    for line in (source_overview or "").splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        name = line[2:].split("(type=", 1)[0].strip()
        for suffix in (".pdf", ".docx", ".doc", ".txt", ".epub", ".jpg", ".jpeg", ".png"):
            if name.lower().endswith(suffix):
                name = name[: -len(suffix)]
                break
        return name.strip()
    return ""


def _derive_title_from_prompt(
    custom_prompt: str,
    fallback_title: str,
    source_overview: str = "",
) -> str:
    """Deterministic fallback for title generation."""
    prompt = (custom_prompt or "").strip()
    source_name = _first_source_name_from_overview(source_overview)

    if source_name:
        if "核心详解" in prompt or "deep dive" in prompt.lower():
            suffix = "核心详解" if _infer_report_language(prompt, "Chinese") == "Chinese" else "Deep Dive"
        elif "内容速读" in prompt or "quick read" in prompt.lower():
            suffix = "内容速读" if _infer_report_language(prompt, "Chinese") == "Chinese" else "Quick Read"
        else:
            suffix = "报告" if _infer_report_language(prompt, "Chinese") == "Chinese" else "Report"
        return f"{source_name[:60]}{suffix}"[:100]

    if not prompt:
        return fallback_title

    if "核心详解" in prompt or "deep dive" in prompt.lower():
        return "核心详解" if _infer_report_language(prompt, "Chinese") == "Chinese" else "Deep Dive"
    if "内容速读" in prompt or "quick read" in prompt.lower():
        return "内容速读" if _infer_report_language(prompt, "Chinese") == "Chinese" else "Quick Read"

    for line in prompt.splitlines():
        title = line.strip(" \t\r\n\"'“”‘’`。.;；")
        if title:
            return title[:60]
    return fallback_title


def _infer_report_language(text: str, fallback: str = "English") -> str:
    if any("\u4e00" <= char <= "\u9fff" for char in text):
        return "Chinese"
    return fallback


def _normalize_report_language(raw_language: Any, user_req: str, fallback_title: str) -> str:
    language = str(raw_language or "").strip()
    normalized = language.lower().strip(" \t\r\n\"'“”‘’`。.;:：")
    language_map = {
        "zh": "Chinese",
        "zh-cn": "Chinese",
        "中文": "Chinese",
        "汉语": "Chinese",
        "chinese": "Chinese",
        "en": "English",
        "en-us": "English",
        "英文": "English",
        "英语": "English",
        "english": "English",
        "ja": "Japanese",
        "日文": "Japanese",
        "日语": "Japanese",
        "japanese": "Japanese",
    }
    if normalized in language_map:
        return language_map[normalized]
    if language and len(language) <= 40:
        return language
    return _infer_report_language(user_req or fallback_title)


def _append_instruction_language_rule(instruction: str, language: str) -> str:
    rule = f"Important: The final answer must be written in {language}."
    text = (instruction or "").strip()
    if rule in text:
        return text
    if not text:
        return rule
    return f"{text}\n\n{rule}"


async def generate_workflow_title(
    custom_prompt: Optional[str],
    project_id: Optional[str] = None,
    file_ids: Optional[List[str]] = None,
    fallback_title: str = "智能报告",
) -> str:
    """根据用户要求和所选来源生成 workflow 标题。"""
    api_key, base_url, model = await config.resolve_llm_config()
    if not api_key or not base_url or not model:
        raise RuntimeError("LLM 未配置，无法生成报告标题")

    user_req = (custom_prompt or "").strip()
    if not user_req:
        return fallback_title

    project_name = ""
    source_overview = ""
    if project_id:
        try:
            project_name, source_overview = await _gather_source_overview(
                project_id,
                file_ids or [],
                summary_chars=180,
                max_files=20,
            )
        except Exception as exc:
            logger.warning("[planner] failed to gather title source overview: %s", exc)

    chat_provider = OpenAILegacy(
        model=model,
        api_key=api_key,
        base_url=base_url,
        reasoning_key="reasoning_content",
    ).with_generation_kwargs(max_tokens=_TITLE_MAX_TOKENS, temperature=0.2)

    retry_note = ""
    for attempt in range(1, _TITLE_MAX_ATTEMPTS + 1):
        result = await kosong.step(
            chat_provider=chat_provider,
            system_prompt=_TITLE_SYSTEM_PROMPT,
            toolset=SimpleToolset([]),
            history=[Message(
                role="user",
                content=(
                    f"Project name:\n{project_name or '(unknown)'}\n\n"
                    f"User requirements:\n{user_req}\n\n"
                    f"Selected source files:\n{source_overview or '(No source overview available.)'}\n\n"
                    f"{retry_note}"
                    "Return only one concise, source-specific title in the same language as the user requirements."
                ),
            )],
        )
        title = _clean_generated_title(result.message.extract_text())
        if title:
            logger.info("[planner] generated workflow title attempt=%d title=%r", attempt, title)
            return title
        logger.warning("[planner] title generation returned empty response attempt=%d/%d", attempt, _TITLE_MAX_ATTEMPTS)
        retry_note = "The previous attempt returned empty content. You must output a non-empty title.\n\n"

    title = _derive_title_from_prompt(user_req, fallback_title, source_overview)
    logger.warning("[planner] title generation fell back to prompt-derived title: %r", title)
    return title


async def _build_planner_tools(citation_state: CitationState):
    tools = []
    ws_enabled, _, _ = await config.resolve_web_search_config()
    for tool_cls in SECTION_TOOL_CLASSES:
        if tool_cls.name == TOOL_WEB_SEARCH and not ws_enabled:
            continue
        tool_impl = TOOL_CLASS_BY_NAME.get(tool_cls.name)
        if tool_impl is None:
            continue
        if tool_cls.name == TOOL_WEB_SEARCH:
            from agent.tools.web_search import WebSearchTool
            _, ws_key, ws_base_url = await config.resolve_web_search_config()
            tools.append(WebSearchTool(
                citation_state=citation_state,
                api_key=ws_key or "",
                base_url=ws_base_url or "",
            ))
        else:
            tools.append(tool_impl(citation_state=citation_state))
    return tools


async def _llm_plan(
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
    *,
    project_id: str,
    file_ids: List[str],
) -> str:
    chat_provider = OpenAILegacy(
        model=model,
        api_key=api_key,
        base_url=base_url,
        reasoning_key="reasoning_content",
    ).with_generation_kwargs(max_tokens=_PLANNER_MAX_TOKENS, temperature=0.1)

    citation_state = CitationState()
    citation_state.project_id = project_id
    citation_state.file_ids = file_ids or None
    toolset = SimpleToolset(await _build_planner_tools(citation_state))
    history: List[Message] = [Message(role="user", content=prompt)]

    for iteration in range(_PLANNER_MAX_ITERATIONS):
        is_final = iteration == _PLANNER_MAX_ITERATIONS - 1
        if is_final:
            history.append(Message(
                role="user",
                content=(
                    "[System notice] The planner tool-call limit has been reached. "
                    "Return the final plan JSON now using the information already available. "
                    "Tools are disabled now; do not call more tools."
                ),
            ))

        result = await kosong.step(
            chat_provider=chat_provider,
            system_prompt=_planner_system_prompt(),
            toolset=SimpleToolset([]) if is_final else toolset,
            history=history,
        )
        if result.tool_calls and not is_final:
            history.append(result.message)
            tool_results = await result.tool_results()
            for tool_call, tool_result in zip(result.tool_calls, tool_results):
                history.append(Message(
                    role="tool",
                    content=_tool_output_to_text(tool_result),
                    tool_call_id=tool_call.id,
                ))
            continue
        if result.tool_calls:
            raise RuntimeError("Planner kept calling tools instead of returning final JSON")
        text = result.message.extract_text().strip()
        if not text:
            raise RuntimeError("Planner returned an empty response")
        return text

    return ""


async def _gather_source_overview(
    project_id: str,
    file_ids: List[str],
    *,
    summary_chars: int = 300,
    max_files: Optional[int] = None,
) -> tuple[str, str]:
    """返回 (project_name, source overview text)。"""
    from database import AsyncSessionLocal
    from models.file import File
    from models.project import Project

    async with AsyncSessionLocal() as db:
        project = await db.get(Project, project_id)
        project_name = project.name if project else "未命名项目"

        query = (
            select(File)
            .where(File.project_id == project_id, File.status == "ready")
            .order_by(File.created_at.asc())
        )
        if file_ids:
            query = query.where(File.id.in_(file_ids))
        result = await db.execute(query)
        files = list(result.scalars().all())

    if project and project.summary:
        lines = [f"Project summary: {project.summary}", ""]
    else:
        lines = []

    lines.append("Source files and summaries:")
    visible_files = files[:max_files] if max_files is not None else files
    for f in visible_files:
        kw = ""
        if f.keywords:
            try:
                parsed = json.loads(f.keywords)
                if isinstance(parsed, list):
                    kw = "; keywords: " + ", ".join(str(k) for k in parsed)
            except json.JSONDecodeError:
                pass
        file_type = f.file_type or "unknown"
        summary = (f.summary or "")[:summary_chars]
        lines.append(f"- {f.file_name} (type={file_type}): {summary}{kw}")
    if max_files is not None and len(files) > max_files:
        lines.append(f"- ...and {len(files) - max_files} more selected source file(s).")

    return project_name, "\n".join(lines)


def _normalize_steps(raw_steps: Any, language: str) -> List[Dict[str, str]]:
    steps: List[Dict[str, str]] = []
    if not isinstance(raw_steps, list):
        return steps
    for item in raw_steps:
        if not isinstance(item, dict):
            continue
        step_name = str(item.get("step_name") or item.get("name") or "").strip()
        if not step_name:
            continue
        feature_type = str(item.get("feature_type") or DEFAULT_FEATURE_TYPE).strip()
        # 仅接受已注册的能力，否则回退默认
        feature_type = get_capability(feature_type).type
        instruction = _append_instruction_language_rule(
            str(item.get("instruction") or item.get("desc") or "").strip(),
            language,
        )
        steps.append(
            {
                "feature_type": feature_type,
                "step_name": step_name[:100],
                "instruction": instruction,
            }
        )
    return steps


def _parse_plan(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # 容错：扫描所有可能的 JSON object。这样前后有废话、甚至废话里带 `{...}`
    # 时，也会优先拿到包含 steps 的 plan object。
    decoder = json.JSONDecoder()
    first_object: Dict[str, Any] | None = None
    for idx, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue
        first_object = first_object or parsed
        if "steps" in parsed:
            return parsed
    if first_object is not None:
        return first_object
    raise ValueError("规划结果中未找到 JSON object")


async def plan_workflow(
    project_id: str,
    custom_prompt: Optional[str],
    file_ids: List[str],
    fallback_title: str = "智能报告",
) -> Dict[str, Any]:
    """规划报告。返回 {"language": str, "steps": [...]}。"""
    api_key, base_url, model = await config.resolve_llm_config()
    if not api_key or not base_url or not model:
        raise RuntimeError("LLM 未配置，无法规划报告")

    project_name, overview = await _gather_source_overview(project_id, file_ids)

    user_req = (custom_prompt or "").strip() or (
        "(The user did not provide extra requirements. Decide based on the source materials.)"
    )

    prompt = f"""Project name: {project_name}

User requirements: {user_req}

Existing report title for context: {fallback_title}

Source material overview:
{overview}

Plan the report sections. Use tools first if the source overview is insufficient for planning specific, executable sections. Do not return or regenerate a report title; include only the final report language in the JSON `language` field and the planned `steps`."""

    last_error: Exception | None = None
    retry_prompt = prompt
    for attempt in range(1, _PLANNER_MAX_ATTEMPTS + 1):
        raw: str | None = None
        try:
            logger.info(
                "[planner] attempt %d/%d project=%s",
                attempt,
                _PLANNER_MAX_ATTEMPTS,
                project_id,
            )
            raw = await _llm_plan(
                retry_prompt,
                api_key,
                base_url,
                model,
                project_id=project_id,
                file_ids=file_ids,
            )
            _log_planner_raw_response(raw)
            parsed = _parse_plan(raw)
            language = _normalize_report_language(parsed.get("language"), user_req, fallback_title)
            steps = _normalize_steps(parsed.get("steps"), language)
            if not steps:
                raise ValueError("规划结果为空")
            plan = {"language": language, "steps": steps}
            logger.info(
                "[planner] project=%s 规划出 %d 个栏目: language=%r",
                project_id,
                len(steps),
                language,
            )
            logger.info(
                "[planner] plan project=%s:\n%s",
                project_id,
                json.dumps(plan, ensure_ascii=False, indent=2),
            )
            return plan
        except Exception as e:
            last_error = e
            logger.warning(
                "[planner] attempt %d/%d failed project=%s: %s",
                attempt,
                _PLANNER_MAX_ATTEMPTS,
                project_id,
                e,
            )
            _log_planner_raw_response(raw, level=logging.WARNING)
            retry_prompt = (
                f"{prompt}\n\n"
                f"The previous attempt failed to produce a valid plan JSON because: {e}\n"
                "Retry now. Return exactly one valid JSON object matching the required shape. "
                "Do not include any text before or after the JSON object."
            )

    raise RuntimeError(f"规划失败，已尝试 {_PLANNER_MAX_ATTEMPTS} 次: {last_error}") from last_error
