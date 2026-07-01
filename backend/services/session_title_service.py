import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import PurePath
from typing import Iterable

import config
import kosong
from kosong.message import Message as KosongMessage
from kosong.tooling.simple import SimpleToolset

from services.llm_provider import create_llm_chat_provider
from services.usage_service import record_model_usage

logger = logging.getLogger("session_title_service")

SESSION_TITLE_STATUS_IDLE = "idle"
SESSION_TITLE_STATUS_GENERATING = "generating"
SESSION_TITLE_STATUS_GENERATED = "generated"
SESSION_TITLE_STATUS_FAILED = "failed"

PLACEHOLDER_SESSION_TITLES = {"", "新对话", "New chat"}
MAX_TITLE_LENGTH = 80
MAX_PROMPT_QUESTION_LENGTH = 1200
MAX_PROMPT_FILE_NAMES = 12
MAX_PROMPT_FILE_NAME_LENGTH = 120
TITLE_MAX_ATTEMPTS = 3
TITLE_MAX_TOKENS = 512
TITLE_GENERATION_LOCK_TTL = timedelta(minutes=5)

_TITLE_SYSTEM_PROMPT = (
    "You generate concise chat session titles for a local document Q&A app. "
    "The title must help the user recognize this conversation later. "
    "Use the primary language of the user's question. "
    "Return only one title, with no quotes, bullets, explanation, or punctuation-only wrapper."
)


def normalize_title_generation_status(value: str | None) -> str:
    value = (value or "").strip()
    if value in {
        SESSION_TITLE_STATUS_IDLE,
        SESSION_TITLE_STATUS_GENERATING,
        SESSION_TITLE_STATUS_GENERATED,
        SESSION_TITLE_STATUS_FAILED,
    }:
        return value
    return SESSION_TITLE_STATUS_IDLE


def is_placeholder_session_title(title: str | None) -> bool:
    return (title or "").strip() in PLACEHOLDER_SESSION_TITLES


def is_title_generation_locked(status: str | None, updated_at: datetime | None) -> bool:
    if normalize_title_generation_status(status) != SESSION_TITLE_STATUS_GENERATING:
        return False
    if updated_at is None:
        return False

    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - updated_at <= TITLE_GENERATION_LOCK_TTL


def _truncate_text(value: str, limit: int) -> str:
    value = " ".join((value or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _clean_generated_title(raw: str) -> str:
    lines = [line.strip() for line in (raw or "").splitlines() if line.strip()]
    if not lines:
        return ""

    title = lines[0]
    title = re.sub(r"^\s*(?:[-*]\s*|\d+[.)]\s*)", "", title)
    title = re.sub(r"^(?:标题|Title)\s*[:：]\s*", "", title, flags=re.IGNORECASE)
    title = title.strip().strip("`\"'“”‘’")
    title = " ".join(title.split())
    return title[:MAX_TITLE_LENGTH].strip()


def _format_file_names(file_names: Iterable[str]) -> str:
    formatted = [
        f"- {_truncate_text(name, MAX_PROMPT_FILE_NAME_LENGTH)}"
        for name in list(file_names)[:MAX_PROMPT_FILE_NAMES]
        if name.strip()
    ]
    return "\n".join(formatted) if formatted else "(No source files selected.)"


def _strip_file_extension(file_name: str) -> str:
    path_name = PurePath(file_name).name
    stem = PurePath(path_name).stem
    return (stem or path_name).strip()


def _looks_like_generic_question(question: str) -> bool:
    normalized = re.sub(r"\s+", "", question)
    if len(normalized) > 40:
        return False
    return bool(re.search(r"(总结|概括|讲什么|说什么|主要内容|这篇|这份|这个文档|this|summari[sz]e|overview)", normalized, re.IGNORECASE))


def _heuristic_session_title(question: str, file_names: list[str]) -> str:
    question_title = _truncate_text(question, MAX_TITLE_LENGTH)
    source_title = ""
    for file_name in file_names:
        source_title = _truncate_text(_strip_file_extension(file_name), 32)
        if source_title:
            break

    if source_title and _looks_like_generic_question(question):
        if re.search(r"[\u4e00-\u9fff]", question):
            return _truncate_text(f"{source_title}要点", MAX_TITLE_LENGTH)
        return _truncate_text(f"{source_title} Overview", MAX_TITLE_LENGTH)

    return question_title or source_title or "New chat"


async def generate_session_title(
    *,
    question: str,
    file_names: list[str],
    user_id: str,
) -> str:
    api_key, base_url, model, api_format = await config.resolve_easy_task_llm_provider_config()
    if not api_key or not model:
        raise RuntimeError("LLM is not configured; session title generation is unavailable.")

    chat_provider = create_llm_chat_provider(
        model=model,
        api_key=api_key,
        base_url=base_url,
        api_format=api_format,
        max_tokens=TITLE_MAX_TOKENS,
        temperature=0.2,
        stream=False,
    )

    prompt = (
        "Generate one clear, searchable chat title from the user's first question "
        "and the selected source file names.\n\n"
        "Requirements:\n"
        "- Prefer a semantic title over a generic label.\n"
        "- Mention the source topic only when it helps recognition.\n"
        "- Keep Chinese titles around 6-18 characters, or English titles around 3-8 words.\n"
        "- Return only the title text.\n\n"
        f"User question:\n{_truncate_text(question, MAX_PROMPT_QUESTION_LENGTH)}\n\n"
        f"Selected source files:\n{_format_file_names(file_names)}"
    )

    retry_note = ""
    for attempt in range(1, TITLE_MAX_ATTEMPTS + 1):
        result = await kosong.step(
            chat_provider=chat_provider,
            system_prompt=_TITLE_SYSTEM_PROMPT,
            toolset=SimpleToolset([]),
            history=[KosongMessage(role="user", content=f"{prompt}\n\n{retry_note}")],
        )
        await record_model_usage(user_id=user_id, model=model, usage=result.usage)

        title = _clean_generated_title(result.message.extract_text())
        if title:
            logger.info("Generated session title attempt=%d title=%r", attempt, title)
            return title

        part_types = [part.type for part in result.message.content]
        logger.warning(
            "Session title generation returned empty text attempt=%d/%d parts=%s",
            attempt,
            TITLE_MAX_ATTEMPTS,
            part_types,
        )
        retry_note = (
            "The previous attempt returned no visible title. "
            "Now return exactly one non-empty title as plain text."
        )

    title = _heuristic_session_title(question, file_names)
    logger.warning("Session title fell back to local heuristic title=%r", title)
    return title
