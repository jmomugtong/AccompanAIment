"""Tests for database connection and session management."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.db.postgres import get_async_engine, get_async_session_factory


class TestAsyncEngineCreation:
    """Test async engine creation and configuration."""

    def test_get_async_engine_returns_engine(self):
        engine = get_async_engine("sqlite+aiosqlite:///:memory:")
        assert isinstance(engine, AsyncEngine)

    def test_get_async_engine_caches_same_url(self):
        url = "sqlite+aiosqlite:///:memory:"
        engine1 = get_async_engine(url)
        engine2 = get_async_engine(url)
        assert engine1 is engine2

    def test_get_async_engine_different_urls_return_different_engines(self):
        engine1 = get_async_engine("sqlite+aiosqlite:///test1.db")
        engine2 = get_async_engine("sqlite+aiosqlite:///test2.db")
        assert engine1 is not engine2


class TestAsyncSessionFactory:
    """Test async session factory creation."""

    def test_get_session_factory_returns_callable(self):
        engine = get_async_engine("sqlite+aiosqlite:///:memory:")
        factory = get_async_session_factory(engine)
        assert callable(factory)


class TestAsyncSessionConnectivity:
    """Test actual async database connectivity."""

    @pytest.mark.asyncio
    async def test_session_can_execute_query(self, async_session: AsyncSession):
        result = await async_session.execute(text("SELECT 1"))
        row = result.scalar()
        assert row == 1

    @pytest.mark.asyncio
    async def test_session_is_async_session_instance(self, async_session):
        assert isinstance(async_session, AsyncSession)

    @pytest.mark.asyncio
    async def test_engine_connects_successfully(self, async_engine):
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
