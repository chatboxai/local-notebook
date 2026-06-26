import asyncio
import json
import logging

import config
from kosong._generate import generate
from kosong.message import Message
from services.llm_provider import create_llm_chat_provider

logger = logging.getLogger("service.summary")

SEGMENT_SUMMARY_PROMPT = """Generate a concise English summary for the following text. The summary will be used for document retrieval and synthesis.

Requirements:
1. Preserve key entities such as names, places, technical terms, and numbers.
2. Highlight the core claim, topic, or finding.
3. Use direct declarative sentences; avoid low-information phrases such as "this text discusses".
4. Write in English. Keep exact source terms, titles, names, and quoted wording unchanged when translation would lose precision.
5. Output only the summary, with no extra explanation.

Text:
{content}

Summary:"""

FILE_SUMMARY_PROMPT = """Using the following file information, generate an overall English summary and keywords.

File name: {filename}

Segment summaries:
{segment_summaries}

=== Summary Requirements ===
1. Write no more than 120 English words. Combine the key information from the segment summaries and extract the file's main purpose.
2. Use concise, information-dense declarative sentences.
3. Bold marking rules (use **bold**):
   - Bold the document's **core claim** or **main conclusion**.
   - Bold **key concept definitions**, especially when a technical term first appears.
   - Do not bold names, places, or concrete examples unless they are the document's main topic.

=== Keyword Requirements ===
1. Extract 5 keywords, each 1-4 English words.
2. Keywords should reflect the document's core themes rather than isolated examples.
3. Prefer disciplines, methods, core concepts, and main viewpoints.

Return strict JSON only:
{{"summary": "Overall file summary...", "keywords": ["keyword 1", "keyword 2", "keyword 3", "keyword 4", "keyword 5"]}}"""

PROJECT_SUMMARY_PROMPT = """Using the following project information and file summaries, generate an overall English project summary in no more than 120 words.

Project name: {project_name}

File summaries:
{file_summaries}

Requirements:
1. Combine the topics and content across all files.
2. Explain the relationships among the files.
3. Highlight the project's core value.
4. Write in English and output only the summary, with no extra explanation.

Project summary:"""


async def _llm_complete(
    prompt: str,
    api_key: str,
    base_url: str | None,
    model: str,
    api_format: str = "openai",
    max_tokens: int = 1024,
    temperature: float = 0.2,
) -> str:
    chat_provider = create_llm_chat_provider(
        api_key=api_key,
        base_url=base_url,
        model=model,
        api_format=api_format,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=False,
    )
    result = await generate(
        chat_provider=chat_provider,
        system_prompt="",
        tools=[],
        history=[Message(role="user", content=prompt)],
    )
    return result.message.extract_text().strip()


async def _resolve_llm() -> tuple[str, str | None, str, str] | None:
    # 解析任务的摘要生成属于「简单任务」,走节省计划:若配置了 easy_task_llm 则用更便宜的
    # 模型(复用主 LLM 的 key/url),否则与主 LLM 一致。
    api_key, base_url, model, api_format = await config.resolve_easy_task_llm_provider_config()
    if not api_key or not model:
        return None
    return api_key, base_url, model, api_format


async def generate_segment_summary(
    content: str,
    api_key: str,
    base_url: str | None,
    model: str,
    api_format: str = "openai",
) -> str:
    if not content or len(content) < 20:
        return content[:200] if content else ""

    prompt = SEGMENT_SUMMARY_PROMPT.format(content=content[:2000])
    summary = await _llm_complete(prompt, api_key, base_url, model, api_format=api_format)

    if len(summary) > 500:
        summary = summary[:500] + "..."
    return summary


async def generate_segment_summaries(
    segments: list[dict],
    api_key: str,
    base_url: str | None,
    model: str,
    api_format: str = "openai",
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
                summary = await generate_segment_summary(
                    content,
                    api_key,
                    base_url,
                    model,
                    api_format=api_format,
                )
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
    base_url: str | None,
    model: str,
    api_format: str = "openai",
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
        raw = await _llm_complete(
            prompt,
            api_key,
            base_url,
            model,
            api_format=api_format,
            max_tokens=1024,
            temperature=0.3,
        )
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
    base_url: str | None,
    model: str,
    api_format: str = "openai",
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
        summary = await _llm_complete(
            prompt,
            api_key,
            base_url,
            model,
            api_format=api_format,
            max_tokens=1024,
            temperature=0.3,
        )
        return summary[:500]
    except Exception as e:
        logger.warning(f"Project summary generation failed: {e}")
        return ""
