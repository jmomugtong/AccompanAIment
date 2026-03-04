"""Tests for MIDI generation: score creation, tracks, tempo, file output."""

import os
import tempfile

import pytest

from src.music.midi_generator import MIDIGenerator


class TestMIDIGeneratorInit:
    """Test MIDIGenerator initialization."""

    def test_initialization(self):
        """MIDIGenerator should initialize without errors."""
        mg = MIDIGenerator()
        assert mg is not None

    def test_initialization_with_defaults(self):
        """MIDIGenerator should have sensible defaults."""
        mg = MIDIGenerator()
        assert mg.tempo == 120
        assert mg.time_signature == (4, 4)

    def test_initialization_with_custom_params(self):
        """MIDIGenerator should accept custom tempo and time signature."""
        mg = MIDIGenerator(tempo=90, time_signature=(3, 4))
        assert mg.tempo == 90
        assert mg.time_signature == (3, 4)


class TestScoreCreation:
    """Test score creation with tempo and time signature."""

    def test_create_score(self):
        """create_score should produce a music21 Score object."""
        mg = MIDIGenerator()
        score = mg.create_score()
        assert score is not None

    def test_create_score_with_tempo(self):
        """Score should have the correct tempo marking."""
        mg = MIDIGenerator(tempo=140)
        score = mg.create_score()
        # Extract tempo from the score
        tempos = score.metronomeMarkBoundaries()
        assert len(tempos) > 0
        # The tempo number should match what we set
        assert tempos[0][2].number == 140

    def test_create_score_with_time_signature(self):
        """Score should have the correct time signature."""
        mg = MIDIGenerator(time_signature=(3, 4))
        score = mg.create_score()
        # Extract time signature from the score
        ts_list = score.getTimeSignatures()
        assert len(ts_list) > 0
        assert ts_list[0].numerator == 3
        assert ts_list[0].denominator == 4

    def test_create_score_default_4_4(self):
        """Default score should be in 4/4 time."""
        mg = MIDIGenerator()
        score = mg.create_score()
        ts_list = score.getTimeSignatures()
        assert len(ts_list) > 0
        assert ts_list[0].numerator == 4
        assert ts_list[0].denominator == 4

    def test_create_score_6_8_time(self):
        """Should support 6/8 time signature."""
        mg = MIDIGenerator(time_signature=(6, 8))
        score = mg.create_score()
        ts_list = score.getTimeSignatures()
        assert ts_list[0].numerator == 6
        assert ts_list[0].denominator == 8


class TestMelodyTrack:
    """Test adding melody track to the score."""

    def test_add_melody_track(self):
        """Should add a melody track with given notes and durations."""
        mg = MIDIGenerator()
        mg.create_score()
        notes = [60, 62, 64, 65, 67]
        durations = [1.0, 1.0, 1.0, 1.0, 1.0]
        mg.add_melody_track(notes, durations)
        assert mg.melody_part is not None

    def test_melody_track_has_correct_note_count(self):
        """Melody track should contain the right number of note events."""
        mg = MIDIGenerator()
        mg.create_score()
        notes = [60, 62, 64]
        durations = [1.0, 1.0, 1.0]
        mg.add_melody_track(notes, durations)
        # Count Note objects in the melody part
        from music21 import note as m21note
        note_count = len(mg.melody_part.recurse().getElementsByClass(m21note.Note))
        assert note_count == 3

    def test_melody_track_note_values(self):
        """Melody notes should correspond to the correct MIDI pitches."""
        mg = MIDIGenerator()
        mg.create_score()
        notes = [60, 64, 67]
        durations = [1.0, 1.0, 1.0]
        mg.add_melody_track(notes, durations)
        from music21 import note as m21note
        melody_notes = list(mg.melody_part.recurse().getElementsByClass(m21note.Note))
        assert melody_notes[0].pitch.midi == 60  # C4
        assert melody_notes[1].pitch.midi == 64  # E4
        assert melody_notes[2].pitch.midi == 67  # G4

    def test_melody_track_durations(self):
        """Melody note durations should match input durations."""
        mg = MIDIGenerator()
        mg.create_score()
        notes = [60, 62]
        durations = [2.0, 0.5]
        mg.add_melody_track(notes, durations)
        from music21 import note as m21note
        melody_notes = list(mg.melody_part.recurse().getElementsByClass(m21note.Note))
        assert melody_notes[0].quarterLength == 2.0
        assert melody_notes[1].quarterLength == 0.5

    def test_melody_track_with_rests(self):
        """MIDI note 0 should be treated as a rest."""
        mg = MIDIGenerator()
        mg.create_score()
        notes = [60, 0, 64]
        durations = [1.0, 1.0, 1.0]
        mg.add_melody_track(notes, durations)
        from music21 import note as m21note
        melody_notes = list(mg.melody_part.recurse().getElementsByClass(m21note.Note))
        # Only 2 actual notes (60, 64); the 0 becomes a rest
        assert len(melody_notes) == 2

    def test_melody_mismatched_lengths_raises_error(self):
        """Notes and durations must have the same length."""
        mg = MIDIGenerator()
        mg.create_score()
        with pytest.raises(ValueError):
            mg.add_melody_track([60, 62], [1.0])


class TestAccompanimentTrack:
    """Test adding accompaniment track with chord voicings."""

    def test_add_accompaniment_track(self):
        """Should add an accompaniment track with chord voicings."""
        mg = MIDIGenerator()
        mg.create_score()
        voicings = [[48, 52, 55], [53, 57, 60]]
        durations = [4.0, 4.0]
        mg.add_accompaniment_track(voicings, durations)
        assert mg.accompaniment_part is not None

    def test_accompaniment_track_has_chords(self):
        """Accompaniment track should contain chord objects."""
        mg = MIDIGenerator()
        mg.create_score()
        voicings = [[48, 52, 55], [53, 57, 60]]
        durations = [4.0, 4.0]
        mg.add_accompaniment_track(voicings, durations)
        from music21 import chord as m21chord
        chords = list(mg.accompaniment_part.recurse().getElementsByClass(m21chord.Chord))
        assert len(chords) == 2

    def test_accompaniment_chord_pitches(self):
        """Chord pitches should match the input voicings."""
        mg = MIDIGenerator()
        mg.create_score()
        voicings = [[48, 52, 55]]
        durations = [4.0]
        mg.add_accompaniment_track(voicings, durations)
        from music21 import chord as m21chord
        chords = list(mg.accompaniment_part.recurse().getElementsByClass(m21chord.Chord))
        midi_values = sorted([p.midi for p in chords[0].pitches])
        assert midi_values == [48, 52, 55]

    def test_accompaniment_durations(self):
        """Accompaniment chord durations should match input."""
        mg = MIDIGenerator()
        mg.create_score()
        voicings = [[48, 52, 55]]
        durations = [2.0]
        mg.add_accompaniment_track(voicings, durations)
        from music21 import chord as m21chord
        chords = list(mg.accompaniment_part.recurse().getElementsByClass(m21chord.Chord))
        assert chords[0].quarterLength == 2.0

    def test_accompaniment_mismatched_lengths_raises_error(self):
        """Voicings and durations must have the same length."""
        mg = MIDIGenerator()
        mg.create_score()
        with pytest.raises(ValueError):
            mg.add_accompaniment_track([[48, 52, 55]], [4.0, 4.0])

    def test_accompaniment_with_empty_voicing_as_rest(self):
        """An empty voicing list should be treated as a rest."""
        mg = MIDIGenerator()
        mg.create_score()
        voicings = [[48, 52, 55], [], [53, 57, 60]]
        durations = [4.0, 4.0, 4.0]
        mg.add_accompaniment_track(voicings, durations)
        from music21 import chord as m21chord
        chords = list(mg.accompaniment_part.recurse().getElementsByClass(m21chord.Chord))
        # Only 2 actual chords; the empty voicing is a rest
        assert len(chords) == 2


class TestMIDIFileOutput:
    """Test writing MIDI files to disk."""

    def test_write_midi_creates_file(self):
        """write_midi should create a MIDI file at the given path."""
        mg = MIDIGenerator()
        mg.create_score()
        mg.add_melody_track([60, 62, 64], [1.0, 1.0, 1.0])
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_output.mid")
            result = mg.write_midi(path)
            assert os.path.exists(result)

    def test_write_midi_file_is_nonempty(self):
        """Written MIDI file should have non-zero size."""
        mg = MIDIGenerator()
        mg.create_score()
        mg.add_melody_track([60, 62, 64], [1.0, 1.0, 1.0])
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_output.mid")
            result = mg.write_midi(path)
            assert os.path.getsize(result) > 0

    def test_write_midi_returns_path(self):
        """write_midi should return the file path as a string."""
        mg = MIDIGenerator()
        mg.create_score()
        mg.add_melody_track([60, 62, 64], [1.0, 1.0, 1.0])
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "output.mid")
            result = mg.write_midi(path)
            assert isinstance(result, str)
            assert result.endswith(".mid")

    def test_write_midi_with_both_tracks(self):
        """Should write a MIDI file containing both melody and accompaniment."""
        mg = MIDIGenerator()
        mg.create_score()
        mg.add_melody_track([60, 64, 67], [1.0, 1.0, 1.0])
        mg.add_accompaniment_track([[48, 52, 55], [53, 57, 60], [43, 47, 50]], [1.0, 1.0, 1.0])
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "full_output.mid")
            result = mg.write_midi(path)
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0

    def test_write_midi_correct_extension(self):
        """Output file should have .mid extension."""
        mg = MIDIGenerator()
        mg.create_score()
        mg.add_melody_track([60], [1.0])
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.mid")
            result = mg.write_midi(path)
            assert result.endswith(".mid")


class TestTrackSeparation:
    """Test that melody and accompaniment are on separate tracks."""

    def test_melody_and_accompaniment_are_separate_parts(self):
        """Melody and accompaniment should be different Part objects in the score."""
        mg = MIDIGenerator()
        mg.create_score()
        mg.add_melody_track([60, 62, 64], [1.0, 1.0, 1.0])
        mg.add_accompaniment_track([[48, 52, 55]], [3.0])
        assert mg.melody_part is not mg.accompaniment_part

    def test_score_has_two_parts(self):
        """Score with both tracks should have exactly 2 parts."""
        mg = MIDIGenerator()
        mg.create_score()
        mg.add_melody_track([60, 62, 64], [1.0, 1.0, 1.0])
        mg.add_accompaniment_track([[48, 52, 55]], [3.0])
        from music21 import stream
        parts = mg.score.getElementsByClass(stream.Part)
        assert len(parts) == 2

    def test_melody_only_score_has_one_part(self):
        """Score with only melody should have 1 part."""
        mg = MIDIGenerator()
        mg.create_score()
        mg.add_melody_track([60, 62, 64], [1.0, 1.0, 1.0])
        from music21 import stream
        parts = mg.score.getElementsByClass(stream.Part)
        assert len(parts) == 1

    def test_accompaniment_only_score_has_one_part(self):
        """Score with only accompaniment should have 1 part."""
        mg = MIDIGenerator()
        mg.create_score()
        mg.add_accompaniment_track([[48, 52, 55]], [4.0])
        from music21 import stream
        parts = mg.score.getElementsByClass(stream.Part)
        assert len(parts) == 1

    def test_parts_have_correct_instrument_names(self):
        """Parts should have identifiable names (melody vs accompaniment)."""
        mg = MIDIGenerator()
        mg.create_score()
        mg.add_melody_track([60, 62, 64], [1.0, 1.0, 1.0])
        mg.add_accompaniment_track([[48, 52, 55]], [3.0])
        assert mg.melody_part.partName is not None
        assert mg.accompaniment_part.partName is not None
        assert mg.melody_part.partName != mg.accompaniment_part.partName

    def test_written_midi_has_separate_tracks(self):
        """Reading the written MIDI back should show separate tracks."""
        mg = MIDIGenerator()
        mg.create_score()
        mg.add_melody_track([60, 64, 67], [1.0, 1.0, 1.0])
        mg.add_accompaniment_track(
            [[48, 52, 55], [53, 57, 60], [55, 59, 62]],
            [1.0, 1.0, 1.0]
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "tracks_test.mid")
            mg.write_midi(path)
            # Read back and verify structure
            from music21 import converter, stream
            parsed = converter.parse(path)
            parts = parsed.getElementsByClass(stream.Part)
            assert len(parts) >= 2
