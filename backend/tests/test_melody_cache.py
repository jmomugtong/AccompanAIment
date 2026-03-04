"""Tests for melody caching."""

import json
import os
import time

import pytest

from src.audio.melody_cache import MelodyCache


@pytest.fixture
def cache(tmp_path):
    return MelodyCache(cache_dir=str(tmp_path), ttl_seconds=5)


class TestMelodyCacheBasic:
    """Test basic cache operations."""

    def test_cache_miss_returns_none(self, cache):
        assert cache.get("nonexistent_song") is None

    def test_cache_set_and_get(self, cache):
        melody_data = {
            "notes": [60, 62, 64],
            "timings": [0.0, 0.5, 1.0],
            "confidence": [0.9, 0.8, 0.7],
            "duration_seconds": 1.5,
        }
        cache.set("song_123", melody_data)
        result = cache.get("song_123")
        assert result is not None
        assert result["notes"] == [60, 62, 64]

    def test_cache_overwrites_existing(self, cache):
        cache.set("song_1", {"notes": [60]})
        cache.set("song_1", {"notes": [72]})
        result = cache.get("song_1")
        assert result["notes"] == [72]

    def test_cache_different_keys_independent(self, cache):
        cache.set("song_a", {"notes": [60]})
        cache.set("song_b", {"notes": [72]})
        assert cache.get("song_a")["notes"] == [60]
        assert cache.get("song_b")["notes"] == [72]

    def test_cache_delete(self, cache):
        cache.set("song_del", {"notes": [60]})
        assert cache.get("song_del") is not None
        cache.delete("song_del")
        assert cache.get("song_del") is None

    def test_cache_delete_nonexistent_no_error(self, cache):
        cache.delete("nonexistent")

    def test_cache_exists(self, cache):
        cache.set("song_ex", {"notes": [60]})
        assert cache.exists("song_ex") is True
        assert cache.exists("nope") is False


class TestMelodyCacheTTL:
    """Test time-to-live expiration."""

    def test_expired_entry_returns_none(self, tmp_path):
        cache = MelodyCache(cache_dir=str(tmp_path), ttl_seconds=1)
        cache.set("song_ttl", {"notes": [60]})
        time.sleep(1.5)
        assert cache.get("song_ttl") is None

    def test_fresh_entry_not_expired(self, cache):
        cache.set("song_fresh", {"notes": [60]})
        assert cache.get("song_fresh") is not None
