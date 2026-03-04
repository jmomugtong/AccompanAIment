"""Generate a synthetic 50-accompaniment evaluation dataset.

Creates a JSON dataset of synthetic accompaniment specifications that
can be used to evaluate the quality of generated piano accompaniments
across all supported styles. Idempotent -- overwrites the output file
if it already exists.
"""

import argparse
import json
import os
import random
import sys
import uuid
from datetime import datetime

STYLES = ["jazz", "soulful", "rnb", "pop", "classical"]

TEMPOS = [72, 80, 90, 100, 110, 120, 130, 140]

TIME_SIGNATURES = ["4/4", "3/4", "6/8"]

KEYS = ["C", "D", "E", "F", "G", "A", "Bb", "Eb", "Ab"]

CHORD_PROGRESSIONS = [
    "C | F | G | C",
    "Am | F | C | G",
    "Dm7 | G7 | Cmaj7 | Cmaj7",
    "C | Am | F | G",
    "C | G | Am | F",
    "Em | C | G | D",
    "Am | Dm | E | Am",
    "F | G | Am | Am",
    "C | Em | F | G",
    "Dm | G | C | Am",
    "Cmaj7 | Fmaj7 | Em7 | Am7",
    "Am | G | F | E",
]

# Synthetic melody fragments (MIDI note sequences) for evaluation.
MELODY_FRAGMENTS = [
    [60, 62, 64, 65, 67, 65, 64, 62],
    [67, 65, 64, 62, 60, 62, 64, 67],
    [60, 64, 67, 72, 67, 64, 60, 64],
    [72, 71, 69, 67, 65, 64, 62, 60],
    [60, 60, 62, 64, 64, 62, 60, 59],
    [65, 67, 69, 67, 65, 64, 62, 64],
    [60, 67, 64, 72, 60, 67, 64, 60],
]


def generate_eval_entry(index: int, seed: int) -> dict:
    """Generate a single evaluation dataset entry.

    Args:
        index: Entry index (0-based).
        seed: Random seed for reproducibility.

    Returns:
        Dictionary with all fields needed for evaluation.
    """
    rng = random.Random(seed + index)

    style = STYLES[index % len(STYLES)]
    tempo = rng.choice(TEMPOS)
    time_sig = rng.choice(TIME_SIGNATURES)
    key = rng.choice(KEYS)
    chords = rng.choice(CHORD_PROGRESSIONS)
    melody = rng.choice(MELODY_FRAGMENTS)
    duration = round(rng.uniform(8.0, 32.0), 1)

    return {
        "eval_id": str(uuid.UUID(int=seed + index)),
        "index": index,
        "style": style,
        "tempo_bpm": tempo,
        "time_signature": time_sig,
        "key": key,
        "chord_progression": chords,
        "melody_notes": melody,
        "melody_timings": [round(i * (duration / len(melody)), 3) for i in range(len(melody))],
        "duration_seconds": duration,
        "expected_voicing_count": len(chords.split("|")),
    }


def generate_dataset(count: int = 50, seed: int = 42) -> list[dict]:
    """Generate the full evaluation dataset.

    Args:
        count: Number of entries to generate.
        seed: Base random seed for reproducibility.

    Returns:
        List of evaluation entry dictionaries.
    """
    return [generate_eval_entry(i, seed) for i in range(count)]


def main() -> None:
    """CLI entry point for generating the evaluation dataset."""
    parser = argparse.ArgumentParser(
        description="Generate a synthetic evaluation dataset for accompaniment quality testing."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of evaluation entries to generate (default: 50)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output",
        default="backend/datasets/eval_dataset.json",
        help="Output file path (default: backend/datasets/eval_dataset.json)",
    )
    args = parser.parse_args()

    print(f"Generating {args.count} evaluation entries (seed={args.seed})...")
    dataset = generate_dataset(count=args.count, seed=args.seed)

    metadata = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(dataset),
        "seed": args.seed,
        "styles": STYLES,
        "version": "1.0",
    }

    output_data = {
        "metadata": metadata,
        "entries": dataset,
    }

    # Ensure output directory exists.
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Done. Wrote {len(dataset)} entries to {args.output}")
    print(f"Styles covered: {', '.join(STYLES)}")
    print(f"Entries per style: {len(dataset) // len(STYLES)}")


if __name__ == "__main__":
    main()
