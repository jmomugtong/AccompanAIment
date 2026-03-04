"""Music theory helper functions for note/MIDI conversion and transposition.

Provides utilities for converting between note names (e.g. "C4") and
MIDI note numbers, looking up interval sizes in semitones, and
transposing MIDI notes.
"""

import re

# Note names in chromatic order using sharps.
_NOTE_NAMES_SHARP = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
]

# Mapping from note letter (with optional accidental) to pitch class (0-11).
_NAME_TO_PC: dict[str, int] = {
    "C": 0, "C#": 1, "Db": 1,
    "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4, "E#": 5,
    "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8,
    "A": 9, "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11, "B#": 0,
}

# Named intervals mapped to semitone counts.
_INTERVALS: dict[str, int] = {
    "unison": 0,
    "minor_second": 1,
    "major_second": 2,
    "minor_third": 3,
    "major_third": 4,
    "perfect_fourth": 5,
    "tritone": 6,
    "perfect_fifth": 7,
    "minor_sixth": 8,
    "major_sixth": 9,
    "minor_seventh": 10,
    "major_seventh": 11,
    "octave": 12,
}

# Regex pattern for note names: letter + optional accidental + octave number
_NOTE_PATTERN = re.compile(r"^([A-Ga-g])(#|b)?(-?\d+)$")


def note_name_to_midi(name: str) -> int:
    """Convert a note name string to a MIDI note number.

    Uses the convention where C4 = MIDI 60 (middle C).

    Args:
        name: Note name with octave, e.g. "C4", "F#3", "Bb2".

    Returns:
        The MIDI note number as an integer.

    Raises:
        ValueError: If the note name cannot be parsed.
    """
    match = _NOTE_PATTERN.match(name)
    if not match:
        raise ValueError(
            f"Invalid note name '{name}'. "
            "Expected format: letter + optional accidental + octave "
            "(e.g. 'C4', 'F#3', 'Bb2')."
        )

    letter = match.group(1).upper()
    accidental = match.group(2) or ""
    octave = int(match.group(3))

    note_key = letter + accidental
    if note_key not in _NAME_TO_PC:
        raise ValueError(f"Unrecognized note: '{note_key}'")

    pitch_class = _NAME_TO_PC[note_key]
    # MIDI formula: C4 = 60, so MIDI = (octave + 1) * 12 + pitch_class
    midi = (octave + 1) * 12 + pitch_class
    return midi


def midi_to_note_name(midi: int) -> str:
    """Convert a MIDI note number to a note name string.

    Uses sharp notation for accidentals (e.g. C# rather than Db).

    Args:
        midi: MIDI note number (0-127).

    Returns:
        Note name string, e.g. "C4", "A#3".
    """
    pitch_class = midi % 12
    octave = (midi // 12) - 1
    return f"{_NOTE_NAMES_SHARP[pitch_class]}{octave}"


def interval_semitones(interval_name: str) -> int:
    """Return the number of semitones for a named interval.

    Args:
        interval_name: Name of the interval, e.g. "major_third",
            "perfect_fifth", "octave".

    Returns:
        The number of semitones as an integer.

    Raises:
        ValueError: If the interval name is not recognized.
    """
    if interval_name not in _INTERVALS:
        raise ValueError(
            f"Unknown interval '{interval_name}'. "
            f"Known intervals: {', '.join(sorted(_INTERVALS.keys()))}"
        )
    return _INTERVALS[interval_name]


def transpose(midi_note: int, semitones: int) -> int:
    """Transpose a MIDI note by a number of semitones.

    Args:
        midi_note: The original MIDI note number.
        semitones: Number of semitones to shift (positive = up, negative = down).

    Returns:
        The transposed MIDI note number.
    """
    return midi_note + semitones
