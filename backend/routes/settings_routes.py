import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import config
from dependencies.auth import get_current_user
from dependencies.database import get_db
from schemas.settings import (
    SETTING_DEFAULTS,
    SETTING_KEYS,
    SettingsResponse,
    SettingsUpdate,
)
from kosong._generate import generate
from kosong.chat_provider import ChatProviderError
from kosong.message import Message
from services.llm_provider import create_llm_chat_provider, normalize_llm_api_format

router = APIRouter(prefix="/settings", tags=["settings"])


async def _full_settings() -> dict[str, str | None]:
    import os
    cached = config.get_all_cached()
    merged: dict[str, str | None] = {}
    for key in SETTING_KEYS:
        merged[key] = cached.get(key) or os.getenv(key.upper()) or SETTING_DEFAULTS.get(key) or None
    return merged


@router.get("", response_model=SettingsResponse)
async def get_settings(
    _: str = Depends(get_current_user),
) -> SettingsResponse:
    all_settings = await _full_settings()
    return SettingsResponse(settings=all_settings)


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    body: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> SettingsResponse:
    filtered = {
        k: v for k, v in body.settings.items() if k in SETTING_KEYS
    }
    if not filtered:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid setting keys provided.",
        )

    if "embedding_source" in filtered and not body.force:
        old_source = await config.get_setting("embedding_source", "")
        new_source = filtered["embedding_source"]
        if old_source and new_source != old_source:
            from sqlalchemy import select, func
            from models.file import File
            count_result = await db.execute(
                select(func.count()).select_from(File).where(File.status == "ready")
            )
            file_count = count_result.scalar() or 0
            if file_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"当前有 {file_count} 个已解析的文档，"
                           "切换 Embedding 服务后这些文档的向量数据将全部失效，"
                           "需要删除项目并重新上传。",
                )

    await config.set_many(filtered, db)
    all_settings = await _full_settings()
    return SettingsResponse(settings=all_settings)


@router.get("/preflight")
async def preflight_check(
    _: str = Depends(get_current_user),
) -> dict:
    # 直接检查用户的"原始设置",不依赖 resolve_*_config 的默认值兜底,
    # 否则会出现"用户没选模型,但 fallback 给了默认值,误报为已配置"的情况。
    llm_source = await config.get_setting("llm_source", "")
    if llm_source == "custom":
        llm_ready = bool(
            (await config.get_setting("llm_api_key", ""))
            and (await config.get_setting("llm_base_url", ""))
            and (await config.get_setting("llm_model", ""))
        )
    else:  # 默认走 bailian
        llm_ready = bool(
            (await config.get_setting("bailian_api_key", ""))
            and (await config.get_setting("llm_bailian_model", ""))
        )

    emb_source = await config.get_setting("embedding_source", "bailian")
    if emb_source == "local":
        embedding_ready = bool(await config.get_setting("embedding_base_url", ""))
    elif emb_source == "custom":
        embedding_ready = bool(
            (await config.get_setting("embedding_api_key", ""))
            and (await config.get_setting("embedding_base_url", ""))
            and (await config.get_setting("embedding_model", ""))
        )
    else:  # bailian
        embedding_ready = bool(
            (await config.get_setting("bailian_api_key", ""))
            and (await config.get_setting("embedding_bailian_model", ""))
        )

    missing = []
    if not llm_ready:
        missing.append("LLM 大语言模型")
    if not embedding_ready:
        missing.append("Embedding 向量模型")

    return {
        "ready": llm_ready and embedding_ready,
        "llm_ready": llm_ready,
        "embedding_ready": embedding_ready,
        "missing": missing,
    }


@router.get("/{key}")
async def get_single_setting(
    key: str,
    _: str = Depends(get_current_user),
) -> dict:
    if key not in SETTING_KEYS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown setting key: {key}",
        )
    value = await config.get_setting(key)
    return {"key": key, "value": value}


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> None:
    if key not in SETTING_KEYS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown setting key: {key}",
        )
    await config.set_setting(key, None, db)


class ChatModelTestRequest(BaseModel):
    # source 字段让前端能在"radio 已切换但还没保存"时测试正确的配置源,
    # 否则后端会按 DB 里旧的 source resolve,得到自定义的 key + 百炼的 model 这种错乱组合。
    source: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    api_format: str | None = None


class EmbeddingTestRequest(BaseModel):
    # source 同 ChatModelTestRequest 的设计:让前端 radio 切换后无需先保存就能正确测试
    source: str | None = None
    mode: str = "local"
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None


async def _mark_verified(key: str, ok: bool, db: AsyncSession) -> None:
    await config.set_setting(key, "true" if ok else "false", db)


async def _test_chat_completions(
    api_key: str, base_url: str, model: str, payload_messages: list,
    verified_key: str, db: AsyncSession,
) -> dict:
    """Shared HTTP probe for LLM / VLM test endpoints."""
    payload = {"model": model, "messages": payload_messages, "max_tokens": 1}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(f"{base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
        if resp.status_code in (200, 201):
            await _mark_verified(verified_key, True, db)
            return {"ok": True, "msg": "连接成功", "verified": True}
        await _mark_verified(verified_key, False, db)
        return {"ok": False, "msg": f"服务返回 {resp.status_code}"}
    except httpx.ConnectError:
        await _mark_verified(verified_key, False, db)
        return {"ok": False, "msg": "无法连接到服务地址"}
    except Exception as exc:
        await _mark_verified(verified_key, False, db)
        return {"ok": False, "msg": str(exc)}


async def _test_llm_provider(
    api_key: str,
    base_url: str | None,
    model: str,
    api_format: str,
    verified_key: str,
    db: AsyncSession,
) -> dict:
    try:
        chat_provider = create_llm_chat_provider(
            api_key=api_key,
            base_url=base_url,
            model=model,
            api_format=api_format,
            max_tokens=1,
            stream=False,
        )
        await generate(
            chat_provider=chat_provider,
            system_prompt="",
            tools=[],
            history=[Message(role="user", content="hi")],
        )
        await _mark_verified(verified_key, True, db)
        return {"ok": True, "msg": "连接成功", "verified": True}
    except ChatProviderError as exc:
        await _mark_verified(verified_key, False, db)
        return {"ok": False, "msg": str(exc)}
    except Exception as exc:
        await _mark_verified(verified_key, False, db)
        return {"ok": False, "msg": str(exc)}


def _require_chat_params(
    api_key: str | None,
    base_url: str | None,
    model: str | None,
    *,
    require_base_url: bool = True,
) -> None:
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    if require_base_url and not base_url:
        raise HTTPException(status_code=400, detail="Base URL is required")
    if not model:
        raise HTTPException(status_code=400, detail="Model is required")


async def _resolve_test_config(
    body: ChatModelTestRequest,
    kind: str,  # "llm" | "vlm"
) -> tuple[str | None, str | None, str | None, str]:
    """按 body.source 独立计算 api_key/base_url/model,不依赖 DB 里已保存的 source,
    让用户在切了 radio 但还没点保存时也能用新配置做测试。"""
    if body.source == "bailian":
        api_key = body.api_key or await config.get_setting("bailian_api_key", "")
        base_url = config.BAILIAN_BASE_URL
        model = body.model
        return api_key, base_url, model, "openai"
    if body.source == "custom":
        api_format = normalize_llm_api_format(body.api_format) if kind == "llm" else "openai"
        return body.api_key, body.base_url, body.model, api_format
    # source 未指定 — 兼容老调用方,按 DB 当前状态解析
    if kind == "vlm":
        default_key, default_url, default_model = await config.resolve_vlm_config()
        default_format = "openai"
    else:
        default_key, default_url, default_model, default_format = await config.resolve_llm_provider_config()
    return (
        body.api_key or default_key,
        body.base_url or default_url,
        body.model or default_model,
        normalize_llm_api_format(body.api_format or default_format),
    )


@router.post("/test/llm")
async def test_llm(
    body: ChatModelTestRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    api_key, base_url, model, api_format = await _resolve_test_config(body, kind="llm")
    _require_chat_params(api_key, base_url, model)

    return await _test_llm_provider(api_key, base_url, model, api_format, "llm_verified", db)


@router.post("/test/easy-task-llm")
async def test_easy_task_llm(
    body: ChatModelTestRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    api_key, base_url, model, api_format = await _resolve_test_config(body, kind="llm")
    _require_chat_params(api_key, base_url, model)

    return await _test_llm_provider(api_key, base_url, model, api_format, "easy_task_llm_verified", db)


@router.post("/test/vlm")
async def test_vlm(
    body: ChatModelTestRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    api_key, base_url, model, _ = await _resolve_test_config(body, kind="vlm")
    _require_chat_params(api_key, base_url, model)

    return await _test_chat_completions(
        api_key, base_url, model,
        [{"role": "user", "content": [{"type": "text", "text": "hi"}]}],
        "vlm_verified", db,
    )


class MinerUTestRequest(BaseModel):
    source: str | None = None
    base_url: str | None = None
    api_key: str | None = None


@router.post("/test/mineru")
async def test_mineru(
    body: MinerUTestRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    from services.mineru_client import health_check

    enabled, default_source, default_url, default_key = await config.resolve_mineru_config()
    source = body.source or default_source or "local"

    if source == "api":
        api_key = body.api_key or default_key
        if not api_key:
            return {"ok": False, "msg": "未配置 API Key"}
        try:
            result = await health_check(api_key=api_key, source="api")
            await _mark_verified("mineru_verified", result["ok"], db)
            if result["ok"]:
                return {"ok": True, "msg": result["msg"], "verified": True}
            return {"ok": False, "msg": result["msg"]}
        except Exception as exc:
            await _mark_verified("mineru_verified", False, db)
            return {"ok": False, "msg": str(exc)}
    else:
        base_url = body.base_url or default_url
        if not base_url:
            return {"ok": False, "msg": "未配置服务地址"}
        try:
            result = await health_check(base_url=base_url, source="local")
            await _mark_verified("mineru_verified", result["ok"], db)
            if result["ok"]:
                return {"ok": True, "msg": f"MinerU 服务连接成功 ({base_url})", "verified": True}
            return {"ok": False, "msg": f"无法连接到 {base_url}"}
        except Exception as exc:
            await _mark_verified("mineru_verified", False, db)
            return {"ok": False, "msg": str(exc)}


@router.post("/test/embedding")
async def test_embedding(
    body: EmbeddingTestRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    # 按 body.source 独立解析,避免依赖 DB 里旧的 embedding_source。
    if body.source == "bailian":
        api_key = body.api_key or await config.get_setting("bailian_api_key", "")
        base_url = config.BAILIAN_BASE_URL
        model = body.model or await config.get_setting("embedding_bailian_model", "")
    elif body.source == "local":
        base_url = body.base_url or ""
        model = body.model or ""
        api_key = "local"
    elif body.source == "custom":
        api_key = body.api_key or ""
        base_url = body.base_url or ""
        model = body.model or ""
    else:
        # 兼容老调用方
        _, default_url, default_model, default_key = await config.resolve_embedding_config()
        base_url = body.base_url or default_url
        model = body.model or default_model
        api_key = body.api_key or default_key

    if not base_url:
        return {"ok": False, "msg": "未配置服务地址"}

    payload: dict = {"model": model, "input": ["测试文本"]}
    if "embedding" in (model or "") and "dashscope" in (base_url or ""):
        payload["dimensions"] = 512

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(f"{base_url.rstrip('/')}/embeddings", json=payload, headers=headers)
        if resp.status_code in (200, 201):
            data = resp.json()
            dim = len(data.get("data", [{}])[0].get("embedding", []))
            await _mark_verified("embedding_verified", True, db)
            return {"ok": True, "msg": f"连接成功 · {model} · 维度 {dim}", "verified": True}
        await _mark_verified("embedding_verified", False, db)
        return {"ok": False, "msg": f"服务返回 {resp.status_code}: {resp.text[:200]}"}
    except httpx.ConnectError:
        await _mark_verified("embedding_verified", False, db)
        return {"ok": False, "msg": f"无法连接到 {base_url}"}
    except Exception as exc:
        await _mark_verified("embedding_verified", False, db)
        return {"ok": False, "msg": str(exc)}


class WebSearchTestRequest(BaseModel):
    api_key: str | None = None


@router.post("/test/web-search")
async def test_web_search(
    body: WebSearchTestRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    enabled, default_key, base_url = await config.resolve_web_search_config()

    api_key = body.api_key or default_key

    if not api_key:
        return {"ok": False, "msg": "未配置 API Key"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/web-search",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": "test",
                    "count": 1,
                    "freshness": "noLimit",
                    "summary": True
                }
            )
        if resp.status_code in (200, 201):
            await _mark_verified("web_search_verified", True, db)
            return {"ok": True, "msg": "博查 API 连接成功", "verified": True}
        if resp.status_code == 401:
            await _mark_verified("web_search_verified", False, db)
            return {"ok": False, "msg": "API Key 无效，请检查密钥"}
        await _mark_verified("web_search_verified", False, db)
        return {"ok": False, "msg": f"服务返回 {resp.status_code}"}
    except httpx.ConnectError:
        await _mark_verified("web_search_verified", False, db)
        return {"ok": False, "msg": "无法连接到博查服务"}
    except Exception as exc:
        await _mark_verified("web_search_verified", False, db)
        return {"ok": False, "msg": str(exc)}
