"""Chord validation using music21 with regex fallback.

Provides the ChordValidator class which can verify individual chord symbols,
return structured chord information, and batch-validate lists of chords.
"""

from __future__ import annotations

import re
from typing import Optional

# Attempt to use music21 for robust chord validation.  If it is unavailable
# (e.g. in a lightweight CI image), fall back to regex-only validation.
try:
    from music21 import harmony

    _HAS_MUSIC21 = True
except ImportError:  # pragma: no cover
    _HAS_MUSIC21 = False

# ---------------------------------------------------------------------------
# Regex pattern that matches the vast majority of chord symbols used in
# popular / jazz lead sheets.
#
# Structure:
#   <root>         : A-G
#   <accidental>   : # or b  (single only)
#   <quality/ext>  : optional combination of quality + extension tokens
#
# Recognised tokens (order matters, longest match first):
#   maj13, maj11, maj9, maj7
#   m13, m11, m9, m7, m6, m
#   add11, add9
#   dim7, dim
#   aug7, aug
#   sus4, sus2
#   7b5, m7b5 (half-diminished shorthand)
#   13, 11, 9, 7, 6
#   +  (augmented)
#   o  (diminished)
# ---------------------------------------------------------------------------

_CHORD_PATTERN = re.compile(
    r"^"
    r"([A-G])"                          # root note
    r"([#b])?"                          # optional single accidental
    r"("
    r"maj13|maj11|maj9|maj7"            # major extended
    r"|m7b5"                            # half-diminished
    r"|m13|m11|m9|m7|m6|m"             # minor variants
    r"|add11|add9"                      # add tones
    r"|dim7|dim"                        # diminished
    r"|aug7|aug"                        # augmented + aug7
    r"|sus[24]"                         # suspended
    r"|13|11|9|7|6"                     # dominant / sixth extensions
    r"|[+]"                             # + for augmented
    r"|o"                               # o for diminished
    r")?"
    r"$"
)

# Quality inference from the suffix token (used by get_chord_info).
_QUALITY_MAP: dict[str, str] = {
    "": "major",
    "m": "minor",
    "m6": "minor",
    "m7": "minor",
    "m9": "minor",
    "m11": "minor",
    "m13": "minor",
    "m7b5": "minor",
    "dim": "diminished",
    "dim7": "diminished",
    "o": "diminished",
    "aug": "augmented",
    "aug7": "augmented",
    "+": "augmented",
    "maj7": "major",
    "maj9": "major",
    "maj11": "major",
    "maj13": "major",
    "7": "dominant",
    "9": "dominant",
    "11": "dominant",
    "13": "dominant",
    "6": "major",
    "sus2": "suspended",
    "sus4": "suspended",
    "add9": "major",
    "add11": "major",
}

# Chord type suffixes that music21 does not recognise.  For these, we trust
# the regex match alone and skip the music21 cross-check.
_MUSIC21_UNSUPPORTED_SUFFIXES = {"maj9", "maj11", "maj13"}


def _to_music21_name(name: str) -> str:
    """Convert standard lead-sheet flat notation to music21 convention.

    Lead sheets use 'b' for flat (e.g. Bb, Ebm7).  music21 expects '-'
    (e.g. B-, E-m7).  This helper performs that conversion only on the
    accidental immediately following the root letter, leaving the rest of
    the chord symbol (which may also contain 'b' in tokens like 'm7b5')
    untouched.
    """
    if len(name) >= 2 and name[0] in "ABCDEFG" and name[1] == "b":
        # Ensure this 'b' is the accidental, not start of a suffix.
        # It is the accidental if it is followed by end-of-string or a
        # non-letter character or the start of a known suffix.
        return name[0] + "-" + name[2:]
    return name


class ChordValidator:
    """Validate and inspect chord symbols.

    Uses music21.harmony.ChordSymbol when available for pitch resolution,
    with a regex guard to reject strings that are not well-formed chord
    symbols (music21 is lenient and may silently accept odd inputs).
    """

    # ---- public API -------------------------------------------------------

    def is_valid_chord(self, name: str) -> bool:
        """Return True if *name* is a recognised chord symbol.

        Examples of accepted names: C, Cm, C7, Cmaj7, Csus4, Cdim, Caug,
        C9, Cm11, Cmaj13, C+, Co, Cm7b5, Cadd9, C6, Cm6.

        Rejects empty strings, lowercase roots, double accidentals, bare
        quality tokens without a root, and other gibberish.
        """
        if not isinstance(name, str) or not name.strip():
            return False

        name = name.strip()

        match = _CHORD_PATTERN.match(name)
        if match is None:
            return False

        suffix = match.group(3) or ""

        # If the suffix is one that music21 does not handle, the regex
        # match alone is sufficient.
        if suffix in _MUSIC21_UNSUPPORTED_SUFFIXES:
            return True

        # If music21 is available, additionally confirm it can build pitches.
        if _HAS_MUSIC21:
            return self._music21_check(name)

        return True

    def get_chord_info(self, name: str) -> Optional[dict]:
        """Return structured information about a chord, or None if invalid.

        Returned dict keys:
            root      -- e.g. "C", "F#", "Bb"
            quality   -- "major", "minor", "diminished", "augmented",
                         "dominant", "suspended"
            extension -- the suffix after root+accidental (may be "")
            pitches   -- list of pitch name strings (e.g. ["C", "E", "G"])
        """
        if not self.is_valid_chord(name):
            return None

        match = _CHORD_PATTERN.match(name.strip())
        if match is None:
            return None

        root_letter = match.group(1)
        accidental = match.group(2) or ""
        suffix = match.group(3) or ""

        root = root_letter + accidental
        quality = _QUALITY_MAP.get(suffix, "major")

        pitches = self._resolve_pitches(name.strip())

        return {
            "root": root,
            "quality": quality,
            "extension": suffix,
            "pitches": pitches,
        }

    def validate_all(self, names: list[str]) -> bool:
        """Return True if every name in the list is a valid chord."""
        return all(self.is_valid_chord(n) for n in names)

    def find_invalid(self, names: list[str]) -> tuple[bool, list[str]]:
        """Return (all_valid, list_of_invalid_names)."""
        bad = [n for n in names if not self.is_valid_chord(n)]
        return (len(bad) == 0, bad)

    # ---- internal helpers -------------------------------------------------

    @staticmethod
    def _music21_check(name: str) -> bool:
        """Use music21 to confirm the chord symbol resolves to pitches."""
        m21_name = _to_music21_name(name)
        try:
            cs = harmony.ChordSymbol(m21_name)
            # A valid chord must resolve to at least 2 distinct pitches
            # (power chords / sus chords can have only 3, but music21
            # always returns at least 3 for standard symbols).
            if len(cs.pitches) < 2:
                return False
            return True
        except Exception:
            return False

    @staticmethod
    def _resolve_pitches(name: str) -> list[str]:
        """Return a list of pitch name strings for the chord."""
        if _HAS_MUSIC21:
            m21_name = _to_music21_name(name)
            try:
                cs = harmony.ChordSymbol(m21_name)
                return [p.name for p in cs.pitches]
            except Exception:
                pass

        # Fallback: return root triad approximation from regex alone.
        match = _CHORD_PATTERN.match(name)
        if match is None:
            return []
        root = match.group(1) + (match.group(2) or "")
        # Cannot derive full pitch set without music21; return root only.
        return [root]
