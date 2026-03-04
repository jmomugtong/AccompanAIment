"""Parse chord progressions, time signatures, and tempo values.

Provides the ChordParser class and supporting data classes for structured
representation of progressions and time signatures.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Union

from src.music.chord_validator import ChordValidator

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ProgressionResult:
    """Parsed chord progression."""

    chords: list[str] = field(default_factory=list)
    bar_count: int = 0
    is_valid: bool = True


@dataclass
class TimeSignature:
    """A simple time-signature representation."""

    numerator: int = 4
    denominator: int = 4


# ---------------------------------------------------------------------------
# Allowed denominator values (must be a power of 2: 1, 2, 4, 8, 16 ...).
# We support the practical range used in popular and classical music.
# ---------------------------------------------------------------------------

_VALID_DENOMINATORS = {1, 2, 4, 8, 16, 32}


class ChordParser:
    """Parse chord progressions from strings, validate tempo and time sigs."""

    def __init__(self) -> None:
        self._validator = ChordValidator()

    # ---- chord progression parsing ----------------------------------------

    def parse_progression(self, text: str) -> ProgressionResult:
        """Parse a pipe-or-dash-delimited chord progression string.

        Accepted formats:
            "C | F | G | C"       -- pipe-delimited bars
            "C - F - G - C"       -- dash-delimited bars
            "C Am | F G | Dm Em"  -- multiple chords per bar (space-separated)
            "C | / | G | /"       -- slash repeats previous chord

        Returns a ProgressionResult with the list of individual chords,
        the bar count, and an is_valid flag.

        Raises ValueError on empty input or if any chord symbol is invalid.
        """
        if not text or not text.strip():
            raise ValueError("Chord progression string is empty.")

        cleaned = text.strip()

        # Normalise delimiters: replace ' - ' (dash with surrounding spaces)
        # with pipe so we can split uniformly.  Bare dashes inside chord names
        # (none exist) are not a concern.
        cleaned = re.sub(r"\s+-\s+", " | ", cleaned)

        # Split into bars on '|'.
        bars = [b.strip() for b in cleaned.split("|")]
        bars = [b for b in bars if b]

        if not bars:
            raise ValueError("Chord progression string is empty.")

        chords: list[str] = []
        previous_chord: str | None = None

        for bar in bars:
            tokens = bar.split()
            for token in tokens:
                if token == "/":
                    if previous_chord is None:
                        raise ValueError(
                            "Invalid progression: '/' used before any chord."
                        )
                    chords.append(previous_chord)
                else:
                    if not self._validator.is_valid_chord(token):
                        raise ValueError(
                            f"Invalid chord symbol: '{token}'"
                        )
                    chords.append(token)
                    previous_chord = token

        return ProgressionResult(
            chords=chords,
            bar_count=len(bars),
            is_valid=True,
        )

    # ---- time signature parsing -------------------------------------------

    def parse_time_signature(self, text: str) -> TimeSignature:
        """Parse a time signature string like '4/4' or '6/8'.

        The numerator must be a positive integer.
        The denominator must be a power of 2 in {1, 2, 4, 8, 16, 32}.

        Raises ValueError on malformed input.
        """
        if not text or not text.strip():
            raise ValueError("Time signature string is empty.")

        text = text.strip()

        parts = text.split("/")
        if len(parts) != 2:
            raise ValueError(
                f"Time signature must be in 'N/D' format, got: '{text}'"
            )

        try:
            numerator = int(parts[0])
            denominator = int(parts[1])
        except ValueError:
            raise ValueError(
                f"Time signature must contain integers, got: '{text}'"
            )

        if numerator < 1:
            raise ValueError(
                f"Time signature numerator must be >= 1, got: {numerator}"
            )
        if denominator not in _VALID_DENOMINATORS:
            raise ValueError(
                f"Time signature denominator must be a power of 2 "
                f"in {sorted(_VALID_DENOMINATORS)}, got: {denominator}"
            )

        return TimeSignature(numerator=numerator, denominator=denominator)

    # ---- tempo validation -------------------------------------------------

    def validate_tempo(self, bpm: Union[int, float]) -> bool:
        """Return True if bpm is within the allowed range [40, 240]."""
        return 40 <= bpm <= 240
