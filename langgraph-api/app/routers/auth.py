"""Auth endpoints: register, login, OAuth, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    create_access_token,
    exchange_github_code,
    get_current_user,
    get_or_create_oauth_user,
    hash_password,
    verify_google_id_token,
    verify_password,
)
from app.database import get_db
from app.models import User
from app.schemas import (
    GitHubAuthRequest,
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, user=UserResponse(id=user.id, email=user.email, onboarding_completed=user.onboarding_completed))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, user=UserResponse(id=user.id, email=user.email, onboarding_completed=user.onboarding_completed))


@router.post("/google", response_model=TokenResponse)
async def google_auth(body: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    info = await verify_google_id_token(body.id_token)
    user = await get_or_create_oauth_user(db, info["email"], "google", info["sub"])
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, user=UserResponse(id=user.id, email=user.email, onboarding_completed=user.onboarding_completed))


@router.post("/github", response_model=TokenResponse)
async def github_auth(body: GitHubAuthRequest, db: AsyncSession = Depends(get_db)):
    info = await exchange_github_code(body.code)
    user = await get_or_create_oauth_user(db, info["email"], "github", info["github_id"])
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, user=UserResponse(id=user.id, email=user.email, onboarding_completed=user.onboarding_completed))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse(id=user.id, email=user.email, onboarding_completed=user.onboarding_completed)
