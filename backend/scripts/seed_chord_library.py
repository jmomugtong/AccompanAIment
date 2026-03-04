"""Seed common chord progressions into the database.

Provides a reference library of well-known chord progressions for
users to browse when creating accompaniments. Idempotent -- skips
progressions that already exist (matched by name).
"""

import argparse
import json
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

CHORD_PROGRESSIONS = [
    {
        "name": "I-V-vi-IV (Pop)",
        "key": "C",
        "chords": "C | G | Am | F",
        "genre": "pop",
        "description": "The most common pop progression. Used in countless hits.",
    },
    {
        "name": "I-IV-V-I (Classic)",
        "key": "C",
        "chords": "C | F | G | C",
        "genre": "pop",
        "description": "Basic three-chord progression. Foundation of rock and folk.",
    },
    {
        "name": "ii-V-I (Jazz)",
        "key": "C",
        "chords": "Dm7 | G7 | Cmaj7 | Cmaj7",
        "genre": "jazz",
        "description": "The essential jazz cadence. Backbone of jazz harmony.",
    },
    {
        "name": "I-vi-IV-V (Doo-Wop)",
        "key": "C",
        "chords": "C | Am | F | G",
        "genre": "pop",
        "description": "Classic 1950s doo-wop progression. Timeless and versatile.",
    },
    {
        "name": "vi-IV-I-V (Modern Pop)",
        "key": "C",
        "chords": "Am | F | C | G",
        "genre": "pop",
        "description": "Minor-starting variant of the pop progression. Emotional feel.",
    },
    {
        "name": "I-IV-vi-V (Anthem)",
        "key": "C",
        "chords": "C | F | Am | G",
        "genre": "pop",
        "description": "Uplifting anthem progression used in stadium rock.",
    },
    {
        "name": "ii-V-I-vi (Jazz Turnaround)",
        "key": "C",
        "chords": "Dm7 | G7 | Cmaj7 | Am7",
        "genre": "jazz",
        "description": "Standard jazz turnaround. Common in standards and bossa nova.",
    },
    {
        "name": "I-iii-IV-V (Ascending)",
        "key": "C",
        "chords": "C | Em | F | G",
        "genre": "pop",
        "description": "Smooth ascending progression. Gentle and flowing feel.",
    },
    {
        "name": "i-VI-III-VII (Andalusian)",
        "key": "Am",
        "chords": "Am | F | C | G",
        "genre": "classical",
        "description": "Descending Andalusian cadence. Spanish and flamenco origins.",
    },
    {
        "name": "I-V-vi-iii-IV (Canon)",
        "key": "C",
        "chords": "C | G | Am | Em | F",
        "genre": "classical",
        "description": "Pachelbel Canon progression. Baroque origin, widely adapted.",
    },
    {
        "name": "i-iv-v-i (Minor Blues)",
        "key": "Am",
        "chords": "Am | Dm | Em | Am",
        "genre": "rnb",
        "description": "Minor blues progression. Moody and soulful character.",
    },
    {
        "name": "I-IV-I-V (12-Bar Intro)",
        "key": "C",
        "chords": "C | F | C | G",
        "genre": "rnb",
        "description": "Simplified 12-bar blues intro. Foundation of blues and RnB.",
    },
    {
        "name": "I-IVmaj7-iii7-vi7 (Neo-Soul)",
        "key": "C",
        "chords": "Cmaj7 | Fmaj7 | Em7 | Am7",
        "genre": "soulful",
        "description": "Neo-soul progression with lush extended chords.",
    },
    {
        "name": "I-V/vii-vi-IV (Slash Bass)",
        "key": "C",
        "chords": "C | G | Am | F",
        "genre": "soulful",
        "description": "Gospel-influenced progression with strong bass movement.",
    },
    {
        "name": "i-VII-VI-V (Harmonic Minor)",
        "key": "Am",
        "chords": "Am | G | F | E",
        "genre": "classical",
        "description": "Harmonic minor descent. Dramatic and passionate character.",
    },
]


def seed_chord_library(database_url: str, dry_run: bool = False) -> int:
    """Insert chord progressions into the database.

    Args:
        database_url: SQLAlchemy-compatible database URL (sync driver).
        dry_run: If True, print what would be inserted without writing.

    Returns:
        Number of progressions inserted.
    """
    engine = create_engine(database_url)
    inserted = 0

    # Ensure the chord_library table exists (create if not present).
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS chord_library ("
                "  progression_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),"
                "  name VARCHAR(200) UNIQUE NOT NULL,"
                "  key VARCHAR(10) NOT NULL,"
                "  chords TEXT NOT NULL,"
                "  genre VARCHAR(50),"
                "  description TEXT,"
                "  created_at TIMESTAMP DEFAULT NOW()"
                ")"
            )
        )

    with Session(engine) as session:
        for prog in CHORD_PROGRESSIONS:
            # Check if progression already exists by name.
            result = session.execute(
                text("SELECT progression_id FROM chord_library WHERE name = :name"),
                {"name": prog["name"]},
            )
            if result.fetchone() is not None:
                print(f"  SKIP: '{prog['name']}' already exists")
                continue

            if dry_run:
                print(f"  DRY-RUN: would insert '{prog['name']}'")
                inserted += 1
                continue

            session.execute(
                text(
                    "INSERT INTO chord_library "
                    "(progression_id, name, key, chords, genre, description) "
                    "VALUES (gen_random_uuid(), :name, :key, :chords, :genre, :description)"
                ),
                prog,
            )
            inserted += 1
            print(f"  INSERTED: '{prog['name']}'")

        if not dry_run:
            session.commit()

    engine.dispose()
    return inserted


def main() -> None:
    """CLI entry point for seeding chord progressions."""
    parser = argparse.ArgumentParser(
        description="Seed common chord progressions into the chord_library table."
    )
    parser.add_argument(
        "--database-url",
        default="postgresql://accompaniment:accompaniment@localhost:5432/accompaniment",
        help="Sync database URL (default: local PostgreSQL)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be inserted without writing to the database",
    )
    args = parser.parse_args()

    print("Seeding chord library...")
    try:
        count = seed_chord_library(args.database_url, dry_run=args.dry_run)
    except Exception as exc:
        print(f"FAILED: {exc}")
        sys.exit(1)

    action = "would insert" if args.dry_run else "inserted"
    print(f"Done. {count} progression(s) {action}.")


if __name__ == "__main__":
    main()
