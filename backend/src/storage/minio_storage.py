"""MinIO S3-compatible storage backend.

Implements the same StorageBackend interface as FilesystemStorage,
but stores objects in a MinIO (or any S3-compatible) server.
"""

import logging
from io import BytesIO

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class MinIOStorage:
    """Store files in a MinIO S3-compatible object store.

    Implements the same interface as FilesystemStorage:
    save, load, delete, exists, get_full_path.

    Args:
        endpoint: MinIO server endpoint (e.g. "localhost:9000").
        access_key: MinIO access key.
        secret_key: MinIO secret key.
        bucket: Name of the S3 bucket to use.
        secure: Whether to use HTTPS (default False for local dev).
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ) -> None:
        self._bucket = bucket
        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

        # Ensure the bucket exists.
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)
            logger.info("Created MinIO bucket: %s", self._bucket)

    def save(self, key: str, data: bytes) -> str:
        """Save data to MinIO.

        Args:
            key: Object key (relative path within the bucket).
            data: Raw bytes to store.

        Returns:
            The object key.
        """
        data_stream = BytesIO(data)
        self._client.put_object(
            self._bucket,
            key,
            data_stream,
            length=len(data),
        )
        logger.info("Saved object: %s/%s", self._bucket, key)
        return key

    def load(self, key: str) -> bytes | None:
        """Load data from MinIO.

        Args:
            key: Object key (relative path within the bucket).

        Returns:
            Raw bytes, or None if the object does not exist.
        """
        try:
            response = self._client.get_object(self._bucket, key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except S3Error:
            return None

    def delete(self, key: str) -> None:
        """Delete an object from MinIO.

        Args:
            key: Object key (relative path within the bucket).
        """
        self._client.remove_object(self._bucket, key)
        logger.info("Deleted object: %s/%s", self._bucket, key)

    def exists(self, key: str) -> bool:
        """Check if an object exists in MinIO.

        Args:
            key: Object key (relative path within the bucket).

        Returns:
            True if the object exists.
        """
        try:
            self._client.stat_object(self._bucket, key)
            return True
        except S3Error:
            return False

    def get_full_path(self, key: str) -> str:
        """Get the full S3 URI for an object.

        Args:
            key: Object key (relative path within the bucket).

        Returns:
            An S3-style URI string, e.g. "s3://bucket/key".
        """
        return f"s3://{self._bucket}/{key}"
