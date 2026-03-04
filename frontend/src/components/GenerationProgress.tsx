import React from "react";
import type { ProgressUpdate } from "../services/websocket";

export interface GenerationProgressProps {
  /** Latest progress update from the WebSocket. */
  progress: ProgressUpdate | null;
  /** Current pipeline step name from the generation hook. */
  step: string;
}

/**
 * Human-readable labels for each pipeline step.
 */
const STEP_LABELS: Record<string, string> = {
  idle: "Waiting",
  uploading: "Uploading audio file",
  extracting: "Extracting melody with CREPE",
  configuring: "Ready for configuration",
  generating: "Generating piano accompaniment",
  rendering: "Rendering audio and sheet music",
  complete: "Generation complete",
  error: "An error occurred",
};

/**
 * Ordered list of steps for the progress indicator dots.
 */
const STEP_ORDER = [
  "uploading",
  "extracting",
  "generating",
  "rendering",
  "complete",
];

/**
 * Progress bar with step indicator, percentage, descriptive text, and ETA.
 * Driven by WebSocket progress updates from the generation pipeline.
 */
export function GenerationProgress({
  progress,
  step,
}: GenerationProgressProps): React.ReactElement {
  const percent = progress?.percent ?? 0;
  const message = progress?.message ?? STEP_LABELS[step] ?? step;
  const etaSeconds = progress?.eta_seconds ?? null;
  const isError = step === "error" || progress?.step === "error";
  const isComplete = step === "complete" || progress?.step === "complete";

  // Determine which steps are done for the step indicator.
  const currentStepIndex = STEP_ORDER.indexOf(
    progress?.step ?? step,
  );

  return (
    <div className="w-full p-6 bg-white border border-gray-200 rounded-lg">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        Generation Progress
      </h3>

      {/* Step indicator dots */}
      <div className="flex items-center justify-between mb-6">
        {STEP_ORDER.map((s, index) => {
          const isDone = index < currentStepIndex || isComplete;
          const isCurrent = index === currentStepIndex && !isComplete;
          const label = STEP_LABELS[s] ?? s;

          return (
            <div key={s} className="flex flex-col items-center flex-1">
              <div className="flex items-center w-full">
                {index > 0 && (
                  <div
                    className={`flex-1 h-0.5 ${isDone ? "bg-indigo-500" : "bg-gray-200"}`}
                  />
                )}
                <div
                  className={`w-4 h-4 rounded-full flex-shrink-0 border-2 transition-colors ${
                    isDone
                      ? "bg-indigo-500 border-indigo-500"
                      : isCurrent
                        ? "bg-white border-indigo-500"
                        : "bg-white border-gray-300"
                  }`}
                  aria-label={label}
                />
                {index < STEP_ORDER.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 ${isDone ? "bg-indigo-500" : "bg-gray-200"}`}
                  />
                )}
              </div>
              <span className="mt-1 text-xs text-gray-500 text-center hidden sm:block">
                {STEP_LABELS[s]?.split(" ").slice(0, 2).join(" ") ?? s}
              </span>
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-3 mb-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            isError
              ? "bg-red-500"
              : isComplete
                ? "bg-green-500"
                : "bg-indigo-500"
          }`}
          style={{ width: `${Math.max(percent, isComplete ? 100 : 0)}%` }}
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Generation progress"
        />
      </div>

      {/* Status text */}
      <div className="flex items-center justify-between">
        <p
          className={`text-sm ${isError ? "text-red-600" : "text-gray-600"}`}
          role={isError ? "alert" : "status"}
        >
          {message}
        </p>

        <div className="flex items-center gap-3 text-sm text-gray-500">
          {!isComplete && !isError && percent > 0 && (
            <span>{percent}%</span>
          )}

          {etaSeconds !== null && !isComplete && !isError && (
            <span>
              ~{formatEta(etaSeconds)} remaining
            </span>
          )}
        </div>
      </div>

      {/* Error detail */}
      {isError && progress?.error && (
        <p className="mt-2 text-xs text-red-500">{progress.error}</p>
      )}
    </div>
  );
}

/**
 * Format an ETA in seconds to a human-readable string.
 */
function formatEta(seconds: number): string {
  if (seconds < 60) {
    return `${Math.ceil(seconds)}s`;
  }
  const mins = Math.floor(seconds / 60);
  const secs = Math.ceil(seconds % 60);
  return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
}
