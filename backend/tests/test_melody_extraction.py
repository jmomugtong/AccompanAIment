"""Tests for CREPE melody extraction."""

import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.audio.crepe_extractor import CREPEExtractor

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _make_mock_crepe_output(n_frames: int = 100):
    """Create synthetic CREPE-like output arrays."""
    time = np.linspace(0, 2.0, n_frames)
    frequency = 440.0 * np.ones(n_frames)  # constant A4
    confidence = 0.9 * np.ones(n_frames)
    # activation is a 2D array (n_frames x 360) in real CREPE
    activation = np.zeros((n_frames, 360))
    return time, frequency, confidence, activation


class TestCREPEExtractorInit:
    """Test CREPEExtractor initialization."""

    def test_default_model_capacity(self):
        extractor = CREPEExtractor()
        assert extractor.model_capacity == "full"

    def test_custom_model_capacity(self):
        extractor = CREPEExtractor(model_capacity="medium")
        assert extractor.model_capacity == "medium"

    def test_default_confidence_threshold(self):
        extractor = CREPEExtractor()
        assert extractor.confidence_threshold == 0.5

    def test_custom_confidence_threshold(self):
        extractor = CREPEExtractor(confidence_threshold=0.7)
        assert extractor.confidence_threshold == 0.7


class TestCREPEExtraction:
    """Test melody extraction from audio files (CREPE mocked)."""

    @patch("src.audio.crepe_extractor.crepe")
    def test_extract_returns_dict_with_required_keys(self, mock_crepe):
        time, freq, conf, act = _make_mock_crepe_output()
        mock_crepe.predict.return_value = (time, freq, conf, act)

        extractor = CREPEExtractor()
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        result = extractor.extract(path)

        assert "notes" in result
        assert "timings" in result
        assert "confidence" in result
        assert "duration_seconds" in result

    @patch("src.audio.crepe_extractor.crepe")
    def test_extract_notes_are_midi_integers(self, mock_crepe):
        time, freq, conf, act = _make_mock_crepe_output()
        mock_crepe.predict.return_value = (time, freq, conf, act)

        extractor = CREPEExtractor()
        result = extractor.extract(os.path.join(FIXTURES_DIR, "test_mono.wav"))

        for note in result["notes"]:
            assert isinstance(note, (int, np.integer))

    @patch("src.audio.crepe_extractor.crepe")
    def test_extract_timings_are_floats(self, mock_crepe):
        time, freq, conf, act = _make_mock_crepe_output()
        mock_crepe.predict.return_value = (time, freq, conf, act)

        extractor = CREPEExtractor()
        result = extractor.extract(os.path.join(FIXTURES_DIR, "test_mono.wav"))

        for t in result["timings"]:
            assert isinstance(t, float)

    @patch("src.audio.crepe_extractor.crepe")
    def test_extract_confidence_values_between_0_and_1(self, mock_crepe):
        time, freq, conf, act = _make_mock_crepe_output()
        mock_crepe.predict.return_value = (time, freq, conf, act)

        extractor = CREPEExtractor()
        result = extractor.extract(os.path.join(FIXTURES_DIR, "test_mono.wav"))

        for c in result["confidence"]:
            assert 0.0 <= c <= 1.0

    @patch("src.audio.crepe_extractor.crepe")
    def test_extract_duration_is_positive(self, mock_crepe):
        time, freq, conf, act = _make_mock_crepe_output()
        mock_crepe.predict.return_value = (time, freq, conf, act)

        extractor = CREPEExtractor()
        result = extractor.extract(os.path.join(FIXTURES_DIR, "test_mono.wav"))

        assert result["duration_seconds"] > 0

    @patch("src.audio.crepe_extractor.crepe")
    def test_extract_filters_low_confidence_frames(self, mock_crepe):
        """Frames below confidence threshold should be excluded."""
        n = 100
        time = np.linspace(0, 2.0, n)
        freq = 440.0 * np.ones(n)
        conf = np.zeros(n)
        conf[:50] = 0.9  # first half voiced
        conf[50:] = 0.1  # second half unvoiced
        act = np.zeros((n, 360))
        mock_crepe.predict.return_value = (time, freq, conf, act)

        extractor = CREPEExtractor(confidence_threshold=0.5)
        result = extractor.extract(os.path.join(FIXTURES_DIR, "test_mono.wav"))

        assert len(result["notes"]) == 50

    @patch("src.audio.crepe_extractor.crepe")
    def test_extract_440hz_maps_to_midi_69(self, mock_crepe):
        """440 Hz should map to MIDI note 69 (A4)."""
        time, freq, conf, act = _make_mock_crepe_output(n_frames=10)
        mock_crepe.predict.return_value = (time, freq, conf, act)

        extractor = CREPEExtractor()
        result = extractor.extract(os.path.join(FIXTURES_DIR, "test_mono.wav"))

        assert all(n == 69 for n in result["notes"])

    @patch("src.audio.crepe_extractor.crepe")
    def test_extract_calls_crepe_predict(self, mock_crepe):
        time, freq, conf, act = _make_mock_crepe_output()
        mock_crepe.predict.return_value = (time, freq, conf, act)

        extractor = CREPEExtractor()
        extractor.extract(os.path.join(FIXTURES_DIR, "test_mono.wav"))

        mock_crepe.predict.assert_called_once()
