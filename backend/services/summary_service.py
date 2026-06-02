import asyncio
import json
import logging
from typing import Optional

import httpx

import config

logger = logging.getLogger("service.summary")

SEGMENT_SUMMARY_PROMPT = """请为以下文本生成一个摘要（不超过200字），用于文档检索和归纳总结。

要求：
1. 保留关键实体（人名、地名、专业术语、数字等）
2. 突出核心观点或主题
3. 使用陈述句，直接描述内容，避免使用"本文讲述了"等缺乏信息密度的通用表述
4. 直接输出结果，不要有任何多余的解释

文本内容：
{content}

摘要："""

FILE_SUMMARY_PROMPT = """基于以下文件信息，生成文件的整体总结和关键词。

文件名：{filename}

段落摘要：
{segment_summaries}

=== 总结要求 ===
1. 不超过200字，综合各段落核心信息，提炼文件主旨
2. 使用简洁的陈述句，信息密度高
3. 加粗标记规则（用 **粗体** 标记）：
   - 加粗文档的**核心论点**或**主要结论**
   - 加粗**关键概念定义**（如专业术语首次出现时）
   - 不要加粗人名、地名等具体例子，除非它们本身就是文档主题

=== 关键词要求 ===
1. 提取5个关键词，每个2-6个字
2. 关键词应体现文档的核心主题，而非具体案例
3. 优先选择：学科领域、研究方法、核心概念、主要观点

严格按 JSON 格式输出：
{{"summary": "文件总结内容...", "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"]}}"""

PROJECT_SUMMARY_PROMPT = """基于以下项目信息和文件总结，生成项目的整体总结（不超过200字）。

项目名称：{project_name}

文件总结：
{file_summaries}

要求：
1. 综合所有文件的主题和内容
2. 体现文件之间的关联
3. 突出项目的核心价值
4. 直接输出结果，不要有任何多余的解释

项目总结："""


async def _llm_complete(
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
    max_tokens: int = 1024,
    temperature: float = 0.2,
) -> str:
    url = f"{base_url.rstrip('/')}/chat/completions"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


async def _resolve_llm() -> tuple[str, str, str] | None:
    api_key, base_url, model = await config.resolve_llm_config()
    if not api_key or not base_url or not model:
        return None
    return api_key, base_url, model


async def generate_segment_summary(
    content: str,
    api_key: str,
    base_url: str,
    model: str,
) -> str:
    if not content or len(content) < 20:
        return content[:200] if content else ""

    prompt = SEGMENT_SUMMARY_PROMPT.format(content=content[:2000])
    summary = await _llm_complete(prompt, api_key, base_url, model)

    if len(summary) > 500:
        summary = summary[:500] + "..."
    return summary


async def generate_segment_summaries(
    segments: list[dict],
    api_key: str,
    base_url: str,
    model: str,
    concurrency: int = 30,
) -> dict[int, str]:
    if not segments:
        return {}

    semaphore = asyncio.Semaphore(concurrency)
    results: dict[int, str] = {}

    async def _do_one(seg: dict):
        idx = seg["segment_index"]
        content = seg["content"]
        async with semaphore:
            try:
                summary = await generate_segment_summary(content, api_key, base_url, model)
                results[idx] = summary
                logger.info(f"segment {idx} summary done ({len(summary)} chars)")
            except Exception as e:
                logger.warning(f"segment {idx} summary failed, skipping: {e}")

    await asyncio.gather(*[_do_one(s) for s in segments])
    return results


async def generate_file_summary(
    file_name: str,
    segment_summaries: list[str],
    api_key: str,
    base_url: str,
    model: str,
) -> dict:
    if not segment_summaries:
        return {"summary": "", "keywords": []}

    if len(segment_summaries) > 20:
        n = len(segment_summaries)
        front = segment_summaries[:int(n * 0.4)]
        mid_start = int(n * 0.4)
        mid_end = int(n * 0.6)
        middle = segment_summaries[mid_start:mid_end]
        back = segment_summaries[int(n * 0.6):]
        sampled = front + middle + back
    else:
        sampled = segment_summaries

    numbered = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sampled))
    prompt = FILE_SUMMARY_PROMPT.format(filename=file_name, segment_summaries=numbered)

    try:
        raw = await _llm_complete(prompt, api_key, base_url, model, max_tokens=1024, temperature=0.3)
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        parsed = json.loads(text)
        return {
            "summary": parsed.get("summary", "")[:500],
            "keywords": parsed.get("keywords", [])[:10],
        }
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"File summary JSON parse failed: {e}, using raw text")
        return {"summary": raw[:500] if raw else "", "keywords": []}
    except Exception as e:
        logger.warning(f"File summary generation failed: {e}")
        return {"summary": "", "keywords": []}


async def generate_project_summary(
    project_name: str,
    file_summaries: list[dict],
    api_key: str,
    base_url: str,
    model: str,
) -> str:
    if not file_summaries:
        return ""

    lines = "\n".join(
        f"- {fs['file_name']}: {fs['summary']}"
        for fs in file_summaries if fs.get("summary")
    )
    if not lines:
        return ""

    prompt = PROJECT_SUMMARY_PROMPT.format(
        project_name=project_name,
        file_summaries=lines,
    )

    try:
        summary = await _llm_complete(prompt, api_key, base_url, model, max_tokens=1024, temperature=0.3)
        return summary[:500]
    except Exception as e:
        logger.warning(f"Project summary generation failed: {e}")
        return ""
