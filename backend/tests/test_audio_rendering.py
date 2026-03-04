"""Tests for FluidSynth audio rendering (Phase 10).

All external tool calls (fluidsynth CLI / pyfluidsynth) are mocked
since FluidSynth may not be installed on the test machine.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch, mock_open

import pytest

from src.generation.audio_renderer import AudioRenderer, AudioRenderError


class TestAudioRendererInit:
    """Test AudioRenderer initialization with soundfont path."""

    def test_init_stores_soundfont_path(self):
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")
        assert renderer.soundfont_path == "/path/to/piano.sf2"

    def test_init_default_sample_rate(self):
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")
        assert renderer.sample_rate == 44100

    def test_init_custom_sample_rate(self):
        renderer = AudioRenderer(
            soundfont_path="/path/to/piano.sf2", sample_rate=22050
        )
        assert renderer.sample_rate == 22050

    def test_init_default_channels(self):
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")
        assert renderer.channels == 2

    def test_init_custom_channels(self):
        renderer = AudioRenderer(
            soundfont_path="/path/to/piano.sf2", channels=1
        )
        assert renderer.channels == 1

    def test_init_stores_gain(self):
        renderer = AudioRenderer(
            soundfont_path="/path/to/piano.sf2", gain=0.5
        )
        assert renderer.gain == 0.5

    def test_init_default_gain(self):
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")
        assert renderer.gain == 1.0


class TestRenderConfig:
    """Test render configuration (sample_rate, channels)."""

    def test_get_config_returns_dict(self):
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")
        config = renderer.get_config()
        assert isinstance(config, dict)

    def test_config_contains_sample_rate(self):
        renderer = AudioRenderer(
            soundfont_path="/path/to/piano.sf2", sample_rate=48000
        )
        config = renderer.get_config()
        assert config["sample_rate"] == 48000

    def test_config_contains_channels(self):
        renderer = AudioRenderer(
            soundfont_path="/path/to/piano.sf2", channels=1
        )
        config = renderer.get_config()
        assert config["channels"] == 1

    def test_config_contains_gain(self):
        renderer = AudioRenderer(
            soundfont_path="/path/to/piano.sf2", gain=0.8
        )
        config = renderer.get_config()
        assert config["gain"] == 0.8

    def test_config_contains_soundfont_path(self):
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")
        config = renderer.get_config()
        assert config["soundfont_path"] == "/path/to/piano.sf2"


class TestRenderMidi:
    """Test render_midi() returns a file path with .wav extension."""

    @patch("src.generation.audio_renderer.subprocess.run")
    @patch("os.path.isfile", return_value=True)
    def test_render_midi_returns_file_path(self, mock_isfile, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")

        with tempfile.TemporaryDirectory() as tmpdir:
            midi_path = os.path.join(tmpdir, "test.mid")
            output_path = os.path.join(tmpdir, "output.wav")
            # Create a dummy MIDI file so the path check passes
            with open(midi_path, "wb") as f:
                f.write(b"MThd" + b"\x00" * 100)

            result = renderer.render_midi(midi_path, output_path)
            assert isinstance(result, str)

    @patch("src.generation.audio_renderer.subprocess.run")
    @patch("os.path.isfile", return_value=True)
    def test_render_midi_output_has_wav_extension(self, mock_isfile, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")

        with tempfile.TemporaryDirectory() as tmpdir:
            midi_path = os.path.join(tmpdir, "test.mid")
            output_path = os.path.join(tmpdir, "output.wav")
            with open(midi_path, "wb") as f:
                f.write(b"MThd" + b"\x00" * 100)

            result = renderer.render_midi(midi_path, output_path)
            assert result.endswith(".wav")

    @patch("src.generation.audio_renderer.subprocess.run")
    @patch("os.path.isfile", return_value=True)
    def test_render_midi_returns_specified_output_path(
        self, mock_isfile, mock_run
    ):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")

        with tempfile.TemporaryDirectory() as tmpdir:
            midi_path = os.path.join(tmpdir, "test.mid")
            output_path = os.path.join(tmpdir, "my_output.wav")
            with open(midi_path, "wb") as f:
                f.write(b"MThd" + b"\x00" * 100)

            result = renderer.render_midi(midi_path, output_path)
            assert result == output_path

    @patch("src.generation.audio_renderer.subprocess.run")
    @patch("os.path.isfile", return_value=True)
    def test_render_midi_calls_fluidsynth(self, mock_isfile, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")

        with tempfile.TemporaryDirectory() as tmpdir:
            midi_path = os.path.join(tmpdir, "test.mid")
            output_path = os.path.join(tmpdir, "output.wav")
            with open(midi_path, "wb") as f:
                f.write(b"MThd" + b"\x00" * 100)

            renderer.render_midi(midi_path, output_path)
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            assert "fluidsynth" in cmd[0]

    @patch("src.generation.audio_renderer.subprocess.run")
    @patch("os.path.isfile", return_value=True)
    def test_render_midi_passes_sample_rate(self, mock_isfile, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        renderer = AudioRenderer(
            soundfont_path="/path/to/piano.sf2", sample_rate=22050
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            midi_path = os.path.join(tmpdir, "test.mid")
            output_path = os.path.join(tmpdir, "output.wav")
            with open(midi_path, "wb") as f:
                f.write(b"MThd" + b"\x00" * 100)

            renderer.render_midi(midi_path, output_path)
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            # sample rate should appear in the command
            assert "22050" in cmd


class TestErrorHandling:
    """Test error handling for missing soundfont and invalid MIDI."""

    def test_render_midi_raises_for_missing_soundfont(self):
        renderer = AudioRenderer(
            soundfont_path="/nonexistent/path/piano.sf2"
        )
        with pytest.raises(AudioRenderError, match="[Ss]oundfont"):
            renderer.render_midi("/some/file.mid", "/some/output.wav")

    def test_render_midi_raises_for_missing_midi_file(self):
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")
        with patch("os.path.isfile") as mock_isfile:
            # soundfont exists, midi does not
            mock_isfile.side_effect = lambda p: p.endswith(".sf2")
            with pytest.raises(AudioRenderError, match="[Mm][Ii][Dd][Ii]"):
                renderer.render_midi(
                    "/nonexistent/file.mid", "/some/output.wav"
                )

    @patch("src.generation.audio_renderer.subprocess.run")
    def test_render_midi_raises_on_fluidsynth_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stderr="fluidsynth: error"
        )
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")

        with patch("os.path.isfile", return_value=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                midi_path = os.path.join(tmpdir, "test.mid")
                output_path = os.path.join(tmpdir, "output.wav")
                with open(midi_path, "wb") as f:
                    f.write(b"MThd" + b"\x00" * 100)

                with pytest.raises(AudioRenderError, match="[Ff]luidsynth"):
                    renderer.render_midi(midi_path, output_path)

    @patch(
        "src.generation.audio_renderer.subprocess.run",
        side_effect=FileNotFoundError("fluidsynth not found"),
    )
    def test_render_midi_raises_when_fluidsynth_not_installed(self, mock_run):
        renderer = AudioRenderer(soundfont_path="/path/to/piano.sf2")

        with patch("os.path.isfile", return_value=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                midi_path = os.path.join(tmpdir, "test.mid")
                output_path = os.path.join(tmpdir, "output.wav")
                with open(midi_path, "wb") as f:
                    f.write(b"MThd" + b"\x00" * 100)

                with pytest.raises(
                    AudioRenderError, match="[Ff]luidsynth.*not.*installed|not found"
                ):
                    renderer.render_midi(midi_path, output_path)
