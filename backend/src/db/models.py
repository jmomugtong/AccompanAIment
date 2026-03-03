"""SQLAlchemy ORM models for AccompanAIment."""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


def _generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    skill_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferred_styles: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    songs: Mapped[list["Song"]] = relationship(back_populates="user")
    feedbacks: Mapped[list["UserFeedback"]] = relationship(back_populates="user")


class Song(Base):
    __tablename__ = "songs"

    song_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.user_id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    tempo_bpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="songs")
    melodies: Mapped[list["Melody"]] = relationship(back_populates="song")
    generations: Mapped[list["Generation"]] = relationship(back_populates="song")

    __table_args__ = (
        Index("ix_songs_user_id", "user_id"),
        Index("ix_songs_uploaded_at", "uploaded_at"),
    )


class Melody(Base):
    __tablename__ = "melodies"

    melody_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    song_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("songs.song_id"), nullable=False
    )
    pitch_contour_json: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(Text, "sqlite"), nullable=True
    )
    confidence_json: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(Text, "sqlite"), nullable=True
    )
    timings_json: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(Text, "sqlite"), nullable=True
    )
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    song: Mapped["Song"] = relationship(back_populates="melodies")

    __table_args__ = (Index("ix_melodies_song_id", "song_id"),)


class Generation(Base):
    __tablename__ = "generations"

    generation_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    song_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("songs.song_id"), nullable=False
    )
    style: Mapped[str] = mapped_column(String(50), nullable=False)
    midi_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sheet_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    song: Mapped["Song"] = relationship(back_populates="generations")
    feedbacks: Mapped[list["UserFeedback"]] = relationship(back_populates="generation")

    __table_args__ = (
        Index("ix_generations_song_id", "song_id"),
        Index("ix_generations_style", "style"),
    )


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    feedback_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    generation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generations.generation_id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.user_id"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    musicality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    style_match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fit_to_melody_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    generation: Mapped["Generation"] = relationship(back_populates="feedbacks")
    user: Mapped["User"] = relationship(back_populates="feedbacks")

    __table_args__ = (
        Index("ix_user_feedback_generation_id", "generation_id"),
        Index("ix_user_feedback_user_id", "user_id"),
    )


class Style(Base):
    __tablename__ = "styles"

    style_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    style_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
