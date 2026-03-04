"""Tests for Celery task workers (Phase 12).

All heavy dependencies (CREPE, FluidSynth, Lilypond, LLM, etc.) are mocked.
The Celery app itself is mocked so no Redis connection is required.
"""

import importlib
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers: mock the celery_app before importing worker modules
# ---------------------------------------------------------------------------

def _make_mock_celery_app():
    """Create a mock Celery app with a task decorator that preserves functions."""
    mock_app = MagicMock()

    def fake_task(**kwargs):
        """Decorator that wraps the function to look like a Celery task."""
        def decorator(func):
            # Attach bind/name metadata
            func.name = kwargs.get("name", func.__name__)
            func.bind = kwargs.get("bind", False)
            func.soft_time_limit = kwargs.get("soft_time_limit", None)
            func.time_limit = kwargs.get("time_limit", None)
            # Provide update_state as a no-op by default
            func.update_state = MagicMock()
            return func
        return decorator

    mock_app.task = fake_task
    return mock_app


_mock_celery = _make_mock_celery_app()


def _reload_melody_worker():
    """Reload the melody_worker module with the mock celery app."""
    with patch("src.celery_app.celery_app", _mock_celery):
        import src.workers.melody_worker as mod
        importlib.reload(mod)
        return mod


def _reload_generation_worker():
    """Reload the generation_worker module with the mock celery app."""
    with patch("src.celery_app.celery_app", _mock_celery):
        import src.workers.generation_worker as mod
        importlib.reload(mod)
        return mod


def _reload_format_worker():
    """Reload the format_worker module with the mock celery app."""
    with patch("src.celery_app.celery_app", _mock_celery):
        import src.workers.format_worker as mod
        importlib.reload(mod)
        return mod


# ===========================================================================
# Test: extract_melody task
# ===========================================================================


class TestExtractMelodyTask:
    """Tests for the extract_melody Celery task."""

    def test_extract_melody_returns_dict(self):
        """extract_melody should return a dict with melody data."""
        mod = _reload_melody_worker()

        mock_instance = MagicMock()
        mock_instance.extract.return_value = {
            "notes": [60, 62, 64],
            "timings": [0.0, 0.5, 1.0],
            "confidence": [0.9, 0.85, 0.92],
            "duration_seconds": 1.5,
        }

        with patch.object(mod, "CREPEExtractor", return_value=mock_instance):
            result = mod.extract_melody("song-123", "/path/to/audio.wav")

        assert isinstance(result, dict)
        assert "notes" in result
        assert "timings" in result
        assert "confidence" in result
        assert "duration_seconds" in result

    def test_extract_melody_calls_crepe_extractor(self):
        """The task should instantiate and call CREPEExtractor.extract()."""
        mod = _reload_melody_worker()

        mock_instance = MagicMock()
        mock_instance.extract.return_value = {
            "notes": [60],
            "timings": [0.0],
            "confidence": [0.9],
            "duration_seconds": 1.0,
        }
        mock_cls = MagicMock(return_value=mock_instance)

        with patch.object(mod, "CREPEExtractor", mock_cls):
            mod.extract_melody("song-456", "/path/to/audio.wav")

        mock_cls.assert_called_once()
        mock_instance.extract.assert_called_once_with("/path/to/audio.wav")

    def test_extract_melody_includes_song_id_in_result(self):
        """The result should include the song_id for downstream correlation."""
        mod = _reload_melody_worker()

        mock_instance = MagicMock()
        mock_instance.extract.return_value = {
            "notes": [60],
            "timings": [0.0],
            "confidence": [0.9],
            "duration_seconds": 1.0,
        }

        with patch.object(mod, "CREPEExtractor", return_value=mock_instance):
            result = mod.extract_melody("song-789", "/path/to/audio.wav")

        assert result["song_id"] == "song-789"

    def test_extract_melody_propagates_notes(self):
        """The returned notes should match what CREPE produces."""
        mod = _reload_melody_worker()

        expected_notes = [60, 62, 64, 65, 67]
        mock_instance = MagicMock()
        mock_instance.extract.return_value = {
            "notes": expected_notes,
            "timings": [0.0, 0.5, 1.0, 1.5, 2.0],
            "confidence": [0.9, 0.88, 0.91, 0.87, 0.93],
            "duration_seconds": 2.5,
        }

        with patch.object(mod, "CREPEExtractor", return_value=mock_instance):
            result = mod.extract_melody("song-abc", "/path/to/audio.wav")

        assert result["notes"] == expected_notes

    def test_extract_melody_error_handling(self):
        """The task should raise when CREPE extraction fails."""
        mod = _reload_melody_worker()

        mock_instance = MagicMock()
        mock_instance.extract.side_effect = RuntimeError("CREPE model failed")

        with patch.object(mod, "CREPEExtractor", return_value=mock_instance):
            with pytest.raises(RuntimeError, match="CREPE model failed"):
                mod.extract_melody("song-err", "/bad/path.wav")


# ===========================================================================
# Test: generate_piano task
# ===========================================================================


class TestGeneratePianoTask:
    """Tests for the generate_piano Celery task."""

    def _setup_mocks(self):
        """Create standard mocks for VoicingGenerator and MIDIGenerator."""
        mock_voicing = MagicMock()
        mock_voicing.generate_voicing.return_value = [48, 52, 55]

        mock_midi = MagicMock()
        mock_midi.write_midi.return_value = "/output/song.mid"

        return mock_voicing, mock_midi

    def test_generate_piano_returns_dict(self):
        """generate_piano should return a dict with generation results."""
        mod = _reload_generation_worker()
        mock_voicing, mock_midi = self._setup_mocks()

        with patch.object(mod, "VoicingGenerator", return_value=mock_voicing), \
             patch.object(mod, "MIDIGenerator", return_value=mock_midi):
            result = mod.generate_piano(
                song_id="song-123",
                chords="C | F | G | C",
                style="pop",
                tempo=120,
                time_signature="4/4",
            )

        assert isinstance(result, dict)

    def test_generate_piano_result_contains_midi_path(self):
        """The result should contain a midi_path."""
        mod = _reload_generation_worker()
        mock_voicing, mock_midi = self._setup_mocks()

        with patch.object(mod, "VoicingGenerator", return_value=mock_voicing), \
             patch.object(mod, "MIDIGenerator", return_value=mock_midi):
            result = mod.generate_piano(
                song_id="song-123",
                chords="C | F | G | C",
                style="pop",
                tempo=120,
                time_signature="4/4",
            )

        assert "midi_path" in result
        assert result["midi_path"] == "/output/song.mid"

    def test_generate_piano_includes_song_id(self):
        """The result should include the song_id."""
        mod = _reload_generation_worker()
        mock_voicing, mock_midi = self._setup_mocks()

        with patch.object(mod, "VoicingGenerator", return_value=mock_voicing), \
             patch.object(mod, "MIDIGenerator", return_value=mock_midi):
            result = mod.generate_piano(
                song_id="song-456",
                chords="Am | F | C | G",
                style="jazz",
                tempo=90,
                time_signature="4/4",
            )

        assert result["song_id"] == "song-456"

    def test_generate_piano_includes_style(self):
        """The result should include the style that was used."""
        mod = _reload_generation_worker()
        mock_voicing, mock_midi = self._setup_mocks()

        with patch.object(mod, "VoicingGenerator", return_value=mock_voicing), \
             patch.object(mod, "MIDIGenerator", return_value=mock_midi):
            result = mod.generate_piano(
                song_id="song-789",
                chords="C | G",
                style="soulful",
                tempo=80,
                time_signature="4/4",
            )

        assert result["style"] == "soulful"

    def test_generate_piano_calls_voicing_generator(self):
        """The task should call VoicingGenerator for each chord."""
        mod = _reload_generation_worker()
        mock_voicing, mock_midi = self._setup_mocks()

        with patch.object(mod, "VoicingGenerator", return_value=mock_voicing), \
             patch.object(mod, "MIDIGenerator", return_value=mock_midi):
            mod.generate_piano(
                song_id="song-123",
                chords="C | F | G | C",
                style="pop",
                tempo=120,
                time_signature="4/4",
            )

        # Should be called once per chord symbol
        assert mock_voicing.generate_voicing.call_count == 4

    def test_generate_piano_creates_midi(self):
        """The task should create a score and write MIDI."""
        mod = _reload_generation_worker()
        mock_voicing, mock_midi = self._setup_mocks()

        with patch.object(mod, "VoicingGenerator", return_value=mock_voicing), \
             patch.object(mod, "MIDIGenerator", return_value=mock_midi):
            mod.generate_piano(
                song_id="song-123",
                chords="C | F",
                style="pop",
                tempo=120,
                time_signature="4/4",
            )

        mock_midi.create_score.assert_called_once()
        mock_midi.add_accompaniment_track.assert_called_once()
        mock_midi.write_midi.assert_called_once()

    def test_generate_piano_error_handling(self):
        """The task should raise when voicing generation fails."""
        mod = _reload_generation_worker()

        mock_voicing = MagicMock()
        mock_voicing.generate_voicing.side_effect = ValueError("Bad chord: XYZ")
        mock_midi = MagicMock()

        with patch.object(mod, "VoicingGenerator", return_value=mock_voicing), \
             patch.object(mod, "MIDIGenerator", return_value=mock_midi):
            with pytest.raises(ValueError, match="Bad chord"):
                mod.generate_piano(
                    song_id="song-err",
                    chords="XYZ",
                    style="pop",
                    tempo=120,
                    time_signature="4/4",
                )


# ===========================================================================
# Test: render_audio task
# ===========================================================================


class TestRenderAudioTask:
    """Tests for the render_audio Celery task."""

    def test_render_audio_returns_file_path(self):
        """render_audio should return the output WAV file path."""
        mod = _reload_format_worker()

        mock_instance = MagicMock()
        mock_instance.render_midi.return_value = "/output/song.wav"

        with patch.object(mod, "AudioRenderer", return_value=mock_instance):
            result = mod.render_audio("/input/song.mid", "/output/song.wav")

        assert isinstance(result, str)
        assert result == "/output/song.wav"

    def test_render_audio_calls_audio_renderer(self):
        """The task should call AudioRenderer.render_midi()."""
        mod = _reload_format_worker()

        mock_instance = MagicMock()
        mock_instance.render_midi.return_value = "/output/song.wav"
        mock_cls = MagicMock(return_value=mock_instance)

        with patch.object(mod, "AudioRenderer", mock_cls):
            mod.render_audio("/input/song.mid", "/output/song.wav")

        mock_cls.assert_called_once()
        mock_instance.render_midi.assert_called_once_with(
            "/input/song.mid", "/output/song.wav"
        )

    def test_render_audio_error_handling(self):
        """The task should propagate AudioRenderError."""
        from src.generation.audio_renderer import AudioRenderError

        mod = _reload_format_worker()

        mock_instance = MagicMock()
        mock_instance.render_midi.side_effect = AudioRenderError(
            "FluidSynth not installed"
        )

        with patch.object(mod, "AudioRenderer", return_value=mock_instance):
            with pytest.raises(AudioRenderError, match="FluidSynth"):
                mod.render_audio("/input/song.mid", "/output/song.wav")


# ===========================================================================
# Test: generate_sheet task
# ===========================================================================


class TestGenerateSheetTask:
    """Tests for the generate_sheet Celery task."""

    def test_generate_sheet_returns_file_path(self):
        """generate_sheet should return the output PDF file path."""
        mod = _reload_format_worker()

        mock_instance = MagicMock()
        mock_instance.generate_sheet.return_value = "/output/song.pdf"

        with patch.object(mod, "SheetGenerator", return_value=mock_instance):
            result = mod.generate_sheet("/input/song.mid", "/output/song.pdf")

        assert isinstance(result, str)
        assert result == "/output/song.pdf"

    def test_generate_sheet_calls_sheet_generator(self):
        """The task should call SheetGenerator.generate_sheet()."""
        mod = _reload_format_worker()

        mock_instance = MagicMock()
        mock_instance.generate_sheet.return_value = "/output/song.pdf"
        mock_cls = MagicMock(return_value=mock_instance)

        with patch.object(mod, "SheetGenerator", mock_cls):
            mod.generate_sheet("/input/song.mid", "/output/song.pdf")

        mock_cls.assert_called_once()
        mock_instance.generate_sheet.assert_called_once_with(
            "/input/song.mid", "/output/song.pdf"
        )

    def test_generate_sheet_error_handling(self):
        """The task should propagate SheetGenerationError."""
        from src.generation.sheet_generator import SheetGenerationError

        mod = _reload_format_worker()

        mock_instance = MagicMock()
        mock_instance.generate_sheet.side_effect = SheetGenerationError(
            "Lilypond not installed"
        )

        with patch.object(mod, "SheetGenerator", return_value=mock_instance):
            with pytest.raises(SheetGenerationError, match="Lilypond"):
                mod.generate_sheet("/input/song.mid", "/output/song.pdf")


# ===========================================================================
# Test: Task status tracking
# ===========================================================================


class TestTaskStatusTracking:
    """Tests for Celery task state tracking (PENDING, STARTED, SUCCESS, FAILURE)."""

    def test_celery_app_has_task_track_started_enabled(self):
        """The celery_app config should enable task_track_started.

        We verify the actual celery_app.py configuration sets
        task_track_started=True. This test reads the real Celery app,
        not the mock, because configuration is a static property.
        """
        # Import fresh -- the autouse fixture does not apply here because
        # we read the actual config value set via celery_app.conf.update().
        from src import celery_app as celery_mod
        importlib.reload(celery_mod)
        assert celery_mod.celery_app.conf.task_track_started is True

    def test_celery_app_acks_late(self):
        """The celery_app should ack tasks late for reliability."""
        from src import celery_app as celery_mod
        importlib.reload(celery_mod)
        assert celery_mod.celery_app.conf.task_acks_late is True

    def test_extract_melody_task_is_registered(self):
        """extract_melody should be decorated as a celery task."""
        mod = _reload_melody_worker()
        assert hasattr(mod.extract_melody, "name")

    def test_generate_piano_task_is_registered(self):
        """generate_piano should be decorated as a celery task."""
        mod = _reload_generation_worker()
        assert hasattr(mod.generate_piano, "name")

    def test_render_audio_task_is_registered(self):
        """render_audio should be decorated as a celery task."""
        mod = _reload_format_worker()
        assert hasattr(mod.render_audio, "name")

    def test_generate_sheet_task_is_registered(self):
        """generate_sheet should be decorated as a celery task."""
        mod = _reload_format_worker()
        assert hasattr(mod.generate_sheet, "name")


# ===========================================================================
# Test: Task progress updates
# ===========================================================================


class TestTaskProgressUpdates:
    """Tests for task progress updates via update_state metadata."""

    def test_extract_melody_updates_progress(self):
        """extract_melody should call update_state with progress info."""
        mod = _reload_melody_worker()

        mock_instance = MagicMock()
        mock_instance.extract.return_value = {
            "notes": [60],
            "timings": [0.0],
            "confidence": [0.9],
            "duration_seconds": 1.0,
        }

        # Reset any prior calls on the task's update_state mock
        mod.extract_melody.update_state.reset_mock()

        with patch.object(mod, "CREPEExtractor", return_value=mock_instance):
            mod.extract_melody("song-123", "/path/to/audio.wav")

        # Should have called update_state at least once
        assert mod.extract_melody.update_state.call_count >= 1
        # Check that at least one call used PROGRESS state
        calls = mod.extract_melody.update_state.call_args_list
        states_used = [
            c.kwargs.get("state", c.args[0] if c.args else None)
            for c in calls
        ]
        assert any(
            s == "PROGRESS" for s in states_used
        ), f"Expected PROGRESS state in calls, got: {calls}"

    def test_generate_piano_updates_progress(self):
        """generate_piano should report progress via update_state."""
        mod = _reload_generation_worker()

        mock_voicing = MagicMock()
        mock_voicing.generate_voicing.return_value = [48, 52, 55]
        mock_midi = MagicMock()
        mock_midi.write_midi.return_value = "/output/song.mid"

        mod.generate_piano.update_state.reset_mock()

        with patch.object(mod, "VoicingGenerator", return_value=mock_voicing), \
             patch.object(mod, "MIDIGenerator", return_value=mock_midi):
            mod.generate_piano(
                song_id="song-123",
                chords="C | F | G | C",
                style="pop",
                tempo=120,
                time_signature="4/4",
            )

        assert mod.generate_piano.update_state.call_count >= 1


# ===========================================================================
# Test: Task timeout configuration
# ===========================================================================


class TestTaskTimeoutConfiguration:
    """Tests for task timeout settings."""

    def test_celery_app_soft_time_limit(self):
        """The celery_app should have a 5-minute soft time limit."""
        from src import celery_app as celery_mod
        importlib.reload(celery_mod)
        assert celery_mod.celery_app.conf.task_soft_time_limit == 300

    def test_celery_app_hard_time_limit(self):
        """The celery_app should have a 10-minute hard time limit."""
        from src import celery_app as celery_mod
        importlib.reload(celery_mod)
        assert celery_mod.celery_app.conf.task_time_limit == 600

    def test_extract_melody_has_timeout(self):
        """extract_melody task should have a soft_time_limit set."""
        mod = _reload_melody_worker()
        assert mod.extract_melody.soft_time_limit is not None

    def test_generate_piano_has_timeout(self):
        """generate_piano task should have a soft_time_limit set."""
        mod = _reload_generation_worker()
        assert mod.generate_piano.soft_time_limit is not None

    def test_render_audio_has_timeout(self):
        """render_audio task should have a soft_time_limit set."""
        mod = _reload_format_worker()
        assert mod.render_audio.soft_time_limit is not None

    def test_generate_sheet_has_timeout(self):
        """generate_sheet task should have a soft_time_limit set."""
        mod = _reload_format_worker()
        assert mod.generate_sheet.soft_time_limit is not None


# ===========================================================================
# Test: Error handling produces FAILURE state
# ===========================================================================


class TestErrorHandlingFailureState:
    """Tests that task errors propagate correctly (Celery marks as FAILURE)."""

    def test_melody_extraction_failure_propagates(self):
        """When CREPE fails, the exception should propagate (Celery sets FAILURE)."""
        mod = _reload_melody_worker()

        mock_instance = MagicMock()
        mock_instance.extract.side_effect = RuntimeError("GPU out of memory")

        with patch.object(mod, "CREPEExtractor", return_value=mock_instance):
            with pytest.raises(RuntimeError, match="GPU out of memory"):
                mod.extract_melody("song-fail", "/path.wav")

    def test_generation_failure_propagates(self):
        """When MIDI generation fails, the exception should propagate."""
        mod = _reload_generation_worker()

        mock_voicing = MagicMock()
        mock_voicing.generate_voicing.return_value = [48, 52, 55]
        mock_midi = MagicMock()
        mock_midi.create_score.side_effect = RuntimeError("Score creation failed")

        with patch.object(mod, "VoicingGenerator", return_value=mock_voicing), \
             patch.object(mod, "MIDIGenerator", return_value=mock_midi):
            with pytest.raises(RuntimeError, match="Score creation failed"):
                mod.generate_piano(
                    song_id="song-fail",
                    chords="C | F",
                    style="pop",
                    tempo=120,
                    time_signature="4/4",
                )

    def test_audio_render_failure_propagates(self):
        """When FluidSynth fails, AudioRenderError should propagate."""
        from src.generation.audio_renderer import AudioRenderError

        mod = _reload_format_worker()

        mock_instance = MagicMock()
        mock_instance.render_midi.side_effect = AudioRenderError("Render failed")

        with patch.object(mod, "AudioRenderer", return_value=mock_instance):
            with pytest.raises(AudioRenderError, match="Render failed"):
                mod.render_audio("/input.mid", "/output.wav")

    def test_sheet_generation_failure_propagates(self):
        """When Lilypond fails, SheetGenerationError should propagate."""
        from src.generation.sheet_generator import SheetGenerationError

        mod = _reload_format_worker()

        mock_instance = MagicMock()
        mock_instance.generate_sheet.side_effect = SheetGenerationError(
            "Rendering timed out"
        )

        with patch.object(mod, "SheetGenerator", return_value=mock_instance):
            with pytest.raises(SheetGenerationError, match="Rendering timed out"):
                mod.generate_sheet("/input.mid", "/output.pdf")
