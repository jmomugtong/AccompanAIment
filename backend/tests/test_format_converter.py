"""Tests for multi-format output conversion."""

import os
import tempfile

import pytest

from src.generation.format_converter import FormatConverter, FormatConversionError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def converter():
    """Create a FormatConverter instance."""
    return FormatConverter()


@pytest.fixture
def dummy_midi_file(tmp_path):
    """Create a dummy MIDI file for testing."""
    midi_path = tmp_path / "test.mid"
    # Write a minimal (fake) MIDI header so the file exists
    midi_path.write_bytes(b"MThd" + b"\x00" * 50)
    return str(midi_path)


# ---------------------------------------------------------------------------
# Tests: FormatConverter
# ---------------------------------------------------------------------------

class TestFormatConverter:
    """Test the FormatConverter class."""

    def test_supported_formats(self, converter):
        """Converter should support midi, wav, and pdf formats."""
        assert "midi" in converter.supported_formats
        assert "wav" in converter.supported_formats
        assert "pdf" in converter.supported_formats

    def test_unsupported_format_raises(self, converter, dummy_midi_file):
        """Requesting an unsupported format should raise FormatConversionError."""
        with pytest.raises(FormatConversionError):
            converter.convert(dummy_midi_file, "mp3")

    def test_missing_input_file_raises(self, converter):
        """A non-existent input file should raise FormatConversionError."""
        with pytest.raises(FormatConversionError):
            converter.convert("/nonexistent/file.mid", "wav")

    def test_convert_returns_string_path(self, converter, dummy_midi_file):
        """convert() should return a string path for the output file."""
        # midi-to-midi is a no-op copy, so it should always succeed
        result = converter.convert(dummy_midi_file, "midi")
        assert isinstance(result, str)

    def test_midi_to_midi_preserves_file(self, converter, dummy_midi_file):
        """Converting MIDI to MIDI should produce an output file that exists."""
        result = converter.convert(dummy_midi_file, "midi")
        assert os.path.exists(result)

    def test_output_path_has_correct_extension(self, converter, dummy_midi_file):
        """The output path should have the correct file extension."""
        result = converter.convert(dummy_midi_file, "midi")
        assert result.endswith(".mid") or result.endswith(".midi")

    def test_convert_midi_to_wav_raises_without_tools(self, converter, dummy_midi_file):
        """Converting to WAV should raise if FluidSynth is not available.

        In a test environment without FluidSynth installed, this should
        raise FormatConversionError rather than crash.
        """
        # This will either succeed (if FluidSynth is installed) or raise
        # FormatConversionError. It should not raise any other exception.
        try:
            converter.convert(dummy_midi_file, "wav")
        except FormatConversionError:
            pass  # Expected in test environments without FluidSynth

    def test_convert_midi_to_pdf_raises_without_tools(self, converter, dummy_midi_file):
        """Converting to PDF should raise if Lilypond is not available.

        In a test environment without Lilypond installed, this should
        raise FormatConversionError rather than crash.
        """
        try:
            converter.convert(dummy_midi_file, "pdf")
        except FormatConversionError:
            pass  # Expected in test environments without Lilypond

    def test_custom_output_path(self, converter, dummy_midi_file, tmp_path):
        """When output_path is specified, the file should be created there."""
        output = str(tmp_path / "custom_output.mid")
        result = converter.convert(dummy_midi_file, "midi", output_path=output)
        assert result == output
        assert os.path.exists(output)
