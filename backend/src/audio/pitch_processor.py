"""Pitch processing: smoothing, voiced detection, MIDI quantization.

Extended with octave ambiguity resolution, timing quantization,
vibrato detection, pitch range validation, and tempo estimation.
"""

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

    # ------------------------------------------------------------------
    # Phase 4 additions
    # ------------------------------------------------------------------

    def resolve_octave_ambiguity(
        self, frequencies: np.ndarray, window: int = 5
    ) -> np.ndarray:
        """Correct spurious octave jumps in a pitch contour.

        CREPE occasionally produces single-frame octave errors (the pitch
        jumps exactly one octave up or down for a very short duration).
        This method detects isolated jumps and snaps them back to the
        local median pitch level.

        Args:
            frequencies: Array of frequency values (Hz). Zero means
                unvoiced.
            window: Number of neighbouring frames on each side used to
                compute the local reference pitch.

        Returns:
            Corrected frequency array (same length as input).
        """
        if len(frequencies) == 0:
            return np.array([], dtype=float)

        result = frequencies.copy().astype(float)
        n = len(result)

        for i in range(n):
            if result[i] <= 0:
                continue

            # Gather voiced neighbours within the window
            lo = max(0, i - window)
            hi = min(n, i + window + 1)
            neighbours = [
                result[j] for j in range(lo, hi) if j != i and result[j] > 0
            ]
            if len(neighbours) < 2:
                continue

            local_median = float(np.median(neighbours))
            if local_median <= 0:
                continue

            ratio = result[i] / local_median

            # Check for approximately 2x (octave up) or 0.5x (octave down)
            if 1.8 < ratio < 2.2:
                result[i] = result[i] / 2.0
            elif 0.45 < ratio < 0.55:
                result[i] = result[i] * 2.0

        return result

    def quantize_timing(
        self,
        onsets: np.ndarray,
        bpm: float,
        resolution: float = 1.0,
    ) -> np.ndarray:
        """Snap note onset times to the nearest beat-grid position.

        Args:
            onsets: Array of onset times in seconds.
            bpm: Tempo in beats per minute.
            resolution: Grid resolution as a fraction of a beat.
                1.0 = quarter note, 0.5 = eighth note,
                0.25 = sixteenth note.

        Returns:
            Array of quantized onset times (seconds).
        """
        if len(onsets) == 0:
            return np.array([], dtype=float)

        beat_duration = 60.0 / bpm  # seconds per beat
        grid_step = beat_duration * resolution  # seconds per grid unit

        quantized = np.round(onsets / grid_step) * grid_step
        return quantized

    def detect_vibrato(
        self,
        frequencies: np.ndarray,
        frame_rate: int = 100,
        min_rate: float = 4.0,
        max_rate: float = 8.0,
    ) -> dict[str, object]:
        """Detect vibrato characteristics in a pitch contour.

        Vibrato is a periodic modulation of pitch, typically 4-8 Hz with
        a depth of 10-100 cents in singing voice. This method uses
        spectral analysis of the pitch contour to identify vibrato.

        Args:
            frequencies: Array of frequency values (Hz).
            frame_rate: Number of pitch frames per second.
            min_rate: Minimum vibrato rate in Hz.
            max_rate: Maximum vibrato rate in Hz.

        Returns:
            Dict with keys:
                has_vibrato (bool): Whether vibrato was detected.
                rate_hz (float): Estimated vibrato rate in Hz (0 if none).
                extent_cents (float): Peak-to-peak vibrato depth in
                    cents (0 if none).
        """
        no_vibrato: dict[str, object] = {
            "has_vibrato": False,
            "rate_hz": 0.0,
            "extent_cents": 0.0,
        }

        if len(frequencies) < 16:
            return no_vibrato

        # Work only with voiced frames
        voiced = frequencies[frequencies > 0]
        if len(voiced) < 16:
            return no_vibrato

        # Convert to cents relative to the mean pitch
        mean_freq = float(np.mean(voiced))
        if mean_freq <= 0:
            return no_vibrato

        cents = 1200.0 * np.log2(voiced / mean_freq)

        # Remove DC / low-frequency trend
        cents = cents - np.mean(cents)

        # Compute FFT of the cents contour
        n = len(cents)
        fft_vals = np.fft.rfft(cents)
        fft_mag = np.abs(fft_vals)
        freqs_axis = np.fft.rfftfreq(n, d=1.0 / frame_rate)

        # Look for a peak in the vibrato frequency range
        mask = (freqs_axis >= min_rate) & (freqs_axis <= max_rate)
        if not np.any(mask):
            return no_vibrato

        vibrato_magnitudes = fft_mag[mask]
        vibrato_freqs = freqs_axis[mask]

        peak_idx = int(np.argmax(vibrato_magnitudes))
        peak_magnitude = vibrato_magnitudes[peak_idx]
        peak_freq = vibrato_freqs[peak_idx]

        # The peak must be significantly above the average magnitude in
        # the vibrato band to count as genuine vibrato
        mean_mag = float(np.mean(fft_mag[1:]))  # exclude DC
        if mean_mag <= 0:
            return no_vibrato

        # Require peak to be at least 3x the mean magnitude
        if peak_magnitude < 3.0 * mean_mag:
            return no_vibrato

        # Estimate extent in cents (peak-to-peak ~ 2 * amplitude)
        # FFT magnitude / (n/2) gives the amplitude of the sinusoid
        amplitude_cents = float(peak_magnitude / (n / 2.0))
        extent_cents = 2.0 * amplitude_cents

        if extent_cents < 3.0:
            return no_vibrato

        return {
            "has_vibrato": True,
            "rate_hz": float(peak_freq),
            "extent_cents": float(extent_cents),
        }

    def validate_pitch_range(
        self,
        midi_notes: np.ndarray,
        min_midi: int = 36,
        max_midi: int = 96,
    ) -> tuple[bool, list[int]]:
        """Validate that all MIDI notes fall within an expected range.

        The default range is C2 (MIDI 36) to C7 (MIDI 96), which covers
        the practical singing range. Notes with value 0 are treated as
        unvoiced and are ignored.

        Args:
            midi_notes: Array of MIDI note numbers.
            min_midi: Minimum valid MIDI note (inclusive).
            max_midi: Maximum valid MIDI note (inclusive).

        Returns:
            Tuple of (is_valid, out_of_range_notes) where is_valid is
            True if all non-zero notes are within range, and
            out_of_range_notes is a sorted list of offending values.
        """
        if len(midi_notes) == 0:
            return True, []

        # Filter out unvoiced (zero) notes
        voiced_notes = midi_notes[midi_notes > 0]
        if len(voiced_notes) == 0:
            return True, []

        out_of_range_mask = (voiced_notes < min_midi) | (voiced_notes > max_midi)
        out_of_range_notes = sorted(set(int(n) for n in voiced_notes[out_of_range_mask]))

        is_valid = len(out_of_range_notes) == 0
        return is_valid, out_of_range_notes

    def estimate_tempo(self, onsets: np.ndarray) -> float:
        """Estimate tempo (BPM) from note onset times.

        Uses the median inter-onset interval to derive a robust tempo
        estimate that is insensitive to outliers.

        Args:
            onsets: Array of onset times in seconds (must be sorted).

        Returns:
            Estimated tempo in BPM, or 0.0 if there are fewer than 2
            onsets.
        """
        if len(onsets) < 2:
            return 0.0

        intervals = np.diff(onsets)
        # Remove non-positive intervals (safety)
        intervals = intervals[intervals > 0]
        if len(intervals) == 0:
            return 0.0

        median_interval = float(np.median(intervals))
        if median_interval <= 0:
            return 0.0

        bpm = 60.0 / median_interval
        return float(bpm)
