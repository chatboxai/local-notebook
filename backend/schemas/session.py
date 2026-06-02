from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    project_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}