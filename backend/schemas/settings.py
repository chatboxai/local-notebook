from typing import Optional
from pydantic import BaseModel


SETTING_KEYS = {
    "bailian_api_key",
    "llm_source",
    "llm_bailian_model",
    "llm_api_key",
    "llm_base_url",
    "llm_model",
    "easy_task_llm",
    "easy_task_llm_verified",
    "vlm_source",
    "vlm_bailian_model",
    "vlm_api_key",
    "vlm_base_url",
    "vlm_model",
    "embedding_source",
    "embedding_bailian_model",
    "embedding_model",
    "embedding_api_key",
    "embedding_base_url",
    "mineru_source",
    "mineru_base_url",
    "mineru_api_key",
    "funasr_base_url",
    "bocha_api_key",
    "llm_verified",
    "vlm_verified",
    "embedding_verified",
    "mineru_verified",
    "web_search_verified",
}


class SettingsUpdate(BaseModel):
    settings: dict[str, Optional[str]]
    force: bool = False


class SettingsResponse(BaseModel):
    settings: dict[str, Optional[str]]
