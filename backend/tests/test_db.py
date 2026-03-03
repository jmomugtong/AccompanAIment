"""Tests for database connection, session management, and schema validation."""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.db.models import (
    Base,
    Generation,
    Melody,
    Song,
    Style,
    User,
    UserFeedback,
)
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


class TestTableSchemaValidation:
    """Test that all required tables exist with correct columns."""

    EXPECTED_TABLES = {"users", "songs", "melodies", "generations", "user_feedback", "styles"}

    def test_all_tables_registered_in_metadata(self):
        table_names = set(Base.metadata.tables.keys())
        assert self.EXPECTED_TABLES.issubset(table_names)

    @pytest.mark.asyncio
    async def test_all_tables_created_in_database(self, async_engine):
        async with async_engine.connect() as conn:
            table_names = await conn.run_sync(
                lambda sync_conn: set(inspect(sync_conn).get_table_names())
            )
        assert self.EXPECTED_TABLES.issubset(table_names)

    @pytest.mark.asyncio
    async def test_users_table_columns(self, async_engine):
        async with async_engine.connect() as conn:
            columns = await conn.run_sync(
                lambda sync_conn: {
                    c["name"] for c in inspect(sync_conn).get_columns("users")
                }
            )
        expected = {"user_id", "email", "skill_level", "preferred_styles", "created_at", "updated_at"}
        assert expected.issubset(columns)

    @pytest.mark.asyncio
    async def test_songs_table_columns(self, async_engine):
        async with async_engine.connect() as conn:
            columns = await conn.run_sync(
                lambda sync_conn: {
                    c["name"] for c in inspect(sync_conn).get_columns("songs")
                }
            )
        expected = {
            "song_id", "user_id", "filename", "original_filename",
            "duration_seconds", "tempo_bpm", "uploaded_at", "deleted_at",
        }
        assert expected.issubset(columns)

    @pytest.mark.asyncio
    async def test_melodies_table_columns(self, async_engine):
        async with async_engine.connect() as conn:
            columns = await conn.run_sync(
                lambda sync_conn: {
                    c["name"] for c in inspect(sync_conn).get_columns("melodies")
                }
            )
        expected = {
            "melody_id", "song_id", "pitch_contour_json",
            "confidence_json", "timings_json", "duration_seconds", "created_at",
        }
        assert expected.issubset(columns)

    @pytest.mark.asyncio
    async def test_generations_table_columns(self, async_engine):
        async with async_engine.connect() as conn:
            columns = await conn.run_sync(
                lambda sync_conn: {
                    c["name"] for c in inspect(sync_conn).get_columns("generations")
                }
            )
        expected = {
            "generation_id", "song_id", "style", "midi_path",
            "audio_path", "sheet_path", "created_at",
        }
        assert expected.issubset(columns)

    @pytest.mark.asyncio
    async def test_user_feedback_table_columns(self, async_engine):
        async with async_engine.connect() as conn:
            columns = await conn.run_sync(
                lambda sync_conn: {
                    c["name"] for c in inspect(sync_conn).get_columns("user_feedback")
                }
            )
        expected = {
            "feedback_id", "generation_id", "user_id", "rating",
            "musicality_score", "style_match_score", "fit_to_melody_score",
            "comment", "created_at",
        }
        assert expected.issubset(columns)

    @pytest.mark.asyncio
    async def test_styles_table_columns(self, async_engine):
        async with async_engine.connect() as conn:
            columns = await conn.run_sync(
                lambda sync_conn: {
                    c["name"] for c in inspect(sync_conn).get_columns("styles")
                }
            )
        expected = {"style_id", "style_name", "description", "template_name", "created_at"}
        assert expected.issubset(columns)
