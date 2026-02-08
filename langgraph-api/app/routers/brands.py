"""Brand profile CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import BrandProfileDB, User
from app.schemas import BrandProfileCreate, BrandProfileResponse

router = APIRouter(prefix="/api/brands", tags=["brands"])


@router.get("/", response_model=list[BrandProfileResponse])
async def list_brands(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BrandProfileDB)
        .where(BrandProfileDB.user_id == user.id)
        .order_by(BrandProfileDB.updated_at.desc())
    )
    return [_to_response(bp) for bp in result.scalars().all()]


@router.post("/", response_model=BrandProfileResponse, status_code=201)
async def create_brand(
    body: BrandProfileCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bp = BrandProfileDB(user_id=user.id, **body.model_dump())
    db.add(bp)
    await db.commit()
    await db.refresh(bp)
    return _to_response(bp)


@router.put("/{brand_id}", response_model=BrandProfileResponse)
async def update_brand(
    brand_id: int,
    body: BrandProfileCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bp = await _get_brand_or_404(brand_id, user.id, db)
    for key, value in body.model_dump().items():
        setattr(bp, key, value)
    await db.commit()
    await db.refresh(bp)
    return _to_response(bp)


@router.delete("/{brand_id}", status_code=204)
async def delete_brand(
    brand_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bp = await _get_brand_or_404(brand_id, user.id, db)
    await db.delete(bp)
    await db.commit()


async def _get_brand_or_404(brand_id: int, user_id: int, db: AsyncSession) -> BrandProfileDB:
    result = await db.execute(
        select(BrandProfileDB).where(
            BrandProfileDB.id == brand_id,
            BrandProfileDB.user_id == user_id,
        )
    )
    bp = result.scalar_one_or_none()
    if not bp:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    return bp


def _to_response(bp: BrandProfileDB) -> BrandProfileResponse:
    return BrandProfileResponse(
        id=bp.id,
        brand_name=bp.brand_name,
        niche=bp.niche,
        target_audience=bp.target_audience,
        voice_description=bp.voice_description,
        tone_keywords=bp.tone_keywords,
        example_posts=bp.example_posts,
        created_at=bp.created_at.isoformat() if bp.created_at else "",
        updated_at=bp.updated_at.isoformat() if bp.updated_at else "",
    )
