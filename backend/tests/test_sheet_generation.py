"""Tests for Lilypond sheet music generation (Phase 11).

External tool calls (lilypond) are mocked where needed since
Lilypond may not be installed on the test machine.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from music21 import converter, note, stream

from src.generation.sheet_generator import SheetGenerator, SheetGenerationError


def _make_simple_score():
    """Create a simple music21 Score for testing."""
    s = stream.Score()
    p = stream.Part()
    p.append(note.Note("C4", quarterLength=1.0))
    p.append(note.Note("E4", quarterLength=1.0))
    p.append(note.Note("G4", quarterLength=1.0))
    p.append(note.Note("C5", quarterLength=1.0))
    s.append(p)
    return s


class TestSheetGeneratorInit:
    """Test SheetGenerator initialization."""

    def test_init_creates_instance(self):
        gen = SheetGenerator()
        assert gen is not None

    def test_init_default_format(self):
        gen = SheetGenerator()
        assert gen.output_format == "pdf"

    def test_init_custom_format(self):
        gen = SheetGenerator(output_format="png")
        assert gen.output_format == "png"

    def test_init_default_title(self):
        gen = SheetGenerator()
        assert gen.default_title == "Piano Accompaniment"

    def test_init_custom_title(self):
        gen = SheetGenerator(default_title="My Song")
        assert gen.default_title == "My Song"


class TestToLilypond:
    """Test to_lilypond() returns string with lilypond notation."""

    def test_to_lilypond_returns_string(self):
        gen = SheetGenerator()
        score = _make_simple_score()
        result = gen.to_lilypond(score)
        assert isinstance(result, str)

    def test_to_lilypond_contains_version(self):
        """Lilypond output should contain a version statement."""
        gen = SheetGenerator()
        score = _make_simple_score()
        result = gen.to_lilypond(score)
        assert "version" in result.lower() or "\\version" in result

    def test_to_lilypond_not_empty(self):
        gen = SheetGenerator()
        score = _make_simple_score()
        result = gen.to_lilypond(score)
        assert len(result.strip()) > 0

    def test_to_lilypond_contains_note_data(self):
        """The lilypond string should contain recognizable note names."""
        gen = SheetGenerator()
        score = _make_simple_score()
        result = gen.to_lilypond(score)
        # music21 lilypond export uses note letters like c, e, g
        lowered = result.lower()
        assert "c" in lowered

    def test_to_lilypond_raises_for_none_input(self):
        gen = SheetGenerator()
        with pytest.raises(SheetGenerationError, match="[Ss]core|[Ii]nvalid"):
            gen.to_lilypond(None)

    def test_to_lilypond_raises_for_non_score_input(self):
        gen = SheetGenerator()
        with pytest.raises(SheetGenerationError, match="[Ss]core|[Ii]nvalid"):
            gen.to_lilypond("not a score")


class TestGenerateSheet:
    """Test generate_sheet() accepts a music21 Score or MIDI path."""

    @patch("src.generation.sheet_generator.subprocess.run")
    def test_generate_sheet_from_score_returns_path(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        gen = SheetGenerator()
        score = _make_simple_score()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.pdf")
            # Create the output file to simulate lilypond producing it
            with open(output_path, "wb") as f:
                f.write(b"%PDF-fake")

            result = gen.generate_sheet(score, output_path)
            assert isinstance(result, str)

    @patch("src.generation.sheet_generator.subprocess.run")
    def test_generate_sheet_output_has_correct_extension(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        gen = SheetGenerator(output_format="pdf")
        score = _make_simple_score()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(b"%PDF-fake")

            result = gen.generate_sheet(score, output_path)
            assert result.endswith(".pdf")

    @patch("src.generation.sheet_generator.subprocess.run")
    def test_generate_sheet_from_midi_path(self, mock_run):
        """generate_sheet should accept a MIDI file path string."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        gen = SheetGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a real MIDI file using music21
            score = _make_simple_score()
            midi_path = os.path.join(tmpdir, "input.mid")
            score.write("midi", fp=midi_path)
            output_path = os.path.join(tmpdir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(b"%PDF-fake")

            result = gen.generate_sheet(midi_path, output_path)
            assert isinstance(result, str)

    @patch("src.generation.sheet_generator.subprocess.run")
    def test_generate_sheet_writes_lilypond_file(self, mock_run):
        """The generator should write a .ly file before calling lilypond."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        gen = SheetGenerator()
        score = _make_simple_score()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(b"%PDF-fake")

            gen.generate_sheet(score, output_path)

            # Check that a .ly file was created in the same directory
            ly_files = [f for f in os.listdir(tmpdir) if f.endswith(".ly")]
            assert len(ly_files) >= 1

    @patch("src.generation.sheet_generator.subprocess.run")
    def test_generate_sheet_calls_lilypond_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        gen = SheetGenerator()
        score = _make_simple_score()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(b"%PDF-fake")

            gen.generate_sheet(score, output_path)
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "lilypond" in cmd[0]


class TestErrorHandling:
    """Test error handling for invalid input and tool failures."""

    def test_generate_sheet_raises_for_none_score(self):
        gen = SheetGenerator()
        with pytest.raises(SheetGenerationError, match="[Ss]core|[Ii]nvalid"):
            gen.generate_sheet(None, "/some/output.pdf")

    def test_generate_sheet_raises_for_invalid_type(self):
        gen = SheetGenerator()
        with pytest.raises(SheetGenerationError, match="[Ss]core|[Ii]nvalid"):
            gen.generate_sheet(12345, "/some/output.pdf")

    @patch("src.generation.sheet_generator.subprocess.run")
    def test_generate_sheet_raises_on_lilypond_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stderr="lilypond: error processing"
        )
        gen = SheetGenerator()
        score = _make_simple_score()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.pdf")
            with pytest.raises(
                SheetGenerationError, match="[Ll]ilypond|[Ff]ailed"
            ):
                gen.generate_sheet(score, output_path)

    @patch(
        "src.generation.sheet_generator.subprocess.run",
        side_effect=FileNotFoundError("lilypond not found"),
    )
    def test_generate_sheet_raises_when_lilypond_not_installed(self, mock_run):
        gen = SheetGenerator()
        score = _make_simple_score()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.pdf")
            with pytest.raises(
                SheetGenerationError,
                match="[Ll]ilypond.*not.*installed|not found",
            ):
                gen.generate_sheet(score, output_path)

    def test_generate_sheet_raises_for_nonexistent_midi_path(self):
        gen = SheetGenerator()
        with pytest.raises(SheetGenerationError, match="[Mm][Ii][Dd][Ii]|not found"):
            gen.generate_sheet(
                "/nonexistent/file.mid", "/some/output.pdf"
            )


class TestOutputFormatValidation:
    """Test output format validation."""

    @patch("src.generation.sheet_generator.subprocess.run")
    def test_pdf_format_accepted(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        gen = SheetGenerator(output_format="pdf")
        score = _make_simple_score()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(b"%PDF-fake")
            result = gen.generate_sheet(score, output_path)
            assert result.endswith(".pdf")

    @patch("src.generation.sheet_generator.subprocess.run")
    def test_png_format_accepted(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        gen = SheetGenerator(output_format="png")
        score = _make_simple_score()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.png")
            with open(output_path, "wb") as f:
                f.write(b"PNG-fake")
            result = gen.generate_sheet(score, output_path)
            assert result.endswith(".png")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="[Ff]ormat"):
            SheetGenerator(output_format="docx")
