"""Tests for pitch processing: smoothing, voiced detection, MIDI quantization."""

import numpy as np
import pytest

from src.audio.pitch_processor import PitchProcessor


class TestPitchSmoothing:
    """Test pitch contour smoothing with median filter."""

    def test_smooth_removes_spikes(self):
        proc = PitchProcessor()
        # Add a spike in an otherwise constant signal
        freqs = np.full(50, 440.0)
        freqs[25] = 880.0  # outlier
        smoothed = proc.smooth_pitch(freqs, kernel_size=5)
        # The spike should be eliminated or reduced
        assert abs(smoothed[25] - 440.0) < 50.0

    def test_smooth_preserves_constant_signal(self):
        proc = PitchProcessor()
        freqs = np.full(50, 440.0)
        smoothed = proc.smooth_pitch(freqs, kernel_size=5)
        np.testing.assert_allclose(smoothed, 440.0, atol=0.01)

    def test_smooth_preserves_length(self):
        proc = PitchProcessor()
        freqs = np.random.uniform(200, 600, size=100)
        smoothed = proc.smooth_pitch(freqs, kernel_size=5)
        assert len(smoothed) == len(freqs)

    def test_smooth_with_kernel_size_1_is_identity(self):
        proc = PitchProcessor()
        freqs = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
        smoothed = proc.smooth_pitch(freqs, kernel_size=1)
        np.testing.assert_allclose(smoothed, freqs)


class TestVoicedUnvoicedDetection:
    """Test voiced/unvoiced region detection."""

    def test_all_voiced_above_threshold(self):
        proc = PitchProcessor(confidence_threshold=0.5)
        conf = np.full(50, 0.9)
        mask = proc.get_voiced_mask(conf)
        assert mask.all()

    def test_all_unvoiced_below_threshold(self):
        proc = PitchProcessor(confidence_threshold=0.5)
        conf = np.full(50, 0.2)
        mask = proc.get_voiced_mask(conf)
        assert not mask.any()

    def test_mixed_voiced_unvoiced(self):
        proc = PitchProcessor(confidence_threshold=0.5)
        conf = np.array([0.9, 0.1, 0.8, 0.3, 0.95])
        mask = proc.get_voiced_mask(conf)
        expected = np.array([True, False, True, False, True])
        np.testing.assert_array_equal(mask, expected)

    def test_custom_threshold(self):
        proc = PitchProcessor(confidence_threshold=0.8)
        conf = np.array([0.9, 0.7, 0.85, 0.5])
        mask = proc.get_voiced_mask(conf)
        expected = np.array([True, False, True, False])
        np.testing.assert_array_equal(mask, expected)


class TestMIDIQuantization:
    """Test frequency to MIDI note quantization."""

    def test_440hz_is_midi_69(self):
        proc = PitchProcessor()
        assert proc.hz_to_midi(440.0) == 69

    def test_261_63hz_is_midi_60(self):
        """Middle C (~261.63 Hz) -> MIDI 60."""
        proc = PitchProcessor()
        assert proc.hz_to_midi(261.63) == 60

    def test_880hz_is_midi_81(self):
        proc = PitchProcessor()
        assert proc.hz_to_midi(880.0) == 81

    def test_zero_hz_returns_0(self):
        proc = PitchProcessor()
        assert proc.hz_to_midi(0.0) == 0

    def test_negative_hz_returns_0(self):
        proc = PitchProcessor()
        assert proc.hz_to_midi(-100.0) == 0

    def test_quantize_array(self):
        proc = PitchProcessor()
        freqs = np.array([440.0, 261.63, 880.0])
        midi_notes = proc.quantize_to_midi(freqs)
        assert list(midi_notes) == [69, 60, 81]

    def test_quantize_filters_zeros(self):
        proc = PitchProcessor()
        freqs = np.array([440.0, 0.0, 880.0])
        midi_notes = proc.quantize_to_midi(freqs)
        # zero-frequency entries should become 0
        assert midi_notes[1] == 0


class TestPhraseSegmentation:
    """Test phrase boundary detection based on silence gaps."""

    def test_single_phrase_no_gaps(self):
        proc = PitchProcessor()
        timings = np.linspace(0, 2.0, 50)
        phrases = proc.segment_phrases(timings, gap_threshold=0.5)
        assert len(phrases) == 1

    def test_two_phrases_with_gap(self):
        proc = PitchProcessor()
        # Two groups separated by a >0.5s gap
        t1 = np.linspace(0, 1.0, 25)
        t2 = np.linspace(2.0, 3.0, 25)
        timings = np.concatenate([t1, t2])
        phrases = proc.segment_phrases(timings, gap_threshold=0.5)
        assert len(phrases) == 2

    def test_three_phrases_with_gaps(self):
        proc = PitchProcessor()
        t1 = np.array([0.0, 0.1, 0.2])
        t2 = np.array([1.0, 1.1, 1.2])
        t3 = np.array([3.0, 3.1, 3.2])
        timings = np.concatenate([t1, t2, t3])
        phrases = proc.segment_phrases(timings, gap_threshold=0.5)
        assert len(phrases) == 3

    def test_empty_timings(self):
        proc = PitchProcessor()
        phrases = proc.segment_phrases(np.array([]), gap_threshold=0.5)
        assert len(phrases) == 0

    def test_phrase_contains_correct_indices(self):
        proc = PitchProcessor()
        t1 = np.array([0.0, 0.1])
        t2 = np.array([1.0, 1.1, 1.2])
        timings = np.concatenate([t1, t2])
        phrases = proc.segment_phrases(timings, gap_threshold=0.5)
        assert len(phrases[0]) == 2
        assert len(phrases[1]) == 3


class TestEdgeCases:
    """Test edge cases: silent audio, single frame."""

    def test_single_frame(self):
        proc = PitchProcessor()
        freqs = np.array([440.0])
        smoothed = proc.smooth_pitch(freqs, kernel_size=1)
        assert len(smoothed) == 1

    def test_all_zero_frequencies(self):
        proc = PitchProcessor()
        freqs = np.zeros(10)
        midi = proc.quantize_to_midi(freqs)
        assert all(n == 0 for n in midi)

    def test_very_high_frequency(self):
        proc = PitchProcessor()
        assert proc.hz_to_midi(4186.0) == 108  # C8

    def test_very_low_frequency(self):
        proc = PitchProcessor()
        assert proc.hz_to_midi(27.5) == 21  # A0


class TestConfidenceScoreCalculations:
    """Test confidence score statistics."""

    def test_mean_confidence(self):
        proc = PitchProcessor()
        conf = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
        stats = proc.compute_confidence_stats(conf)
        assert abs(stats["mean"] - 0.7) < 0.01

    def test_min_max_confidence(self):
        proc = PitchProcessor()
        conf = np.array([0.3, 0.5, 0.9])
        stats = proc.compute_confidence_stats(conf)
        assert abs(stats["min"] - 0.3) < 0.01
        assert abs(stats["max"] - 0.9) < 0.01

    def test_empty_confidence(self):
        proc = PitchProcessor()
        stats = proc.compute_confidence_stats(np.array([]))
        assert stats["mean"] == 0.0

    def test_voiced_ratio(self):
        proc = PitchProcessor(confidence_threshold=0.5)
        conf = np.array([0.9, 0.1, 0.8, 0.3])
        stats = proc.compute_confidence_stats(conf)
        assert abs(stats["voiced_ratio"] - 0.5) < 0.01
