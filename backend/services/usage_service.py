import logging
import os
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from database import AsyncSessionLocal
from models.usage import UserModelUsageDaily

logger = logging.getLogger("service.usage")


def current_usage_date() -> date:
    timezone_name = os.getenv("USAGE_TIMEZONE", "Asia/Shanghai")
    try:
        usage_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        usage_timezone = timezone.utc
    return datetime.now(timezone.utc).astimezone(usage_timezone).date()


def _token_value(value: int | None) -> int:
    return max(0, int(value or 0))


async def record_model_usage(
    *,
    user_id: str | None,
    model: str | None,
    usage,
) -> None:
    if not user_id or not model or usage is None:
        return

    usage_date = current_usage_date()
    model_name = model.strip()
    if not model_name:
        return

    input_uncached = _token_value(getattr(usage, "input_other", 0))
    input_cache_read = _token_value(getattr(usage, "input_cache_read", 0))
    input_cache_write = _token_value(getattr(usage, "input_cache_creation", 0))
    output = _token_value(getattr(usage, "output", 0))

    async with AsyncSessionLocal() as db:
        try:
            updated = await _increment_usage(
                db,
                user_id=user_id,
                usage_date=usage_date,
                model=model_name,
                input_uncached=input_uncached,
                input_cache_read=input_cache_read,
                input_cache_write=input_cache_write,
                output=output,
            )
            if updated:
                await db.commit()
                return

            row = UserModelUsageDaily(
                user_id=user_id,
                usage_date=usage_date,
                model=model_name,
                call_count=1,
                input_uncached_tokens=input_uncached,
                input_cache_read_tokens=input_cache_read,
                input_cache_write_tokens=input_cache_write,
                output_tokens=output,
            )
            db.add(row)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            await _increment_usage(
                db,
                user_id=user_id,
                usage_date=usage_date,
                model=model_name,
                input_uncached=input_uncached,
                input_cache_read=input_cache_read,
                input_cache_write=input_cache_write,
                output=output,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("Failed to record model usage")


async def _increment_usage(
    db,
    *,
    user_id: str,
    usage_date,
    model: str,
    input_uncached: int,
    input_cache_read: int,
    input_cache_write: int,
    output: int,
) -> bool:
    result = await db.execute(
        update(UserModelUsageDaily)
        .where(
            UserModelUsageDaily.user_id == user_id,
            UserModelUsageDaily.usage_date == usage_date,
            UserModelUsageDaily.model == model,
        )
        .values(
            call_count=UserModelUsageDaily.call_count + 1,
            input_uncached_tokens=UserModelUsageDaily.input_uncached_tokens + input_uncached,
            input_cache_read_tokens=UserModelUsageDaily.input_cache_read_tokens + input_cache_read,
            input_cache_write_tokens=UserModelUsageDaily.input_cache_write_tokens + input_cache_write,
            output_tokens=UserModelUsageDaily.output_tokens + output,
            updated_at=datetime.now(timezone.utc),
        )
    )
    return bool(result.rowcount)
