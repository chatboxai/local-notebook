from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import get_current_admin, hash_password
from dependencies.database import get_db
from models.user import User
from models.usage import UserModelUsageDaily
from schemas.admin import (
    AdminPasswordReset,
    AdminUsageResponse,
    AdminUsageRow,
    AdminUsageTotals,
    AdminUserCreate,
    AdminUserListResponse,
    AdminUserResponse,
)
from services.usage_service import current_usage_date

router = APIRouter(prefix="/admin", tags=["admin"])


def _serialize_user(user: User) -> AdminUserResponse:
    return AdminUserResponse(
        user_id=user.id,
        username=user.username,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


async def _get_user_or_404(db: AsyncSession, user_id: str) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminUserListResponse:
    result = await db.execute(
        select(User)
        .order_by(User.role.desc(), User.created_at.asc())
    )
    users = result.scalars().all()
    return AdminUserListResponse(
        users=[_serialize_user(user) for user in users],
        total=len(users),
    )


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminUserResponse:
    username = body.username.strip()
    if len(username) < 2:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username must be at least 2 characters")

    existing = await db.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    user = User(
        username=username,
        password_hash=hash_password(body.password),
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _serialize_user(user)


@router.get("/usage", response_model=AdminUsageResponse)
async def list_usage(
    start_date: date | None = None,
    end_date: date | None = None,
    user_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminUsageResponse:
    today = current_usage_date()
    start = start_date or (today - timedelta(days=29))
    end = end_date or today
    if start > end:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="start_date must be before end_date")

    query = (
        select(UserModelUsageDaily, User.username)
        .join(User, UserModelUsageDaily.user_id == User.id)
        .where(
            UserModelUsageDaily.usage_date >= start,
            UserModelUsageDaily.usage_date <= end,
        )
        .order_by(
            UserModelUsageDaily.usage_date.desc(),
            User.username.asc(),
            UserModelUsageDaily.model.asc(),
        )
    )
    if user_id:
        query = query.where(UserModelUsageDaily.user_id == user_id)

    result = await db.execute(query)
    rows: list[AdminUsageRow] = []
    totals = {
        "call_count": 0,
        "input_uncached_tokens": 0,
        "input_cache_read_tokens": 0,
        "input_cache_write_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }

    for usage, username in result.all():
        total_tokens = (
            usage.input_uncached_tokens
            + usage.input_cache_read_tokens
            + usage.input_cache_write_tokens
            + usage.output_tokens
        )
        row = AdminUsageRow(
            usage_date=usage.usage_date,
            user_id=usage.user_id,
            username=username,
            model=usage.model,
            call_count=usage.call_count,
            input_uncached_tokens=usage.input_uncached_tokens,
            input_cache_read_tokens=usage.input_cache_read_tokens,
            input_cache_write_tokens=usage.input_cache_write_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=total_tokens,
        )
        rows.append(row)
        totals["call_count"] += usage.call_count
        totals["input_uncached_tokens"] += usage.input_uncached_tokens
        totals["input_cache_read_tokens"] += usage.input_cache_read_tokens
        totals["input_cache_write_tokens"] += usage.input_cache_write_tokens
        totals["output_tokens"] += usage.output_tokens
        totals["total_tokens"] += total_tokens

    return AdminUsageResponse(
        rows=rows,
        totals=AdminUsageTotals(**totals),
    )


@router.post("/users/{user_id}/password")
async def reset_user_password(
    user_id: str,
    body: AdminPasswordReset,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> dict:
    user = await _get_user_or_404(db, user_id)
    user.password_hash = hash_password(body.new_password)
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"success": True, "message": "Password reset"}
