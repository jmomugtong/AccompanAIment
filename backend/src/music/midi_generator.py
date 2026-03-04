"""MIDI generation with melody and accompaniment tracks.

Creates multi-track MIDI files using music21, with support for tempo,
time signatures, melody tracks (single notes), and accompaniment tracks
(chord voicings). Outputs standard MIDI files (.mid).
"""

from __future__ import annotations

from music21 import chord as m21chord
from music21 import instrument, meter, note, stream, tempo


class MIDIGenerator:
    """Generates MIDI files with melody and accompaniment tracks.

    Uses music21 to build a Score containing separate Part objects
    for melody and accompaniment, then writes to a standard MIDI file.

    Attributes:
        tempo: Beats per minute.
        time_signature: Tuple of (numerator, denominator).
        score: The music21 Score object (created via create_score).
        melody_part: The melody Part (added via add_melody_track).
        accompaniment_part: The accompaniment Part (added via add_accompaniment_track).
    """

    def __init__(
        self,
        tempo: int = 120,
        time_signature: tuple[int, int] = (4, 4),
    ) -> None:
        """Initialize MIDIGenerator with tempo and time signature.

        Args:
            tempo: Beats per minute (default 120).
            time_signature: Time signature as (numerator, denominator) tuple.
        """
        self.tempo = tempo
        self.time_signature = time_signature
        self.score: stream.Score | None = None
        self.melody_part: stream.Part | None = None
        self.accompaniment_part: stream.Part | None = None

    def create_score(self) -> stream.Score:
        """Create a new music21 Score with tempo and time signature.

        Returns:
            A music21 Score object configured with the specified
            tempo and time signature.
        """
        self.score = stream.Score()

        # Add tempo marking.
        mm = tempo.MetronomeMark(number=self.tempo)
        self.score.insert(0, mm)

        # Add time signature.
        ts = meter.TimeSignature(
            f"{self.time_signature[0]}/{self.time_signature[1]}"
        )
        self.score.insert(0, ts)

        return self.score

    def add_melody_track(
        self,
        notes: list[int],
        durations: list[float],
    ) -> None:
        """Add a melody track to the score.

        Args:
            notes: List of MIDI note numbers (0 = rest).
            durations: List of quarter-note durations for each note.

        Raises:
            ValueError: If notes and durations have different lengths.
            RuntimeError: If create_score has not been called.
        """
        if len(notes) != len(durations):
            raise ValueError(
                f"Notes ({len(notes)}) and durations ({len(durations)}) "
                f"must have the same length."
            )
        if self.score is None:
            raise RuntimeError("Call create_score() before adding tracks.")

        self.melody_part = stream.Part()
        self.melody_part.partName = "Melody"
        self.melody_part.insert(0, instrument.Piano())

        for midi_num, dur in zip(notes, durations):
            if midi_num == 0:
                # Treat MIDI 0 as a rest.
                r = note.Rest(quarterLength=dur)
                self.melody_part.append(r)
            else:
                n = note.Note(midi_num, quarterLength=dur)
                self.melody_part.append(n)

        self.score.insert(0, self.melody_part)

    def add_accompaniment_track(
        self,
        voicings: list[list[int]],
        durations: list[float],
    ) -> None:
        """Add an accompaniment track with chord voicings to the score.

        Args:
            voicings: List of chord voicings, where each voicing is a list
                      of MIDI note numbers. An empty list represents a rest.
            durations: List of quarter-note durations for each chord.

        Raises:
            ValueError: If voicings and durations have different lengths.
            RuntimeError: If create_score has not been called.
        """
        if len(voicings) != len(durations):
            raise ValueError(
                f"Voicings ({len(voicings)}) and durations ({len(durations)}) "
                f"must have the same length."
            )
        if self.score is None:
            raise RuntimeError("Call create_score() before adding tracks.")

        self.accompaniment_part = stream.Part()
        self.accompaniment_part.partName = "Accompaniment"
        self.accompaniment_part.insert(0, instrument.Piano())

        for voicing, dur in zip(voicings, durations):
            if not voicing:
                # Empty voicing = rest.
                r = note.Rest(quarterLength=dur)
                self.accompaniment_part.append(r)
            else:
                c = m21chord.Chord(voicing, quarterLength=dur)
                self.accompaniment_part.append(c)

        self.score.insert(0, self.accompaniment_part)

    def write_midi(self, file_path: str) -> str:
        """Write the score to a MIDI file.

        Args:
            file_path: Destination file path (should end with .mid).

        Returns:
            The absolute path to the written MIDI file.

        Raises:
            RuntimeError: If create_score has not been called or no tracks added.
        """
        if self.score is None:
            raise RuntimeError("Call create_score() before writing MIDI.")

        # Ensure .mid extension.
        if not file_path.endswith(".mid"):
            file_path = file_path + ".mid"

        self.score.write("midi", fp=file_path)
        return file_path
