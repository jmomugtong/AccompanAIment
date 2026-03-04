"""Filesystem-based melody cache with TTL support."""

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


class MelodyCache:
    """Cache extracted melody data to avoid repeated CREPE inference."""

    def __init__(self, cache_dir: str, ttl_seconds: int = 604800) -> None:
        self._cache_dir = cache_dir
        self._ttl = ttl_seconds
        os.makedirs(cache_dir, exist_ok=True)

    def _key_path(self, song_id: str) -> str:
        return os.path.join(self._cache_dir, f"{song_id}.json")

    def get(self, song_id: str) -> dict[str, Any] | None:
        """Retrieve cached melody data.

        Args:
            song_id: Unique song identifier.

        Returns:
            Melody data dict, or None on cache miss or expiration.
        """
        path = self._key_path(song_id)
        if not os.path.exists(path):
            return None

        mtime = os.path.getmtime(path)
        if time.time() - mtime > self._ttl:
            logger.info("Cache expired for %s", song_id)
            os.remove(path)
            return None

        with open(path, "r") as f:
            return json.load(f)

    def set(self, song_id: str, melody_data: dict[str, Any]) -> None:
        """Store melody data in cache.

        Args:
            song_id: Unique song identifier.
            melody_data: Dict with notes, timings, confidence, duration.
        """
        path = self._key_path(song_id)
        with open(path, "w") as f:
            json.dump(melody_data, f)
        logger.info("Cached melody for %s", song_id)

    def delete(self, song_id: str) -> None:
        """Remove a cached melody entry.

        Args:
            song_id: Unique song identifier.
        """
        path = self._key_path(song_id)
        if os.path.exists(path):
            os.remove(path)

    def exists(self, song_id: str) -> bool:
        """Check if a cache entry exists (ignoring TTL).

        Args:
            song_id: Unique song identifier.

        Returns:
            True if cached.
        """
        return os.path.exists(self._key_path(song_id))
