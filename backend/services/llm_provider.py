from typing import Literal

from kosong.chat_provider import ChatProvider
from kosong.contrib.chat_provider.anthropic import Anthropic
from kosong.contrib.chat_provider.openai_legacy import OpenAILegacy


LLM_API_FORMAT_OPENAI: Literal["openai"] = "openai"
LLM_API_FORMAT_ANTHROPIC: Literal["anthropic"] = "anthropic"
LLMApiFormat = Literal["openai", "anthropic"]


def normalize_llm_api_format(value: str | None) -> LLMApiFormat:
    normalized = (value or "").strip().lower().replace("-", "_")
    if normalized in {"anthropic", "anthropic_messages", "claude", "claude_messages"}:
        return LLM_API_FORMAT_ANTHROPIC
    return LLM_API_FORMAT_OPENAI


def normalize_anthropic_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    normalized = base_url.strip().rstrip("/")
    if normalized.endswith("/v1"):
        normalized = normalized[:-3].rstrip("/")
    return normalized or None


def create_llm_chat_provider(
    *,
    api_key: str,
    base_url: str | None,
    model: str,
    api_format: str | None = None,
    max_tokens: int = 4000,
    temperature: float | None = None,
    stream: bool = True,
) -> ChatProvider:
    generation_kwargs: dict = {"max_tokens": max_tokens}
    if temperature is not None:
        generation_kwargs["temperature"] = temperature

    if normalize_llm_api_format(api_format) == LLM_API_FORMAT_ANTHROPIC:
        provider = Anthropic(
            model=model,
            api_key=api_key,
            base_url=normalize_anthropic_base_url(base_url),
            stream=stream,
            default_max_tokens=max_tokens,
            prompt_cache=False,
        )
        return provider.with_generation_kwargs(
            beta_features=[],
            **generation_kwargs,
        )

    provider = OpenAILegacy(
        model=model,
        api_key=api_key,
        base_url=base_url,
        stream=stream,
        reasoning_key="reasoning_content",
    )
    return provider.with_generation_kwargs(**generation_kwargs)
