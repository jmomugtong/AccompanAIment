"""Celery task for piano accompaniment generation.

Generates MIDI piano accompaniment from chord progressions using
voicing templates and the MIDI generator pipeline.
"""

import logging
import os
import tempfile

from src.celery_app import celery_app
from src.music.midi_generator import MIDIGenerator
from src.music.voicing_generator import VoicingGenerator

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=False,
    name="workers.generate_piano",
    soft_time_limit=240,
    time_limit=300,
)
def generate_piano(
    song_id: str,
    chords: str,
    style: str,
    tempo: int,
    time_signature: str,
) -> dict:
    """Generate piano accompaniment MIDI from chords and style.

    Args:
        song_id: Unique identifier for the song.
        chords: Chord progression string (pipe-separated, e.g. "C | F | G | C").
        style: Voicing style name (pop, jazz, classical, soulful, rnb).
        tempo: Beats per minute.
        time_signature: Time signature string (e.g. "4/4", "3/4").

    Returns:
        Dict with keys: song_id, midi_path, style, tempo, chords.

    Raises:
        ValueError: If chord parsing or voicing generation fails.
        RuntimeError: If MIDI creation fails.
    """
    generate_piano.update_state(
        state="PROGRESS",
        meta={"stage": "parsing_chords", "progress": 0, "song_id": song_id},
    )

    logger.info(
        "Starting piano generation for song %s: style=%s, tempo=%d, chords=%s",
        song_id,
        style,
        tempo,
        chords,
    )

    # Parse chord symbols from the progression string
    chord_symbols = [c.strip() for c in chords.split("|") if c.strip()]

    # Parse time signature
    ts_parts = time_signature.split("/")
    ts_tuple = (int(ts_parts[0]), int(ts_parts[1]))

    generate_piano.update_state(
        state="PROGRESS",
        meta={"stage": "generating_voicings", "progress": 25, "song_id": song_id},
    )

    # Generate voicings for each chord
    voicing_gen = VoicingGenerator()
    voicings = []
    for chord_name in chord_symbols:
        voicing = voicing_gen.generate_voicing(chord_name, style=style)
        voicings.append(voicing)

    # Each chord gets a duration of one measure (in quarter notes)
    beats_per_measure = ts_tuple[0]
    durations = [float(beats_per_measure)] * len(voicings)

    generate_piano.update_state(
        state="PROGRESS",
        meta={"stage": "creating_midi", "progress": 50, "song_id": song_id},
    )

    # Create MIDI
    midi_gen = MIDIGenerator(tempo=tempo, time_signature=ts_tuple)
    midi_gen.create_score()
    midi_gen.add_accompaniment_track(voicings, durations)

    # Write MIDI to a temporary path
    output_dir = tempfile.mkdtemp(prefix="accompaniment_")
    midi_path = os.path.join(output_dir, f"{song_id}_piano.mid")
    midi_path = midi_gen.write_midi(midi_path)

    generate_piano.update_state(
        state="PROGRESS",
        meta={"stage": "generation_complete", "progress": 100, "song_id": song_id},
    )

    logger.info(
        "Piano generation complete for song %s: %s (%d chords)",
        song_id,
        midi_path,
        len(chord_symbols),
    )

    return {
        "song_id": song_id,
        "midi_path": midi_path,
        "style": style,
        "tempo": tempo,
        "chords": chord_symbols,
    }
