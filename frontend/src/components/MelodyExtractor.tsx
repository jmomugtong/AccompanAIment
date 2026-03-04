import React from "react";
import type { MelodyFrame } from "../services/api";

export interface MelodyExtractorProps {
  /** Array of melody frames from CREPE pitch extraction. */
  frames: MelodyFrame[] | null;
  /** Whether extraction is currently in progress. */
  loading?: boolean;
  /** Error message if extraction failed. */
  error?: string | null;
}

/**
 * Displays the extracted melody as a scrollable list of detected notes
 * with their timestamps, frequencies, and confidence scores.
 */
export function MelodyExtractor({
  frames,
  loading = false,
  error = null,
}: MelodyExtractorProps): React.ReactElement {
  if (loading) {
    return (
      <div className="w-full p-6 bg-white border border-gray-200 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Melody Extraction
        </h3>
        <div className="flex items-center gap-3 text-gray-500">
          <svg
            className="animate-spin h-5 w-5 text-indigo-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <span>Extracting melody with CREPE...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full p-6 bg-white border border-red-200 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">
          Melody Extraction
        </h3>
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      </div>
    );
  }

  if (!frames || frames.length === 0) {
    return (
      <div className="w-full p-6 bg-white border border-gray-200 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">
          Melody Extraction
        </h3>
        <p className="text-sm text-gray-500">
          No melody data available. Upload a song to begin extraction.
        </p>
      </div>
    );
  }

  // Compute summary statistics.
  const avgConfidence =
    frames.reduce((sum, f) => sum + f.confidence, 0) / frames.length;
  const uniqueNotes = new Set(frames.map((f) => f.note_name)).size;
  const durationSeconds = frames[frames.length - 1].time - frames[0].time;

  return (
    <div className="w-full p-6 bg-white border border-gray-200 rounded-lg">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        Melody Extraction
      </h3>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center p-3 bg-gray-50 rounded-md">
          <p className="text-2xl font-bold text-indigo-600">{frames.length}</p>
          <p className="text-xs text-gray-500">Frames</p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-md">
          <p className="text-2xl font-bold text-indigo-600">{uniqueNotes}</p>
          <p className="text-xs text-gray-500">Unique Notes</p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-md">
          <p className="text-2xl font-bold text-indigo-600">
            {(avgConfidence * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500">Avg Confidence</p>
        </div>
      </div>

      <p className="text-xs text-gray-400 mb-3">
        Duration: {durationSeconds.toFixed(1)}s
      </p>

      {/* Scrollable note list */}
      <div className="max-h-64 overflow-y-auto border border-gray-100 rounded-md">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              <th className="text-left px-3 py-2 text-gray-600 font-medium">
                Time
              </th>
              <th className="text-left px-3 py-2 text-gray-600 font-medium">
                Note
              </th>
              <th className="text-right px-3 py-2 text-gray-600 font-medium">
                Frequency
              </th>
              <th className="text-right px-3 py-2 text-gray-600 font-medium">
                Confidence
              </th>
            </tr>
          </thead>
          <tbody>
            {frames.map((frame, index) => (
              <tr
                key={index}
                className="border-t border-gray-50 hover:bg-gray-50"
              >
                <td className="px-3 py-1.5 text-gray-700">
                  {frame.time.toFixed(2)}s
                </td>
                <td className="px-3 py-1.5 font-mono text-indigo-700">
                  {frame.note_name}
                </td>
                <td className="px-3 py-1.5 text-right text-gray-600">
                  {frame.frequency.toFixed(1)} Hz
                </td>
                <td className="px-3 py-1.5 text-right">
                  <span
                    className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                      frame.confidence >= 0.8
                        ? "bg-green-100 text-green-700"
                        : frame.confidence >= 0.5
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-red-100 text-red-700"
                    }`}
                  >
                    {(frame.confidence * 100).toFixed(0)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
