from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import (
    create_access_token,
    decode_token,
    get_current_user,
    verify_password,
)
from dependencies.database import get_db
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> dict:
    return {
        "success": True,
        "user": {
            "user_id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "created_at": current_user.created_at.isoformat(),
        },
        "username": current_user.username,
        "user_id": current_user.id,
        "role": current_user.role,
    }


@router.post("/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(User).where(User.username == form.username.strip()))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = {"sub": user.id, "username": user.username, "role": user.role}
    token = create_access_token(token_payload)
    refresh = create_access_token(token_payload, refresh=True)
    return {
        "success": True,
        "access_token": token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "username": user.username,
        "user_id": user.id,
        "role": user.role,
        "user": {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
        },
    }


@router.post("/refresh")
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    old_token = auth_header[7:]

    try:
        payload = decode_token(old_token, expected_type="refresh")
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.get(User, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    token_payload = {"sub": user.id, "username": user.username, "role": user.role}
    token = create_access_token(token_payload)
    refresh = create_access_token(token_payload, refresh=True)
    return {
        "success": True,
        "access_token": token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "role": user.role,
    }
