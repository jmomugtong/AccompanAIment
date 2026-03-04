import { useState, useCallback, useEffect, useRef } from "react";
import {
  uploadSong,
  getMelody,
  generatePiano,
  type Song,
  type MelodyData,
  type Generation,
  type GeneratePianoRequest,
} from "../services/api";
import {
  GenerationWebSocket,
  type ProgressUpdate,
} from "../services/websocket";

/**
 * Discrete steps of the generation pipeline as seen by the UI.
 */
export type GenerationStep =
  | "idle"
  | "uploading"
  | "extracting"
  | "configuring"
  | "generating"
  | "complete"
  | "error";

/**
 * Full state object exposed by the useGeneration hook.
 */
export interface GenerationState {
  step: GenerationStep;
  song: Song | null;
  melody: MelodyData | null;
  generation: Generation | null;
  progress: ProgressUpdate | null;
  error: string | null;
}

/**
 * Actions returned by the useGeneration hook.
 */
export interface GenerationActions {
  /** Upload an audio file and begin melody extraction. */
  upload: (file: File) => Promise<void>;
  /** Fetch the extracted melody for the current song. */
  fetchMelody: () => Promise<void>;
  /** Trigger piano accompaniment generation with the given parameters. */
  generate: (params: GeneratePianoRequest) => Promise<void>;
  /** Reset all state back to idle. */
  reset: () => void;
}

const INITIAL_STATE: GenerationState = {
  step: "idle",
  song: null,
  melody: null,
  generation: null,
  progress: null,
  error: null,
};

/**
 * Hook that manages the full generation workflow:
 *   idle -> uploading -> extracting -> configuring -> generating -> complete
 *
 * Automatically connects a WebSocket for real-time progress while generating.
 */
export function useGeneration(): [GenerationState, GenerationActions] {
  const [state, setState] = useState<GenerationState>(INITIAL_STATE);
  const wsRef = useRef<GenerationWebSocket | null>(null);

  // Clean up WebSocket on unmount.
  useEffect(() => {
    return () => {
      wsRef.current?.disconnect();
    };
  }, []);

  const upload = useCallback(async (file: File) => {
    try {
      setState((prev) => ({ ...prev, step: "uploading", error: null }));
      const song = await uploadSong(file);
      setState((prev) => ({ ...prev, step: "extracting", song }));

      // Automatically fetch melody after upload.
      const melody = await getMelody(song.id);
      setState((prev) => ({ ...prev, step: "configuring", melody }));
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Upload failed. Please try again.";
      setState((prev) => ({ ...prev, step: "error", error: message }));
    }
  }, []);

  const fetchMelody = useCallback(async () => {
    const songId = state.song?.id;
    if (!songId) return;

    try {
      setState((prev) => ({ ...prev, step: "extracting", error: null }));
      const melody = await getMelody(songId);
      setState((prev) => ({ ...prev, step: "configuring", melody }));
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Melody extraction failed. Please try again.";
      setState((prev) => ({ ...prev, step: "error", error: message }));
    }
  }, [state.song?.id]);

  const generate = useCallback(
    async (params: GeneratePianoRequest) => {
      const songId = state.song?.id;
      if (!songId) return;

      try {
        setState((prev) => ({ ...prev, step: "generating", error: null }));

        const generation = await generatePiano(songId, params);
        setState((prev) => ({ ...prev, generation }));

        // Connect WebSocket for real-time progress.
        wsRef.current?.disconnect();
        const ws = new GenerationWebSocket(songId);
        wsRef.current = ws;

        ws.onProgress((update: ProgressUpdate) => {
          setState((prev) => ({ ...prev, progress: update }));

          if (update.step === "complete") {
            setState((prev) => ({ ...prev, step: "complete" }));
            ws.disconnect();
          } else if (update.step === "error") {
            setState((prev) => ({
              ...prev,
              step: "error",
              error: update.error ?? "Generation failed.",
            }));
            ws.disconnect();
          }
        });

        ws.connect();
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Generation request failed. Please try again.";
        setState((prev) => ({ ...prev, step: "error", error: message }));
      }
    },
    [state.song?.id],
  );

  const reset = useCallback(() => {
    wsRef.current?.disconnect();
    wsRef.current = null;
    setState(INITIAL_STATE);
  }, []);

  return [state, { upload, fetchMelody, generate, reset }];
}
