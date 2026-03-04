"""Lilypond sheet music generation from music21 Scores.

Converts music21 Score objects (or MIDI files) to Lilypond notation
and renders them to PDF or PNG using the lilypond CLI. Falls back
with a clear error if Lilypond is not installed.
"""

import logging
import os
import subprocess

from music21 import converter, stream
from music21.lily import translate as lily_translate

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = {"pdf", "png", "svg"}


class SheetGenerationError(Exception):
    """Raised when sheet music generation fails."""

    pass


def _create_lilypond_converter():
    """Create a LilypondConverter with setupTools bypassed.

    music21's LilypondConverter.__init__ calls setupTools(), which
    attempts to run the lilypond binary to check the version. We
    patch setupTools to a no-op so that the converter can be created
    even when Lilypond is not installed. The textFromMusic21Object
    method only needs Python, not the lilypond binary.

    Returns:
        A LilypondConverter instance with sensible defaults.
    """
    original_setup = lily_translate.LilypondConverter.setupTools
    try:
        lily_translate.LilypondConverter.setupTools = lambda self: None
        lpc = lily_translate.LilypondConverter()
    finally:
        lily_translate.LilypondConverter.setupTools = original_setup

    # Set version defaults that setupTools would normally set
    lpc.majorVersion = "2"
    lpc.minorVersion = "24"
    lpc.versionString = '\\version "2.24"'
    from music21.lily import lilyObjects as lyo

    lpc.versionScheme = lyo.LyEmbeddedScm(lpc.versionString)
    lpc.headerScheme = lyo.LyEmbeddedScm(lpc.bookHeader)
    lpc.backendString = "-dbackend="
    return lpc


class SheetGenerator:
    """Generates sheet music from music21 Scores via Lilypond.

    Args:
        output_format: Target format -- "pdf", "png", or "svg" (default "pdf").
        default_title: Title to embed in the sheet music header.

    Raises:
        ValueError: If output_format is not one of the supported formats.
    """

    def __init__(
        self,
        output_format: str = "pdf",
        default_title: str = "Piano Accompaniment",
    ) -> None:
        if output_format not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Format '{output_format}' is not supported. "
                f"Choose from: {', '.join(sorted(SUPPORTED_FORMATS))}"
            )
        self.output_format = output_format
        self.default_title = default_title

    def to_lilypond(self, score: object) -> str:
        """Convert a music21 Score to a Lilypond notation string.

        Uses music21's LilypondConverter to generate the notation
        purely in Python, without requiring the lilypond binary.

        Args:
            score: A music21 stream.Score object.

        Returns:
            A string containing valid Lilypond notation.

        Raises:
            SheetGenerationError: If the input is not a valid Score.
        """
        if score is None or not isinstance(score, stream.Score):
            raise SheetGenerationError(
                "Invalid input: expected a music21 Score object, "
                f"got {type(score).__name__}"
            )

        try:
            lpc = _create_lilypond_converter()
            ly_text = lpc.textFromMusic21Object(score)
            return ly_text
        except SheetGenerationError:
            raise
        except Exception as exc:
            raise SheetGenerationError(
                f"Failed to convert score to Lilypond: {exc}"
            ) from exc

    def _resolve_score(self, score_or_path: object) -> stream.Score:
        """Resolve the input to a music21 Score.

        Accepts either a music21 Score object or a path to a MIDI file.

        Args:
            score_or_path: A music21 Score or a string path to a MIDI file.

        Returns:
            A music21 Score object.

        Raises:
            SheetGenerationError: If the input cannot be resolved.
        """
        if score_or_path is None:
            raise SheetGenerationError(
                "Invalid input: score cannot be None"
            )

        if isinstance(score_or_path, stream.Score):
            return score_or_path

        if isinstance(score_or_path, str):
            if not os.path.isfile(score_or_path):
                raise SheetGenerationError(
                    f"MIDI file not found: {score_or_path}"
                )
            try:
                parsed = converter.parse(score_or_path)
                if isinstance(parsed, stream.Score):
                    return parsed
                # converter.parse may return an Opus or Part; wrap if needed
                s = stream.Score()
                if isinstance(parsed, stream.Part):
                    s.append(parsed)
                elif hasattr(parsed, "parts"):
                    for part in parsed.parts:
                        s.append(part)
                else:
                    s.append(parsed)
                return s
            except Exception as exc:
                raise SheetGenerationError(
                    f"Failed to parse MIDI file: {exc}"
                ) from exc

        raise SheetGenerationError(
            f"Invalid input type: expected Score or MIDI path string, "
            f"got {type(score_or_path).__name__}"
        )

    def generate_sheet(self, score_or_path: object, output_path: str) -> str:
        """Generate sheet music from a Score or MIDI path.

        Writes a Lilypond .ly file, then invokes the lilypond CLI to
        produce the final output (PDF/PNG/SVG).

        Args:
            score_or_path: A music21 Score or path to a MIDI file.
            output_path: Desired output file path.

        Returns:
            The output file path on success.

        Raises:
            SheetGenerationError: On invalid input, Lilypond not installed,
                or rendering failure.
        """
        score = self._resolve_score(score_or_path)

        # Generate Lilypond notation
        ly_content = self.to_lilypond(score)

        # Write the .ly file
        output_dir = os.path.dirname(output_path) or "."
        base_name = os.path.splitext(os.path.basename(output_path))[0]
        ly_path = os.path.join(output_dir, f"{base_name}.ly")

        with open(ly_path, "w", encoding="utf-8") as f:
            f.write(ly_content)

        logger.info("Wrote Lilypond file: %s", ly_path)

        # Build lilypond command
        fmt_flag = f"--{self.output_format}"
        cmd = [
            "lilypond",
            fmt_flag,
            "-o", os.path.join(output_dir, base_name),
            ly_path,
        ]

        logger.info(
            "Rendering sheet music: %s -> %s",
            ly_path,
            output_path,
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except FileNotFoundError:
            raise SheetGenerationError(
                "Lilypond is not installed or not found in PATH. "
                "Install it with: apt-get install lilypond (Linux), "
                "brew install lilypond (macOS), or download from "
                "https://lilypond.org/"
            )
        except subprocess.TimeoutExpired:
            raise SheetGenerationError(
                "Lilypond rendering timed out after 120 seconds."
            )

        if result.returncode != 0:
            raise SheetGenerationError(
                f"Lilypond rendering failed (exit code {result.returncode}): "
                f"{result.stderr}"
            )

        logger.info("Sheet music generation complete: %s", output_path)
        return output_path
