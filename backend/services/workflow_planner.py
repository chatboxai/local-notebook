"""Plan 总模型：根据源材料 + 用户要求，动态规划报告栏目。

输出结构化的 steps 列表，交给后台任务逐栏目用 while-loop agent 生成。
"""

import json
import logging
import re
from functools import lru_cache
from typing import Any, Awaitable, Callable, Dict, List, Optional

from sqlalchemy import select

import config
import kosong
from agent.capabilities import (
    SECTION_TOOL_CLASSES,
    SOURCE_TOOL_CLASSES,
    TOOL_CLASS_BY_NAME,
    TOOL_WEB_SEARCH,
)
from agent.tools.query_knowledge_base import CitationState
from kosong.message import Message
from kosong.tooling.simple import SimpleToolset
from services.llm_provider import create_llm_chat_provider
from services.usage_service import record_model_usage

logger = logging.getLogger("service.workflow_planner")

# 单次结构化规划调用；规划可能包含多步 JSON，reasoning 模型需要更大输出预算。
_PLANNER_MAX_TOKENS = 8192
_TITLE_MAX_TOKENS = 1536
_PLANNER_RAW_LOG_LIMIT = 8000
_PLANNER_MAX_ATTEMPTS = 3
_TITLE_MAX_ATTEMPTS = 3
_PLANNER_MAX_ITERATIONS = 12
STEP_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
CITATION_MARKER_RE = re.compile(
    r"\s*\[citation_(?:\d+|[a-z][a-z0-9_]*_\d+)"
    r"(?:-citation_(?:\d+|[a-z][a-z0-9_]*_\d+))?\]"
)

_PLAN_BASE_SYSTEM_PROMPT = """You are an expert report planner for Local Notebook.

Your job is to plan report sections from source materials and the user's requirements. Only plan the structure; do not write the report body.

You may use tools to inspect available files, search source material, read original segments, or inspect image evidence before planning. Use tools when the source overview is too thin, ambiguous, or when the user's requirements depend on specific source details.
"""

_PLANNER_JSON_ONLY_RULE = """Return exactly one JSON object. Do not wrap it in Markdown or a code fence. Do not add a preface, explanation, or trailing text.
The first non-whitespace character of your final response must be `{`; the last non-whitespace character must be `}`.
Inside JSON string values, do not use raw ASCII double quotes; use Chinese quotation marks or escape them as `\"`."""

_STRUCTURE_OUTPUT_REQUIREMENTS = """Planner structure output requirements:
1. Plan 4 to 9 sections in the final report display order. Cover the user's requirements and the core source material without duplication.
2. For each section, provide `step_id`, `step_name`, and `instruction`.
3. `step_id` must be stable English snake_case matching `^[a-z][a-z0-9_]{0,63}$`. Do not use spaces, hyphens, Chinese characters, punctuation, or duplicate step_ids.
4. Each `instruction` must be concise: 1 to 3 sentences describing what the downstream section agent should investigate and write.
5. Do not write the report body, source excerpts, detailed evidence chains, or citation markers such as `[citation_0]`.
6. Do not output `feature_type`.
7. Write every `step_name` and every `instruction` in the required final report language.
8. Use the downstream section generation agent contract and tools to make every `instruction` executable by that agent.

Required JSON shape:
{"steps": [{"step_id": "story_overview", "step_name": "Section name", "instruction": "What this section should cover"}]}
"""

_DEPENDENCY_OUTPUT_REQUIREMENTS = """Planner dependency output requirements:
1. Use only the already validated `step_id` values.
2. `depends_on` means generation prerequisites: steps that must finish before the current step can be generated.
3. Dependencies may reference any other step in the report, regardless of display order or execution layer.
4. The dependency graph must be a DAG: no self-dependencies and no cycles.
5. Independent steps must use an empty `depends_on` array.
6. Do not add, remove, rename, or reorder steps.

Required JSON shape:
{"dependencies": [{"step_id": "theme_analysis", "depends_on": ["story_overview"]}]}
"""

_TITLE_SYSTEM_PROMPT = """You generate concise report titles for Local Notebook workflows.

Given the user's requirements and selected source files, write one clear report title.

Rules:
1. Write the title in the required title language.
2. Output only the title text. Do not include quotes, Markdown, explanations, subtitles, or trailing punctuation unless it is part of the title.
3. Keep it concise and natural for the required language.
4. Prefer source-specific topics, names, books, documents, people, or concepts when they are clear from the file list or summaries.
5. Avoid generic preset labels unless the source context is truly unavailable.
"""

CancellationCheck = Callable[[], Awaitable[None]]


def _is_cancellation_exception(exc: Exception) -> bool:
    return exc.__class__.__name__ == "WorkflowCancelled"


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
        _describe_generation_agent_for_planner().strip(),
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


def _append_instruction_language_rule(instruction: str, language: str) -> str:
    rule = f"Important: The final answer must be written in {language}."
    text = (instruction or "").strip()
    if rule in text:
        return text
    if not text:
        return rule
    return f"{text}\n\n{rule}"


def _strip_citation_markers(text: str) -> str:
    """Planner citations belong to planning context and must not leak into feature prompts."""
    cleaned = CITATION_MARKER_RE.sub("", text or "")
    return re.sub(r"[ \t]{2,}", " ", cleaned).strip()


def _strip_json_markdown_fence(text: str) -> str:
    text = (text or "").strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _next_nonspace_index(text: str, start: int) -> int:
    idx = start
    while idx < len(text) and text[idx].isspace():
        idx += 1
    return idx


def _quoted_token_is_object_key(text: str, quote_index: int) -> bool:
    escaped = False
    idx = quote_index + 1
    while idx < len(text):
        char = text[idx]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            return _next_nonspace_index(text, idx + 1) < len(text) and text[_next_nonspace_index(text, idx + 1)] == ":"
        idx += 1
    return False


def _json_quote_closes_string(text: str, quote_index: int) -> bool:
    idx = _next_nonspace_index(text, quote_index + 1)
    if idx >= len(text) or text[idx] in {"}", "]", ":"}:
        return True
    if text[idx] != ",":
        return False

    next_idx = _next_nonspace_index(text, idx + 1)
    if next_idx >= len(text) or text[next_idx] in {"}", "]"}:
        return True
    if text[next_idx] == '"':
        return _quoted_token_is_object_key(text, next_idx)
    return text[next_idx] in "{["


def _repair_unescaped_json_string_quotes(text: str) -> str:
    """Escape common model-produced quotes inside JSON string values.

    LLMs often return fenced JSON with natural-language values such as
    `"instruction": "说明"黑盒"方案"`. Strict JSON rejects those inner quotes,
    even though the surrounding object is otherwise usable.
    """
    out: list[str] = []
    in_string = False
    escaped = False

    for idx, char in enumerate(text):
        if escaped:
            out.append(char)
            escaped = False
            continue

        if in_string and char == "\\":
            out.append(char)
            escaped = True
            continue

        if char != '"':
            out.append(char)
            continue

        if not in_string:
            in_string = True
            out.append(char)
            continue

        if _json_quote_closes_string(text, idx):
            in_string = False
            out.append(char)
        else:
            out.append('\\"')

    return "".join(out)


async def generate_workflow_title(
    custom_prompt: Optional[str],
    project_id: Optional[str] = None,
    file_ids: Optional[List[str]] = None,
    output_language: str = "",
    user_id: str | None = None,
    cancellation_check: Optional[CancellationCheck] = None,
) -> str:
    """根据用户要求和所选来源生成 workflow 标题。"""
    api_key, base_url, model, api_format = await config.resolve_llm_provider_config()
    if not api_key or not model:
        raise RuntimeError("LLM 未配置，无法生成报告标题")

    user_req = (custom_prompt or "").strip()
    if not user_req:
        raise ValueError("缺少工作流要求，无法生成报告标题")
    title_language = (output_language or "").strip()
    if not title_language:
        raise ValueError("缺少输出语言，无法生成报告标题")

    project_name = ""
    source_overview = ""
    if cancellation_check:
        await cancellation_check()
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

    chat_provider = create_llm_chat_provider(
        model=model,
        api_key=api_key,
        base_url=base_url,
        api_format=api_format,
        max_tokens=_TITLE_MAX_TOKENS,
        temperature=0.2,
    )

    retry_note = ""
    for attempt in range(1, _TITLE_MAX_ATTEMPTS + 1):
        if cancellation_check:
            await cancellation_check()
        result = await kosong.step(
            chat_provider=chat_provider,
            system_prompt=_TITLE_SYSTEM_PROMPT,
            toolset=SimpleToolset([]),
            history=[Message(
                role="user",
                content=(
                    f"Project name:\n{project_name or '(unknown)'}\n\n"
                    f"User requirements:\n{user_req}\n\n"
                    f"Required title language:\n{title_language}\n\n"
                    f"Selected source files:\n{source_overview or '(No source overview available.)'}\n\n"
                    f"{retry_note}"
                    f"Return only one concise, source-specific title in {title_language}."
                ),
            )],
        )
        if cancellation_check:
            await cancellation_check()
        await record_model_usage(user_id=user_id, model=model, usage=result.usage)
        title = _clean_generated_title(result.message.extract_text())
        if title:
            logger.info("[planner] generated workflow title attempt=%d title=%r", attempt, title)
            return title
        logger.warning("[planner] title generation returned empty response attempt=%d/%d", attempt, _TITLE_MAX_ATTEMPTS)
        retry_note = "The previous attempt returned empty content. You must output a non-empty title.\n\n"

    raise RuntimeError(f"报告标题生成失败，已尝试 {_TITLE_MAX_ATTEMPTS} 次: 模型返回空标题")


async def _build_planner_tools(citation_state: CitationState):
    tools = []
    ws_enabled, _, _ = await config.resolve_web_search_config()
    for tool_cls in SOURCE_TOOL_CLASSES:
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


async def _llm_plan_turn(
    history: List[Message],
    api_key: str,
    base_url: str | None,
    model: str,
    api_format: str,
    *,
    project_id: str,
    file_ids: List[str],
    citation_state: CitationState,
    user_id: str | None = None,
    enable_tools: bool = True,
    cancellation_check: Optional[CancellationCheck] = None,
) -> str:
    chat_provider = create_llm_chat_provider(
        model=model,
        api_key=api_key,
        base_url=base_url,
        api_format=api_format,
        max_tokens=_PLANNER_MAX_TOKENS,
        temperature=0.1,
    )

    toolset = SimpleToolset(await _build_planner_tools(citation_state)) if enable_tools else SimpleToolset([])

    for iteration in range(_PLANNER_MAX_ITERATIONS):
        if cancellation_check:
            await cancellation_check()

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
            toolset=SimpleToolset([]) if is_final or not enable_tools else toolset,
            history=history,
        )
        if cancellation_check:
            await cancellation_check()
        await record_model_usage(user_id=user_id, model=model, usage=result.usage)

        if result.tool_calls and not is_final:
            history.append(result.message)
            tool_results = await result.tool_results()
            if cancellation_check:
                await cancellation_check()
            for tool_call, tool_result in zip(result.tool_calls, tool_results):
                history.append(Message(
                    role="tool",
                    content=_tool_output_to_text(tool_result),
                    tool_call_id=tool_call.id,
                ))
            continue
        if result.tool_calls:
            raise RuntimeError("Planner kept calling tools instead of returning final JSON")
        if cancellation_check:
            await cancellation_check()
        text = result.message.extract_text().strip()
        if not text:
            raise RuntimeError("Planner returned an empty response")
        history.append(result.message)
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


def _normalize_steps(raw_steps: Any, language: str) -> List[Dict[str, Any]]:
    errors: List[str] = []
    steps: List[Dict[str, Any]] = []
    seen_step_ids: set[str] = set()

    if not isinstance(raw_steps, list):
        raise ValueError("`steps` must be an array")
    if not raw_steps:
        raise ValueError("`steps` must not be empty")

    for idx, item in enumerate(raw_steps):
        if not isinstance(item, dict):
            errors.append(f"steps[{idx}] must be an object")
            continue

        step_id = str(item.get("step_id") or "").strip()
        step_name = str(item.get("step_name") or item.get("name") or "").strip()
        instruction = _strip_citation_markers(
            str(item.get("instruction") or item.get("desc") or "")
        )

        if not step_id:
            errors.append(f"steps[{idx}].step_id is required")
        elif not STEP_ID_RE.fullmatch(step_id):
            errors.append(
                f"steps[{idx}].step_id={step_id!r} must match ^[a-z][a-z0-9_]{{0,63}}$"
            )
        elif step_id in seen_step_ids:
            errors.append(f"duplicate step_id: {step_id!r}")
        else:
            seen_step_ids.add(step_id)

        if not step_name:
            errors.append(f"steps[{idx}].step_name is required")
        if not instruction:
            errors.append(f"steps[{idx}].instruction is required")

        if step_id and step_name and instruction:
            steps.append({
                "step_id": step_id,
                "step_name": step_name[:100],
                "instruction": _append_instruction_language_rule(instruction, language),
            })

    if errors:
        raise ValueError("; ".join(errors))
    return steps


def _parse_json_object(raw: str, preferred_keys: tuple[str, ...] = ()) -> Dict[str, Any]:
    text = _strip_json_markdown_fence(raw)
    decoder = json.JSONDecoder()

    def _scan(candidate: str) -> tuple[Dict[str, Any] | None, Dict[str, Any] | None]:
        first_object: Dict[str, Any] | None = None
        preferred_object: Dict[str, Any] | None = None
        for idx, char in enumerate(candidate):
            if char != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(candidate[idx:])
            except json.JSONDecodeError:
                continue
            if not isinstance(parsed, dict):
                continue
            first_object = first_object or parsed
            if preferred_keys and any(key in parsed for key in preferred_keys):
                preferred_object = parsed
                break
            if not preferred_keys:
                preferred_object = parsed
                break
        return first_object, preferred_object

    first_object, preferred_object = _scan(text)
    if preferred_object is not None:
        return preferred_object
    if first_object is not None and not preferred_keys:
        return first_object

    repaired = _repair_unescaped_json_string_quotes(text)
    if repaired != text:
        first_object, preferred_object = _scan(repaired)
        if preferred_object is not None:
            logger.info("[planner] parsed JSON after repairing unescaped quotes")
            return preferred_object
        if first_object is not None and not preferred_keys:
            logger.info("[planner] parsed JSON after repairing unescaped quotes")
            return first_object

    if preferred_keys:
        keys = ", ".join(preferred_keys)
        raise ValueError(f"规划结果中未找到包含 {keys} 的完整 JSON object")
    raise ValueError("规划结果中未找到 JSON object")


def _extract_dependency_items(parsed: Dict[str, Any]) -> Any:
    if "dependencies" in parsed:
        return parsed.get("dependencies")
    if "steps" in parsed:
        steps = parsed.get("steps")
        if isinstance(steps, list):
            return [
                {
                    "step_id": item.get("step_id"),
                    "depends_on": item.get("depends_on", []),
                }
                for item in steps
                if isinstance(item, dict)
            ]
    return None


def _normalize_dependencies(raw_dependencies: Any, steps: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    errors: List[str] = []
    step_ids = [step["step_id"] for step in steps]
    step_id_set = set(step_ids)
    dep_map: Dict[str, List[str]] = {step_id: [] for step_id in step_ids}

    if raw_dependencies is None:
        raise ValueError("`dependencies` is required")
    if not isinstance(raw_dependencies, list):
        raise ValueError("`dependencies` must be an array")

    seen_rows: set[str] = set()
    for idx, item in enumerate(raw_dependencies):
        if not isinstance(item, dict):
            errors.append(f"dependencies[{idx}] must be an object")
            continue
        step_id = str(item.get("step_id") or "").strip()
        depends_on = item.get("depends_on", [])
        if step_id not in step_id_set:
            errors.append(f"dependencies[{idx}].step_id={step_id!r} does not exist in steps")
            continue
        if step_id in seen_rows:
            errors.append(f"duplicate dependencies row for step_id={step_id!r}")
        seen_rows.add(step_id)
        if depends_on is None:
            depends_on = []
        if not isinstance(depends_on, list):
            errors.append(f"dependencies[{idx}].depends_on must be an array")
            continue

        normalized: List[str] = []
        for dep in depends_on:
            dep_id = str(dep or "").strip()
            if dep_id not in step_id_set:
                errors.append(f"step {step_id!r} depends on unknown step_id {dep_id!r}")
                continue
            if dep_id == step_id:
                errors.append(f"step {step_id!r} cannot depend on itself")
                continue
            if dep_id not in normalized:
                normalized.append(dep_id)
        dep_map[step_id] = normalized

    if errors:
        raise ValueError("; ".join(errors))

    layers: Dict[str, int] = {}
    visiting: set[str] = set()

    def layer_of(step_id: str) -> int:
        if step_id in layers:
            return layers[step_id]
        if step_id in visiting:
            raise ValueError(f"dependency cycle detected at step_id {step_id!r}")
        visiting.add(step_id)
        deps = dep_map.get(step_id, [])
        layer = 0 if not deps else max(layer_of(dep_id) for dep_id in deps) + 1
        visiting.remove(step_id)
        layers[step_id] = layer
        return layer

    for step_id in step_ids:
        layer_of(step_id)

    return dep_map


def _merge_dependencies(
    steps: List[Dict[str, Any]],
    dep_map: Dict[str, List[str]],
) -> List[Dict[str, Any]]:
    return [
        {
            **step,
            "depends_on": dep_map.get(step["step_id"], []),
        }
        for step in steps
    ]


def _validate_full_plan(
    parsed: Dict[str, Any],
    required_language: str,
) -> Dict[str, Any]:
    steps = _normalize_steps(parsed.get("steps"), required_language)
    dep_map = _normalize_dependencies(_extract_dependency_items(parsed), steps)
    return {"steps": _merge_dependencies(steps, dep_map)}


def _build_json_correction_message(error: Exception, required_shape: str) -> str:
    return (
        "Your previous JSON failed validation:\n"
        f"- {error}\n\n"
        f"{required_shape}\n\n"
        "Return the corrected JSON only.\n"
        "(Generate the final complete result directly. Do not include any explanation, "
        "preface, Markdown fence, or extra text.)"
    )


async def plan_workflow(
    project_id: str,
    custom_prompt: Optional[str],
    file_ids: List[str],
    report_title: str = "",
    output_language: str = "",
    user_id: str | None = None,
    cancellation_check: Optional[CancellationCheck] = None,
) -> Dict[str, Any]:
    """规划报告。返回 {"steps": [...]}。"""
    api_key, base_url, model, api_format = await config.resolve_llm_provider_config()
    if not api_key or not model:
        raise RuntimeError("LLM 未配置，无法规划报告")

    if cancellation_check:
        await cancellation_check()
    project_name, overview = await _gather_source_overview(project_id, file_ids)
    if cancellation_check:
        await cancellation_check()

    user_req = (custom_prompt or "").strip()
    if not user_req:
        raise ValueError("缺少工作流要求，无法规划报告")
    required_language = (output_language or "").strip()
    if not required_language:
        raise ValueError("缺少输出语言，无法规划报告")
    report_title = (report_title or "").strip()
    if not report_title:
        raise ValueError("缺少报告标题，无法规划报告")

    structure_prompt = f"""Project name: {project_name}

User requirements: {user_req}

Existing report title for context: {report_title}

Required final report language: {required_language}

Source material overview:
{overview}

Plan the report section structure first. Use tools first if the source overview is insufficient for planning specific, executable sections. Do not return or regenerate a report title.

{_STRUCTURE_OUTPUT_REQUIREMENTS.strip()}

{_PLANNER_JSON_ONLY_RULE.strip()}"""

    citation_state = CitationState()
    citation_state.project_id = project_id
    citation_state.file_ids = file_ids or None
    history: List[Message] = [Message(role="user", content=structure_prompt)]

    steps: List[Dict[str, Any]] = []
    last_error: Exception | None = None

    for attempt in range(1, _PLANNER_MAX_ATTEMPTS + 1):
        raw: str | None = None
        try:
            if cancellation_check:
                await cancellation_check()
            logger.info("[planner] structure attempt %d/%d project=%s", attempt, _PLANNER_MAX_ATTEMPTS, project_id)
            raw = await _llm_plan_turn(
                history,
                api_key,
                base_url,
                model,
                api_format,
                project_id=project_id,
                file_ids=file_ids,
                citation_state=citation_state,
                user_id=user_id,
                cancellation_check=cancellation_check,
            )
            if cancellation_check:
                await cancellation_check()
            _log_planner_raw_response(raw)
            parsed = _parse_json_object(raw, preferred_keys=("steps",))
            steps = _normalize_steps(parsed.get("steps"), required_language)
            break
        except Exception as e:
            if _is_cancellation_exception(e):
                raise
            last_error = e
            logger.warning("[planner] structure attempt %d/%d failed project=%s: %s", attempt, _PLANNER_MAX_ATTEMPTS, project_id, e)
            _log_planner_raw_response(raw, level=logging.WARNING)
            if attempt >= _PLANNER_MAX_ATTEMPTS:
                raise RuntimeError(f"规划结构失败，已尝试 {_PLANNER_MAX_ATTEMPTS} 次: {e}") from e
            history.append(Message(
                role="user",
                content=_build_json_correction_message(e, _STRUCTURE_OUTPUT_REQUIREMENTS.strip()),
            ))

    dependency_prompt = f"""The section structure below passed validation:
{json.dumps({"steps": steps}, ensure_ascii=False, indent=2)}

Now plan generation prerequisites between these steps.

{_DEPENDENCY_OUTPUT_REQUIREMENTS.strip()}

{_PLANNER_JSON_ONLY_RULE.strip()}"""
    dependency_history: List[Message] = [Message(role="user", content=dependency_prompt)]

    dep_map: Dict[str, List[str]] = {}
    for attempt in range(1, _PLANNER_MAX_ATTEMPTS + 1):
        raw = None
        try:
            if cancellation_check:
                await cancellation_check()
            logger.info("[planner] dependency attempt %d/%d project=%s", attempt, _PLANNER_MAX_ATTEMPTS, project_id)
            raw = await _llm_plan_turn(
                dependency_history,
                api_key,
                base_url,
                model,
                api_format,
                project_id=project_id,
                file_ids=file_ids,
                citation_state=citation_state,
                user_id=user_id,
                enable_tools=False,
                cancellation_check=cancellation_check,
            )
            if cancellation_check:
                await cancellation_check()
            _log_planner_raw_response(raw)
            parsed = _parse_json_object(raw, preferred_keys=("dependencies", "steps"))
            dep_map = _normalize_dependencies(_extract_dependency_items(parsed), steps)
            break
        except Exception as e:
            if _is_cancellation_exception(e):
                raise
            last_error = e
            logger.warning("[planner] dependency attempt %d/%d failed project=%s: %s", attempt, _PLANNER_MAX_ATTEMPTS, project_id, e)
            _log_planner_raw_response(raw, level=logging.WARNING)
            if attempt >= _PLANNER_MAX_ATTEMPTS:
                raise RuntimeError(f"规划依赖失败，已尝试 {_PLANNER_MAX_ATTEMPTS} 次: {e}") from e
            dependency_history.append(Message(
                role="user",
                content=_build_json_correction_message(e, _DEPENDENCY_OUTPUT_REQUIREMENTS.strip()),
            ))

    plan = {"steps": _merge_dependencies(steps, dep_map)}

    for attempt in range(1, _PLANNER_MAX_ATTEMPTS + 1):
        try:
            if cancellation_check:
                await cancellation_check()
            plan = _validate_full_plan(plan, required_language)
            logger.info(
                "[planner] project=%s 规划出 %d 个栏目",
                project_id,
                len(plan["steps"]),
            )
            logger.info(
                "[planner] plan project=%s:\n%s",
                project_id,
                json.dumps(plan, ensure_ascii=False, indent=2),
            )
            return plan
        except Exception as e:
            if _is_cancellation_exception(e):
                raise
            last_error = e
            logger.warning("[planner] final validation attempt %d/%d failed project=%s: %s", attempt, _PLANNER_MAX_ATTEMPTS, project_id, e)
            if attempt >= _PLANNER_MAX_ATTEMPTS:
                raise RuntimeError(f"规划最终校验失败，已尝试 {_PLANNER_MAX_ATTEMPTS} 次: {e}") from e
            history.append(Message(
                role="user",
                content=_build_json_correction_message(
                    e,
                    (
                        "Required complete JSON shape:\n"
                        '{"steps": [{"step_id": "story_overview", '
                        '"step_name": "Section name", "instruction": "What this section should cover", '
                        '"depends_on": []}]}'
                    ),
                ),
            ))
            try:
                if cancellation_check:
                    await cancellation_check()
                raw = await _llm_plan_turn(
                    history,
                    api_key,
                    base_url,
                    model,
                    api_format,
                    project_id=project_id,
                    file_ids=file_ids,
                    citation_state=citation_state,
                    user_id=user_id,
                    cancellation_check=cancellation_check,
                )
                if cancellation_check:
                    await cancellation_check()
                _log_planner_raw_response(raw)
                plan = _parse_json_object(raw, preferred_keys=("steps",))
            except Exception as turn_error:
                if _is_cancellation_exception(turn_error):
                    raise
                plan = {}
                last_error = turn_error

    raise RuntimeError(f"规划失败: {last_error}") from last_error
