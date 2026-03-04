"""Celery tasks for output format rendering.

Handles conversion of MIDI files to audio (WAV via FluidSynth) and
sheet music (PDF via Lilypond).
"""

import logging

from src.celery_app import celery_app
from src.config import settings
from src.generation.audio_renderer import AudioRenderer
from src.generation.sheet_generator import SheetGenerator

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=False,
    name="workers.render_audio",
    soft_time_limit=300,
    time_limit=600,
)
def render_audio(midi_path: str, output_path: str) -> str:
    """Render a MIDI file to WAV audio using FluidSynth.

    Args:
        midi_path: Path to the input MIDI file.
        output_path: Desired path for the output WAV file.

    Returns:
        The output file path on success.

    Raises:
        AudioRenderError: If rendering fails.
    """
    render_audio.update_state(
        state="PROGRESS",
        meta={"stage": "rendering_audio", "progress": 0, "midi_path": midi_path},
    )

    logger.info("Starting audio rendering: %s -> %s", midi_path, output_path)

    renderer = AudioRenderer(soundfont_path=settings.soundfont_path)
    result_path = renderer.render_midi(midi_path, output_path)

    render_audio.update_state(
        state="PROGRESS",
        meta={"stage": "rendering_complete", "progress": 100, "midi_path": midi_path},
    )

    logger.info("Audio rendering complete: %s", result_path)
    return result_path


@celery_app.task(
    bind=False,
    name="workers.generate_sheet",
    soft_time_limit=120,
    time_limit=180,
)
def generate_sheet(midi_path: str, output_path: str) -> str:
    """Generate sheet music (PDF) from a MIDI file using Lilypond.

    Args:
        midi_path: Path to the input MIDI file.
        output_path: Desired path for the output PDF file.

    Returns:
        The output file path on success.

    Raises:
        SheetGenerationError: If generation fails.
    """
    generate_sheet.update_state(
        state="PROGRESS",
        meta={"stage": "generating_sheet", "progress": 0, "midi_path": midi_path},
    )

    logger.info("Starting sheet music generation: %s -> %s", midi_path, output_path)

    generator = SheetGenerator()
    result_path = generator.generate_sheet(midi_path, output_path)

    generate_sheet.update_state(
        state="PROGRESS",
        meta={"stage": "sheet_complete", "progress": 100, "midi_path": midi_path},
    )

    logger.info("Sheet music generation complete: %s", result_path)
    return result_path
