"""Tests for audio upload handling and preprocessing."""

import os
import tempfile

import numpy as np
import pytest
import soundfile as sf

from src.audio.audio_utils import (
    get_audio_metadata,
    normalize_volume,
    resample_audio,
    validate_audio_corruption,
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


class TestResamplingAndMonoConversion:
    """Test resampling to 22.05kHz and stereo-to-mono conversion."""

    def test_resample_from_44100_to_22050(self):
        sr = 44100
        duration = 1.0
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sr * duration)))
        resampled = resample_audio(audio, orig_sr=sr, target_sr=22050)
        expected_length = int(22050 * duration)
        assert abs(len(resampled) - expected_length) <= 1

    def test_resample_from_48000_to_22050(self):
        sr = 48000
        duration = 1.0
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sr * duration)))
        resampled = resample_audio(audio, orig_sr=sr, target_sr=22050)
        expected_length = int(22050 * duration)
        assert abs(len(resampled) - expected_length) <= 1

    def test_resample_same_rate_returns_same_length(self):
        sr = 22050
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, sr))
        resampled = resample_audio(audio, orig_sr=sr, target_sr=sr)
        assert len(resampled) == len(audio)

    def test_stereo_to_mono_via_librosa(self):
        """Loading a stereo file with librosa mono=True should return 1D."""
        path = os.path.join(FIXTURES_DIR, "test_stereo.wav")
        import librosa

        audio, sr = librosa.load(path, sr=None, mono=True)
        assert audio.ndim == 1

    def test_mono_file_stays_mono(self):
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        import librosa

        audio, sr = librosa.load(path, sr=None, mono=True)
        assert audio.ndim == 1

    def test_resample_preserves_1d(self):
        sr = 44100
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, sr))
        resampled = resample_audio(audio, orig_sr=sr, target_sr=22050)
        assert resampled.ndim == 1


class TestAudioCorruptionDetection:
    """Test detection of corrupted audio files."""

    def test_valid_wav_passes(self):
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        assert validate_audio_corruption(path) is True

    def test_valid_stereo_passes(self):
        path = os.path.join(FIXTURES_DIR, "test_stereo.wav")
        assert validate_audio_corruption(path) is True

    def test_nonexistent_file_fails(self):
        assert validate_audio_corruption("/nonexistent/file.wav") is False

    def test_corrupted_file_fails(self):
        """A file with random bytes should fail."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"this is not audio data at all")
            f.flush()
            path = f.name
        try:
            assert validate_audio_corruption(path) is False
        finally:
            os.unlink(path)

    def test_empty_file_fails(self):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        try:
            assert validate_audio_corruption(path) is False
        finally:
            os.unlink(path)


class TestMetadataExtraction:
    """Test audio metadata extraction."""

    def test_mono_wav_metadata(self):
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        meta = get_audio_metadata(path)
        assert meta["sample_rate"] == 44100
        assert meta["channels"] == 1
        assert abs(meta["duration"] - 2.0) < 0.1

    def test_stereo_wav_metadata(self):
        path = os.path.join(FIXTURES_DIR, "test_stereo.wav")
        meta = get_audio_metadata(path)
        assert meta["sample_rate"] == 44100
        assert meta["channels"] == 2
        assert abs(meta["duration"] - 2.0) < 0.1

    def test_high_sr_wav_metadata(self):
        path = os.path.join(FIXTURES_DIR, "test_high_sr.wav")
        meta = get_audio_metadata(path)
        assert meta["sample_rate"] == 48000

    def test_metadata_includes_format(self):
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        meta = get_audio_metadata(path)
        assert "format" in meta

    def test_nonexistent_file_returns_none(self):
        meta = get_audio_metadata("/nonexistent/file.wav")
        assert meta is None
