"""Audio validation helpers and processing utilities."""

import logging
import os
from pathlib import Path
from typing import Any

import librosa
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

ALLOWED_FORMATS = {".mp3", ".wav", ".m4a", ".flac"}
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_DURATION_SECONDS = 600  # 10 minutes
TARGET_SAMPLE_RATE = 22050
TARGET_PEAK_DB = -3.0


def validate_file_format(filename: str) -> bool:
    """Check if the file has an allowed audio extension.

    Args:
        filename: Original filename to check.

    Returns:
        True if the format is supported, False otherwise.
    """
    if not filename:
        return False
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_FORMATS


def validate_file_size(file_path: str, max_bytes: int = MAX_FILE_SIZE_BYTES) -> bool:
    """Check if the file is within the allowed size limit.

    Args:
        file_path: Path to the file on disk.
        max_bytes: Maximum allowed size in bytes.

    Returns:
        True if within limit, False otherwise.
    """
    try:
        return os.path.getsize(file_path) <= max_bytes
    except OSError:
        return False


def validate_audio_duration(
    file_path: str, max_seconds: float = MAX_DURATION_SECONDS
) -> bool:
    """Check if audio duration is within the allowed limit.

    Args:
        file_path: Path to the audio file.
        max_seconds: Maximum allowed duration in seconds.

    Returns:
        True if within limit, False otherwise.
    """
    try:
        duration = librosa.get_duration(path=file_path)
        return duration <= max_seconds
    except Exception:
        return False


def normalize_volume(
    audio: np.ndarray, sr: int, target_db: float = TARGET_PEAK_DB
) -> np.ndarray:
    """Normalize audio peak amplitude to target dB level.

    Args:
        audio: Audio samples as numpy array.
        sr: Sample rate.
        target_db: Target peak level in dB.

    Returns:
        Normalized audio samples.
    """
    peak = np.max(np.abs(audio))
    if peak == 0:
        return audio
    target_linear = 10 ** (target_db / 20.0)
    return audio * (target_linear / peak)


def resample_audio(
    audio: np.ndarray, orig_sr: int, target_sr: int = TARGET_SAMPLE_RATE
) -> np.ndarray:
    """Resample audio to the target sample rate.

    Args:
        audio: Audio samples.
        orig_sr: Original sample rate.
        target_sr: Target sample rate.

    Returns:
        Resampled audio samples.
    """
    raise NotImplementedError


def validate_audio_corruption(file_path: str) -> bool:
    """Check if the audio file is readable and not corrupted.

    Args:
        file_path: Path to the audio file.

    Returns:
        True if the file is valid, False if corrupted.
    """
    raise NotImplementedError


def get_audio_metadata(file_path: str) -> dict[str, Any]:
    """Extract metadata from an audio file.

    Args:
        file_path: Path to the audio file.

    Returns:
        Dict with keys: sample_rate, channels, duration, format.
    """
    raise NotImplementedError
