"""Async PostgreSQL connection, engine, and session factory."""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings

_engine_cache: dict[str, AsyncEngine] = {}


def get_async_engine(url: str | None = None) -> AsyncEngine:
    """Create or retrieve a cached async engine for the given URL.

    Args:
        url: Database URL. Defaults to settings.database_url.

    Returns:
        An AsyncEngine instance, cached per URL.
    """
    db_url = url or settings.database_url
    if db_url not in _engine_cache:
        _engine_cache[db_url] = create_async_engine(
            db_url,
            echo=settings.debug,
            pool_pre_ping=True,
        )
    return _engine_cache[db_url]


def get_async_session_factory(
    engine: AsyncEngine | None = None,
) -> sessionmaker:
    """Create an async session factory.

    Args:
        engine: AsyncEngine to bind. Defaults to the engine from settings.

    Returns:
        A sessionmaker configured for AsyncSession.
    """
    eng = engine or get_async_engine()
    return sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
