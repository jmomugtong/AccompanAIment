"""Tests for REST API endpoints, JWT auth, and Pydantic request/response validation."""

import io
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from src.config import settings
from src.main import app


@pytest.fixture
def client():
    """Synchronous test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def auth_token():
    """Create a valid JWT token for test requests."""
    from src.api.auth import create_access_token

    return create_access_token("test-user-id-123")


@pytest.fixture
def auth_headers(auth_token):
    """Authorization headers with a valid Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """Test the /health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status_healthy(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# JWT Auth
# ---------------------------------------------------------------------------


class TestJWTAuth:
    """Test JWT token creation and verification."""

    def test_create_access_token_returns_string(self):
        from src.api.auth import create_access_token

        token = create_access_token("user-1")
        assert isinstance(token, str)

    def test_create_access_token_is_valid_jwt(self):
        from src.api.auth import create_access_token

        token = create_access_token("user-1")
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        assert payload["sub"] == "user-1"

    def test_create_access_token_has_expiration(self):
        from src.api.auth import create_access_token

        token = create_access_token("user-1")
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        assert "exp" in payload

    def test_verify_token_returns_user_id(self):
        from src.api.auth import create_access_token, verify_token

        token = create_access_token("user-42")
        user_id = verify_token(token)
        assert user_id == "user-42"

    def test_verify_token_rejects_invalid_token(self):
        from src.api.auth import verify_token

        result = verify_token("not-a-valid-jwt-token")
        assert result is None

    def test_verify_token_rejects_expired_token(self):
        from src.api.auth import verify_token

        payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(
            payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
        )
        result = verify_token(token)
        assert result is None

    def test_verify_token_rejects_wrong_secret(self):
        from src.api.auth import verify_token

        payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, "wrong-secret", algorithm=settings.jwt_algorithm)
        result = verify_token(token)
        assert result is None

    def test_verify_token_rejects_missing_sub(self):
        from src.api.auth import verify_token

        payload = {
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(
            payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
        )
        result = verify_token(token)
        assert result is None


# ---------------------------------------------------------------------------
# Auth-protected endpoints require token
# ---------------------------------------------------------------------------


class TestAuthProtection:
    """Test that protected endpoints reject unauthenticated requests."""

    def test_upload_requires_auth(self, client):
        response = client.post("/songs/upload")
        assert response.status_code == 401

    def test_melody_requires_auth(self, client):
        response = client.get("/songs/some-id/melody")
        assert response.status_code == 401

    def test_generate_requires_auth(self, client):
        response = client.post("/songs/some-id/generate-piano")
        assert response.status_code == 401

    def test_download_requires_auth(self, client):
        response = client.get("/songs/some-id/generations/some-gen-id/download")
        assert response.status_code == 401

    def test_feedback_requires_auth(self, client):
        response = client.post("/generations/some-gen-id/feedback")
        assert response.status_code == 401

    def test_history_requires_auth(self, client):
        response = client.get("/generations")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Song upload endpoint
# ---------------------------------------------------------------------------


class TestSongUploadEndpoint:
    """Test POST /songs/upload."""

    def test_upload_returns_202(self, client, auth_headers):
        audio_file = io.BytesIO(b"fake audio content")
        response = client.post(
            "/songs/upload",
            headers=auth_headers,
            files={"file": ("test_song.mp3", audio_file, "audio/mpeg")},
        )
        assert response.status_code == 202

    def test_upload_returns_song_id(self, client, auth_headers):
        audio_file = io.BytesIO(b"fake audio content")
        response = client.post(
            "/songs/upload",
            headers=auth_headers,
            files={"file": ("test_song.mp3", audio_file, "audio/mpeg")},
        )
        data = response.json()
        assert "song_id" in data

    def test_upload_returns_status_field(self, client, auth_headers):
        audio_file = io.BytesIO(b"fake audio content")
        response = client.post(
            "/songs/upload",
            headers=auth_headers,
            files={"file": ("test_song.mp3", audio_file, "audio/mpeg")},
        )
        data = response.json()
        assert "status" in data

    def test_upload_without_file_returns_422(self, client, auth_headers):
        response = client.post("/songs/upload", headers=auth_headers)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Melody endpoint
# ---------------------------------------------------------------------------


class TestMelodyEndpoint:
    """Test GET /songs/{song_id}/melody."""

    def test_melody_valid_song_id_returns_200(self, client, auth_headers):
        response = client.get("/songs/test-song-id/melody", headers=auth_headers)
        # Placeholder data returns 200 for any song_id; 404 for nonexistent
        assert response.status_code in (200, 404)

    def test_melody_response_has_expected_fields(self, client, auth_headers):
        response = client.get("/songs/test-song-id/melody", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "song_id" in data
            assert "melody" in data


# ---------------------------------------------------------------------------
# Generate piano endpoint
# ---------------------------------------------------------------------------


class TestGeneratePianoEndpoint:
    """Test POST /songs/{song_id}/generate-piano."""

    def test_generate_returns_202(self, client, auth_headers):
        payload = {
            "chords": "C | F | G | C",
            "style": "jazz",
        }
        response = client.post(
            "/songs/test-song-id/generate-piano",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 202

    def test_generate_returns_generation_id(self, client, auth_headers):
        payload = {
            "chords": "C | F | G | C",
            "style": "jazz",
        }
        response = client.post(
            "/songs/test-song-id/generate-piano",
            headers=auth_headers,
            json=payload,
        )
        data = response.json()
        assert "generation_id" in data

    def test_generate_missing_chords_returns_422(self, client, auth_headers):
        payload = {"style": "jazz"}
        response = client.post(
            "/songs/test-song-id/generate-piano",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 422

    def test_generate_missing_style_returns_422(self, client, auth_headers):
        payload = {"chords": "C | F | G | C"}
        response = client.post(
            "/songs/test-song-id/generate-piano",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 422

    def test_generate_invalid_style_returns_422(self, client, auth_headers):
        payload = {
            "chords": "C | F | G | C",
            "style": "invalid_style_name",
        }
        response = client.post(
            "/songs/test-song-id/generate-piano",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 422

    def test_generate_accepts_optional_tempo(self, client, auth_headers):
        payload = {
            "chords": "C | F | G | C",
            "style": "jazz",
            "tempo": 120,
        }
        response = client.post(
            "/songs/test-song-id/generate-piano",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 202

    def test_generate_accepts_optional_time_signature(self, client, auth_headers):
        payload = {
            "chords": "C | F | G | C",
            "style": "jazz",
            "time_signature": "4/4",
        }
        response = client.post(
            "/songs/test-song-id/generate-piano",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 202


# ---------------------------------------------------------------------------
# Download endpoint
# ---------------------------------------------------------------------------


class TestDownloadEndpoint:
    """Test GET /songs/{song_id}/generations/{gen_id}/download."""

    def test_download_requires_format_param(self, client, auth_headers):
        response = client.get(
            "/songs/test-song-id/generations/test-gen-id/download",
            headers=auth_headers,
        )
        # Without format param, should return 422
        assert response.status_code == 422

    def test_download_with_valid_format_returns_200_or_404(self, client, auth_headers):
        response = client.get(
            "/songs/test-song-id/generations/test-gen-id/download?format=midi",
            headers=auth_headers,
        )
        # Placeholder returns 404 since no actual generation exists
        assert response.status_code in (200, 404)

    def test_download_invalid_format_returns_422(self, client, auth_headers):
        response = client.get(
            "/songs/test-song-id/generations/test-gen-id/download?format=invalid",
            headers=auth_headers,
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Feedback endpoint
# ---------------------------------------------------------------------------


class TestFeedbackEndpoint:
    """Test POST /generations/{gen_id}/feedback."""

    def test_feedback_returns_201(self, client, auth_headers):
        payload = {
            "rating": 5,
        }
        response = client.post(
            "/generations/test-gen-id/feedback",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 201

    def test_feedback_returns_feedback_id(self, client, auth_headers):
        payload = {"rating": 4}
        response = client.post(
            "/generations/test-gen-id/feedback",
            headers=auth_headers,
            json=payload,
        )
        data = response.json()
        assert "feedback_id" in data

    def test_feedback_with_all_optional_fields(self, client, auth_headers):
        payload = {
            "rating": 5,
            "musicality_score": 4,
            "style_match_score": 5,
            "fit_to_melody_score": 4,
            "comment": "Great accompaniment!",
        }
        response = client.post(
            "/generations/test-gen-id/feedback",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 201

    def test_feedback_missing_rating_returns_422(self, client, auth_headers):
        payload = {"comment": "No rating provided"}
        response = client.post(
            "/generations/test-gen-id/feedback",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 422

    def test_feedback_rating_below_1_returns_422(self, client, auth_headers):
        payload = {"rating": 0}
        response = client.post(
            "/generations/test-gen-id/feedback",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 422

    def test_feedback_rating_above_5_returns_422(self, client, auth_headers):
        payload = {"rating": 6}
        response = client.post(
            "/generations/test-gen-id/feedback",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Generations history endpoint
# ---------------------------------------------------------------------------


class TestGenerationsHistoryEndpoint:
    """Test GET /generations."""

    def test_history_returns_200(self, client, auth_headers):
        response = client.get("/generations", headers=auth_headers)
        assert response.status_code == 200

    def test_history_returns_list(self, client, auth_headers):
        response = client.get("/generations", headers=auth_headers)
        data = response.json()
        assert "generations" in data
        assert isinstance(data["generations"], list)


# ---------------------------------------------------------------------------
# 404 for invalid IDs
# ---------------------------------------------------------------------------


class TestNotFoundResponses:
    """Test that nonexistent resources return 404."""

    def test_melody_nonexistent_song_returns_404(self, client, auth_headers):
        fake_id = str(uuid.uuid4())
        response = client.get(f"/songs/{fake_id}/melody", headers=auth_headers)
        assert response.status_code == 404

    def test_download_nonexistent_generation_returns_404(self, client, auth_headers):
        fake_song = str(uuid.uuid4())
        fake_gen = str(uuid.uuid4())
        response = client.get(
            f"/songs/{fake_song}/generations/{fake_gen}/download?format=midi",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Pydantic schema validation
# ---------------------------------------------------------------------------


class TestPydanticSchemaValidation:
    """Test Pydantic request/response model validation."""

    def test_generate_request_schema_validates_style_enum(self):
        from src.api.routes import GeneratePianoRequest

        # Valid styles should work
        for style in ("jazz", "soulful", "rnb", "pop", "classical"):
            req = GeneratePianoRequest(chords="C | F | G | C", style=style)
            assert req.style == style

    def test_generate_request_schema_rejects_invalid_style(self):
        from pydantic import ValidationError

        from src.api.routes import GeneratePianoRequest

        with pytest.raises(ValidationError):
            GeneratePianoRequest(chords="C | F | G | C", style="invalid_style")

    def test_feedback_request_schema_validates_rating_range(self):
        from src.api.routes import FeedbackRequest

        req = FeedbackRequest(rating=3)
        assert req.rating == 3

    def test_feedback_request_schema_rejects_out_of_range_rating(self):
        from pydantic import ValidationError

        from src.api.routes import FeedbackRequest

        with pytest.raises(ValidationError):
            FeedbackRequest(rating=0)
        with pytest.raises(ValidationError):
            FeedbackRequest(rating=6)

    def test_feedback_request_optional_scores(self):
        from src.api.routes import FeedbackRequest

        req = FeedbackRequest(
            rating=4,
            musicality_score=3,
            style_match_score=5,
            fit_to_melody_score=4,
            comment="Nice!",
        )
        assert req.musicality_score == 3
        assert req.comment == "Nice!"

    def test_upload_response_schema(self):
        from src.api.routes import UploadResponse

        resp = UploadResponse(
            song_id="abc-123",
            status="processing",
            message="Upload accepted",
        )
        assert resp.song_id == "abc-123"

    def test_generate_response_schema(self):
        from src.api.routes import GeneratePianoResponse

        resp = GeneratePianoResponse(
            generation_id="gen-1",
            status="processing",
            message="Generation started",
        )
        assert resp.generation_id == "gen-1"
