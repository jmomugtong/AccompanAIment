"""Tests for storage backends: FilesystemStorage and MinIOStorage."""

import os
import tempfile
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from src.storage.filesystem_storage import FilesystemStorage
from src.storage.minio_storage import MinIOStorage


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


# ---------------------------------------------------------------------------
# Tests: MinIOStorage (all MinIO client calls are mocked)
# ---------------------------------------------------------------------------

class TestMinIOStorage:
    """Test MinIOStorage with a mocked MinIO client."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock MinIO client."""
        client = MagicMock()
        client.bucket_exists.return_value = True
        return client

    @pytest.fixture
    def storage(self, mock_client):
        """Create a MinIOStorage backed by the mock client."""
        with patch("src.storage.minio_storage.Minio", return_value=mock_client):
            s = MinIOStorage(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="test-bucket",
                secure=False,
            )
        return s

    def test_save_calls_put_object(self, storage, mock_client):
        """save() should call the MinIO put_object method."""
        data = b"test audio data"
        result = storage.save("uploads/song.wav", data)
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        assert call_args[0][0] == "test-bucket"  # bucket
        assert call_args[0][1] == "uploads/song.wav"  # object name
        assert isinstance(result, str)

    def test_save_returns_key(self, storage):
        """save() should return the object key."""
        result = storage.save("uploads/song.wav", b"data")
        assert result == "uploads/song.wav"

    def test_load_returns_data(self, storage, mock_client):
        """load() should retrieve object data from MinIO."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"loaded data"
        mock_response.close.return_value = None
        mock_response.release_conn.return_value = None
        mock_client.get_object.return_value = mock_response

        result = storage.load("uploads/song.wav")
        assert result == b"loaded data"
        mock_client.get_object.assert_called_once_with(
            "test-bucket", "uploads/song.wav"
        )

    def test_load_nonexistent_returns_none(self, storage, mock_client):
        """load() should return None when the object does not exist."""
        from minio.error import S3Error

        mock_response = MagicMock()
        mock_response.status = 404
        mock_client.get_object.side_effect = S3Error(
            mock_response,
            "NoSuchKey",
            "The specified key does not exist.",
            "uploads/missing.wav",
            "test-request-id",
            "test-host-id",
        )
        result = storage.load("uploads/missing.wav")
        assert result is None

    def test_delete_calls_remove_object(self, storage, mock_client):
        """delete() should call the MinIO remove_object method."""
        storage.delete("uploads/song.wav")
        mock_client.remove_object.assert_called_once_with(
            "test-bucket", "uploads/song.wav"
        )

    def test_exists_returns_true(self, storage, mock_client):
        """exists() should return True when the object is found."""
        mock_client.stat_object.return_value = MagicMock()
        assert storage.exists("uploads/song.wav") is True

    def test_exists_returns_false(self, storage, mock_client):
        """exists() should return False when the object is not found."""
        from minio.error import S3Error

        mock_response = MagicMock()
        mock_response.status = 404
        mock_client.stat_object.side_effect = S3Error(
            mock_response,
            "NoSuchKey",
            "The specified key does not exist.",
            "uploads/missing.wav",
            "test-request-id",
            "test-host-id",
        )
        assert storage.exists("uploads/missing.wav") is False

    def test_get_full_path_returns_s3_uri(self, storage):
        """get_full_path() should return an S3-style URI."""
        path = storage.get_full_path("uploads/song.wav")
        assert "test-bucket" in path
        assert "uploads/song.wav" in path

    def test_bucket_created_if_missing(self):
        """If the bucket does not exist, it should be created."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False

        with patch("src.storage.minio_storage.Minio", return_value=mock_client):
            MinIOStorage(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="new-bucket",
                secure=False,
            )

        mock_client.make_bucket.assert_called_once_with("new-bucket")

    def test_delete_nonexistent_does_not_raise(self, storage, mock_client):
        """Deleting a non-existent key should not raise."""
        # remove_object does not raise on missing objects in MinIO
        storage.delete("missing/key.wav")
