import React from "react";

/**
 * Available accompaniment styles.
 */
export interface StyleOption {
  value: string;
  label: string;
  description: string;
}

const STYLES: StyleOption[] = [
  {
    value: "jazz",
    label: "Jazz",
    description:
      "Sophisticated voicings with 7ths, 9ths, and 13ths. Swing feel with walking bass lines.",
  },
  {
    value: "soulful",
    label: "Soulful",
    description:
      "Warm, gospel-influenced chords with rich harmonic extensions and expressive dynamics.",
  },
  {
    value: "rnb",
    label: "R&B",
    description:
      "Smooth, syncopated rhythms with lush chord pads and contemporary voicings.",
  },
  {
    value: "pop",
    label: "Pop",
    description:
      "Clean, accessible patterns with steady rhythm and singable accompaniment.",
  },
  {
    value: "classical",
    label: "Classical",
    description:
      "Traditional voice leading with arpeggiated patterns and Alberti bass figures.",
  },
];

export interface StyleSelectorProps {
  /** The currently selected style value. */
  value: string;
  /** Called when the user selects a different style. */
  onChange: (style: string) => void;
  /** Whether the selector is disabled. */
  disabled?: boolean;
}

/**
 * Style selection component that presents the five available accompaniment
 * styles as cards with descriptions. The selected style is highlighted.
 */
export function StyleSelector({
  value,
  onChange,
  disabled = false,
}: StyleSelectorProps): React.ReactElement {
  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-gray-700 mb-3">
        Accompaniment Style
      </label>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {STYLES.map((style) => {
          const isSelected = value === style.value;
          return (
            <button
              key={style.value}
              type="button"
              disabled={disabled}
              onClick={() => onChange(style.value)}
              className={`text-left p-4 rounded-lg border-2 transition-all ${
                isSelected
                  ? "border-indigo-500 bg-indigo-50 ring-2 ring-indigo-200"
                  : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50"
              } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
              aria-pressed={isSelected}
              aria-label={`Select ${style.label} style`}
            >
              <p
                className={`text-sm font-semibold ${isSelected ? "text-indigo-700" : "text-gray-800"}`}
              >
                {style.label}
              </p>
              <p className="mt-1 text-xs text-gray-500">{style.description}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
