from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

import config
from dependencies.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from dependencies.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_me(username: str = Depends(get_current_user)) -> dict:
    return {"username": username, "user_id": username}


@router.post("/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stored_username = await config.get_setting("auth_username", "admin")
    stored_hash = await config.get_setting("auth_password_hash")

    if form.username != stored_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if stored_hash is None:
        new_hash = hash_password(form.password)
        await config.set_many(
            {"auth_password_hash": new_hash},
            db,
        )
    elif not verify_password(form.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": form.username})
    refresh = create_access_token({"sub": form.username}, refresh=True)
    return {
        "success": True,
        "access_token": token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "username": form.username,
        "user_id": form.username,
    }


@router.post("/refresh")
async def refresh_token(request: Request) -> dict:
    from jose import JWTError, jwt as jose_jwt
    from dependencies.auth import SECRET_KEY, ALGORITHM

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    old_token = auth_header[7:]

    try:
        payload = jose_jwt.decode(
            old_token, SECRET_KEY, algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    token = create_access_token({"sub": username})
    refresh = create_access_token({"sub": username}, refresh=True)
    return {
        "success": True,
        "access_token": token,
        "refresh_token": refresh,
        "token_type": "bearer",
    }
