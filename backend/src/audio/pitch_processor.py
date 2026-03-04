"""Pitch processing: smoothing, voiced detection, MIDI quantization."""

import logging

import numpy as np
from scipy.ndimage import median_filter

logger = logging.getLogger(__name__)


class PitchProcessor:
    """Post-process raw pitch contours from CREPE."""

    def __init__(self, confidence_threshold: float = 0.5) -> None:
        self.confidence_threshold = confidence_threshold

    def smooth_pitch(
        self, frequencies: np.ndarray, kernel_size: int = 5
    ) -> np.ndarray:
        """Smooth a pitch contour using a median filter.

        Args:
            frequencies: Array of frequency values (Hz).
            kernel_size: Size of the median filter kernel.

        Returns:
            Smoothed frequency array.
        """
        return median_filter(frequencies, size=kernel_size)

    def get_voiced_mask(self, confidence: np.ndarray) -> np.ndarray:
        """Create a boolean mask for voiced frames.

        Args:
            confidence: Array of confidence scores (0-1).

        Returns:
            Boolean array where True = voiced.
        """
        return confidence >= self.confidence_threshold

    @staticmethod
    def hz_to_midi(frequency: float) -> int:
        """Convert a frequency in Hz to the nearest MIDI note number.

        Args:
            frequency: Frequency in Hz.

        Returns:
            MIDI note number (0 for invalid/zero frequency).
        """
        if frequency <= 0:
            return 0
        return int(round(12 * np.log2(frequency / 440.0) + 69))

    def quantize_to_midi(self, frequencies: np.ndarray) -> np.ndarray:
        """Convert an array of frequencies to MIDI note numbers.

        Args:
            frequencies: Array of frequency values (Hz).

        Returns:
            Array of MIDI note numbers.
        """
        return np.array([self.hz_to_midi(f) for f in frequencies])

    def segment_phrases(
        self, timings: np.ndarray, gap_threshold: float = 0.5
    ) -> list[np.ndarray]:
        """Segment timings into phrases based on silence gaps.

        Args:
            timings: Array of frame timestamps (seconds).
            gap_threshold: Minimum gap (seconds) to split phrases.

        Returns:
            List of arrays, each containing timing indices for one phrase.
        """
        if len(timings) == 0:
            return []

        phrases: list[list[int]] = [[0]]
        for i in range(1, len(timings)):
            if timings[i] - timings[i - 1] > gap_threshold:
                phrases.append([i])
            else:
                phrases[-1].append(i)

        return [np.array(p) for p in phrases]

    def compute_confidence_stats(self, confidence: np.ndarray) -> dict[str, float]:
        """Compute summary statistics for confidence scores.

        Args:
            confidence: Array of confidence scores.

        Returns:
            Dict with mean, min, max, and voiced_ratio.
        """
        if len(confidence) == 0:
            return {"mean": 0.0, "min": 0.0, "max": 0.0, "voiced_ratio": 0.0}

        voiced_mask = self.get_voiced_mask(confidence)
        return {
            "mean": float(np.mean(confidence)),
            "min": float(np.min(confidence)),
            "max": float(np.max(confidence)),
            "voiced_ratio": float(np.sum(voiced_mask) / len(confidence)),
        }
