import React, { useState, useCallback } from "react";
import { downloadGeneration, type DownloadFormat } from "../services/api";

export interface DownloadPanelProps {
  /** Song ID owning the generation. */
  songId: string;
  /** Generation ID to download artifacts from. */
  generationId: string;
  /** Whether the generation is complete and downloads are available. */
  ready: boolean;
}

interface DownloadOption {
  format: DownloadFormat;
  label: string;
  description: string;
  fileExtension: string;
  mimeType: string;
}

const DOWNLOAD_OPTIONS: DownloadOption[] = [
  {
    format: "midi",
    label: "MIDI",
    description: "Standard MIDI file for DAWs and music software",
    fileExtension: ".mid",
    mimeType: "audio/midi",
  },
  {
    format: "audio",
    label: "Audio (WAV)",
    description: "Rendered piano audio using FluidSynth",
    fileExtension: ".wav",
    mimeType: "audio/wav",
  },
  {
    format: "sheet",
    label: "Sheet Music (PDF)",
    description: "Engraved score generated with Lilypond",
    fileExtension: ".pdf",
    mimeType: "application/pdf",
  },
];

/**
 * Download panel providing buttons for MIDI, audio (WAV), and sheet music (PDF).
 * Each button triggers a download via the API and saves the file locally.
 */
export function DownloadPanel({
  songId,
  generationId,
  ready,
}: DownloadPanelProps): React.ReactElement {
  const [downloading, setDownloading] = useState<DownloadFormat | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = useCallback(
    async (option: DownloadOption) => {
      if (!ready || downloading) return;

      setDownloading(option.format);
      setError(null);

      try {
        const blob = await downloadGeneration(
          songId,
          generationId,
          option.format,
        );

        // Create a temporary link to trigger the browser download dialog.
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = `accompaniment_${generationId}${option.fileExtension}`;
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
        URL.revokeObjectURL(url);
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : `Failed to download ${option.label}. Please try again.`;
        setError(message);
      } finally {
        setDownloading(null);
      }
    },
    [songId, generationId, ready, downloading],
  );

  return (
    <div className="w-full p-6 bg-white border border-gray-200 rounded-lg">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        Download Your Accompaniment
      </h3>

      {!ready && (
        <p className="text-sm text-gray-500 mb-4">
          Downloads will be available once generation is complete.
        </p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {DOWNLOAD_OPTIONS.map((option) => (
          <button
            key={option.format}
            type="button"
            disabled={!ready || downloading !== null}
            onClick={() => handleDownload(option)}
            className={`flex flex-col items-center p-4 rounded-lg border-2 transition-all ${
              ready
                ? "border-gray-200 hover:border-indigo-400 hover:bg-indigo-50 cursor-pointer"
                : "border-gray-100 bg-gray-50 cursor-not-allowed opacity-50"
            } ${downloading === option.format ? "border-indigo-500 bg-indigo-50" : ""}`}
            aria-label={`Download ${option.label}`}
          >
            {/* Icon */}
            <div className="mb-2">
              {downloading === option.format ? (
                <svg
                  className="animate-spin h-8 w-8 text-indigo-600"
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
              ) : (
                <svg
                  className="h-8 w-8 text-gray-400"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                  />
                </svg>
              )}
            </div>

            <p className="text-sm font-semibold text-gray-800">
              {option.label}
            </p>
            <p className="mt-1 text-xs text-gray-500 text-center">
              {option.description}
            </p>
          </button>
        ))}
      </div>

      {error && (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
