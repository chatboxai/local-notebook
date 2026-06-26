from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from schemas.base import UTCDateTimeModel


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(UTCDateTimeModel):
    id: str
    name: str
    description: Optional[str]
    summary: Optional[str] = None
    color: Optional[str] = None
    file_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
