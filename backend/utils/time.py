from datetime import datetime, timezone


def utc_isoformat(value: datetime | None) -> str | None:
    """Serialize datetimes as explicit UTC ISO strings for browser-safe parsing."""
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    return value.isoformat().replace("+00:00", "Z")
