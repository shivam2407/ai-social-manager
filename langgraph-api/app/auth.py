"""Password hashing, JWT creation/verification, OAuth helpers, and auth dependencies."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")

security = HTTPBearer()

# Cache for Google JWKS keys
_google_jwks_cache: dict | None = None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# OAuth helpers
# ---------------------------------------------------------------------------

async def _get_google_jwks() -> dict:
    """Fetch and cache Google's public JWKS for ID token verification."""
    global _google_jwks_cache
    if _google_jwks_cache is not None:
        return _google_jwks_cache
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://www.googleapis.com/oauth2/v3/certs")
        resp.raise_for_status()
        _google_jwks_cache = resp.json()
    return _google_jwks_cache


async def verify_google_id_token(id_token: str) -> dict:
    """Decode and verify a Google ID token. Returns {email, sub, email_verified}."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    keys_data = await _get_google_jwks()

    # Get the key id from the token header
    try:
        header = jwt.get_unverified_header(id_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Google ID token")

    kid = header.get("kid")
    # Find the matching key
    rsa_key = None
    for key in keys_data.get("keys", []):
        if key["kid"] == kid:
            rsa_key = key
            break

    if rsa_key is None:
        # Invalidate cache and retry once
        global _google_jwks_cache
        _google_jwks_cache = None
        keys_data = await _get_google_jwks()
        for key in keys_data.get("keys", []):
            if key["kid"] == kid:
                rsa_key = key
                break

    if rsa_key is None:
        raise HTTPException(status_code=401, detail="Unable to verify Google ID token")

    try:
        payload = jwt.decode(
            id_token,
            rsa_key,
            algorithms=["RS256"],
            audience=GOOGLE_CLIENT_ID,
            issuer=["https://accounts.google.com", "accounts.google.com"],
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Google ID token")

    if not payload.get("email_verified", False):
        raise HTTPException(status_code=401, detail="Google email not verified")

    return {
        "email": payload["email"],
        "sub": payload["sub"],
        "email_verified": payload.get("email_verified", False),
    }


async def exchange_github_code(code: str) -> dict:
    """Exchange a GitHub OAuth code for user profile info. Returns {email, github_id}."""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")

    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=401, detail="GitHub OAuth failed")

        gh_headers = {"Authorization": f"Bearer {access_token}"}

        # Get user profile
        user_resp = await client.get("https://api.github.com/user", headers=gh_headers)
        user_data = user_resp.json()
        github_id = str(user_data.get("id", ""))

        # Get primary email
        email = user_data.get("email")
        if not email:
            emails_resp = await client.get(
                "https://api.github.com/user/emails", headers=gh_headers
            )
            for em in emails_resp.json():
                if em.get("primary") and em.get("verified"):
                    email = em["email"]
                    break

        if not email:
            raise HTTPException(
                status_code=401, detail="No verified email found on GitHub account"
            )

    return {"email": email, "github_id": github_id}


async def get_or_create_oauth_user(
    db: AsyncSession, email: str, provider: str, provider_id: str
) -> User:
    """Find existing user by email or create a new OAuth user."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        # Link OAuth provider if not yet linked
        if not user.auth_provider:
            user.auth_provider = provider
            user.auth_provider_id = provider_id
            await db.commit()
            await db.refresh(user)
        return user

    # Create new OAuth user (no password)
    user = User(
        email=email,
        hashed_password=None,
        auth_provider=provider,
        auth_provider_id=provider_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
