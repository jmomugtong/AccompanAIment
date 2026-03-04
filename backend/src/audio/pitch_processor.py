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
