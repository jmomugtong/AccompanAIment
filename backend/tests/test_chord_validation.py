"""Tests for chord validation, parsing, and music theory utilities.

Covers:
- Valid chord name parsing (triads, 7ths, extended, altered, sus, dim, aug)
- Invalid chord rejection (gibberish strings)
- Chord progression parsing from string ("C | F | G | C")
- Time signature parsing (4/4, 3/4, 6/8)
- Tempo validation (40-240 BPM)
- Extended chord support (9ths, 11ths, 13ths)
"""

import pytest

from src.music.chord_validator import ChordValidator
from src.music.chord_parser import ChordParser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def validator():
    """Return a ChordValidator instance."""
    return ChordValidator()


@pytest.fixture
def parser():
    """Return a ChordParser instance."""
    return ChordParser()


# ===========================================================================
# ChordValidator -- valid chord name parsing
# ===========================================================================

class TestValidChordNames:
    """Ensure common chord symbols are recognised as valid."""

    @pytest.mark.parametrize("chord_name", [
        "C", "D", "E", "F", "G", "A", "B",
    ])
    def test_natural_major_triads(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Cm", "Dm", "Em", "Fm", "Gm", "Am", "Bm",
    ])
    def test_natural_minor_triads(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "C#", "Db", "F#", "Gb", "Bb", "Eb", "Ab",
    ])
    def test_sharps_and_flats(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "C#m", "Dbm", "F#m", "Gbm", "Bbm", "Ebm", "Abm",
    ])
    def test_sharp_flat_minor_triads(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "C7", "D7", "G7", "Bb7", "F#7",
    ])
    def test_dominant_seventh(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Cmaj7", "Dmaj7", "Fmaj7", "Bbmaj7", "Ebmaj7",
    ])
    def test_major_seventh(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Cm7", "Dm7", "Am7", "Bbm7", "F#m7",
    ])
    def test_minor_seventh(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Csus4", "Dsus4", "Gsus4", "Absus4",
    ])
    def test_sus4_chords(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Csus2", "Dsus2", "Gsus2",
    ])
    def test_sus2_chords(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Cdim", "Ddim", "Bdim", "F#dim",
    ])
    def test_diminished_triads(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Cdim7", "Ddim7", "Bdim7",
    ])
    def test_diminished_seventh(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Caug", "Daug", "Eaug", "Abaug",
    ])
    def test_augmented_triads(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "C+", "D+", "Ab+",
    ])
    def test_augmented_plus_notation(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Co", "Do", "F#o",
    ])
    def test_diminished_circle_notation(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    def test_half_diminished(self, validator):
        assert validator.is_valid_chord("Cm7b5") is True

    def test_augmented_seventh(self, validator):
        assert validator.is_valid_chord("Caug7") is True

    def test_add9(self, validator):
        assert validator.is_valid_chord("Cadd9") is True

    def test_add11(self, validator):
        assert validator.is_valid_chord("Cadd11") is True

    def test_six_chord(self, validator):
        assert validator.is_valid_chord("C6") is True

    def test_minor_six_chord(self, validator):
        assert validator.is_valid_chord("Cm6") is True


# ===========================================================================
# ChordValidator -- extended chords (9ths, 11ths, 13ths)
# ===========================================================================

class TestExtendedChords:
    """Test 9th, 11th, 13th chords and their variations."""

    @pytest.mark.parametrize("chord_name", [
        "C9", "D9", "G9", "Bb9",
    ])
    def test_dominant_ninth(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Cmaj9", "Fmaj9", "Bbmaj9",
    ])
    def test_major_ninth(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Cm9", "Dm9", "Am9",
    ])
    def test_minor_ninth(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "C11", "G11", "Bb11",
    ])
    def test_dominant_eleventh(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Cm11", "Dm11",
    ])
    def test_minor_eleventh(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "C13", "G13", "Bb13",
    ])
    def test_dominant_thirteenth(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Cmaj13", "Fmaj13",
    ])
    def test_major_thirteenth(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True

    @pytest.mark.parametrize("chord_name", [
        "Cm13", "Am13",
    ])
    def test_minor_thirteenth(self, validator, chord_name):
        assert validator.is_valid_chord(chord_name) is True


# ===========================================================================
# ChordValidator -- invalid chord rejection
# ===========================================================================

class TestInvalidChordNames:
    """Gibberish and malformed strings must be rejected."""

    @pytest.mark.parametrize("bad_name", [
        "",
        "X",
        "H",
        "Cmayor",
        "hello",
        "123",
        "Czz",
        "C##",
        "Cbb",
        "M7",
        "m7",
        "sus4",
        "dim",
        "CMAJ7",
        "c",
        "  ",
        "C |",
        "Cmaj7b5#11add13",
    ])
    def test_gibberish_rejected(self, validator, bad_name):
        assert validator.is_valid_chord(bad_name) is False


# ===========================================================================
# ChordValidator -- validate_chord_name returns details
# ===========================================================================

class TestChordDetails:
    """validate_chord_name should return structured info about a chord."""

    def test_returns_root_for_c_major(self, validator):
        info = validator.get_chord_info("C")
        assert info is not None
        assert info["root"] == "C"

    def test_returns_quality_major(self, validator):
        info = validator.get_chord_info("C")
        assert info["quality"] == "major"

    def test_returns_quality_minor(self, validator):
        info = validator.get_chord_info("Cm")
        assert info["quality"] == "minor"

    def test_returns_root_with_accidental(self, validator):
        info = validator.get_chord_info("F#m")
        assert info["root"] == "F#"

    def test_returns_root_with_flat(self, validator):
        info = validator.get_chord_info("Bb7")
        assert info["root"] == "Bb"

    def test_returns_none_for_invalid(self, validator):
        info = validator.get_chord_info("XYZ")
        assert info is None

    def test_returns_extensions(self, validator):
        info = validator.get_chord_info("Cmaj7")
        assert info is not None
        assert "7" in info.get("extension", "")

    def test_returns_pitches_list(self, validator):
        info = validator.get_chord_info("C")
        assert info is not None
        assert isinstance(info["pitches"], list)
        assert len(info["pitches"]) >= 3


# ===========================================================================
# ChordParser -- progression parsing
# ===========================================================================

class TestChordProgressionParsing:
    """Parse chord progressions from pipe-delimited strings."""

    def test_basic_four_bar_progression(self, parser):
        result = parser.parse_progression("C | F | G | C")
        assert result.chords == ["C", "F", "G", "C"]

    def test_progression_with_minor_chords(self, parser):
        result = parser.parse_progression("Am | F | C | G")
        assert result.chords == ["Am", "F", "C", "G"]

    def test_progression_with_sevenths(self, parser):
        result = parser.parse_progression("Cmaj7 | Dm7 | G7 | Cmaj7")
        assert result.chords == ["Cmaj7", "Dm7", "G7", "Cmaj7"]

    def test_whitespace_is_trimmed(self, parser):
        result = parser.parse_progression("  C  |  F  |  G  |  C  ")
        assert result.chords == ["C", "F", "G", "C"]

    def test_single_chord(self, parser):
        result = parser.parse_progression("Am")
        assert result.chords == ["Am"]

    def test_many_bars(self, parser):
        prog = "C | Am | F | G | C | Am | F | G"
        result = parser.parse_progression(prog)
        assert len(result.chords) == 8

    def test_extended_chords_in_progression(self, parser):
        result = parser.parse_progression("Cmaj9 | Dm11 | G13 | Cmaj7")
        assert result.chords == ["Cmaj9", "Dm11", "G13", "Cmaj7"]

    def test_sharp_flat_chords_in_progression(self, parser):
        result = parser.parse_progression("F#m | Bb | Eb | Ab")
        assert result.chords == ["F#m", "Bb", "Eb", "Ab"]

    def test_empty_string_raises(self, parser):
        with pytest.raises(ValueError, match="empty"):
            parser.parse_progression("")

    def test_whitespace_only_raises(self, parser):
        with pytest.raises(ValueError, match="empty"):
            parser.parse_progression("   ")

    def test_invalid_chord_in_progression_raises(self, parser):
        with pytest.raises(ValueError, match="[Ii]nvalid"):
            parser.parse_progression("C | XYZ | G | C")

    def test_result_has_bar_count(self, parser):
        result = parser.parse_progression("C | F | G | C")
        assert result.bar_count == 4

    def test_result_is_valid_flag(self, parser):
        result = parser.parse_progression("C | F | G | C")
        assert result.is_valid is True

    def test_dash_delimiter(self, parser):
        """Allow dash as an alternative delimiter."""
        result = parser.parse_progression("C - F - G - C")
        assert result.chords == ["C", "F", "G", "C"]

    def test_two_chords_per_bar(self, parser):
        """Two chords in a single bar separated by space within a bar."""
        result = parser.parse_progression("C Am | F G | Dm Em | C G")
        assert len(result.chords) == 8

    def test_repeat_slash_notation(self, parser):
        """A slash '/' within a bar means repeat previous chord."""
        result = parser.parse_progression("C | / | G | /")
        assert result.chords == ["C", "C", "G", "G"]


# ===========================================================================
# ChordParser -- time signature parsing
# ===========================================================================

class TestTimeSignatureParsing:
    """Parse and validate time signatures."""

    @pytest.mark.parametrize("ts_str,beats,beat_type", [
        ("4/4", 4, 4),
        ("3/4", 3, 4),
        ("6/8", 6, 8),
        ("2/4", 2, 4),
        ("5/4", 5, 4),
        ("7/8", 7, 8),
        ("12/8", 12, 8),
        ("2/2", 2, 2),
    ])
    def test_valid_time_signatures(self, parser, ts_str, beats, beat_type):
        ts = parser.parse_time_signature(ts_str)
        assert ts.numerator == beats
        assert ts.denominator == beat_type

    @pytest.mark.parametrize("bad_ts", [
        "",
        "4",
        "/4",
        "4/",
        "0/4",
        "4/0",
        "4/3",
        "abc",
        "4/4/4",
        "-1/4",
        "4/5",
    ])
    def test_invalid_time_signatures_raise(self, parser, bad_ts):
        with pytest.raises(ValueError):
            parser.parse_time_signature(bad_ts)


# ===========================================================================
# ChordParser -- tempo validation
# ===========================================================================

class TestTempoValidation:
    """Validate tempo is within 40-240 BPM."""

    @pytest.mark.parametrize("bpm", [40, 60, 100, 120, 180, 240])
    def test_valid_tempos(self, parser, bpm):
        assert parser.validate_tempo(bpm) is True

    @pytest.mark.parametrize("bpm", [0, -10, 39, 241, 300, 1000])
    def test_invalid_tempos(self, parser, bpm):
        assert parser.validate_tempo(bpm) is False

    def test_boundary_40(self, parser):
        assert parser.validate_tempo(40) is True

    def test_boundary_240(self, parser):
        assert parser.validate_tempo(240) is True

    def test_boundary_39(self, parser):
        assert parser.validate_tempo(39) is False

    def test_boundary_241(self, parser):
        assert parser.validate_tempo(241) is False

    def test_float_tempo_accepted(self, parser):
        """Float BPM like 120.5 should be accepted if in range."""
        assert parser.validate_tempo(120.5) is True

    def test_float_tempo_out_of_range(self, parser):
        assert parser.validate_tempo(240.1) is False


# ===========================================================================
# ChordValidator -- batch validation
# ===========================================================================

class TestBatchValidation:
    """Validate a list of chord names in one call."""

    def test_all_valid_returns_true(self, validator):
        assert validator.validate_all(["C", "Am", "F", "G"]) is True

    def test_one_invalid_returns_false(self, validator):
        assert validator.validate_all(["C", "XYZ", "F", "G"]) is False

    def test_empty_list_returns_true(self, validator):
        assert validator.validate_all([]) is True

    def test_returns_invalid_chords_list(self, validator):
        ok, bad = validator.find_invalid(["C", "XYZ", "F", "HH"])
        assert ok is False
        assert "XYZ" in bad
        assert "HH" in bad
        assert "C" not in bad
