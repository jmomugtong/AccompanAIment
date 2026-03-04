import React, { useState, useCallback } from "react";

/**
 * Common chord symbols recognized by music21.
 * Used for client-side validation hints.
 */
const VALID_ROOTS = [
  "C",
  "C#",
  "Db",
  "D",
  "D#",
  "Eb",
  "E",
  "F",
  "F#",
  "Gb",
  "G",
  "G#",
  "Ab",
  "A",
  "A#",
  "Bb",
  "B",
];

const VALID_QUALITIES = [
  "",
  "m",
  "7",
  "m7",
  "maj7",
  "dim",
  "dim7",
  "aug",
  "sus2",
  "sus4",
  "9",
  "m9",
  "11",
  "13",
  "6",
  "m6",
  "add9",
  "7b5",
  "7#5",
  "m7b5",
];

export interface ChordInputProps {
  /** Called with the validated chord progression string. */
  onChordsChange: (chords: string) => void;
  /** The current chord progression value (controlled). */
  value: string;
  /** Whether the input is disabled. */
  disabled?: boolean;
}

interface ValidationResult {
  valid: boolean;
  message: string | null;
}

/**
 * Validate a single chord symbol (e.g. "Am7", "F#dim", "Bbmaj7").
 */
function validateChord(chord: string): boolean {
  const trimmed = chord.trim();
  if (trimmed === "" || trimmed === "|") return true;

  for (const root of VALID_ROOTS) {
    if (trimmed.startsWith(root)) {
      const quality = trimmed.slice(root.length);
      if (VALID_QUALITIES.includes(quality)) return true;
    }
  }
  return false;
}

/**
 * Validate the full chord progression string.
 */
function validateProgression(input: string): ValidationResult {
  const trimmed = input.trim();
  if (trimmed === "") {
    return { valid: true, message: null };
  }

  // Split on whitespace, pipe, comma, or dash.
  const tokens = trimmed.split(/[\s|,\-]+/).filter((t) => t.length > 0);

  if (tokens.length === 0) {
    return { valid: true, message: null };
  }

  const invalid = tokens.filter((t) => !validateChord(t));

  if (invalid.length > 0) {
    return {
      valid: false,
      message: `Unrecognized chord(s): ${invalid.join(", ")}. Use standard notation like Am7, Cmaj7, F#dim.`,
    };
  }

  return {
    valid: true,
    message: `${tokens.length} chord(s) recognized.`,
  };
}

/**
 * Text input for entering a chord progression with real-time validation.
 *
 * Chords can be separated by spaces, pipes (|), commas, or dashes.
 * Validates against standard chord symbol notation (root + quality).
 */
export function ChordInput({
  onChordsChange,
  value,
  disabled = false,
}: ChordInputProps): React.ReactElement {
  const [validation, setValidation] = useState<ValidationResult>({
    valid: true,
    message: null,
  });

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newValue = e.target.value;
      onChordsChange(newValue);

      const result = validateProgression(newValue);
      setValidation(result);
    },
    [onChordsChange],
  );

  return (
    <div className="w-full">
      <label
        htmlFor="chord-input"
        className="block text-sm font-medium text-gray-700 mb-1"
      >
        Chord Progression
      </label>

      <textarea
        id="chord-input"
        value={value}
        onChange={handleChange}
        disabled={disabled}
        placeholder="e.g. Am | F | C | G    or    Dm7 G7 Cmaj7 Fmaj7"
        rows={3}
        className={`w-full px-3 py-2 border rounded-lg text-sm font-mono resize-none transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
          !validation.valid
            ? "border-red-300 bg-red-50"
            : "border-gray-300 bg-white"
        } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
        aria-describedby="chord-input-help chord-input-validation"
      />

      <p id="chord-input-help" className="mt-1 text-xs text-gray-400">
        Separate chords with spaces, pipes (|), or commas. Supported qualities:
        m, 7, m7, maj7, dim, aug, sus2, sus4, 9, and more.
      </p>

      {validation.message && (
        <p
          id="chord-input-validation"
          className={`mt-1 text-xs ${validation.valid ? "text-green-600" : "text-red-600"}`}
          role={validation.valid ? "status" : "alert"}
        >
          {validation.message}
        </p>
      )}
    </div>
  );
}
