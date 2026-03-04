"""FastAPI REST API routes for AccompanAIment."""

import uuid
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from src.api.auth import get_current_user

router = APIRouter()


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class StyleEnum(str, Enum):
    """Supported piano accompaniment styles."""

    jazz = "jazz"
    soulful = "soulful"
    rnb = "rnb"
    pop = "pop"
    classical = "classical"


class DownloadFormat(str, Enum):
    """Supported download file formats."""

    midi = "midi"
    audio = "audio"
    sheet = "sheet"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class GeneratePianoRequest(BaseModel):
    """Request body for piano accompaniment generation."""

    chords: str = Field(..., description="Chord progression, e.g. 'C | F | G | C'")
    style: StyleEnum = Field(..., description="Accompaniment style")
    tempo: int | None = Field(None, ge=40, le=300, description="BPM tempo (optional)")
    time_signature: str | None = Field(
        None, description="Time signature, e.g. '4/4' (optional)"
    )


class FeedbackRequest(BaseModel):
    """Request body for submitting feedback on a generation."""

    rating: int = Field(..., ge=1, le=5, description="Overall rating (1-5)")
    musicality_score: int | None = Field(
        None, ge=1, le=5, description="Musicality score (1-5)"
    )
    style_match_score: int | None = Field(
        None, ge=1, le=5, description="Style match score (1-5)"
    )
    fit_to_melody_score: int | None = Field(
        None, ge=1, le=5, description="Fit to melody score (1-5)"
    )
    comment: str | None = Field(None, max_length=2000, description="Optional comment")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class UploadResponse(BaseModel):
    """Response after uploading a song."""

    song_id: str
    status: str
    message: str


class MelodyResponse(BaseModel):
    """Response containing extracted melody data."""

    song_id: str
    melody: dict | None = None


class GeneratePianoResponse(BaseModel):
    """Response after triggering piano generation."""

    generation_id: str
    status: str
    message: str


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    feedback_id: str
    status: str


class GenerationItem(BaseModel):
    """A single generation entry in the history list."""

    generation_id: str
    song_id: str
    style: str
    created_at: str | None = None


class GenerationsHistoryResponse(BaseModel):
    """Response containing the user's generation history."""

    generations: list[GenerationItem]


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/songs/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_song(
    file: UploadFile,
    user_id: str = Depends(get_current_user),
) -> UploadResponse:
    """Upload a song file for processing.

    Accepts MP3, WAV, M4A, and FLAC files up to 100MB. Returns 202 Accepted
    with a song_id. Processing happens asynchronously via Celery workers.
    """
    song_id = str(uuid.uuid4())
    return UploadResponse(
        song_id=song_id,
        status="processing",
        message="Upload accepted. Processing will begin shortly.",
    )


@router.get(
    "/songs/{song_id}/melody",
    response_model=MelodyResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_melody(
    song_id: str,
    user_id: str = Depends(get_current_user),
) -> MelodyResponse:
    """Get the extracted melody data for a song.

    Returns the pitch contour, confidence, and timing data extracted
    by the CREPE melody extraction pipeline.
    """
    # Placeholder: in production, query DB for song belonging to user_id
    # For now, return 404 to indicate the song does not exist yet
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Song {song_id} not found",
    )


@router.post(
    "/songs/{song_id}/generate-piano",
    response_model=GeneratePianoResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={404: {"model": ErrorResponse}},
)
async def generate_piano(
    song_id: str,
    request: GeneratePianoRequest,
    user_id: str = Depends(get_current_user),
) -> GeneratePianoResponse:
    """Trigger piano accompaniment generation for a song.

    Accepts chord progression, style, and optional tempo/time_signature.
    Returns 202 Accepted with a generation_id. The actual generation
    runs asynchronously. Connect to the WebSocket endpoint
    /songs/{song_id}/status for real-time progress updates.
    """
    generation_id = str(uuid.uuid4())
    return GeneratePianoResponse(
        generation_id=generation_id,
        status="processing",
        message="Generation started. Connect to WebSocket for progress.",
    )


@router.get(
    "/songs/{song_id}/generations/{gen_id}/download",
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def download_generation(
    song_id: str,
    gen_id: str,
    format: DownloadFormat = Query(..., description="Download format: midi, audio, or sheet"),
    user_id: str = Depends(get_current_user),
) -> dict:
    """Download a generated accompaniment in the specified format.

    Supported formats: midi, audio (WAV), sheet (PDF).
    """
    # Placeholder: in production, look up the generation and return the file
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Generation {gen_id} not found for song {song_id}",
    )


@router.post(
    "/generations/{gen_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    gen_id: str,
    request: FeedbackRequest,
    user_id: str = Depends(get_current_user),
) -> FeedbackResponse:
    """Submit feedback for a generation.

    Accepts overall rating (1-5) and optional dimensional scores
    (musicality, style match, fit to melody) plus a text comment.
    """
    feedback_id = str(uuid.uuid4())
    return FeedbackResponse(
        feedback_id=feedback_id,
        status="submitted",
    )


@router.get(
    "/generations",
    response_model=GenerationsHistoryResponse,
)
async def get_generations_history(
    user_id: str = Depends(get_current_user),
) -> GenerationsHistoryResponse:
    """Get the current user's generation history.

    Returns a list of all generations created by the authenticated user,
    ordered by creation time (newest first).
    """
    # Placeholder: in production, query DB for user's generations
    return GenerationsHistoryResponse(generations=[])
