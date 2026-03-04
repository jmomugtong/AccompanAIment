"""Filesystem-based storage backend."""

import logging
import os
from typing import Protocol

logger = logging.getLogger(__name__)


class StorageBackend(Protocol):
    """Protocol defining the storage interface."""

    def save(self, key: str, data: bytes) -> str: ...

    def load(self, key: str) -> bytes | None: ...

    def delete(self, key: str) -> None: ...

    def exists(self, key: str) -> bool: ...

    def get_full_path(self, key: str) -> str: ...


class FilesystemStorage:
    """Store files on the local filesystem."""

    def __init__(self, base_path: str) -> None:
        self._base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def save(self, key: str, data: bytes) -> str:
        """Save data to the filesystem.

        Args:
            key: Relative path within the storage root.
            data: Raw bytes to write.

        Returns:
            Absolute path to the saved file.
        """
        full_path = self.get_full_path(key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        logger.info("Saved file: %s", full_path)
        return full_path

    def load(self, key: str) -> bytes | None:
        """Load data from the filesystem.

        Args:
            key: Relative path within the storage root.

        Returns:
            Raw bytes, or None if file does not exist.
        """
        full_path = self.get_full_path(key)
        if not os.path.exists(full_path):
            return None
        with open(full_path, "rb") as f:
            return f.read()

    def delete(self, key: str) -> None:
        """Delete a file from the filesystem.

        Args:
            key: Relative path within the storage root.
        """
        full_path = self.get_full_path(key)
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info("Deleted file: %s", full_path)

    def exists(self, key: str) -> bool:
        """Check if a file exists.

        Args:
            key: Relative path within the storage root.

        Returns:
            True if the file exists.
        """
        return os.path.exists(self.get_full_path(key))

    def get_full_path(self, key: str) -> str:
        """Get the absolute filesystem path for a key.

        Args:
            key: Relative path within the storage root.

        Returns:
            Absolute path.
        """
        return os.path.join(self._base_path, key)
