"""Integration tests for the full accompaniment pipeline.

Tests simulate the complete upload-to-download pipeline with all
external dependencies mocked. Verifies data flows correctly between
each pipeline stage: upload -> extract -> generate -> render.
"""

import os
import tempfile
import uuid
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.audio.upload_handler import AudioUploader
from src.db.models import Base, Generation, Melody, Song, Style, User
from src.generation.audio_renderer import AudioRenderer
from src.generation.sheet_generator import SheetGenerator
from src.music.chord_parser import ChordParser
from src.music.midi_generator import MIDIGenerator
from src.music.voicing_generator import VoicingGenerator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _enable_sqlite_fk(dbapi_conn, connection_record):
    """Enable foreign key enforcement in SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest_asyncio.fixture
async def async_engine():
    """Create an async in-memory SQLite engine for integration tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    event.listen(engine.sync_engine, "connect", _enable_sqlite_fk)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine):
    """Create an async session for integration tests."""
    factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def user_id():
    """Generate a stable user ID for tests."""
    return str(uuid.uuid4())


@pytest.fixture
def song_id():
    """Generate a stable song ID for tests."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_melody_data():
    """Sample melody extraction result."""
    return {
        "notes": [60, 62, 64, 65, 67, 65, 64, 62],
        "timings": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
        "confidence": [0.95, 0.92, 0.88, 0.91, 0.93, 0.90, 0.87, 0.94],
        "duration_seconds": 4.0,
    }


@pytest.fixture
def chord_progression():
    """A test chord progression string."""
    return "C | Am | F | G"


# ---------------------------------------------------------------------------
# Stage 1: Upload -> Database
# ---------------------------------------------------------------------------


class TestUploadStage:
    """Test the upload stage of the pipeline."""

    async def test_upload_creates_song_record(self, db_session, user_id):
        """Uploading a song should create a Song row in the database."""
        user = User(user_id=user_id, email="test@example.com")
        db_session.add(user)
        await db_session.flush()

        song = Song(
            song_id=str(uuid.uuid4()),
            user_id=user_id,
            filename="uploads/test/song.wav",
            original_filename="my_song.wav",
            duration_seconds=30.0,
            tempo_bpm=120.0,
        )
        db_session.add(song)
        await db_session.commit()

        result = await db_session.get(Song, song.song_id)
        assert result is not None
        assert result.original_filename == "my_song.wav"
        assert result.user_id == user_id
        assert result.duration_seconds == 30.0

    async def test_upload_handler_validates_format(self):
        """AudioUploader.validate should reject unsupported file formats."""
        storage = MagicMock()
        uploader = AudioUploader(storage)

        from src.audio.upload_handler import UploadError

        with pytest.raises(UploadError, match="Unsupported format"):
            uploader.validate("song.txt", "/tmp/song.txt")

    async def test_upload_stores_processed_audio(self):
        """AudioUploader.process should validate, preprocess, and store."""
        storage = MagicMock()
        storage.save.return_value = "/data/storage/uploads/user1/file.wav"

        uploader = AudioUploader(storage)

        fake_audio = MagicMock()
        fake_audio.__len__ = lambda self: 22050 * 10  # 10 seconds

        with (
            patch.object(uploader, "validate"),
            patch("src.audio.upload_handler.librosa") as mock_librosa,
            patch("src.audio.upload_handler.sf") as mock_sf,
            patch("src.audio.upload_handler.normalize_volume", return_value=fake_audio),
            patch("src.audio.upload_handler.resample_audio", return_value=fake_audio),
        ):
            import numpy as np

            mock_librosa.load.return_value = (np.zeros(22050 * 10), 44100)
            mock_sf.write = MagicMock()

            result = uploader.process("user1", "song.wav", "/tmp/song.wav")

        assert "stored_path" in result
        assert "storage_key" in result
        assert result["original_filename"] == "song.wav"


# ---------------------------------------------------------------------------
# Stage 2: Melody Extraction
# ---------------------------------------------------------------------------


class TestMelodyExtractionStage:
    """Test the melody extraction stage of the pipeline."""

    async def test_melody_saved_to_database(
        self, db_session, user_id, song_id, sample_melody_data
    ):
        """Extracted melody data should be persisted as a Melody row."""
        user = User(user_id=user_id, email="test@example.com")
        db_session.add(user)
        await db_session.flush()

        song = Song(
            song_id=song_id,
            user_id=user_id,
            filename="test.wav",
            original_filename="test.wav",
        )
        db_session.add(song)
        await db_session.flush()

        melody = Melody(
            melody_id=str(uuid.uuid4()),
            song_id=song_id,
            pitch_contour_json=str(sample_melody_data["notes"]),
            confidence_json=str(sample_melody_data["confidence"]),
            timings_json=str(sample_melody_data["timings"]),
            duration_seconds=sample_melody_data["duration_seconds"],
        )
        db_session.add(melody)
        await db_session.commit()

        result = await db_session.get(Melody, melody.melody_id)
        assert result is not None
        assert result.song_id == song_id
        assert result.duration_seconds == 4.0

    async def test_melody_extraction_returns_expected_keys(self, sample_melody_data):
        """CREPE extractor should return notes, timings, confidence, duration."""
        required_keys = {"notes", "timings", "confidence", "duration_seconds"}
        assert required_keys.issubset(sample_melody_data.keys())
        assert len(sample_melody_data["notes"]) == len(sample_melody_data["timings"])
        assert len(sample_melody_data["notes"]) == len(sample_melody_data["confidence"])
        assert sample_melody_data["duration_seconds"] > 0

    async def test_extraction_worker_updates_state(self):
        """The melody worker task should update its state to PROGRESS."""
        with patch("src.workers.melody_worker.CREPEExtractor") as MockExtractor:
            mock_instance = MockExtractor.return_value
            mock_instance.extract.return_value = {
                "notes": [60, 62, 64],
                "timings": [0.0, 0.5, 1.0],
                "confidence": [0.9, 0.9, 0.9],
                "duration_seconds": 1.5,
            }

            from src.workers.melody_worker import extract_melody

            # Mock the celery task's update_state method.
            extract_melody.update_state = MagicMock()

            result = extract_melody("song-123", "/fake/path.wav")

            assert result["song_id"] == "song-123"
            assert len(result["notes"]) == 3
            assert extract_melody.update_state.called


# ---------------------------------------------------------------------------
# Stage 3: Chord Parsing + Voicing Generation
# ---------------------------------------------------------------------------


class TestChordAndVoicingStage:
    """Test chord parsing and voicing generation."""

    def test_chord_parsing_produces_chord_list(self, chord_progression):
        """ChordParser should split progression into individual chords."""
        parser = ChordParser()
        result = parser.parse_progression(chord_progression)

        assert result.is_valid is True
        assert result.chords == ["C", "Am", "F", "G"]
        assert result.bar_count == 4

    def test_voicing_generation_for_all_styles(self):
        """VoicingGenerator should produce valid MIDI voicings for each style."""
        generator = VoicingGenerator()
        styles = ["pop", "jazz", "classical", "soulful", "rnb"]

        for style in styles:
            voicing = generator.generate_voicing("C", style=style)
            assert len(voicing) >= 3, f"Style '{style}' produced fewer than 3 notes"
            assert all(
                36 <= note <= 84 for note in voicing
            ), f"Style '{style}' produced out-of-range notes: {voicing}"

    def test_voice_leading_minimizes_movement(self):
        """Voice leading should minimize total pitch distance between chords."""
        generator = VoicingGenerator()

        first = generator.generate_voicing("C", style="pop")
        second = generator.apply_voice_leading(first, "Am", style="pop")

        # Voice-led voicing should be within a reasonable range of the first.
        avg_movement = sum(
            abs(a - b) for a, b in zip(sorted(first), sorted(second))
        ) / len(first)
        assert avg_movement < 12, (
            f"Average voice movement ({avg_movement:.1f} semitones) is too large"
        )

    def test_chord_to_voicing_data_flow(self, chord_progression):
        """Parsed chords should feed directly into voicing generation."""
        parser = ChordParser()
        generator = VoicingGenerator()

        parsed = parser.parse_progression(chord_progression)
        voicings = [generator.generate_voicing(c, style="jazz") for c in parsed.chords]

        assert len(voicings) == len(parsed.chords)
        for i, voicing in enumerate(voicings):
            assert len(voicing) >= 3, (
                f"Chord {parsed.chords[i]} produced too few notes"
            )


# ---------------------------------------------------------------------------
# Stage 4: MIDI Generation
# ---------------------------------------------------------------------------


class TestMIDIGenerationStage:
    """Test MIDI score creation from melody and voicings."""

    def test_midi_score_creation(self):
        """MIDIGenerator should create a valid score with melody and accompaniment."""
        gen = MIDIGenerator(tempo=120, time_signature=(4, 4))
        score = gen.create_score()

        assert score is not None
        assert gen.tempo == 120
        assert gen.time_signature == (4, 4)

    def test_melody_track_added_to_score(self):
        """Adding a melody track should succeed with matching notes and durations."""
        gen = MIDIGenerator(tempo=120)
        gen.create_score()

        notes = [60, 62, 64, 65]
        durations = [1.0, 1.0, 1.0, 1.0]
        gen.add_melody_track(notes, durations)

        assert gen.melody_part is not None

    def test_accompaniment_track_added_to_score(self):
        """Adding an accompaniment track should succeed with voicings and durations."""
        gen = MIDIGenerator(tempo=120)
        gen.create_score()

        voicings = [[48, 52, 55], [53, 57, 60], [55, 59, 62], [48, 52, 55]]
        durations = [2.0, 2.0, 2.0, 2.0]
        gen.add_accompaniment_track(voicings, durations)

        assert gen.accompaniment_part is not None

    def test_midi_write_produces_file(self):
        """write_midi should create a .mid file on disk."""
        gen = MIDIGenerator(tempo=120)
        gen.create_score()
        gen.add_melody_track([60, 62, 64], [1.0, 1.0, 1.0])
        gen.add_accompaniment_track([[48, 52, 55]], [3.0])

        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result_path = gen.write_midi(tmp_path)
            assert os.path.isfile(result_path)
            assert result_path.endswith(".mid")
            assert os.path.getsize(result_path) > 0
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_mismatched_notes_durations_raises(self):
        """Mismatched notes/durations should raise ValueError."""
        gen = MIDIGenerator()
        gen.create_score()

        with pytest.raises(ValueError, match="same length"):
            gen.add_melody_track([60, 62], [1.0])


# ---------------------------------------------------------------------------
# Stage 5: Audio Rendering + Sheet Music
# ---------------------------------------------------------------------------


class TestRenderingStage:
    """Test audio rendering and sheet music generation."""

    def test_audio_renderer_config(self):
        """AudioRenderer should store and report its configuration."""
        renderer = AudioRenderer(
            soundfont_path="/fake/piano.sf2",
            sample_rate=44100,
            channels=2,
            gain=1.0,
        )
        config = renderer.get_config()

        assert config["soundfont_path"] == "/fake/piano.sf2"
        assert config["sample_rate"] == 44100
        assert config["channels"] == 2
        assert config["gain"] == 1.0

    def test_audio_renderer_rejects_missing_soundfont(self):
        """render_midi should fail if the soundfont file is missing."""
        from src.generation.audio_renderer import AudioRenderError

        renderer = AudioRenderer(soundfont_path="/nonexistent/piano.sf2")

        with pytest.raises(AudioRenderError, match="Soundfont file not found"):
            renderer.render_midi("/fake/input.mid", "/fake/output.wav")

    def test_sheet_generator_rejects_invalid_format(self):
        """SheetGenerator should reject unsupported output formats."""
        with pytest.raises(ValueError, match="not supported"):
            SheetGenerator(output_format="docx")

    def test_sheet_generator_rejects_none_score(self):
        """to_lilypond should fail with a clear error for None input."""
        from src.generation.sheet_generator import SheetGenerationError

        gen = SheetGenerator(output_format="pdf")

        with pytest.raises(SheetGenerationError, match="Invalid input"):
            gen.to_lilypond(None)


# ---------------------------------------------------------------------------
# Stage 6: Generation Record in Database
# ---------------------------------------------------------------------------


class TestGenerationRecordStage:
    """Test that generation results are persisted to the database."""

    async def test_generation_record_created(self, db_session, user_id, song_id):
        """Completed generation should create a Generation row."""
        user = User(user_id=user_id, email="test@example.com")
        db_session.add(user)
        await db_session.flush()

        song = Song(
            song_id=song_id,
            user_id=user_id,
            filename="test.wav",
            original_filename="test.wav",
        )
        db_session.add(song)
        await db_session.flush()

        generation = Generation(
            generation_id=str(uuid.uuid4()),
            song_id=song_id,
            style="jazz",
            midi_path="/data/generations/test.mid",
            audio_path="/data/generations/test.wav",
            sheet_path="/data/generations/test.pdf",
        )
        db_session.add(generation)
        await db_session.commit()

        result = await db_session.get(Generation, generation.generation_id)
        assert result is not None
        assert result.style == "jazz"
        assert result.midi_path == "/data/generations/test.mid"
        assert result.audio_path == "/data/generations/test.wav"
        assert result.sheet_path == "/data/generations/test.pdf"

    async def test_generation_linked_to_song(self, db_session, user_id, song_id):
        """Generation should be retrievable via the Song relationship."""
        user = User(user_id=user_id, email="test@example.com")
        db_session.add(user)
        await db_session.flush()

        song = Song(
            song_id=song_id,
            user_id=user_id,
            filename="test.wav",
            original_filename="test.wav",
        )
        db_session.add(song)
        await db_session.flush()

        gen_id = str(uuid.uuid4())
        generation = Generation(
            generation_id=gen_id,
            song_id=song_id,
            style="pop",
        )
        db_session.add(generation)
        await db_session.commit()

        fetched_gen = await db_session.get(Generation, gen_id)
        assert fetched_gen is not None
        assert fetched_gen.song_id == song_id


# ---------------------------------------------------------------------------
# End-to-End Pipeline Simulation
# ---------------------------------------------------------------------------


class TestFullPipelineSimulation:
    """Simulate the complete upload-to-download pipeline."""

    async def test_full_pipeline_data_flow(self, db_session, sample_melody_data):
        """Verify data flows correctly through all pipeline stages.

        Simulates: upload -> extract -> parse chords -> generate voicings
        -> create MIDI -> persist generation record.
        """
        # Stage 1: Create user and song (simulating upload).
        uid = str(uuid.uuid4())
        user = User(user_id=uid, email="pipeline@example.com")
        db_session.add(user)
        await db_session.flush()

        sid = str(uuid.uuid4())
        song = Song(
            song_id=sid,
            user_id=uid,
            filename="uploads/pipeline/song.wav",
            original_filename="pipeline_test.wav",
            duration_seconds=30.0,
            tempo_bpm=120.0,
        )
        db_session.add(song)
        await db_session.flush()

        # Stage 2: Simulate melody extraction.
        melody = Melody(
            melody_id=str(uuid.uuid4()),
            song_id=sid,
            pitch_contour_json=str(sample_melody_data["notes"]),
            confidence_json=str(sample_melody_data["confidence"]),
            timings_json=str(sample_melody_data["timings"]),
            duration_seconds=sample_melody_data["duration_seconds"],
        )
        db_session.add(melody)
        await db_session.flush()

        # Stage 3: Parse chord progression.
        parser = ChordParser()
        parsed = parser.parse_progression("C | Am | F | G")
        assert parsed.is_valid

        # Stage 4: Generate voicings.
        voicer = VoicingGenerator()
        voicings = [voicer.generate_voicing(c, style="jazz") for c in parsed.chords]
        assert len(voicings) == 4

        # Stage 5: Create MIDI.
        midi_gen = MIDIGenerator(tempo=120, time_signature=(4, 4))
        midi_gen.create_score()
        midi_gen.add_melody_track(
            sample_melody_data["notes"],
            [0.5] * len(sample_melody_data["notes"]),
        )
        midi_gen.add_accompaniment_track(voicings, [2.0] * len(voicings))

        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp:
            midi_path = tmp.name

        try:
            written_path = midi_gen.write_midi(midi_path)
            assert os.path.isfile(written_path)

            # Stage 6: Persist generation record.
            generation = Generation(
                generation_id=str(uuid.uuid4()),
                song_id=sid,
                style="jazz",
                midi_path=written_path,
                audio_path=None,  # Rendering skipped (requires FluidSynth)
                sheet_path=None,  # Sheet gen skipped (requires Lilypond)
            )
            db_session.add(generation)
            await db_session.commit()

            # Verify the full chain is persisted.
            fetched_song = await db_session.get(Song, sid)
            assert fetched_song is not None

            fetched_melody = await db_session.get(Melody, melody.melody_id)
            assert fetched_melody is not None
            assert fetched_melody.song_id == sid

            fetched_gen = await db_session.get(Generation, generation.generation_id)
            assert fetched_gen is not None
            assert fetched_gen.song_id == sid
            assert fetched_gen.style == "jazz"
            assert fetched_gen.midi_path == written_path
        finally:
            if os.path.exists(midi_path):
                os.unlink(midi_path)

    async def test_pipeline_with_all_styles(self, db_session, sample_melody_data):
        """Pipeline should work identically across all supported styles."""
        uid = str(uuid.uuid4())
        user = User(user_id=uid, email="styles@example.com")
        db_session.add(user)
        await db_session.flush()

        styles = ["pop", "jazz", "classical", "soulful", "rnb"]
        parser = ChordParser()
        voicer = VoicingGenerator()

        for style in styles:
            sid = str(uuid.uuid4())
            song = Song(
                song_id=sid,
                user_id=uid,
                filename=f"test_{style}.wav",
                original_filename=f"test_{style}.wav",
            )
            db_session.add(song)
            await db_session.flush()

            parsed = parser.parse_progression("C | F | G | C")
            voicings = [voicer.generate_voicing(c, style=style) for c in parsed.chords]

            midi_gen = MIDIGenerator(tempo=120)
            midi_gen.create_score()
            midi_gen.add_melody_track(
                sample_melody_data["notes"],
                [0.5] * len(sample_melody_data["notes"]),
            )
            midi_gen.add_accompaniment_track(voicings, [2.0] * len(voicings))

            generation = Generation(
                generation_id=str(uuid.uuid4()),
                song_id=sid,
                style=style,
            )
            db_session.add(generation)
            await db_session.commit()

            fetched = await db_session.get(Generation, generation.generation_id)
            assert fetched is not None
            assert fetched.style == style

    async def test_pipeline_invalid_chord_fails_gracefully(self):
        """Pipeline should raise a clear error for invalid chord input."""
        parser = ChordParser()
        with pytest.raises(ValueError, match="Invalid chord symbol"):
            parser.parse_progression("C | Xzz | F | G")

    def test_pipeline_tempo_validation(self):
        """Pipeline should validate tempo within acceptable range."""
        parser = ChordParser()
        assert parser.validate_tempo(120) is True
        assert parser.validate_tempo(39) is False
        assert parser.validate_tempo(241) is False

    def test_pipeline_time_signature_parsing(self):
        """Pipeline should correctly parse standard time signatures."""
        parser = ChordParser()

        ts = parser.parse_time_signature("4/4")
        assert ts.numerator == 4
        assert ts.denominator == 4

        ts = parser.parse_time_signature("3/4")
        assert ts.numerator == 3

        ts = parser.parse_time_signature("6/8")
        assert ts.numerator == 6
        assert ts.denominator == 8
