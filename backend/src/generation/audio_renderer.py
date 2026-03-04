"""FluidSynth audio rendering for MIDI-to-WAV conversion.

Uses the fluidsynth CLI to render MIDI files to WAV audio using a
specified SoundFont. Falls back with a clear error message if
FluidSynth is not installed on the system.
"""

import logging
import os
import subprocess

logger = logging.getLogger(__name__)


class AudioRenderError(Exception):
    """Raised when audio rendering fails."""

    pass


class AudioRenderer:
    """Renders MIDI files to WAV audio using FluidSynth.

    Args:
        soundfont_path: Absolute path to a .sf2 SoundFont file.
        sample_rate: Output sample rate in Hz (default 44100).
        channels: Number of audio channels (1=mono, 2=stereo; default 2).
        gain: Output gain multiplier (default 1.0).
    """

    def __init__(
        self,
        soundfont_path: str,
        sample_rate: int = 44100,
        channels: int = 2,
        gain: float = 1.0,
    ) -> None:
        self.soundfont_path = soundfont_path
        self.sample_rate = sample_rate
        self.channels = channels
        self.gain = gain

    def get_config(self) -> dict:
        """Return the current render configuration as a dictionary.

        Returns:
            Dictionary with keys: soundfont_path, sample_rate, channels, gain.
        """
        return {
            "soundfont_path": self.soundfont_path,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "gain": self.gain,
        }

    def render_midi(self, midi_path: str, output_path: str) -> str:
        """Render a MIDI file to WAV audio using FluidSynth.

        Args:
            midi_path: Path to the input MIDI file.
            output_path: Path for the output WAV file.

        Returns:
            The output file path on success.

        Raises:
            AudioRenderError: If the soundfont is missing, the MIDI file
                is missing, FluidSynth is not installed, or rendering fails.
        """
        # Validate soundfont exists
        if not os.path.isfile(self.soundfont_path):
            raise AudioRenderError(
                f"Soundfont file not found: {self.soundfont_path}"
            )

        # Validate MIDI file exists
        if not os.path.isfile(midi_path):
            raise AudioRenderError(
                f"MIDI file not found: {midi_path}"
            )

        # Ensure output path has .wav extension
        if not output_path.endswith(".wav"):
            output_path = output_path + ".wav"

        # Build fluidsynth command
        cmd = [
            "fluidsynth",
            "-ni",                          # non-interactive, no shell
            "-g", str(self.gain),           # gain
            "-r", str(self.sample_rate),    # sample rate
            "-o", f"audio.file.name={output_path}",
            "-o", f"synth.audio-channels={self.channels}",
            "-T", "wav",                    # output type
            "-F", output_path,              # output file
            self.soundfont_path,
            midi_path,
        ]

        logger.info(
            "Rendering MIDI to WAV: %s -> %s (sr=%d, ch=%d)",
            midi_path,
            output_path,
            self.sample_rate,
            self.channels,
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except FileNotFoundError:
            raise AudioRenderError(
                "FluidSynth is not installed or not found in PATH. "
                "Install it with: apt-get install fluidsynth (Linux), "
                "brew install fluidsynth (macOS), or download from "
                "https://www.fluidsynth.org/"
            )
        except subprocess.TimeoutExpired:
            raise AudioRenderError(
                "FluidSynth rendering timed out after 300 seconds."
            )

        if result.returncode != 0:
            raise AudioRenderError(
                f"FluidSynth rendering failed (exit code {result.returncode}): "
                f"{result.stderr}"
            )

        logger.info("Audio rendering complete: %s", output_path)
        return output_path
