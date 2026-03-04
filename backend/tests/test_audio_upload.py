"""Tests for audio upload handling and preprocessing."""

import os
import tempfile

import numpy as np
import pytest
import soundfile as sf

from src.audio.audio_utils import validate_file_format

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
