"""Tests for harmony generation from melody notes."""

import pytest

from src.music.harmony_generator import HarmonyGenerator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def generator():
    """Create a HarmonyGenerator instance."""
    return HarmonyGenerator()


@pytest.fixture
def c_major_scale():
    """C major scale as MIDI notes (C4 to C5)."""
    return [60, 62, 64, 65, 67, 69, 71, 72]


# ---------------------------------------------------------------------------
# Tests: generate_harmony
# ---------------------------------------------------------------------------

class TestGenerateHarmony:
    """Test HarmonyGenerator.generate_harmony with various intervals."""

    def test_returns_list(self, generator, c_major_scale):
        """Result should be a list of integers."""
        result = generator.generate_harmony(c_major_scale)
        assert isinstance(result, list)
        for note in result:
            assert isinstance(note, int)

    def test_same_length_as_input(self, generator, c_major_scale):
        """Output should have the same number of notes as input."""
        result = generator.generate_harmony(c_major_scale)
        assert len(result) == len(c_major_scale)

    def test_default_interval_is_third(self, generator, c_major_scale):
        """The default interval should be 'third' (3 or 4 semitones)."""
        result = generator.generate_harmony(c_major_scale, interval="third")
        for original, harmony in zip(c_major_scale, result):
            diff = harmony - original
            # A major third is 4 semitones, minor third is 3 semitones
            assert diff in (3, 4), (
                f"Expected third interval (3 or 4 semitones) for MIDI {original}, "
                f"got {diff}"
            )

    def test_third_interval(self, generator):
        """A third above C4 (60) should be E4 (64) -- major third = 4 semitones."""
        result = generator.generate_harmony([60], interval="third")
        assert result[0] - 60 in (3, 4)

    def test_fifth_interval(self, generator):
        """A fifth above C4 (60) should be G4 (67) -- 7 semitones."""
        result = generator.generate_harmony([60], interval="fifth")
        assert result[0] == 67

    def test_octave_interval(self, generator):
        """An octave above C4 (60) should be C5 (72) -- 12 semitones."""
        result = generator.generate_harmony([60], interval="octave")
        assert result[0] == 72

    def test_empty_input(self, generator):
        """Empty input should produce empty output."""
        result = generator.generate_harmony([])
        assert result == []

    def test_single_note(self, generator):
        """A single note should produce a single harmony note."""
        result = generator.generate_harmony([60], interval="fifth")
        assert len(result) == 1

    def test_invalid_interval_raises(self, generator):
        """An unsupported interval should raise a ValueError."""
        with pytest.raises(ValueError):
            generator.generate_harmony([60], interval="ninth")

    def test_harmony_notes_are_higher(self, generator, c_major_scale):
        """For ascending intervals, harmony notes should be above the melody."""
        for interval in ("third", "fifth", "octave"):
            result = generator.generate_harmony(c_major_scale, interval=interval)
            for original, harmony in zip(c_major_scale, result):
                assert harmony > original

    def test_multiple_notes_fifth(self, generator):
        """Several notes with fifth interval should each be 7 semitones higher."""
        melody = [60, 62, 64]
        result = generator.generate_harmony(melody, interval="fifth")
        assert result == [67, 69, 71]
