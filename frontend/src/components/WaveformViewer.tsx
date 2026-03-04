import React, { useEffect, useRef, useState } from "react";

export interface WaveformViewerProps {
  /** URL or object URL of the audio file to visualize. */
  audioUrl: string | null;
  /** Current playback position in seconds (controlled externally). */
  currentTime?: number;
  /** Called when the user seeks by clicking on the waveform. */
  onSeek?: (timeSeconds: number) => void;
  /** Height of the waveform container in pixels. */
  height?: number;
}

/**
 * Waveform display placeholder for Wavesurfer.js integration.
 *
 * This component renders a container element where Wavesurfer.js will
 * attach its canvas. In the current implementation it shows a styled
 * placeholder. A future phase will initialize the actual Wavesurfer
 * instance with peaks rendering and cursor tracking.
 */
export function WaveformViewer({
  audioUrl,
  currentTime = 0,
  onSeek,
  height = 128,
}: WaveformViewerProps): React.ReactElement {
  const containerRef = useRef<HTMLDivElement>(null);
  const [duration, setDuration] = useState<number>(0);
  const [isLoaded, setIsLoaded] = useState(false);

  // When the audio URL changes, simulate loading the waveform.
  useEffect(() => {
    setIsLoaded(false);
    setDuration(0);

    if (!audioUrl) return;

    // In a full implementation, this is where Wavesurfer.js would be
    // initialized with:
    //   const ws = WaveSurfer.create({ container: containerRef.current, ... });
    //   ws.load(audioUrl);
    //
    // For now we use a plain Audio element to get the duration.
    const audio = new Audio(audioUrl);

    const handleLoaded = () => {
      setDuration(audio.duration);
      setIsLoaded(true);
    };

    audio.addEventListener("loadedmetadata", handleLoaded);
    audio.load();

    return () => {
      audio.removeEventListener("loadedmetadata", handleLoaded);
      audio.src = "";
    };
  }, [audioUrl]);

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!onSeek || !duration || !containerRef.current) return;

    const rect = containerRef.current.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    const seekTime = ratio * duration;
    onSeek(Math.max(0, Math.min(seekTime, duration)));
  };

  const progressPercent =
    duration > 0 ? Math.min((currentTime / duration) * 100, 100) : 0;

  return (
    <div className="w-full">
      <div
        ref={containerRef}
        role="img"
        aria-label="Audio waveform display"
        className="relative w-full rounded-lg bg-gray-100 border border-gray-200 overflow-hidden cursor-pointer"
        style={{ height: `${height}px` }}
        onClick={handleClick}
      >
        {!audioUrl && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
            No audio loaded
          </div>
        )}

        {audioUrl && !isLoaded && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
            <svg
              className="animate-spin h-5 w-5 mr-2 text-indigo-500"
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
            Loading waveform...
          </div>
        )}

        {isLoaded && (
          <>
            {/* Placeholder waveform bars */}
            <div className="absolute inset-0 flex items-center justify-center gap-px px-2">
              {Array.from({ length: 80 }).map((_, i) => {
                // Generate deterministic pseudo-random bar heights.
                const h = 20 + ((i * 37 + 13) % 60);
                return (
                  <div
                    key={i}
                    className="flex-1 bg-indigo-300 rounded-sm min-w-[2px]"
                    style={{ height: `${h}%` }}
                  />
                );
              })}
            </div>

            {/* Playback progress overlay */}
            <div
              className="absolute top-0 left-0 bottom-0 bg-indigo-600 opacity-20 pointer-events-none transition-all"
              style={{ width: `${progressPercent}%` }}
            />

            {/* Cursor line */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-indigo-700 pointer-events-none transition-all"
              style={{ left: `${progressPercent}%` }}
            />
          </>
        )}
      </div>

      {/* Duration info */}
      {isLoaded && duration > 0 && (
        <div className="mt-1 flex justify-between text-xs text-gray-500">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      )}
    </div>
  );
}

/**
 * Format seconds as mm:ss.
 */
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
