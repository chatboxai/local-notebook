from datetime import datetime

from pydantic import BaseModel, field_serializer

from utils.time import utc_isoformat


class UTCDateTimeModel(BaseModel):
    @field_serializer(
        "created_at",
        "updated_at",
        "started_at",
        "finished_at",
        check_fields=False,
    )
    def serialize_datetime(self, value: datetime | None) -> str | None:
        return utc_isoformat(value)
