"""Seed the styles table with predefined accompaniment styles.

Populates the database with jazz, soulful, rnb, pop, and classical
style templates. Idempotent -- skips styles that already exist.
"""

import argparse
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

STYLES = [
    {
        "style_name": "jazz",
        "description": (
            "Extended harmony with 7ths, 9ths, and 13ths. Swing rhythms, "
            "walking bass lines, and rich chord voicings typical of jazz piano."
        ),
        "template_name": "jazz_voicing",
    },
    {
        "style_name": "soulful",
        "description": (
            "Warm, gospel-influenced voicings with suspended chords, "
            "minor 7ths, and expressive dynamics. Emphasis on feel and groove."
        ),
        "template_name": "soulful_voicing",
    },
    {
        "style_name": "rnb",
        "description": (
            "Rich extended voicings with color tones, neo-soul influences, "
            "and smooth chord transitions. Emphasizes 9ths, 11ths, and altered chords."
        ),
        "template_name": "rnb_voicing",
    },
    {
        "style_name": "pop",
        "description": (
            "Clean triads and power chords with simple, memorable patterns. "
            "Straightforward voicings that support vocal melodies without complexity."
        ),
        "template_name": "pop_voicing",
    },
    {
        "style_name": "classical",
        "description": (
            "Four-part SATB-style harmony following traditional voice-leading rules. "
            "Balanced voicings with proper doubling and smooth part motion."
        ),
        "template_name": "classical_voicing",
    },
]


def seed_styles(database_url: str, dry_run: bool = False) -> int:
    """Insert styles into the database.

    Args:
        database_url: SQLAlchemy-compatible database URL (sync driver).
        dry_run: If True, print what would be inserted without writing.

    Returns:
        Number of styles inserted.
    """
    engine = create_engine(database_url)
    inserted = 0

    with Session(engine) as session:
        for style in STYLES:
            # Check if style already exists.
            result = session.execute(
                text("SELECT style_id FROM styles WHERE style_name = :name"),
                {"name": style["style_name"]},
            )
            if result.fetchone() is not None:
                print(f"  SKIP: '{style['style_name']}' already exists")
                continue

            if dry_run:
                print(f"  DRY-RUN: would insert '{style['style_name']}'")
                inserted += 1
                continue

            session.execute(
                text(
                    "INSERT INTO styles (style_id, style_name, description, template_name) "
                    "VALUES (gen_random_uuid(), :style_name, :description, :template_name)"
                ),
                style,
            )
            inserted += 1
            print(f"  INSERTED: '{style['style_name']}'")

        if not dry_run:
            session.commit()

    engine.dispose()
    return inserted


def main() -> None:
    """CLI entry point for seeding styles."""
    parser = argparse.ArgumentParser(
        description="Seed the styles table with predefined accompaniment styles."
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

    print("Seeding styles table...")
    try:
        count = seed_styles(args.database_url, dry_run=args.dry_run)
    except Exception as exc:
        print(f"FAILED: {exc}")
        sys.exit(1)

    action = "would insert" if args.dry_run else "inserted"
    print(f"Done. {count} style(s) {action}.")


if __name__ == "__main__":
    main()
