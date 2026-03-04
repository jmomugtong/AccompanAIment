"""Generate synthetic sample songs for development and testing.

Creates WAV files with sine wave tones at various musical frequencies.
Useful for testing the upload and melody extraction pipeline without
requiring real audio files. Idempotent -- skips files that already exist.
"""

import argparse
import os
import struct
import sys
import wave
from pathlib import Path

import numpy as np

# Musical frequencies (Hz) for a variety of pitches
SAMPLE_SONGS = [
    {
        "filename": "sample_c_major_scale.wav",
        "description": "C major scale ascending",
        "frequencies": [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25],
        "duration_per_note": 0.5,
    },
    {
        "filename": "sample_a_minor_melody.wav",
        "description": "A minor pentatonic melody",
        "frequencies": [220.00, 261.63, 293.66, 329.63, 392.00, 329.63, 293.66, 220.00],
        "duration_per_note": 0.4,
    },
    {
        "filename": "sample_g_blues.wav",
        "description": "G blues scale phrase",
        "frequencies": [196.00, 233.08, 261.63, 277.18, 293.66, 349.23, 392.00],
        "duration_per_note": 0.35,
    },
    {
        "filename": "sample_e_minor_arpeggio.wav",
        "description": "E minor arpeggio pattern",
        "frequencies": [164.81, 196.00, 246.94, 329.63, 246.94, 196.00, 164.81],
        "duration_per_note": 0.45,
    },
    {
        "filename": "sample_d_major_chord.wav",
        "description": "D major chord tones",
        "frequencies": [146.83, 185.00, 220.00, 293.66, 369.99, 293.66, 220.00, 146.83],
        "duration_per_note": 0.5,
    },
    {
        "filename": "sample_f_lydian.wav",
        "description": "F Lydian mode ascending",
        "frequencies": [174.61, 196.00, 220.00, 246.94, 261.63, 293.66, 329.63, 349.23],
        "duration_per_note": 0.4,
    },
    {
        "filename": "sample_bb_jazz_phrase.wav",
        "description": "Bb jazz melodic phrase",
        "frequencies": [233.08, 261.63, 293.66, 311.13, 349.23, 392.00, 349.23, 233.08],
        "duration_per_note": 0.3,
    },
    {
        "filename": "sample_chromatic_run.wav",
        "description": "Chromatic run from C4 to G4",
        "frequencies": [
            261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00,
        ],
        "duration_per_note": 0.25,
    },
    {
        "filename": "sample_whole_tone.wav",
        "description": "Whole tone scale from C4",
        "frequencies": [261.63, 293.66, 329.63, 369.99, 415.30, 466.16, 523.25],
        "duration_per_note": 0.45,
    },
    {
        "filename": "sample_octave_jumps.wav",
        "description": "Octave jumps pattern",
        "frequencies": [220.00, 440.00, 261.63, 523.25, 329.63, 659.26, 261.63, 523.25],
        "duration_per_note": 0.35,
    },
]

SAMPLE_RATE = 22050
AMPLITUDE = 0.8


def generate_sine_wave(
    frequencies: list[float],
    duration_per_note: float,
    sample_rate: int = SAMPLE_RATE,
    amplitude: float = AMPLITUDE,
) -> np.ndarray:
    """Generate a concatenated sine wave signal from a list of frequencies.

    Each frequency plays for duration_per_note seconds. A short fade-in
    and fade-out is applied to each note to avoid click artifacts.

    Args:
        frequencies: List of frequencies in Hz for each note.
        duration_per_note: Duration of each note in seconds.
        sample_rate: Audio sample rate in Hz.
        amplitude: Peak amplitude (0.0 to 1.0).

    Returns:
        NumPy array of 16-bit PCM audio samples.
    """
    samples_per_note = int(sample_rate * duration_per_note)
    fade_length = min(int(sample_rate * 0.01), samples_per_note // 4)
    t = np.arange(samples_per_note) / sample_rate

    all_samples = []
    for freq in frequencies:
        note = amplitude * np.sin(2 * np.pi * freq * t)
        # Apply fade-in and fade-out to prevent clicks
        if fade_length > 0:
            fade_in = np.linspace(0.0, 1.0, fade_length)
            fade_out = np.linspace(1.0, 0.0, fade_length)
            note[:fade_length] *= fade_in
            note[-fade_length:] *= fade_out
        all_samples.append(note)

    signal = np.concatenate(all_samples)
    # Convert to 16-bit PCM
    pcm = (signal * 32767).astype(np.int16)
    return pcm


def write_wav(filepath: Path, samples: np.ndarray, sample_rate: int = SAMPLE_RATE) -> None:
    """Write a NumPy array of 16-bit PCM samples to a WAV file.

    Args:
        filepath: Output file path.
        samples: 16-bit PCM audio samples.
        sample_rate: Audio sample rate in Hz.
    """
    with wave.open(str(filepath), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())


def generate_sample_songs(
    output_dir: Path,
    count: int = 5,
    dry_run: bool = False,
) -> int:
    """Generate synthetic WAV sample songs.

    Args:
        output_dir: Directory to write WAV files into.
        count: Number of songs to generate (max is len(SAMPLE_SONGS)).
        dry_run: If True, print what would be created without writing files.

    Returns:
        Number of files created (or would be created in dry-run mode).
    """
    songs = SAMPLE_SONGS[:count]
    created = 0

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    for song in songs:
        filepath = output_dir / song["filename"]

        if filepath.exists():
            print(f"  SKIP: '{song['filename']}' already exists")
            continue

        if dry_run:
            print(
                f"  DRY-RUN: would create '{song['filename']}' "
                f"-- {song['description']}"
            )
            created += 1
            continue

        samples = generate_sine_wave(
            frequencies=song["frequencies"],
            duration_per_note=song["duration_per_note"],
        )
        write_wav(filepath, samples)
        created += 1
        print(f"  CREATED: '{song['filename']}' -- {song['description']}")

    return created


def main() -> None:
    """CLI entry point for generating sample songs."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic sample WAV songs for development and testing."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of sample songs to generate (default: 5, max: %d)" % len(SAMPLE_SONGS),
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/storage/samples",
        help="Directory to write sample WAV files (default: data/storage/samples)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without writing files",
    )
    args = parser.parse_args()

    count = min(args.count, len(SAMPLE_SONGS))
    output_dir = Path(args.output_dir)

    print(f"Generating {count} sample song(s) in '{output_dir}'...")
    try:
        created = generate_sample_songs(output_dir, count=count, dry_run=args.dry_run)
    except Exception as exc:
        print(f"FAILED: {exc}")
        sys.exit(1)

    action = "would create" if args.dry_run else "created"
    print(f"Done. {created} file(s) {action}.")


if __name__ == "__main__":
    main()
