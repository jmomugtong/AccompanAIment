"""Tests for AudioUploader end-to-end pipeline."""

import os
import tempfile

import numpy as np
import pytest
import soundfile as sf

from src.audio.upload_handler import AudioUploader, UploadError
from src.storage.filesystem_storage import FilesystemStorage

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def storage(tmp_path):
    return FilesystemStorage(base_path=str(tmp_path))


@pytest.fixture
def uploader(storage):
    return AudioUploader(storage=storage)


class TestAudioUploaderValidation:
    """Test upload validation before processing."""

    def test_rejects_unsupported_format(self, uploader):
        with pytest.raises(UploadError, match="format"):
            uploader.validate("song.ogg", os.path.join(FIXTURES_DIR, "test_mono.wav"))

    def test_rejects_nonexistent_file(self, uploader):
        with pytest.raises(UploadError, match="corrupt"):
            uploader.validate("song.wav", "/nonexistent/file.wav")

    def test_rejects_oversized_file(self, uploader):
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        with pytest.raises(UploadError, match="size"):
            uploader.validate("song.wav", path, max_size_bytes=10)

    def test_accepts_valid_file(self, uploader):
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        uploader.validate("song.wav", path)


class TestAudioUploaderProcessing:
    """Test the full upload processing pipeline."""

    def test_process_returns_result_dict(self, uploader):
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        result = uploader.process("user1", "my_song.wav", path)
        assert "stored_path" in result
        assert "metadata" in result
        assert result["original_filename"] == "my_song.wav"

    def test_process_stores_file(self, uploader, storage):
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        result = uploader.process("user1", "song.wav", path)
        assert storage.exists(result["storage_key"])

    def test_process_normalizes_and_resamples(self, uploader, storage):
        path = os.path.join(FIXTURES_DIR, "test_stereo.wav")
        result = uploader.process("user1", "stereo.wav", path)
        # Result should be mono, 22050 Hz
        assert result["metadata"]["sample_rate"] == 22050
        assert result["metadata"]["channels"] == 1

    def test_process_preserves_user_isolation(self, uploader):
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        r1 = uploader.process("userA", "song1.wav", path)
        r2 = uploader.process("userB", "song2.wav", path)
        assert "userA" in r1["storage_key"]
        assert "userB" in r2["storage_key"]


class TestAudioUploaderCleanup:
    """Test cleanup on failed uploads."""

    def test_cleanup_removes_stored_file(self, uploader, storage):
        path = os.path.join(FIXTURES_DIR, "test_mono.wav")
        result = uploader.process("user1", "song.wav", path)
        key = result["storage_key"]
        assert storage.exists(key)
        uploader.cleanup(key)
        assert not storage.exists(key)

    def test_cleanup_nonexistent_does_not_raise(self, uploader):
        uploader.cleanup("nonexistent/key.wav")
