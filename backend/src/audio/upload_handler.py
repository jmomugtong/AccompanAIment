"""Audio upload handler -- validates, preprocesses, and stores uploads."""

import logging
import uuid
from typing import Any

import librosa
import numpy as np
import soundfile as sf

from src.audio.audio_utils import (
    TARGET_SAMPLE_RATE,
    normalize_volume,
    resample_audio,
    validate_audio_corruption,
    validate_file_format,
    validate_file_size,
)
from src.storage.filesystem_storage import FilesystemStorage

logger = logging.getLogger(__name__)


class UploadError(Exception):
    """Raised when an upload fails validation."""

    pass


class AudioUploader:
    """Handles audio file uploads: validation, preprocessing, storage."""

    def __init__(self, storage: FilesystemStorage) -> None:
        self._storage = storage

    def validate(
        self,
        filename: str,
        file_path: str,
        max_size_bytes: int = 100 * 1024 * 1024,
    ) -> None:
        """Validate an uploaded file before processing.

        Args:
            filename: Original filename from the user.
            file_path: Path to the temporary uploaded file.
            max_size_bytes: Maximum allowed file size.

        Raises:
            UploadError: If validation fails.
        """
        if not validate_file_format(filename):
            raise UploadError(
                "Unsupported format. Allowed: MP3, WAV, M4A, FLAC."
            )
        if not validate_audio_corruption(file_path):
            raise UploadError("File appears to be corrupt or unreadable.")
        if not validate_file_size(file_path, max_bytes=max_size_bytes):
            raise UploadError(
                f"File size exceeds the maximum allowed ({max_size_bytes // (1024 * 1024)}MB)."
            )

    def process(
        self,
        user_id: str,
        original_filename: str,
        file_path: str,
    ) -> dict[str, Any]:
        """Validate, preprocess, and store an uploaded audio file.

        Args:
            user_id: ID of the uploading user.
            original_filename: Original filename from the user.
            file_path: Path to the temporary uploaded file on disk.

        Returns:
            Dict with stored_path, storage_key, original_filename, metadata.

        Raises:
            UploadError: If validation fails.
        """
        self.validate(original_filename, file_path)

        # Load audio as mono
        audio, sr = librosa.load(file_path, sr=None, mono=True)

        # Normalize volume to -3dB
        audio = normalize_volume(audio, sr)

        # Resample to target rate
        audio = resample_audio(audio, orig_sr=sr, target_sr=TARGET_SAMPLE_RATE)

        # Generate storage key
        file_id = str(uuid.uuid4())
        storage_key = f"uploads/{user_id}/{file_id}.wav"

        # Write processed audio to a temporary buffer, then store
        import io
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            sf.write(tmp_path, audio, TARGET_SAMPLE_RATE)
            with open(tmp_path, "rb") as f:
                data = f.read()
            stored_path = self._storage.save(storage_key, data)
        finally:
            import os

            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        metadata = {
            "sample_rate": TARGET_SAMPLE_RATE,
            "channels": 1,
            "duration": len(audio) / TARGET_SAMPLE_RATE,
        }

        logger.info(
            "Processed upload: user=%s file=%s key=%s",
            user_id,
            original_filename,
            storage_key,
        )

        return {
            "stored_path": stored_path,
            "storage_key": storage_key,
            "original_filename": original_filename,
            "metadata": metadata,
        }

    def cleanup(self, storage_key: str) -> None:
        """Remove a stored file (e.g., after a failed downstream step).

        Args:
            storage_key: The key used when the file was saved.
        """
        self._storage.delete(storage_key)
