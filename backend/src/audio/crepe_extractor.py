"""CREPE-based melody extraction from audio files."""

import logging
from typing import Any

import librosa
import numpy as np

try:
    import crepe
except ImportError:
    crepe = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _hz_to_midi(frequency: float) -> int:
    """Convert frequency in Hz to the nearest MIDI note number."""
    if frequency <= 0:
        return 0
    return int(round(12 * np.log2(frequency / 440.0) + 69))


class CREPEExtractor:
    """Extract melody pitch contours from audio using CREPE."""

    def __init__(
        self,
        model_capacity: str = "full",
        confidence_threshold: float = 0.5,
    ) -> None:
        self.model_capacity = model_capacity
        self.confidence_threshold = confidence_threshold

    def extract(self, file_path: str) -> dict[str, Any]:
        """Extract melody from an audio file.

        Args:
            file_path: Path to a mono WAV file.

        Returns:
            Dict with notes (MIDI ints), timings (floats),
            confidence (floats), and duration_seconds.
        """
        if crepe is None:
            raise RuntimeError("crepe is not installed")

        audio, sr = librosa.load(file_path, sr=None, mono=True)

        time, frequency, confidence, _ = crepe.predict(
            audio,
            sr,
            model_capacity=self.model_capacity,
            viterbi=True,
        )

        # Filter by confidence threshold
        voiced_mask = confidence >= self.confidence_threshold
        voiced_time = time[voiced_mask]
        voiced_freq = frequency[voiced_mask]
        voiced_conf = confidence[voiced_mask]

        # Convert to MIDI notes
        notes = [_hz_to_midi(f) for f in voiced_freq]

        duration = float(time[-1]) if len(time) > 0 else 0.0

        logger.info(
            "Extracted %d voiced frames from %s (%.1fs, avg confidence %.2f)",
            len(notes),
            file_path,
            duration,
            float(np.mean(voiced_conf)) if len(voiced_conf) > 0 else 0.0,
        )

        return {
            "notes": notes,
            "timings": [float(t) for t in voiced_time],
            "confidence": [float(c) for c in voiced_conf],
            "duration_seconds": duration,
        }
