import asyncio
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

_cache: dict[str, str] = {}
_lock: asyncio.Lock = asyncio.Lock()


async def load_settings(db: AsyncSession) -> None:
    from models.settings import Setting

    async with _lock:
        result = await db.execute(select(Setting))
        rows = result.scalars().all()
        _cache.clear()
        for row in rows:
            if row.value is not None:
                _cache[row.key] = row.value


async def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    if key in _cache:
        return _cache[key]
    return os.getenv(key.upper(), default)


async def _upsert_setting(
    key: str, value: Optional[str], db: AsyncSession
) -> None:
    """Insert or update a single setting row (caller holds _lock)."""
    from models.settings import Setting

    result = await db.execute(select(Setting).where(Setting.key == key))
    row = result.scalar_one_or_none()

    if row is None:
        row = Setting(key=key, value=value)
        db.add(row)
    else:
        row.value = value
        row.updated_at = datetime.now(timezone.utc)


def _update_cache(key: str, value: Optional[str]) -> None:
    if value is None:
        _cache.pop(key, None)
    else:
        _cache[key] = value


async def set_setting(key: str, value: Optional[str], db: AsyncSession) -> None:
    async with _lock:
        await _upsert_setting(key, value, db)
        await db.commit()
        _update_cache(key, value)


async def set_many(settings: dict[str, Optional[str]], db: AsyncSession) -> None:
    async with _lock:
        for key, value in settings.items():
            await _upsert_setting(key, value, db)
        await db.commit()
        for key, value in settings.items():
            _update_cache(key, value)


def get_all_cached() -> dict[str, Optional[str]]:
    return dict(_cache)


BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


async def resolve_mineru_config() -> tuple[bool, str, str | None, str | None]:
    source = await get_setting("mineru_source", "api")

    if source == "local":
        base_url = await get_setting("mineru_base_url", "")
        if base_url and base_url.strip():
            return True, "local", base_url.strip().rstrip("/"), None
        return False, "local", None, None

    api_key = await get_setting("mineru_api_key", "")
    if api_key and api_key.strip():
        return True, "api", None, api_key.strip()
    return False, "api", None, None


BOCHA_BASE_URL = "https://api.bochaai.com/v1"

async def resolve_web_search_config() -> tuple[bool, str | None, str | None]:
    api_key = await get_setting("bocha_api_key", "")

    enabled = bool(api_key and api_key.strip())
    return enabled, api_key.strip() if api_key else None, BOCHA_BASE_URL


async def resolve_llm_config() -> tuple[str | None, str | None, str | None]:
    source = await get_setting("llm_source", "")

    if source == "custom":
        api_key = await get_setting("llm_api_key", "")
        base_url = await get_setting("llm_base_url", "")
        model = await get_setting("llm_model", "")
        return api_key or None, base_url or None, model or None

    api_key = await get_setting("bailian_api_key", "")
    model = await get_setting("llm_bailian_model", "")
    return api_key or None, BAILIAN_BASE_URL, model or None


async def resolve_llm_provider_config() -> tuple[str | None, str | None, str | None, str]:
    api_key, base_url, model = await resolve_llm_config()
    source = await get_setting("llm_source", "")
    if source == "custom":
        api_format = await get_setting("llm_api_format", "openai")
    else:
        api_format = "openai"
    return api_key, base_url, model, api_format or "openai"


async def is_easy_task_llm_configured() -> bool:
    """用户是否单独配置了「简单任务模型」(节省计划开关是否实际生效)。

    为空表示简单任务与主 LLM 共用同一个模型。
    """
    easy_model = await get_setting("easy_task_llm", "")
    return bool(easy_model and easy_model.strip())


async def resolve_easy_task_llm_config() -> tuple[str | None, str | None, str | None]:
    """「节省计划」:简单任务(解析时的摘要生成)用的 LLM 配置。

    复用主 LLM 的 provider(key + base_url),仅在配置了 easy_task_llm 时替换模型名;
    未配置则与主 LLM 完全一致,即简单任务和复杂任务共用一个模型。
    """
    api_key, base_url, model = await resolve_llm_config()
    if await is_easy_task_llm_configured():
        model = (await get_setting("easy_task_llm", "")).strip()
    return api_key, base_url, model


async def resolve_easy_task_llm_provider_config() -> tuple[str | None, str | None, str | None, str]:
    """Like resolve_easy_task_llm_config(), but includes the selected request format."""
    api_key, base_url, model, api_format = await resolve_llm_provider_config()
    if await is_easy_task_llm_configured():
        model = (await get_setting("easy_task_llm", "")).strip()
    return api_key, base_url, model, api_format


async def resolve_vlm_config() -> tuple[str | None, str | None, str | None]:
    source = await get_setting("vlm_source", "")

    if source == "custom":
        api_key = await get_setting("vlm_api_key", "")
        base_url = await get_setting("vlm_base_url", "")
        model = await get_setting("vlm_model", "")
        return api_key or None, base_url or None, model or None

    api_key = await get_setting("bailian_api_key", "")
    model = await get_setting("vlm_bailian_model", "")
    return api_key or None, BAILIAN_BASE_URL, model or None


async def resolve_embedding_config() -> tuple[str, str, str, str]:
    source = await get_setting("embedding_source", "bailian")

    if source == "local":
        base_url = await get_setting("embedding_base_url", "")
        model = await get_setting("embedding_model", "")
        return "local", base_url or "", model or "", "local"

    if source == "custom":
        base_url = await get_setting("embedding_base_url", "")
        model = await get_setting("embedding_model", "")
        api_key = await get_setting("embedding_api_key", "")
        return "api", base_url or "", model or "", api_key or ""

    api_key = await get_setting("bailian_api_key", "")
    model = await get_setting("embedding_bailian_model", "")
    return "api", BAILIAN_BASE_URL, model or "", api_key or ""
