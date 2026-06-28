from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from schemas.base import UTCDateTimeModel


class FileResponse(UTCDateTimeModel):
    id: str
    project_id: str
    file_name: str
    file_type: Optional[str]
    file_size: Optional[int]
    status: str
    error_message: Optional[str]
    processing_current: Optional[int]
    processing_total: Optional[int]
    processing_message: Optional[str]
    job_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FileStatusUpdate(BaseModel):
    status: str
    error_message: Optional[str] = None
