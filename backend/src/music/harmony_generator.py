"""Harmony generation: creates parallel harmony lines from melody notes.

Given a sequence of MIDI note numbers representing a melody, the
HarmonyGenerator produces a parallel harmony line at a specified
musical interval (third, fifth, or octave).
"""

import logging

logger = logging.getLogger(__name__)

# Mapping from interval name to semitone offset.
# For "third", we use a major third (4 semitones) by default.
_INTERVAL_SEMITONES: dict[str, int] = {
    "third": 4,   # major third
    "fifth": 7,   # perfect fifth
    "octave": 12,  # octave
}


class HarmonyGenerator:
    """Generates harmony lines from melody MIDI notes.

    Supports parallel harmonization at intervals of a third, fifth,
    or octave above the melody.
    """

    def generate_harmony(
        self,
        melody_notes: list[int],
        interval: str = "third",
    ) -> list[int]:
        """Generate a harmony line at the specified interval above the melody.

        For the "third" interval, a major third (4 semitones) is used.
        For "fifth", a perfect fifth (7 semitones).
        For "octave", a full octave (12 semitones).

        Args:
            melody_notes: A list of MIDI note numbers representing the melody.
            interval: The harmonization interval -- "third", "fifth", or "octave".

        Returns:
            A list of MIDI note numbers for the harmony line, one per
            input note.

        Raises:
            ValueError: If the interval name is not recognized.
        """
        if interval not in _INTERVAL_SEMITONES:
            raise ValueError(
                f"Unsupported interval '{interval}'. "
                f"Supported intervals: {', '.join(sorted(_INTERVAL_SEMITONES.keys()))}"
            )

        semitones = _INTERVAL_SEMITONES[interval]
        harmony: list[int] = []

        for note in melody_notes:
            harmony.append(note + semitones)

        logger.debug(
            "Generated %s harmony for %d notes (offset=%d semitones)",
            interval,
            len(melody_notes),
            semitones,
        )

        return harmony
