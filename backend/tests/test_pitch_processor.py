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


class TestOctaveAmbiguityResolution:
    """Test octave ambiguity resolution in pitch contours.

    CREPE sometimes jumps an octave up or down on a single frame. The
    resolver should detect these spurious jumps and correct them to the
    neighbouring pitch level.
    """

    def test_single_octave_jump_up_is_corrected(self):
        """A lone frame one octave above its neighbours should snap back."""
        proc = PitchProcessor()
        # Stable at 440 Hz, one frame jumps to 880 (octave up)
        freqs = np.full(20, 440.0)
        freqs[10] = 880.0
        resolved = proc.resolve_octave_ambiguity(freqs)
        assert abs(resolved[10] - 440.0) < 1.0

    def test_single_octave_jump_down_is_corrected(self):
        """A lone frame one octave below its neighbours should snap back."""
        proc = PitchProcessor()
        freqs = np.full(20, 440.0)
        freqs[10] = 220.0
        resolved = proc.resolve_octave_ambiguity(freqs)
        assert abs(resolved[10] - 440.0) < 1.0

    def test_legitimate_octave_change_preserved(self):
        """A sustained octave shift (many consecutive frames) is genuine."""
        proc = PitchProcessor()
        # First half at 440 Hz, second half at 880 Hz
        freqs = np.concatenate([np.full(20, 440.0), np.full(20, 880.0)])
        resolved = proc.resolve_octave_ambiguity(freqs)
        # The sustained region should remain at 880 Hz
        np.testing.assert_allclose(resolved[30:], 880.0, atol=1.0)

    def test_constant_pitch_unchanged(self):
        """A constant-pitch contour should pass through untouched."""
        proc = PitchProcessor()
        freqs = np.full(50, 330.0)
        resolved = proc.resolve_octave_ambiguity(freqs)
        np.testing.assert_allclose(resolved, 330.0, atol=0.01)

    def test_zero_frequencies_ignored(self):
        """Zero (unvoiced) frames should remain zero after resolution."""
        proc = PitchProcessor()
        freqs = np.array([440.0, 0.0, 440.0, 880.0, 440.0])
        resolved = proc.resolve_octave_ambiguity(freqs)
        assert resolved[1] == 0.0

    def test_empty_array(self):
        """Empty input should return an empty array."""
        proc = PitchProcessor()
        resolved = proc.resolve_octave_ambiguity(np.array([]))
        assert len(resolved) == 0

    def test_preserves_length(self):
        """Output length must equal input length."""
        proc = PitchProcessor()
        freqs = np.random.uniform(200, 600, size=100)
        resolved = proc.resolve_octave_ambiguity(freqs)
        assert len(resolved) == len(freqs)


class TestTimingQuantization:
    """Test beat-grid timing quantization (snap note onsets to grid)."""

    def test_snap_to_nearest_beat(self):
        """Onsets close to a beat should snap exactly to it."""
        proc = PitchProcessor()
        bpm = 120.0  # beat every 0.5 s
        onsets = np.array([0.02, 0.48, 1.03])  # near 0.0, 0.5, 1.0
        quantized = proc.quantize_timing(onsets, bpm, resolution=1.0)
        np.testing.assert_allclose(quantized, [0.0, 0.5, 1.0], atol=0.001)

    def test_snap_to_eighth_note_grid(self):
        """With resolution=0.5, grid is every eighth note."""
        proc = PitchProcessor()
        bpm = 120.0  # beat = 0.5 s, eighth = 0.25 s
        onsets = np.array([0.12, 0.26, 0.74])
        quantized = proc.quantize_timing(onsets, bpm, resolution=0.5)
        # Grid: 0.0, 0.25, 0.5, 0.75 ...
        np.testing.assert_allclose(quantized, [0.0, 0.25, 0.75], atol=0.001)

    def test_snap_to_sixteenth_note_grid(self):
        """With resolution=0.25, grid is every sixteenth note."""
        proc = PitchProcessor()
        bpm = 120.0  # beat = 0.5 s, sixteenth = 0.125 s
        onsets = np.array([0.06, 0.13, 0.19])
        quantized = proc.quantize_timing(onsets, bpm, resolution=0.25)
        np.testing.assert_allclose(quantized, [0.0, 0.125, 0.25], atol=0.001)

    def test_exact_on_beat_unchanged(self):
        """Onsets already on the grid should not move."""
        proc = PitchProcessor()
        bpm = 120.0
        onsets = np.array([0.0, 0.5, 1.0, 1.5])
        quantized = proc.quantize_timing(onsets, bpm, resolution=1.0)
        np.testing.assert_allclose(quantized, onsets, atol=0.001)

    def test_empty_onsets(self):
        """Empty onset array should return empty."""
        proc = PitchProcessor()
        quantized = proc.quantize_timing(np.array([]), 120.0)
        assert len(quantized) == 0

    def test_preserves_order(self):
        """Quantized onsets must remain in ascending order."""
        proc = PitchProcessor()
        onsets = np.array([0.03, 0.27, 0.52, 0.78, 1.01])
        quantized = proc.quantize_timing(onsets, 100.0, resolution=1.0)
        assert all(quantized[i] <= quantized[i + 1] for i in range(len(quantized) - 1))


class TestVibratoDetection:
    """Test vibrato detection in pitch contours."""

    def test_detect_vibrato_in_sine_modulated_pitch(self):
        """A sine-modulated pitch signal should be detected as vibrato."""
        proc = PitchProcessor()
        sr = 100  # frames per second
        t = np.linspace(0, 2.0, sr * 2)  # 2 seconds
        # 5 Hz vibrato with +/- 15 cents modulation around A4
        vibrato_rate = 5.0
        cents_depth = 15.0
        base_freq = 440.0
        freqs = base_freq * (2 ** (cents_depth * np.sin(2 * np.pi * vibrato_rate * t) / 1200))
        result = proc.detect_vibrato(freqs, frame_rate=sr)
        assert result["has_vibrato"] is True
        assert 4.0 <= result["rate_hz"] <= 7.0
        assert result["extent_cents"] > 5.0

    def test_no_vibrato_in_constant_pitch(self):
        """A flat pitch contour should NOT be flagged as vibrato."""
        proc = PitchProcessor()
        freqs = np.full(200, 440.0)
        result = proc.detect_vibrato(freqs, frame_rate=100)
        assert result["has_vibrato"] is False

    def test_no_vibrato_in_noise(self):
        """Random noise should not register as vibrato."""
        proc = PitchProcessor()
        np.random.seed(42)
        freqs = np.random.uniform(400, 480, size=200)
        result = proc.detect_vibrato(freqs, frame_rate=100)
        # Random noise lacks the periodic structure of vibrato
        assert result["has_vibrato"] is False

    def test_vibrato_result_keys(self):
        """Result dict must contain standard keys."""
        proc = PitchProcessor()
        freqs = np.full(200, 440.0)
        result = proc.detect_vibrato(freqs, frame_rate=100)
        assert "has_vibrato" in result
        assert "rate_hz" in result
        assert "extent_cents" in result

    def test_empty_contour(self):
        """Empty pitch array should return no vibrato."""
        proc = PitchProcessor()
        result = proc.detect_vibrato(np.array([]), frame_rate=100)
        assert result["has_vibrato"] is False
        assert result["rate_hz"] == 0.0
        assert result["extent_cents"] == 0.0

    def test_short_contour_no_crash(self):
        """Very short contours (< 1 period) should not crash."""
        proc = PitchProcessor()
        freqs = np.array([440.0, 441.0, 439.0])
        result = proc.detect_vibrato(freqs, frame_rate=100)
        assert "has_vibrato" in result


class TestPitchRangeValidation:
    """Test pitch range validation (C2-C7, MIDI 36-96)."""

    def test_in_range_notes_pass(self):
        """Notes within C2-C7 should all be valid."""
        proc = PitchProcessor()
        midi_notes = np.array([36, 60, 72, 96])
        valid, out_of_range = proc.validate_pitch_range(midi_notes)
        assert valid is True
        assert len(out_of_range) == 0

    def test_below_range_detected(self):
        """Notes below MIDI 36 (C2) should be flagged."""
        proc = PitchProcessor()
        midi_notes = np.array([30, 60, 72])
        valid, out_of_range = proc.validate_pitch_range(midi_notes)
        assert valid is False
        assert 30 in out_of_range

    def test_above_range_detected(self):
        """Notes above MIDI 96 (C7) should be flagged."""
        proc = PitchProcessor()
        midi_notes = np.array([60, 100, 72])
        valid, out_of_range = proc.validate_pitch_range(midi_notes)
        assert valid is False
        assert 100 in out_of_range

    def test_zeros_ignored(self):
        """MIDI 0 (unvoiced) should not be treated as out-of-range."""
        proc = PitchProcessor()
        midi_notes = np.array([0, 60, 0, 72])
        valid, out_of_range = proc.validate_pitch_range(midi_notes)
        assert valid is True
        assert len(out_of_range) == 0

    def test_boundary_values(self):
        """MIDI 36 and 96 are inclusive boundaries."""
        proc = PitchProcessor()
        midi_notes = np.array([36, 96])
        valid, _ = proc.validate_pitch_range(midi_notes)
        assert valid is True

    def test_just_outside_boundaries(self):
        """MIDI 35 and 97 should fail."""
        proc = PitchProcessor()
        midi_notes = np.array([35, 97])
        valid, out_of_range = proc.validate_pitch_range(midi_notes)
        assert valid is False
        assert 35 in out_of_range
        assert 97 in out_of_range

    def test_empty_array_is_valid(self):
        """Empty array should be considered valid."""
        proc = PitchProcessor()
        valid, out_of_range = proc.validate_pitch_range(np.array([], dtype=int))
        assert valid is True
        assert len(out_of_range) == 0

    def test_custom_range(self):
        """Support custom min/max MIDI range."""
        proc = PitchProcessor()
        midi_notes = np.array([40, 50, 60])
        valid, out_of_range = proc.validate_pitch_range(
            midi_notes, min_midi=45, max_midi=55
        )
        assert valid is False
        assert 40 in out_of_range
        assert 60 in out_of_range


class TestTempoEstimation:
    """Test tempo estimation from note onset timing variations."""

    def test_steady_120bpm(self):
        """Evenly spaced onsets at 0.5s intervals -> ~120 BPM."""
        proc = PitchProcessor()
        onsets = np.arange(0, 5.0, 0.5)  # every 0.5 s
        bpm = proc.estimate_tempo(onsets)
        assert abs(bpm - 120.0) < 5.0

    def test_steady_60bpm(self):
        """Evenly spaced onsets at 1.0s intervals -> ~60 BPM."""
        proc = PitchProcessor()
        onsets = np.arange(0, 10.0, 1.0)
        bpm = proc.estimate_tempo(onsets)
        assert abs(bpm - 60.0) < 5.0

    def test_steady_90bpm(self):
        """Onsets at 0.6667s intervals -> ~90 BPM."""
        proc = PitchProcessor()
        beat_dur = 60.0 / 90.0
        onsets = np.arange(0, 8 * beat_dur, beat_dur)
        bpm = proc.estimate_tempo(onsets)
        assert abs(bpm - 90.0) < 5.0

    def test_slightly_noisy_onsets(self):
        """Small timing jitter should still yield a reasonable estimate."""
        proc = PitchProcessor()
        np.random.seed(0)
        beat_dur = 0.5  # 120 BPM
        onsets = np.arange(0, 5.0, beat_dur) + np.random.normal(0, 0.02, 10)
        onsets = np.sort(onsets)
        bpm = proc.estimate_tempo(onsets)
        assert abs(bpm - 120.0) < 10.0

    def test_too_few_onsets_returns_zero(self):
        """Fewer than 2 onsets should return 0.0 (cannot estimate)."""
        proc = PitchProcessor()
        assert proc.estimate_tempo(np.array([1.0])) == 0.0
        assert proc.estimate_tempo(np.array([])) == 0.0

    def test_result_is_positive(self):
        """Estimated tempo must always be positive (when enough onsets)."""
        proc = PitchProcessor()
        onsets = np.array([0.0, 0.5, 1.0, 1.5])
        bpm = proc.estimate_tempo(onsets)
        assert bpm > 0.0
