"""Tests for audio upload handling and preprocessing."""

import os
import tempfile

import numpy as np
import pytest
import soundfile as sf

from src.audio.audio_utils import validate_file_format, validate_file_size

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
