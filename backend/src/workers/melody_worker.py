"""Celery task for melody extraction using CREPE.

Extracts vocal melody pitch contours from uploaded audio files
and returns structured melody data for downstream pipeline stages.
"""

import logging

from src.audio.crepe_extractor import CREPEExtractor
from src.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=False,
    name="workers.extract_melody",
    soft_time_limit=240,
    time_limit=300,
)
def extract_melody(song_id: str, file_path: str) -> dict:
    """Extract melody from an audio file using CREPE pitch tracking.

    Args:
        song_id: Unique identifier for the song being processed.
        file_path: Absolute path to the audio file (WAV, resampled).

    Returns:
        Dict with keys: song_id, notes, timings, confidence,
        duration_seconds.

    Raises:
        RuntimeError: If CREPE extraction fails.
    """
    extract_melody.update_state(
        state="PROGRESS",
        meta={"stage": "extracting_melody", "progress": 0, "song_id": song_id},
    )

    logger.info("Starting melody extraction for song %s from %s", song_id, file_path)

    extractor = CREPEExtractor()
    melody_data = extractor.extract(file_path)

    extract_melody.update_state(
        state="PROGRESS",
        meta={"stage": "extraction_complete", "progress": 100, "song_id": song_id},
    )

    logger.info(
        "Melody extraction complete for song %s: %d notes, %.1fs duration",
        song_id,
        len(melody_data["notes"]),
        melody_data["duration_seconds"],
    )

    return {
        "song_id": song_id,
        "notes": melody_data["notes"],
        "timings": melody_data["timings"],
        "confidence": melody_data["confidence"],
        "duration_seconds": melody_data["duration_seconds"],
    }
