"""Multi-format output conversion for generated accompaniments.

Converts between MIDI, WAV (audio), and PDF (sheet music) formats,
delegating to FluidSynth for audio rendering and Lilypond for sheet
music generation.
"""

import logging
import os
import shutil
import subprocess

logger = logging.getLogger(__name__)


class FormatConversionError(Exception):
    """Raised when a format conversion fails."""

    pass


class FormatConverter:
    """Converts accompaniment files between supported formats.

    Supported formats:
        - midi: Standard MIDI file (.mid)
        - wav: Audio file rendered via FluidSynth (.wav)
        - pdf: Sheet music rendered via Lilypond (.pdf)

    For WAV and PDF conversion, the corresponding external tools
    (FluidSynth, Lilypond) must be installed and available on PATH.
    """

    supported_formats = {"midi", "wav", "pdf"}

    def __init__(
        self,
        soundfont_path: str | None = None,
        sample_rate: int = 44100,
    ) -> None:
        """Initialize the format converter.

        Args:
            soundfont_path: Path to a .sf2 SoundFont file for WAV rendering.
                If None, the converter will attempt to use a default path.
            sample_rate: Sample rate for audio rendering (default 44100 Hz).
        """
        self.soundfont_path = soundfont_path
        self.sample_rate = sample_rate

    def convert(
        self,
        input_path: str,
        output_format: str,
        output_path: str | None = None,
    ) -> str:
        """Convert an input file to the specified output format.

        Args:
            input_path: Path to the input file (typically a .mid MIDI file).
            output_format: Target format -- "midi", "wav", or "pdf".
            output_path: Optional explicit output file path. If not provided,
                the output file is placed next to the input with the
                appropriate extension.

        Returns:
            The path to the output file.

        Raises:
            FormatConversionError: If the format is unsupported, the input
                file is missing, or the conversion tool is not available.
        """
        if output_format not in self.supported_formats:
            raise FormatConversionError(
                f"Unsupported output format '{output_format}'. "
                f"Supported formats: {', '.join(sorted(self.supported_formats))}"
            )

        if not os.path.isfile(input_path):
            raise FormatConversionError(
                f"Input file not found: {input_path}"
            )

        if output_path is None:
            base, _ = os.path.splitext(input_path)
            ext_map = {"midi": ".mid", "wav": ".wav", "pdf": ".pdf"}
            output_path = base + ext_map[output_format]

        if output_format == "midi":
            return self._convert_to_midi(input_path, output_path)
        elif output_format == "wav":
            return self._convert_to_wav(input_path, output_path)
        elif output_format == "pdf":
            return self._convert_to_pdf(input_path, output_path)

        # Should not be reachable, but satisfies type checking.
        raise FormatConversionError(f"Unhandled format: {output_format}")

    def _convert_to_midi(self, input_path: str, output_path: str) -> str:
        """Copy/rename the input as a MIDI file.

        If the input is already a MIDI file, this is essentially a copy.

        Args:
            input_path: Source file path.
            output_path: Destination file path.

        Returns:
            The output file path.
        """
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            shutil.copy2(input_path, output_path)
        logger.info("MIDI output: %s", output_path)
        return output_path

    def _convert_to_wav(self, input_path: str, output_path: str) -> str:
        """Render a MIDI file to WAV using FluidSynth.

        Args:
            input_path: Path to the input MIDI file.
            output_path: Path for the output WAV file.

        Returns:
            The output file path.

        Raises:
            FormatConversionError: If FluidSynth is not installed or fails.
        """
        if self.soundfont_path is None or not os.path.isfile(self.soundfont_path):
            raise FormatConversionError(
                "Cannot convert to WAV: no valid SoundFont file configured. "
                "Set soundfont_path when creating the FormatConverter."
            )

        cmd = [
            "fluidsynth",
            "-ni",
            "-r", str(self.sample_rate),
            "-T", "wav",
            "-F", output_path,
            self.soundfont_path,
            input_path,
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
        except FileNotFoundError:
            raise FormatConversionError(
                "FluidSynth is not installed or not found in PATH."
            )
        except subprocess.TimeoutExpired:
            raise FormatConversionError(
                "FluidSynth rendering timed out after 300 seconds."
            )

        if result.returncode != 0:
            raise FormatConversionError(
                f"FluidSynth failed (exit {result.returncode}): {result.stderr}"
            )

        logger.info("WAV output: %s", output_path)
        return output_path

    def _convert_to_pdf(self, input_path: str, output_path: str) -> str:
        """Render a MIDI file to PDF sheet music using Lilypond.

        This is a simplified conversion that invokes Lilypond via music21.
        For full-featured sheet generation, use SheetGenerator directly.

        Args:
            input_path: Path to the input MIDI file.
            output_path: Path for the output PDF file.

        Returns:
            The output file path.

        Raises:
            FormatConversionError: If Lilypond is not installed or fails.
        """
        try:
            from music21 import converter as m21converter
        except ImportError:
            raise FormatConversionError(
                "music21 is required for PDF conversion but is not installed."
            )

        try:
            score = m21converter.parse(input_path)
        except Exception as exc:
            raise FormatConversionError(
                f"Failed to parse MIDI file for PDF conversion: {exc}"
            ) from exc

        output_dir = os.path.dirname(output_path) or "."
        base_name = os.path.splitext(os.path.basename(output_path))[0]

        # Generate Lilypond source and render
        try:
            from music21.lily import translate as lily_translate

            original_setup = lily_translate.LilypondConverter.setupTools
            try:
                lily_translate.LilypondConverter.setupTools = lambda self: None
                lpc = lily_translate.LilypondConverter()
            finally:
                lily_translate.LilypondConverter.setupTools = original_setup

            lpc.majorVersion = "2"
            lpc.minorVersion = "24"
            lpc.versionString = '\\version "2.24"'
            from music21.lily import lilyObjects as lyo

            lpc.versionScheme = lyo.LyEmbeddedScm(lpc.versionString)
            lpc.headerScheme = lyo.LyEmbeddedScm(lpc.bookHeader)
            lpc.backendString = "-dbackend="

            ly_content = lpc.textFromMusic21Object(score)
        except Exception as exc:
            raise FormatConversionError(
                f"Failed to generate Lilypond notation: {exc}"
            ) from exc

        ly_path = os.path.join(output_dir, f"{base_name}.ly")
        with open(ly_path, "w", encoding="utf-8") as f:
            f.write(ly_content)

        cmd = [
            "lilypond",
            "--pdf",
            "-o", os.path.join(output_dir, base_name),
            ly_path,
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
        except FileNotFoundError:
            raise FormatConversionError(
                "Lilypond is not installed or not found in PATH."
            )
        except subprocess.TimeoutExpired:
            raise FormatConversionError(
                "Lilypond rendering timed out after 120 seconds."
            )

        if result.returncode != 0:
            raise FormatConversionError(
                f"Lilypond failed (exit {result.returncode}): {result.stderr}"
            )

        logger.info("PDF output: %s", output_path)
        return output_path
