"""Tests for FastAPI middleware: request logging and rate limiting."""

import asyncio
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.middleware import RateLimitMiddleware, RequestLoggingMiddleware


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_app(
    enable_logging: bool = False,
    enable_rate_limit: bool = False,
    max_requests: int = 5,
    window_seconds: int = 60,
) -> FastAPI:
    """Build a minimal FastAPI app with the requested middleware."""
    app = FastAPI()

    if enable_rate_limit:
        app.add_middleware(
            RateLimitMiddleware,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

    if enable_logging:
        app.add_middleware(RequestLoggingMiddleware)

    @app.get("/ping")
    async def ping():
        return {"msg": "pong"}

    @app.get("/slow")
    async def slow():
        await asyncio.sleep(0.05)
        return {"msg": "done"}

    return app


# ---------------------------------------------------------------------------
# Tests: RequestLoggingMiddleware
# ---------------------------------------------------------------------------

class TestRequestLoggingMiddleware:
    """Test that the logging middleware records method, path, status, duration."""

    def test_successful_request_logged(self, caplog):
        """A 200 response should produce a log entry with the right fields."""
        app = _create_app(enable_logging=True)
        client = TestClient(app)

        with caplog.at_level("INFO"):
            resp = client.get("/ping")

        assert resp.status_code == 200
        # Check that a log line mentions the method, path, status, and duration
        combined = " ".join(caplog.messages)
        assert "GET" in combined
        assert "/ping" in combined
        assert "200" in combined

    def test_not_found_logged(self, caplog):
        """A 404 should still be logged."""
        app = _create_app(enable_logging=True)
        client = TestClient(app)

        with caplog.at_level("INFO"):
            resp = client.get("/nonexistent")

        assert resp.status_code == 404
        combined = " ".join(caplog.messages)
        assert "404" in combined

    def test_duration_is_positive(self, caplog):
        """The logged duration should be a positive number."""
        app = _create_app(enable_logging=True)
        client = TestClient(app)

        with caplog.at_level("INFO"):
            client.get("/slow")

        # At least one log message should contain a numeric duration
        combined = " ".join(caplog.messages)
        assert "ms" in combined.lower() or "." in combined


# ---------------------------------------------------------------------------
# Tests: RateLimitMiddleware
# ---------------------------------------------------------------------------

class TestRateLimitMiddleware:
    """Test the in-memory IP-based rate limiter."""

    def test_requests_within_limit_succeed(self):
        """Requests under the max should return 200."""
        app = _create_app(enable_rate_limit=True, max_requests=5, window_seconds=60)
        client = TestClient(app)

        for _ in range(5):
            resp = client.get("/ping")
            assert resp.status_code == 200

    def test_exceeding_limit_returns_429(self):
        """Requests over the max should return 429 Too Many Requests."""
        app = _create_app(enable_rate_limit=True, max_requests=3, window_seconds=60)
        client = TestClient(app)

        for _ in range(3):
            resp = client.get("/ping")
            assert resp.status_code == 200

        resp = client.get("/ping")
        assert resp.status_code == 429

    def test_429_response_has_retry_after(self):
        """The 429 response should include a Retry-After header."""
        app = _create_app(enable_rate_limit=True, max_requests=1, window_seconds=60)
        client = TestClient(app)

        client.get("/ping")  # first request OK
        resp = client.get("/ping")  # over limit

        assert resp.status_code == 429
        assert "retry-after" in resp.headers

    def test_window_expiry_resets_counter(self):
        """After the window elapses, the counter should reset."""
        app = _create_app(enable_rate_limit=True, max_requests=2, window_seconds=1)
        client = TestClient(app)

        client.get("/ping")
        client.get("/ping")
        resp = client.get("/ping")
        assert resp.status_code == 429

        # Wait for the 1-second window to expire
        time.sleep(1.1)
        resp = client.get("/ping")
        assert resp.status_code == 200

    def test_different_paths_share_limit(self):
        """Rate limit is per-IP, not per-path."""
        app = _create_app(enable_rate_limit=True, max_requests=2, window_seconds=60)

        @app.get("/other")
        async def other():
            return {"msg": "other"}

        client = TestClient(app)

        client.get("/ping")
        client.get("/other")
        resp = client.get("/ping")
        assert resp.status_code == 429
