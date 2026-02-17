"""Settings router — CRUD for user API keys and provider info."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.encryption import decrypt_api_key, encrypt_api_key
from app.llm_factory import create_llm
from app.models import User, UserApiKey
from app.schemas import (
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyTestRequest,
    ApiKeyTestResponse,
    PROVIDER_DEFAULT_MODELS,
    PROVIDER_MODELS,
    ProviderInfo,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _mask_key(encrypted_key: str) -> str:
    """Show only last 4 characters of the decrypted key."""
    try:
        plain = decrypt_api_key(encrypted_key)
        return f"...{plain[-4:]}" if len(plain) >= 4 else "****"
    except Exception:
        return "****"


def _to_response(row: UserApiKey) -> ApiKeyResponse:
    return ApiKeyResponse(
        provider=row.provider,
        model=row.model,
        is_default=row.is_default,
        key_hint=_mask_key(row.encrypted_api_key),
        created_at=row.created_at.isoformat() if row.created_at else "",
        updated_at=row.updated_at.isoformat() if row.updated_at else "",
    )


@router.get("/providers", response_model=list[ProviderInfo])
async def list_providers():
    return [
        ProviderInfo(provider=p, models=models, default_model=PROVIDER_DEFAULT_MODELS[p])
        for p, models in PROVIDER_MODELS.items()
    ]


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserApiKey).where(UserApiKey.user_id == user.id)
    )
    return [_to_response(row) for row in result.scalars().all()]


@router.post("/api-keys", response_model=ApiKeyResponse)
async def upsert_api_key(
    body: ApiKeyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    provider = body.provider.value
    model = body.model or PROVIDER_DEFAULT_MODELS[provider]

    # Validate model
    if model not in PROVIDER_MODELS[provider]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model '{model}' for provider '{provider}'. "
                   f"Allowed: {PROVIDER_MODELS[provider]}",
        )

    # Check for existing key for this provider
    result = await db.execute(
        select(UserApiKey).where(
            UserApiKey.user_id == user.id,
            UserApiKey.provider == provider,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        if body.api_key:
            existing.encrypted_api_key = encrypt_api_key(body.api_key)
        existing.model = model
        existing.is_default = body.is_default
    else:
        if not body.api_key:
            raise HTTPException(status_code=400, detail="API key is required for new providers")
        existing = UserApiKey(
            user_id=user.id,
            provider=provider,
            encrypted_api_key=encrypt_api_key(body.api_key),
            model=model,
            is_default=body.is_default,
        )
        db.add(existing)

    # If marking as default, clear other defaults
    if body.is_default:
        others = await db.execute(
            select(UserApiKey).where(
                UserApiKey.user_id == user.id,
                UserApiKey.provider != provider,
            )
        )
        for other in others.scalars().all():
            other.is_default = False

    await db.commit()
    await db.refresh(existing)
    return _to_response(existing)


@router.delete("/api-keys/{provider}", status_code=204)
async def delete_api_key(
    provider: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserApiKey).where(
            UserApiKey.user_id == user.id,
            UserApiKey.provider == provider,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(row)
    await db.commit()


@router.post("/api-keys/test", response_model=ApiKeyTestResponse)
async def test_api_key(body: ApiKeyTestRequest):
    provider = body.provider.value
    model = body.model or PROVIDER_DEFAULT_MODELS[provider]

    if model not in PROVIDER_MODELS[provider]:
        return ApiKeyTestResponse(success=False, message=f"Invalid model: {model}")

    if provider == "mock":
        return ApiKeyTestResponse(success=True, message="Mock provider — always works")

    try:
        llm = create_llm(
            provider=provider,
            api_key=body.api_key,
            model=model,
            agent_name="test",
        )
        response = await llm.ainvoke("Say 'ok' and nothing else.")
        if response and response.content:
            return ApiKeyTestResponse(success=True, message="API key is valid")
        return ApiKeyTestResponse(success=False, message="Empty response from provider")
    except Exception as e:
        logger.warning("API key test failed for %s: %s", provider, e)
        return ApiKeyTestResponse(success=False, message=f"Key validation failed: {e}")
