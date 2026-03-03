"""Tests for database connection, session management, and schema validation."""

import pytest
from sqlalchemy import DateTime, Float, Integer, String, Text, inspect, text
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


class TestColumnTypeValidation:
    """Test that columns have correct types, especially JSONB fields."""

    def _get_column_type(self, model, column_name: str) -> type:
        """Get the SQLAlchemy type class for a model column."""
        col = model.__table__.columns[column_name]
        return type(col.type)

    def test_user_id_is_string(self):
        assert self._get_column_type(User, "user_id") is String

    def test_user_email_is_string(self):
        assert self._get_column_type(User, "email") is String

    def test_user_email_max_length_255(self):
        col = User.__table__.columns["email"]
        assert col.type.length == 255

    def test_song_duration_is_float(self):
        assert self._get_column_type(Song, "duration_seconds") is Float

    def test_song_tempo_is_float(self):
        assert self._get_column_type(Song, "tempo_bpm") is Float

    def test_melody_pitch_contour_is_jsonb_on_postgres(self):
        """Melody JSONB columns use JSONB on Postgres, Text variant on SQLite."""
        from sqlalchemy.dialects.postgresql import JSONB

        col = Melody.__table__.columns["pitch_contour_json"]
        assert isinstance(col.type, JSONB)

    def test_melody_confidence_is_jsonb_on_postgres(self):
        from sqlalchemy.dialects.postgresql import JSONB

        col = Melody.__table__.columns["confidence_json"]
        assert isinstance(col.type, JSONB)

    def test_melody_timings_is_jsonb_on_postgres(self):
        from sqlalchemy.dialects.postgresql import JSONB

        col = Melody.__table__.columns["timings_json"]
        assert isinstance(col.type, JSONB)

    def test_feedback_rating_is_integer(self):
        assert self._get_column_type(UserFeedback, "rating") is Integer

    def test_feedback_scores_are_integer(self):
        for col_name in ("musicality_score", "style_match_score", "fit_to_melody_score"):
            assert self._get_column_type(UserFeedback, col_name) is Integer

    def test_feedback_comment_is_text(self):
        assert self._get_column_type(UserFeedback, "comment") is Text

    def test_style_name_max_length_100(self):
        col = Style.__table__.columns["style_name"]
        assert col.type.length == 100

    def test_generation_style_max_length_50(self):
        col = Generation.__table__.columns["style"]
        assert col.type.length == 50

    def test_timestamp_columns_are_datetime(self):
        assert self._get_column_type(User, "created_at") is DateTime
        assert self._get_column_type(Song, "uploaded_at") is DateTime
        assert self._get_column_type(Song, "deleted_at") is DateTime
