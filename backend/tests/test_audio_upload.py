"""Tests for audio upload handling and preprocessing."""

import os
import tempfile

import numpy as np
import pytest
import soundfile as sf

from src.audio.audio_utils import (
    normalize_volume,
    validate_audio_duration,
    validate_file_format,
    validate_file_size,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestFileFormatValidation:
    """Test audio file format validation."""

    def test_wav_format_accepted(self):
        assert validate_file_format("song.wav") is True

    def test_mp3_format_accepted(self):
        assert validate_file_format("song.mp3") is True

    def test_m4a_format_accepted(self):
        assert validate_file_format("song.m4a") is True

    def test_flac_format_accepted(self):
        assert validate_file_format("song.flac") is True

    def test_uppercase_extension_accepted(self):
        assert validate_file_format("song.WAV") is True

    def test_mixed_case_extension_accepted(self):
        assert validate_file_format("song.Mp3") is True

    def test_txt_format_rejected(self):
        assert validate_file_format("notes.txt") is False

    def test_pdf_format_rejected(self):
        assert validate_file_format("sheet.pdf") is False

    def test_ogg_format_rejected(self):
        assert validate_file_format("song.ogg") is False

    def test_no_extension_rejected(self):
        assert validate_file_format("songfile") is False

    def test_empty_string_rejected(self):
        assert validate_file_format("") is False


class TestFileSizeValidation:
    """Test audio file size validation (max 100MB)."""

    def test_small_file_accepted(self):
        """A small WAV fixture should be well under 100MB."""
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        assert validate_file_size(path) is True

    def test_file_under_custom_limit_accepted(self):
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        assert validate_file_size(path, max_bytes=10 * 1024 * 1024) is True

    def test_file_over_custom_limit_rejected(self):
        """Set a tiny limit so even a small file fails."""
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        assert validate_file_size(path, max_bytes=100) is False

    def test_nonexistent_file_rejected(self):
        assert validate_file_size("/nonexistent/file.wav") is False

    def test_exact_limit_accepted(self):
        """File exactly at the limit should pass."""
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        file_size = os.path.getsize(path)
        assert validate_file_size(path, max_bytes=file_size) is True


class TestAudioDurationValidation:
    """Test audio duration validation (max 10 minutes)."""

    def test_short_audio_accepted(self):
        """2-second fixture should pass default 10-minute limit."""
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        assert validate_audio_duration(path) is True

    def test_audio_over_custom_limit_rejected(self):
        """Reject audio over a 1-second custom limit."""
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        assert validate_audio_duration(path, max_seconds=1.0) is False

    def test_audio_under_custom_limit_accepted(self):
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        assert validate_audio_duration(path, max_seconds=10.0) is True

    def test_nonexistent_file_rejected(self):
        assert validate_audio_duration("/nonexistent/file.wav") is False

    def test_silent_audio_accepted(self):
        """Silent audio is still valid audio."""
        path = os.path.join(FIXTURES_DIR, "test_silent.wav")
        assert validate_audio_duration(path) is True


class TestVolumeNormalization:
    """Test volume normalization to -3dB peak."""

    def test_normalize_increases_quiet_audio(self):
        """Quiet audio (0.1 amplitude) should be boosted."""
        sr = 22050
        audio = 0.1 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, sr))
        normalized = normalize_volume(audio, sr, target_db=-3.0)
        assert np.max(np.abs(normalized)) > np.max(np.abs(audio))

    def test_normalize_reduces_loud_audio(self):
        """Full-scale audio should be reduced to -3dB."""
        sr = 22050
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, sr))
        normalized = normalize_volume(audio, sr, target_db=-3.0)
        assert np.max(np.abs(normalized)) < np.max(np.abs(audio))

    def test_normalize_peak_matches_target(self):
        """Peak should be close to -3dB (approx 0.7079)."""
        sr = 22050
        audio = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, sr))
        normalized = normalize_volume(audio, sr, target_db=-3.0)
        target_linear = 10 ** (-3.0 / 20.0)  # ~0.7079
        assert abs(np.max(np.abs(normalized)) - target_linear) < 0.01

    def test_normalize_preserves_shape(self):
        sr = 22050
        audio = 0.3 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, sr))
        normalized = normalize_volume(audio, sr, target_db=-3.0)
        assert normalized.shape == audio.shape

    def test_normalize_silent_audio_returns_silent(self):
        """All-zero audio should remain all-zero."""
        sr = 22050
        audio = np.zeros(sr)
        normalized = normalize_volume(audio, sr, target_db=-3.0)
        assert np.max(np.abs(normalized)) == 0.0
