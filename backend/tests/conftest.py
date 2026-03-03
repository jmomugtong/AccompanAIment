"""Shared test fixtures for database testing."""

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base


def _enable_sqlite_fk(dbapi_conn, connection_record):
    """Enable foreign key enforcement in SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest_asyncio.fixture
async def async_engine():
    """Create an async in-memory SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    event.listen(engine.sync_engine, "connect", _enable_sqlite_fk)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create an async session bound to the test engine."""
    async_session_factory = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session


@pytest.fixture
def sample_chord_progression() -> str:
    """A simple chord progression for testing."""
    return "C | F | G | C"


@pytest.fixture
def sample_melody_data() -> dict:
    """Sample extracted melody data for testing."""
    return {
        "notes": [60, 62, 64, 65, 67, 69, 71, 72],
        "timings": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
        "confidence": [0.95, 0.92, 0.88, 0.91, 0.93, 0.90, 0.87, 0.94],
        "duration_seconds": 4.0,
    }
