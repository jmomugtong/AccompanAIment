"""Tests for filesystem storage abstraction."""

import os
import tempfile

import pytest

from src.storage.filesystem_storage import FilesystemStorage


class TestFilesystemStorage:
    """Test FilesystemStorage for saving, loading, and deleting files."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create a FilesystemStorage rooted at a temp directory."""
        return FilesystemStorage(base_path=str(tmp_path))

    def test_save_creates_file(self, storage):
        data = b"test audio data"
        path = storage.save("uploads/user1/song.wav", data)
        assert os.path.exists(path)

    def test_save_creates_subdirectories(self, storage):
        data = b"nested data"
        path = storage.save("deep/nested/dir/file.wav", data)
        assert os.path.exists(path)

    def test_load_returns_saved_data(self, storage):
        data = b"audio bytes here"
        storage.save("test/file.wav", data)
        loaded = storage.load("test/file.wav")
        assert loaded == data

    def test_delete_removes_file(self, storage):
        data = b"to be deleted"
        path = storage.save("test/delete_me.wav", data)
        assert os.path.exists(path)
        storage.delete("test/delete_me.wav")
        assert not os.path.exists(path)

    def test_exists_returns_true_for_saved_file(self, storage):
        storage.save("test/exists.wav", b"data")
        assert storage.exists("test/exists.wav") is True

    def test_exists_returns_false_for_missing_file(self, storage):
        assert storage.exists("test/nope.wav") is False

    def test_delete_nonexistent_file_does_not_raise(self, storage):
        storage.delete("test/nonexistent.wav")

    def test_get_full_path(self, storage):
        full = storage.get_full_path("uploads/song.wav")
        assert "uploads" in full
        assert "song.wav" in full

    def test_load_nonexistent_returns_none(self, storage):
        result = storage.load("missing/file.wav")
        assert result is None
