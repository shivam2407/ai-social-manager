"""Async SQLAlchemy engine, session factory, and DB helpers."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Detect database URL: prefer PostgreSQL from env, fall back to local SQLite
_raw_url = os.environ.get("DATABASE_URL", "")

if _raw_url.startswith("postgres://") or _raw_url.startswith("postgresql://"):
    # Convert to async driver URL (Neon / Render provide postgresql:// URLs)
    DATABASE_URL = _raw_url.replace("postgresql://", "postgresql+asyncpg://", 1).replace(
        "postgres://", "postgresql+asyncpg://", 1
    )
    engine = create_async_engine(DATABASE_URL, echo=False)
else:
    # Local dev: SQLite in langgraph-api/data/app.db
    _data_dir = Path(__file__).resolve().parent.parent / "data"
    _data_dir.mkdir(exist_ok=True)
    DATABASE_URL = f"sqlite+aiosqlite:///{_data_dir / 'app.db'}"
    engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Create all tables if they don't exist."""
    from app.models import Base as _  # noqa: F401 – ensure models are registered

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """FastAPI dependency that yields an async DB session."""
    async with async_session() as session:
        yield session
