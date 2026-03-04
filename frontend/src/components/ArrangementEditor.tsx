import React from "react";

export interface NoteEvent {
  /** MIDI note number (0-127). */
  pitch: number;
  /** Start time in seconds. */
  start: number;
  /** Duration in seconds. */
  duration: number;
  /** Velocity (0-127). */
  velocity: number;
}

export interface ArrangementEditorProps {
  /** Array of MIDI note events to display. */
  notes: NoteEvent[];
  /** Total duration of the arrangement in seconds. */
  totalDuration: number;
  /** Called when the user modifies a note (future functionality). */
  onNoteChange?: (index: number, note: NoteEvent) => void;
  /** Whether the editor allows modification. */
  editable?: boolean;
}

/**
 * Lowest and highest MIDI pitches to display in the piano roll.
 */
const MIN_PITCH = 36; // C2
const MAX_PITCH = 96; // C7
const PITCH_RANGE = MAX_PITCH - MIN_PITCH;

/**
 * Convert a MIDI note number to a note name string.
 */
function midiToNoteName(midi: number): string {
  const noteNames = [
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
  ];
  const note = noteNames[midi % 12];
  const octave = Math.floor(midi / 12) - 1;
  return `${note}${octave}`;
}

/**
 * Check if a MIDI note number corresponds to a black key.
 */
function isBlackKey(midi: number): boolean {
  const pc = midi % 12;
  return [1, 3, 6, 8, 10].includes(pc);
}

/**
 * Placeholder piano roll editor for viewing and (eventually) editing
 * the generated MIDI arrangement.
 *
 * Renders a grid with pitch on the Y-axis and time on the X-axis.
 * Note blocks are positioned and sized according to their pitch, start
 * time, and duration. Full editing support (drag to move, resize, add,
 * delete) will be implemented in a later phase.
 */
export function ArrangementEditor({
  notes,
  totalDuration,
  editable = false,
}: ArrangementEditorProps): React.ReactElement {
  const gridHeight = 400;
  const gridWidth = 800;
  const rowHeight = gridHeight / PITCH_RANGE;

  return (
    <div className="w-full p-6 bg-white border border-gray-200 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Arrangement Editor
        </h3>
        {editable && (
          <span className="text-xs text-gray-400 px-2 py-1 bg-gray-100 rounded">
            Editing enabled (coming soon)
          </span>
        )}
      </div>

      {notes.length === 0 ? (
        <div
          className="flex items-center justify-center bg-gray-50 border border-gray-200 rounded-lg"
          style={{ height: `${gridHeight}px` }}
        >
          <p className="text-sm text-gray-400">
            No arrangement data. Generate an accompaniment to see the piano
            roll.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <div
            className="relative bg-gray-900 rounded-lg"
            style={{
              width: `${gridWidth}px`,
              height: `${gridHeight}px`,
              minWidth: "100%",
            }}
          >
            {/* Horizontal pitch grid lines and labels */}
            {Array.from({ length: PITCH_RANGE }).map((_, i) => {
              const pitch = MAX_PITCH - i;
              const y = i * rowHeight;
              const black = isBlackKey(pitch);

              return (
                <div key={pitch}>
                  {/* Grid row background */}
                  <div
                    className={`absolute left-0 right-0 border-b border-gray-800 ${
                      black ? "bg-gray-850" : ""
                    }`}
                    style={{
                      top: `${y}px`,
                      height: `${rowHeight}px`,
                      backgroundColor: black
                        ? "rgba(0, 0, 0, 0.3)"
                        : undefined,
                    }}
                  />

                  {/* Pitch label for C notes */}
                  {pitch % 12 === 0 && (
                    <span
                      className="absolute left-1 text-xs text-gray-500 pointer-events-none"
                      style={{ top: `${y}px` }}
                    >
                      {midiToNoteName(pitch)}
                    </span>
                  )}
                </div>
              );
            })}

            {/* Note blocks */}
            {notes.map((note, index) => {
              const clampedPitch = Math.max(
                MIN_PITCH,
                Math.min(MAX_PITCH, note.pitch),
              );
              const y =
                (MAX_PITCH - clampedPitch) * rowHeight;
              const x =
                totalDuration > 0
                  ? (note.start / totalDuration) * gridWidth
                  : 0;
              const width =
                totalDuration > 0
                  ? Math.max(
                      (note.duration / totalDuration) * gridWidth,
                      2,
                    )
                  : 4;

              // Color intensity based on velocity.
              const opacity = 0.5 + (note.velocity / 127) * 0.5;

              return (
                <div
                  key={index}
                  className="absolute rounded-sm"
                  style={{
                    left: `${x}px`,
                    top: `${y}px`,
                    width: `${width}px`,
                    height: `${Math.max(rowHeight - 1, 2)}px`,
                    backgroundColor: `rgba(99, 102, 241, ${opacity})`,
                  }}
                  title={`${midiToNoteName(note.pitch)} | ${note.start.toFixed(2)}s | vel: ${note.velocity}`}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Summary */}
      {notes.length > 0 && (
        <div className="mt-3 flex gap-4 text-xs text-gray-500">
          <span>{notes.length} notes</span>
          <span>{totalDuration.toFixed(1)}s duration</span>
          <span>
            Range: {midiToNoteName(Math.min(...notes.map((n) => n.pitch)))} -{" "}
            {midiToNoteName(Math.max(...notes.map((n) => n.pitch)))}
          </span>
        </div>
      )}
    </div>
  );
}
