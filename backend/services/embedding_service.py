import asyncio
import logging
from typing import Awaitable, Callable

import httpx

import config

logger = logging.getLogger("embedding_service")


async def _get_config() -> tuple[str, str, str, str]:
    mode, base_url, model, api_key = await config.resolve_embedding_config()

    if not base_url:
        raise RuntimeError(
            "Embedding base URL is not configured. Set base_url in Settings > Embedding. "
            "Docker deployments cannot use localhost; see the Settings hint."
        )
    # API 模式(bailian/custom)必须有显式 model;
    # local 模式 model 字段由本地服务忽略(用其启动时 MODEL env),空串透传即可。
    if mode == "api" and not model:
        raise RuntimeError(
            "Embedding model is not configured. Select a model in Settings > Embedding."
        )
    if not api_key:
        api_key = "local"

    return mode, base_url.rstrip("/"), model, api_key


EMBED_BATCH_SIZE = 10


async def embed_texts(
    texts: list[str],
    progress_callback: Callable[[int], Awaitable[None]] | None = None,
) -> list[list[float]]:
    if not texts:
        return []

    mode, base_url, model, api_key = await _get_config()

    is_dashscope = "dashscope" in base_url
    batch_size = EMBED_BATCH_SIZE

    url = f"{base_url}/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    logger.info(f"[embed] mode={mode} url={url} model={model} input_count={len(texts)} batch_size={batch_size}")

    all_results: list[list[float]] = [[] for _ in texts]

    for batch_start in range(0, len(texts), batch_size):
        batch = texts[batch_start:batch_start + batch_size]

        payload: dict = {"model": model, "input": batch}
        if is_dashscope and "embedding" in model:
            payload["dimensions"] = 512

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload, headers=headers)
                logger.info(f"[embed] batch {batch_start//batch_size + 1} status={resp.status_code}")
                resp.raise_for_status()
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to the embedding service ({base_url}). "
                "Configure the embedding service address in Settings first. "
                "For local mode, start it with: cd services/embedding && python server.py"
            )
        except httpx.ReadTimeout:
            raise RuntimeError(
                f"Embedding service timed out ({base_url}). "
                "Check whether the embedding service is running correctly."
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Embedding service returned error {e.response.status_code}: {e.response.text}")

        data = resp.json()
        items = sorted(data["data"], key=lambda x: x["index"])
        for i, item in enumerate(items):
            all_results[batch_start + i] = item["embedding"]
        if progress_callback:
            await progress_callback(len(batch))

    return all_results


async def embed_single(text: str) -> list[float]:
    results = await embed_texts([text])
    return results[0]


def embed_single_sync(text: str) -> list[float]:
    return asyncio.run(embed_single(text))


async def health_check() -> dict:
    mode, base_url, model, _ = await _get_config()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{base_url}/health")
            if resp.status_code == 200:
                return {"ok": True, "mode": mode, "model": model, "detail": resp.json()}
            return {"ok": False, "mode": mode, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"ok": False, "mode": mode, "error": str(e)}
