"""Chord voicing generation with style-specific templates.

Generates MIDI note voicings for chord symbols using music21, with support
for inversions, voice leading, register constraints, and style-specific rules
(jazz extensions, pop triads, classical four-part harmony, etc.).
"""

from __future__ import annotations

from typing import Optional

from music21 import chord as m21chord
from music21 import harmony, pitch

# Register constraints: all voicings must fall within this MIDI range.
MIN_MIDI = 36  # C2
MAX_MIDI = 84  # C6

# Default octave for root-position voicings (middle of piano).
DEFAULT_OCTAVE = 4

# Style configuration: maps style name to voicing rules.
STYLE_TEMPLATES: dict[str, dict] = {
    "pop": {
        "note_count": 3,
        "extensions": False,
        "description": "Simple triads, clean voicings",
    },
    "jazz": {
        "note_count": 4,
        "extensions": True,
        "add_seventh": True,
        "description": "Extended harmony with 7ths, 9ths",
    },
    "classical": {
        "note_count": 4,
        "extensions": False,
        "double_root": True,
        "description": "Four-part SATB-style harmony",
    },
    "soulful": {
        "note_count": 4,
        "extensions": True,
        "add_seventh": True,
        "description": "Warm extended voicings with 7ths",
    },
    "rnb": {
        "note_count": 4,
        "extensions": True,
        "add_seventh": True,
        "description": "Rich extended voicings with color tones",
    },
}


def _normalize_chord_name(chord_name: str) -> str:
    """Normalize common chord notation to music21-compatible format.

    music21 uses '-' for flats (e.g. 'B-' not 'Bb', 'E-' not 'Eb').
    This function converts conventional flat notation ('b' after a root
    letter) to music21's '-' notation.

    Args:
        chord_name: Chord symbol in any common notation.

    Returns:
        Normalized chord name compatible with music21.
    """
    if len(chord_name) < 2:
        return chord_name

    # Replace 'b' (flat) immediately after a root note letter with '-'.
    # Must be careful: 'b' could be the note B, or 'b' could be a flat sign.
    # Pattern: a root letter [A-G] followed by 'b' where 'b' means flat.
    # E.g. "Bb" -> "B-", "Ebm" -> "E-m", "Abmaj7" -> "A-maj7"
    # But "Bm" should stay "Bm", and "Bdim" should stay "Bdim".
    import re

    # Match a root letter followed by 'b' that is NOT the start of a quality
    # like "dim", "aug", "m", "maj", etc. The 'b' is a flat if it appears
    # right after the root letter.
    normalized = re.sub(
        r"^([A-G])b(?!$)",  # root letter + 'b' + more characters
        r"\1-",
        chord_name,
    )
    # Handle the case where the chord is just "Xb" (e.g. "Bb", "Eb")
    normalized = re.sub(
        r"^([A-G])b$",
        r"\1-",
        normalized,
    )
    return normalized


def _chord_symbol_to_music21(chord_name: str) -> harmony.ChordSymbol:
    """Parse a chord name string into a music21 ChordSymbol.

    Args:
        chord_name: Chord symbol string (e.g. "C", "Am", "F#m", "Cmaj7").

    Returns:
        A music21 ChordSymbol object.

    Raises:
        ValueError: If the chord name cannot be parsed.
    """
    normalized = _normalize_chord_name(chord_name)
    try:
        cs = harmony.ChordSymbol(normalized)
        # Verify it has actual pitches (music21 may silently accept garbage).
        if len(cs.pitches) == 0:
            raise ValueError(f"No pitches resolved for chord: {chord_name}")
        return cs
    except Exception as exc:
        raise ValueError(f"Cannot parse chord symbol '{chord_name}': {exc}") from exc


def _clamp_to_register(midi_note: int) -> int:
    """Move a MIDI note into the valid register by shifting octaves."""
    while midi_note < MIN_MIDI:
        midi_note += 12
    while midi_note > MAX_MIDI:
        midi_note -= 12
    return midi_note


def _move_to_octave(midi_note: int, target_octave: int) -> int:
    """Place a pitch class into a specific octave.

    Args:
        midi_note: Original MIDI note number.
        target_octave: music21 octave number (4 = middle C octave).

    Returns:
        MIDI note in the target octave.
    """
    pc = midi_note % 12
    result = pc + (target_octave + 1) * 12  # music21: octave 4 -> MIDI 60 range
    return _clamp_to_register(result)


class VoicingGenerator:
    """Generates chord voicings as lists of MIDI note numbers.

    Supports multiple styles (pop, jazz, classical, soulful, rnb),
    inversions, and voice leading between consecutive chords.
    """

    def __init__(self) -> None:
        """Initialize VoicingGenerator with style templates."""
        self.style_templates = STYLE_TEMPLATES

    def generate_voicing(
        self,
        chord_name: str,
        style: str = "pop",
        inversion: int = 0,
    ) -> list[int]:
        """Generate a voicing for the given chord.

        Args:
            chord_name: Chord symbol (e.g. "C", "Am", "G7", "Fmaj7").
            style: Voicing style ("pop", "jazz", "classical", "soulful", "rnb").
            inversion: 0 = root position, 1 = first inversion, 2 = second inversion.

        Returns:
            Sorted list of MIDI note numbers (ascending).

        Raises:
            ValueError: If the chord name is invalid.
        """
        cs = _chord_symbol_to_music21(chord_name)
        template = self.style_templates.get(style, self.style_templates["pop"])

        # Get the basic pitch classes from music21.
        base_pitches = [p.midi % 12 for p in cs.pitches]
        root_pc = cs.root().midi % 12

        # Check if the chord symbol already has extensions (e.g. C7, Cmaj7).
        # If so, honor them even in simpler styles like pop.
        symbol_has_extensions = len(base_pitches) > 3

        # Build voicing based on style.
        if template.get("extensions") and template.get("add_seventh"):
            midi_notes = self._build_extended_voicing(chord_name, cs, base_pitches, root_pc)
        elif template.get("double_root"):
            midi_notes = self._build_four_part_voicing(base_pitches, root_pc)
        elif symbol_has_extensions:
            # The chord symbol itself specifies extensions (e.g. C7, Cmaj7).
            # Build a voicing that respects all pitches in the symbol.
            midi_notes = self._build_symbol_voicing(base_pitches, root_pc)
        else:
            midi_notes = self._build_triad_voicing(base_pitches, root_pc)

        # Apply inversion.
        midi_notes = self._apply_inversion(midi_notes, inversion)

        # Clamp all notes to valid register.
        midi_notes = [_clamp_to_register(n) for n in midi_notes]

        return sorted(midi_notes)

    def _build_triad_voicing(
        self, pitch_classes: list[int], root_pc: int
    ) -> list[int]:
        """Build a simple triad voicing (3 notes).

        Places the root in octave 3 (MIDI ~48-59 range) and voices
        the remaining notes close above it.
        """
        # Root in octave 3.
        root_midi = root_pc + 48  # octave 3 base
        if root_midi < MIN_MIDI:
            root_midi += 12

        notes = [root_midi]
        for pc in pitch_classes:
            if pc == root_pc:
                continue
            # Place above root, in closest position.
            n = pc + 48
            while n <= root_midi:
                n += 12
            # Keep within range.
            n = _clamp_to_register(n)
            notes.append(n)

        return sorted(notes)[:3]

    def _build_symbol_voicing(
        self, pitch_classes: list[int], root_pc: int
    ) -> list[int]:
        """Build a voicing using all pitch classes from the chord symbol.

        Used when the chord symbol itself specifies extensions (e.g. C7, Cmaj7)
        and we want to honor them regardless of style.
        """
        root_midi = root_pc + 48
        if root_midi < MIN_MIDI:
            root_midi += 12

        notes = [root_midi]
        for pc in pitch_classes:
            if pc == root_pc:
                continue
            n = pc + 48
            while n <= root_midi:
                n += 12
            n = _clamp_to_register(n)
            notes.append(n)

        return sorted(notes)

    def _build_four_part_voicing(
        self, pitch_classes: list[int], root_pc: int
    ) -> list[int]:
        """Build a four-part (classical SATB) voicing.

        Bass note in octave 3, upper three voices in octave 4,
        with root doubled if needed.
        """
        # Bass: root in low register.
        bass = root_pc + 48
        if bass < MIN_MIDI:
            bass += 12

        # Upper voices above bass.
        upper_notes = []
        for pc in pitch_classes:
            n = pc + 60  # octave 4 base
            while n <= bass:
                n += 12
            n = _clamp_to_register(n)
            upper_notes.append(n)

        # Remove duplicates and sort.
        upper_notes = sorted(set(upper_notes))

        # Build final four-part voicing.
        result = [bass]
        added = 0
        for n in upper_notes:
            if n != bass:
                result.append(n)
                added += 1
            if added >= 3:
                break

        # If we still need notes to reach 4, double the root up an octave.
        while len(result) < 4:
            doubled = bass + 12
            doubled = _clamp_to_register(doubled)
            if doubled not in result:
                result.append(doubled)
            else:
                # Add another pitch class an octave up.
                for pc in pitch_classes:
                    candidate = pc + 72
                    candidate = _clamp_to_register(candidate)
                    if candidate not in result:
                        result.append(candidate)
                        break
                else:
                    break

        return sorted(result)[:4]

    def _build_extended_voicing(
        self,
        chord_name: str,
        cs: harmony.ChordSymbol,
        pitch_classes: list[int],
        root_pc: int,
    ) -> list[int]:
        """Build an extended voicing for jazz/soulful/rnb styles.

        Includes at least a 7th. For major chords, adds major 7th;
        for minor chords, adds minor 7th; for dominant chords, uses
        minor 7th (already present in the symbol).
        """
        # Start with the basic triad.
        triad = self._build_triad_voicing(pitch_classes, root_pc)

        # Determine what extensions to add.
        # Check if a 7th is already in the chord symbol pitches.
        existing_pcs = set(p.midi % 12 for p in cs.pitches)
        triad_pcs = set(n % 12 for n in triad)

        seventh_pc = None
        # If chord already specifies a 7th (e.g. "C7", "Cmaj7"), use it.
        for p in cs.pitches:
            interval_from_root = (p.midi % 12 - root_pc) % 12
            if interval_from_root in (10, 11):  # minor 7th or major 7th
                seventh_pc = p.midi % 12
                break

        if seventh_pc is None:
            # Determine quality to decide 7th type.
            chord_quality = cs.quality
            if chord_quality == "minor":
                # Minor chord: add minor 7th.
                seventh_pc = (root_pc + 10) % 12
            else:
                # Major chord: add major 7th for jazz/soulful/rnb.
                seventh_pc = (root_pc + 11) % 12

        # Place the 7th near the top of the voicing.
        top_note = max(triad)
        seventh_midi = seventh_pc + (top_note // 12) * 12
        while seventh_midi <= top_note:
            seventh_midi += 12
        # If it went too high, bring it down.
        if seventh_midi > MAX_MIDI:
            seventh_midi -= 12
        seventh_midi = _clamp_to_register(seventh_midi)

        result = triad + [seventh_midi]
        return sorted(set(result))

    def _apply_inversion(self, midi_notes: list[int], inversion: int) -> list[int]:
        """Apply inversion by rotating the bottom note(s) up an octave.

        Args:
            midi_notes: Sorted list of MIDI notes.
            inversion: 0 = root, 1 = first, 2 = second.

        Returns:
            New list of MIDI notes with inversion applied.
        """
        if inversion == 0 or not midi_notes:
            return list(midi_notes)

        notes = sorted(midi_notes)
        for _ in range(min(inversion, len(notes) - 1)):
            lowest = notes.pop(0)
            moved = lowest + 12
            moved = _clamp_to_register(moved)
            notes.append(moved)
        return sorted(notes)

    def apply_voice_leading(
        self, prev_voicing: list[int], next_chord: str, style: str = "pop"
    ) -> list[int]:
        """Generate a voice-led voicing for the next chord.

        Minimizes total pitch movement from the previous voicing by
        choosing the closest available pitch for each voice.

        Args:
            prev_voicing: Previous chord voicing (list of MIDI notes).
            next_chord: Next chord symbol.
            style: Voicing style.

        Returns:
            Voice-led voicing with same number of notes as prev_voicing.
        """
        cs = _chord_symbol_to_music21(next_chord)
        target_pcs = [p.midi % 12 for p in cs.pitches]
        template = self.style_templates.get(style, self.style_templates["pop"])

        # For extended styles, add the 7th pitch class.
        if template.get("extensions") and template.get("add_seventh"):
            root_pc = cs.root().midi % 12
            # Check if a 7th is already present.
            has_seventh = False
            for p in cs.pitches:
                interval = (p.midi % 12 - root_pc) % 12
                if interval in (10, 11):
                    has_seventh = True
                    break
            if not has_seventh:
                if cs.quality == "minor":
                    target_pcs.append((root_pc + 10) % 12)
                else:
                    target_pcs.append((root_pc + 11) % 12)

        # For classical, ensure we have enough pitch classes.
        if template.get("double_root"):
            root_pc = cs.root().midi % 12
            # Ensure root is in target_pcs twice conceptually.
            if len(target_pcs) < len(prev_voicing):
                target_pcs.append(root_pc)

        num_voices = len(prev_voicing)
        result = []

        # For each voice in the previous voicing, find the closest note
        # that belongs to the target chord.
        used_assignments: list[tuple[int, int]] = []  # (voice_idx, chosen_midi)

        for i, prev_note in enumerate(prev_voicing):
            best_note: Optional[int] = None
            best_dist = float("inf")
            for pc in target_pcs:
                # Try the pitch class in multiple octaves near the previous note.
                for octave_shift in range(-1, 2):
                    candidate = pc + ((prev_note // 12) + octave_shift) * 12
                    if MIN_MIDI <= candidate <= MAX_MIDI:
                        dist = abs(candidate - prev_note)
                        if dist < best_dist:
                            best_dist = dist
                            best_note = candidate
            if best_note is not None:
                result.append(best_note)
            else:
                # Fallback: use previous note adjusted to nearest target pc.
                result.append(_clamp_to_register(prev_note))

        # Ensure we have all required pitch classes represented.
        result_pcs = set(n % 12 for n in result)
        for pc in target_pcs:
            if pc not in result_pcs:
                # Find the voice that can best accommodate this pitch class.
                best_idx = -1
                best_dist = float("inf")
                for i, note in enumerate(result):
                    for octave_shift in range(-1, 2):
                        candidate = pc + ((note // 12) + octave_shift) * 12
                        if MIN_MIDI <= candidate <= MAX_MIDI:
                            dist = abs(candidate - prev_voicing[i])
                            if dist < best_dist:
                                best_dist = dist
                                best_idx = i
                                best_candidate = candidate
                if best_idx >= 0:
                    result[best_idx] = best_candidate
                    result_pcs = set(n % 12 for n in result)

        # Clamp and sort.
        result = [_clamp_to_register(n) for n in result]
        return sorted(result)
