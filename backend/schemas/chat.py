from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel

from schemas.base import UTCDateTimeModel


class ChatRequest(BaseModel):
    session_id: str
    message: str
    file_ids: list[str] = []
    enable_web_search: bool = False


class EditMessageRequest(BaseModel):
    content: str
    file_ids: Optional[list[str]] = None
    enable_web_search: bool = False
    agent_role: str = "default"


class CitationItem(BaseModel):
    block_id: str
    file_id: str
    file_name: str
    page_num: Optional[int]
    content_snippet: str


class MessageResponse(UTCDateTimeModel):
    id: str
    session_id: str
    role: str
    content: str
    citations: Optional[list[CitationItem]]
    created_at: datetime

    model_config = {"from_attributes": True}
