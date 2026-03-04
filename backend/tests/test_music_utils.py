"""Tests for music theory utility functions."""

import pytest

from src.music.music_utils import (
    interval_semitones,
    midi_to_note_name,
    note_name_to_midi,
    transpose,
)


# ---------------------------------------------------------------------------
# Tests: note_name_to_midi
# ---------------------------------------------------------------------------

class TestNoteNameToMidi:
    """Test conversion from note name strings to MIDI numbers."""

    def test_middle_c(self):
        """C4 should map to MIDI 60."""
        assert note_name_to_midi("C4") == 60

    def test_a4_concert_pitch(self):
        """A4 should map to MIDI 69 (concert A = 440 Hz)."""
        assert note_name_to_midi("A4") == 69

    def test_lowest_piano_key(self):
        """A0 should map to MIDI 21."""
        assert note_name_to_midi("A0") == 21

    def test_c_sharp(self):
        """C#4 should map to MIDI 61."""
        assert note_name_to_midi("C#4") == 61

    def test_d_flat(self):
        """Db4 should map to MIDI 61 (enharmonic of C#4)."""
        assert note_name_to_midi("Db4") == 61

    def test_b4(self):
        """B4 should map to MIDI 71."""
        assert note_name_to_midi("B4") == 71

    def test_c5(self):
        """C5 should map to MIDI 72."""
        assert note_name_to_midi("C5") == 72

    def test_f_sharp_3(self):
        """F#3 should map to MIDI 54."""
        assert note_name_to_midi("F#3") == 54

    def test_invalid_note_raises(self):
        """An invalid note name should raise a ValueError."""
        with pytest.raises(ValueError):
            note_name_to_midi("X4")

    def test_missing_octave_raises(self):
        """A note name without an octave should raise a ValueError."""
        with pytest.raises(ValueError):
            note_name_to_midi("C")

    def test_e_flat_2(self):
        """Eb2 should map to MIDI 39."""
        assert note_name_to_midi("Eb2") == 39

    def test_g_sharp_5(self):
        """G#5 should map to MIDI 80."""
        assert note_name_to_midi("G#5") == 80


# ---------------------------------------------------------------------------
# Tests: midi_to_note_name
# ---------------------------------------------------------------------------

class TestMidiToNoteName:
    """Test conversion from MIDI numbers to note name strings."""

    def test_midi_60_is_c4(self):
        """MIDI 60 should be C4."""
        assert midi_to_note_name(60) == "C4"

    def test_midi_69_is_a4(self):
        """MIDI 69 should be A4."""
        assert midi_to_note_name(69) == "A4"

    def test_midi_21_is_a0(self):
        """MIDI 21 should be A0."""
        assert midi_to_note_name(21) == "A0"

    def test_midi_72_is_c5(self):
        """MIDI 72 should be C5."""
        assert midi_to_note_name(72) == "C5"

    def test_midi_61_is_sharp(self):
        """MIDI 61 should be C#4 (using sharp convention)."""
        result = midi_to_note_name(61)
        # Accept either C#4 or Db4
        assert result in ("C#4", "Db4")

    def test_roundtrip_c4(self):
        """Converting C4 to MIDI and back should return C4."""
        midi = note_name_to_midi("C4")
        name = midi_to_note_name(midi)
        assert name == "C4"

    def test_roundtrip_a4(self):
        """Converting A4 to MIDI and back should return A4."""
        midi = note_name_to_midi("A4")
        name = midi_to_note_name(midi)
        assert name == "A4"


# ---------------------------------------------------------------------------
# Tests: interval_semitones
# ---------------------------------------------------------------------------

class TestIntervalSemitones:
    """Test interval name to semitone count mapping."""

    def test_unison(self):
        assert interval_semitones("unison") == 0

    def test_minor_second(self):
        assert interval_semitones("minor_second") == 1

    def test_major_second(self):
        assert interval_semitones("major_second") == 2

    def test_minor_third(self):
        assert interval_semitones("minor_third") == 3

    def test_major_third(self):
        assert interval_semitones("major_third") == 4

    def test_perfect_fourth(self):
        assert interval_semitones("perfect_fourth") == 5

    def test_tritone(self):
        assert interval_semitones("tritone") == 6

    def test_perfect_fifth(self):
        assert interval_semitones("perfect_fifth") == 7

    def test_octave(self):
        assert interval_semitones("octave") == 12

    def test_invalid_interval_raises(self):
        with pytest.raises(ValueError):
            interval_semitones("thirteenth")


# ---------------------------------------------------------------------------
# Tests: transpose
# ---------------------------------------------------------------------------

class TestTranspose:
    """Test MIDI note transposition."""

    def test_transpose_up(self):
        """Transposing C4 up 7 semitones gives G4."""
        assert transpose(60, 7) == 67

    def test_transpose_down(self):
        """Transposing C4 down 12 semitones gives C3."""
        assert transpose(60, -12) == 48

    def test_transpose_zero(self):
        """Transposing by 0 returns the same note."""
        assert transpose(60, 0) == 60

    def test_transpose_preserves_type(self):
        """Result should be an integer."""
        result = transpose(60, 5)
        assert isinstance(result, int)

    def test_transpose_negative_result(self):
        """Large downward transposition can go below zero."""
        result = transpose(10, -20)
        assert result == -10
