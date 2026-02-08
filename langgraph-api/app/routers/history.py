"""History list, stats, and clear endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Generation, Post, User
from app.schemas import DashboardStats, GenerationHistoryResponse, PostResponse

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/", response_model=list[GenerationHistoryResponse])
async def list_history(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Generation)
        .where(Generation.user_id == user.id)
        .options(selectinload(Generation.posts))
        .order_by(Generation.created_at.desc())
        .limit(min(limit, 200))
    )
    generations = result.scalars().all()
    return [_gen_to_response(g) for g in generations]


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Count generations
    gen_count_result = await db.execute(
        select(func.count(Generation.id)).where(Generation.user_id == user.id)
    )
    total_generations = gen_count_result.scalar() or 0

    # Count posts and avg score
    post_result = await db.execute(
        select(func.count(Post.id), func.avg(Post.critic_score))
        .join(Generation, Post.generation_id == Generation.id)
        .where(Generation.user_id == user.id)
    )
    row = post_result.one()
    total_posts = row[0] or 0
    avg_score = round(row[1], 1) if row[1] else 0

    return DashboardStats(
        total_generations=total_generations,
        total_posts=total_posts,
        avg_critic_score=avg_score,
    )


@router.delete("/", status_code=204)
async def clear_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Delete posts first (via cascade), then generations
    gen_ids_result = await db.execute(
        select(Generation.id).where(Generation.user_id == user.id)
    )
    gen_ids = [r[0] for r in gen_ids_result.all()]
    if gen_ids:
        await db.execute(delete(Post).where(Post.generation_id.in_(gen_ids)))
        await db.execute(delete(Generation).where(Generation.user_id == user.id))
        await db.commit()


def _gen_to_response(g: Generation) -> GenerationHistoryResponse:
    return GenerationHistoryResponse(
        id=g.id,
        thread_id=g.thread_id,
        content_request=g.content_request,
        brand_name=g.brand_name,
        status=g.status,
        revision_count=g.revision_count,
        critic_summary=g.critic_summary,
        created_at=g.created_at.isoformat() if g.created_at else "",
        posts=[
            PostResponse(
                id=p.id,
                platform=p.platform,
                content=p.content,
                hashtags=p.hashtags,
                call_to_action=p.call_to_action,
                content_type=p.content_type,
                image_prompt=p.image_prompt,
                critic_score=p.critic_score,
            )
            for p in g.posts
        ],
    )
