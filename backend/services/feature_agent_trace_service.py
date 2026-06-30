import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete as sa_delete, select

from database import AsyncSessionLocal
from models.feature_agent_trace import FeatureAgentTrace

logger = logging.getLogger(__name__)

DEFAULT_TRACE_TTL_HOURS = float(os.getenv("FEATURE_AGENT_TRACE_TTL_HOURS", "6"))
TRACE_SCHEMA_VERSION = 1


def _expires_at(ttl_hours: float | None = None) -> datetime:
    hours = DEFAULT_TRACE_TTL_HOURS if ttl_hours is None else ttl_hours
    return datetime.now(timezone.utc) + timedelta(hours=max(0.1, float(hours)))


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump(mode="json", exclude_none=True))
    if hasattr(value, "__dict__"):
        return _jsonable(vars(value))
    return str(value)


async def upsert_feature_agent_trace(
    *,
    workflow_id: str,
    feature_id: str,
    phase: str,
    status: str,
    payload: dict[str, Any],
    ttl_hours: float | None = None,
) -> None:
    if not workflow_id or not feature_id:
        return

    now = datetime.now(timezone.utc)
    normalized_payload = {
        "schema_version": TRACE_SCHEMA_VERSION,
        **_jsonable(payload),
    }

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FeatureAgentTrace).where(
                FeatureAgentTrace.feature_id == feature_id,
                FeatureAgentTrace.phase == phase,
            )
        )
        trace = result.scalar_one_or_none()
        if trace is None:
            trace = FeatureAgentTrace(
                workflow_id=workflow_id,
                feature_id=feature_id,
                phase=phase,
                status=status,
                payload=FeatureAgentTrace.pack_payload(normalized_payload),
                expires_at=_expires_at(ttl_hours),
                created_at=now,
                updated_at=now,
            )
            db.add(trace)
        else:
            trace.workflow_id = workflow_id
            trace.status = status
            trace.set_payload(normalized_payload)
            trace.expires_at = _expires_at(ttl_hours)
            trace.updated_at = now
        await db.commit()


async def get_feature_agent_trace(
    *,
    feature_id: str,
    phase: str = "draft",
) -> dict[str, Any] | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FeatureAgentTrace).where(
                FeatureAgentTrace.feature_id == feature_id,
                FeatureAgentTrace.phase == phase,
            )
        )
        trace = result.scalar_one_or_none()
        if trace is None:
            return None
        return trace.get_payload()


async def cleanup_expired_feature_agent_traces() -> int:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            sa_delete(FeatureAgentTrace).where(
                FeatureAgentTrace.expires_at.is_not(None),
                FeatureAgentTrace.expires_at < now,
            )
        )
        await db.commit()
        deleted = int(result.rowcount or 0)
        if deleted:
            logger.info("Deleted %d expired feature agent trace(s)", deleted)
        return deleted
