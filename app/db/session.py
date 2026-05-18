from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.database_url, future=True)


def create_session_factory(
    settings: Settings,
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    engine = engine or create_engine(settings)
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
