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


class TestCRUDOperations:
    """Test create, read, update, delete for each model."""

    @pytest.mark.asyncio
    async def test_create_and_read_user(self, async_session):
        user = User(user_id="u1", email="test@example.com", skill_level="intermediate")
        async_session.add(user)
        await async_session.commit()

        from sqlalchemy import select

        result = await async_session.execute(select(User).where(User.user_id == "u1"))
        fetched = result.scalar_one()
        assert fetched.email == "test@example.com"
        assert fetched.skill_level == "intermediate"

    @pytest.mark.asyncio
    async def test_update_user(self, async_session):
        user = User(user_id="u2", email="update@example.com")
        async_session.add(user)
        await async_session.commit()

        user.skill_level = "advanced"
        await async_session.commit()

        from sqlalchemy import select

        result = await async_session.execute(select(User).where(User.user_id == "u2"))
        fetched = result.scalar_one()
        assert fetched.skill_level == "advanced"

    @pytest.mark.asyncio
    async def test_delete_user(self, async_session):
        user = User(user_id="u3", email="delete@example.com")
        async_session.add(user)
        await async_session.commit()

        await async_session.delete(user)
        await async_session.commit()

        from sqlalchemy import select

        result = await async_session.execute(select(User).where(User.user_id == "u3"))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_create_and_read_song(self, async_session):
        user = User(user_id="u4", email="song@example.com")
        async_session.add(user)
        await async_session.commit()

        song = Song(
            song_id="s1",
            user_id="u4",
            filename="processed.wav",
            original_filename="my_song.mp3",
            duration_seconds=180.5,
            tempo_bpm=120.0,
        )
        async_session.add(song)
        await async_session.commit()

        from sqlalchemy import select

        result = await async_session.execute(select(Song).where(Song.song_id == "s1"))
        fetched = result.scalar_one()
        assert fetched.original_filename == "my_song.mp3"
        assert fetched.duration_seconds == 180.5

    @pytest.mark.asyncio
    async def test_create_and_read_melody(self, async_session):
        user = User(user_id="u5", email="melody@example.com")
        song = Song(
            song_id="s2", user_id="u5", filename="f.wav", original_filename="f.mp3"
        )
        async_session.add_all([user, song])
        await async_session.commit()

        melody = Melody(
            melody_id="m1",
            song_id="s2",
            pitch_contour_json='[60, 62, 64]',
            confidence_json='[0.9, 0.8, 0.7]',
            timings_json='[0.0, 0.5, 1.0]',
            duration_seconds=1.5,
        )
        async_session.add(melody)
        await async_session.commit()

        from sqlalchemy import select

        result = await async_session.execute(
            select(Melody).where(Melody.melody_id == "m1")
        )
        fetched = result.scalar_one()
        assert fetched.duration_seconds == 1.5

    @pytest.mark.asyncio
    async def test_create_and_read_generation(self, async_session):
        user = User(user_id="u6", email="gen@example.com")
        song = Song(
            song_id="s3", user_id="u6", filename="g.wav", original_filename="g.mp3"
        )
        async_session.add_all([user, song])
        await async_session.commit()

        gen = Generation(
            generation_id="g1",
            song_id="s3",
            style="jazz",
            midi_path="/data/g1.mid",
        )
        async_session.add(gen)
        await async_session.commit()

        from sqlalchemy import select

        result = await async_session.execute(
            select(Generation).where(Generation.generation_id == "g1")
        )
        fetched = result.scalar_one()
        assert fetched.style == "jazz"

    @pytest.mark.asyncio
    async def test_create_and_read_feedback(self, async_session):
        user = User(user_id="u7", email="fb@example.com")
        song = Song(
            song_id="s4", user_id="u7", filename="fb.wav", original_filename="fb.mp3"
        )
        gen = Generation(generation_id="g2", song_id="s4", style="pop")
        async_session.add_all([user, song, gen])
        await async_session.commit()

        fb = UserFeedback(
            feedback_id="f1",
            generation_id="g2",
            user_id="u7",
            rating=5,
            musicality_score=4,
            style_match_score=5,
            fit_to_melody_score=4,
            comment="Sounds great",
        )
        async_session.add(fb)
        await async_session.commit()

        from sqlalchemy import select

        result = await async_session.execute(
            select(UserFeedback).where(UserFeedback.feedback_id == "f1")
        )
        fetched = result.scalar_one()
        assert fetched.rating == 5
        assert fetched.comment == "Sounds great"

    @pytest.mark.asyncio
    async def test_create_and_read_style(self, async_session):
        style = Style(
            style_id="st1",
            style_name="jazz",
            description="Jazz style with extensions and syncopation",
            template_name="jazz_template",
        )
        async_session.add(style)
        await async_session.commit()

        from sqlalchemy import select

        result = await async_session.execute(
            select(Style).where(Style.style_id == "st1")
        )
        fetched = result.scalar_one()
        assert fetched.style_name == "jazz"

    @pytest.mark.asyncio
    async def test_update_generation(self, async_session):
        user = User(user_id="u8", email="upgen@example.com")
        song = Song(
            song_id="s5", user_id="u8", filename="ug.wav", original_filename="ug.mp3"
        )
        gen = Generation(generation_id="g3", song_id="s5", style="pop")
        async_session.add_all([user, song, gen])
        await async_session.commit()

        gen.audio_path = "/data/g3.wav"
        gen.sheet_path = "/data/g3.pdf"
        await async_session.commit()

        from sqlalchemy import select

        result = await async_session.execute(
            select(Generation).where(Generation.generation_id == "g3")
        )
        fetched = result.scalar_one()
        assert fetched.audio_path == "/data/g3.wav"
        assert fetched.sheet_path == "/data/g3.pdf"

    @pytest.mark.asyncio
    async def test_delete_generation(self, async_session):
        user = User(user_id="u9", email="delgen@example.com")
        song = Song(
            song_id="s6", user_id="u9", filename="dg.wav", original_filename="dg.mp3"
        )
        gen = Generation(generation_id="g4", song_id="s6", style="classical")
        async_session.add_all([user, song, gen])
        await async_session.commit()

        await async_session.delete(gen)
        await async_session.commit()

        from sqlalchemy import select

        result = await async_session.execute(
            select(Generation).where(Generation.generation_id == "g4")
        )
        assert result.scalar_one_or_none() is None


class TestForeignKeyRelationships:
    """Test foreign key constraints and ORM relationships."""

    @pytest.mark.asyncio
    async def test_song_belongs_to_user_via_relationship(self, async_session):
        user = User(user_id="fk1", email="fk1@example.com")
        song = Song(
            song_id="fks1", user_id="fk1", filename="a.wav", original_filename="a.mp3"
        )
        async_session.add_all([user, song])
        await async_session.commit()

        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await async_session.execute(
            select(User).where(User.user_id == "fk1").options(selectinload(User.songs))
        )
        fetched = result.scalar_one()
        assert len(fetched.songs) == 1
        assert fetched.songs[0].song_id == "fks1"

    @pytest.mark.asyncio
    async def test_melody_belongs_to_song(self, async_session):
        user = User(user_id="fk2", email="fk2@example.com")
        song = Song(
            song_id="fks2", user_id="fk2", filename="b.wav", original_filename="b.mp3"
        )
        melody = Melody(melody_id="fkm1", song_id="fks2", duration_seconds=3.0)
        async_session.add_all([user, song, melody])
        await async_session.commit()

        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await async_session.execute(
            select(Song).where(Song.song_id == "fks2").options(selectinload(Song.melodies))
        )
        fetched = result.scalar_one()
        assert len(fetched.melodies) == 1

    @pytest.mark.asyncio
    async def test_generation_belongs_to_song(self, async_session):
        user = User(user_id="fk3", email="fk3@example.com")
        song = Song(
            song_id="fks3", user_id="fk3", filename="c.wav", original_filename="c.mp3"
        )
        gen = Generation(generation_id="fkg1", song_id="fks3", style="jazz")
        async_session.add_all([user, song, gen])
        await async_session.commit()

        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await async_session.execute(
            select(Song)
            .where(Song.song_id == "fks3")
            .options(selectinload(Song.generations))
        )
        fetched = result.scalar_one()
        assert len(fetched.generations) == 1

    @pytest.mark.asyncio
    async def test_feedback_belongs_to_generation_and_user(self, async_session):
        user = User(user_id="fk4", email="fk4@example.com")
        song = Song(
            song_id="fks4", user_id="fk4", filename="d.wav", original_filename="d.mp3"
        )
        gen = Generation(generation_id="fkg2", song_id="fks4", style="pop")
        fb = UserFeedback(
            feedback_id="fkf1", generation_id="fkg2", user_id="fk4", rating=4
        )
        async_session.add_all([user, song, gen, fb])
        await async_session.commit()

        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await async_session.execute(
            select(Generation)
            .where(Generation.generation_id == "fkg2")
            .options(selectinload(Generation.feedbacks))
        )
        fetched = result.scalar_one()
        assert len(fetched.feedbacks) == 1
        assert fetched.feedbacks[0].user_id == "fk4"

    @pytest.mark.asyncio
    async def test_song_fk_constraint_requires_valid_user(self, async_session):
        """Inserting a song with a nonexistent user_id raises IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        song = Song(
            song_id="bad1",
            user_id="nonexistent",
            filename="x.wav",
            original_filename="x.mp3",
        )
        async_session.add(song)
        with pytest.raises(IntegrityError):
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_feedback_fk_constraint_requires_valid_generation(self, async_session):
        """Inserting feedback with a nonexistent generation_id raises IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        user = User(user_id="fk5", email="fk5@example.com")
        async_session.add(user)
        await async_session.commit()

        fb = UserFeedback(
            feedback_id="badfb",
            generation_id="nonexistent",
            user_id="fk5",
            rating=3,
        )
        async_session.add(fb)
        with pytest.raises(IntegrityError):
            await async_session.commit()
