"""Initial schema - all tables.

Revision ID: 001
Revises:
Create Date: 2026-03-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("skill_level", sa.String(50), nullable=True),
        sa.Column("preferred_styles", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "songs",
        sa.Column("song_id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("tempo_bpm", sa.Float(), nullable=True),
        sa.Column(
            "uploaded_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_songs_user_id", "songs", ["user_id"])
    op.create_index("ix_songs_uploaded_at", "songs", ["uploaded_at"])

    op.create_table(
        "melodies",
        sa.Column("melody_id", sa.String(36), primary_key=True),
        sa.Column(
            "song_id",
            sa.String(36),
            sa.ForeignKey("songs.song_id"),
            nullable=False,
        ),
        sa.Column("pitch_contour_json", sa.Text(), nullable=True),
        sa.Column("confidence_json", sa.Text(), nullable=True),
        sa.Column("timings_json", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_melodies_song_id", "melodies", ["song_id"])

    op.create_table(
        "generations",
        sa.Column("generation_id", sa.String(36), primary_key=True),
        sa.Column(
            "song_id",
            sa.String(36),
            sa.ForeignKey("songs.song_id"),
            nullable=False,
        ),
        sa.Column("style", sa.String(50), nullable=False),
        sa.Column("midi_path", sa.String(500), nullable=True),
        sa.Column("audio_path", sa.String(500), nullable=True),
        sa.Column("sheet_path", sa.String(500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_generations_song_id", "generations", ["song_id"])
    op.create_index("ix_generations_style", "generations", ["style"])

    op.create_table(
        "user_feedback",
        sa.Column("feedback_id", sa.String(36), primary_key=True),
        sa.Column(
            "generation_id",
            sa.String(36),
            sa.ForeignKey("generations.generation_id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("musicality_score", sa.Integer(), nullable=True),
        sa.Column("style_match_score", sa.Integer(), nullable=True),
        sa.Column("fit_to_melody_score", sa.Integer(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_user_feedback_generation_id", "user_feedback", ["generation_id"]
    )
    op.create_index("ix_user_feedback_user_id", "user_feedback", ["user_id"])

    op.create_table(
        "styles",
        sa.Column("style_id", sa.String(36), primary_key=True),
        sa.Column("style_name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_name", sa.String(100), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("styles")
    op.drop_table("user_feedback")
    op.drop_table("generations")
    op.drop_table("melodies")
    op.drop_table("songs")
    op.drop_table("users")
