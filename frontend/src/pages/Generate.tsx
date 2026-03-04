import React, { useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { UploadArea } from "../components/UploadArea";
import { WaveformViewer } from "../components/WaveformViewer";
import { MelodyExtractor } from "../components/MelodyExtractor";
import { ChordInput } from "../components/ChordInput";
import { StyleSelector } from "../components/StyleSelector";
import { GenerationProgress } from "../components/GenerationProgress";
import { ArrangementEditor } from "../components/ArrangementEditor";
import { DownloadPanel } from "../components/DownloadPanel";
import { useGeneration } from "../hooks/useGeneration";

/**
 * Main workflow page that orchestrates the entire generation pipeline:
 *   Upload -> Melody Extraction -> Chord/Style Config -> Generate -> Download
 *
 * Uses the useGeneration hook to manage state transitions and WebSocket
 * progress tracking.
 */
export function Generate(): React.ReactElement {
  const [state, actions] = useGeneration();

  // Local form state for generation parameters.
  const [chords, setChords] = useState("");
  const [style, setStyle] = useState("pop");
  const [tempo, setTempo] = useState(120);
  const [timeSignature, setTimeSignature] = useState("4/4");

  // Audio URL for the waveform viewer (created from uploaded file).
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const handleFileSelected = useCallback(
    (file: File) => {
      // Create object URL for the waveform viewer.
      const url = URL.createObjectURL(file);
      setAudioUrl(url);
      actions.upload(file);
    },
    [actions],
  );

  const handleGenerate = useCallback(() => {
    if (!chords.trim()) return;

    actions.generate({
      chord_progression: chords.trim(),
      style,
      tempo,
      time_signature: timeSignature,
    });
  }, [actions, chords, style, tempo, timeSignature]);

  const handleReset = useCallback(() => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setChords("");
    setStyle("pop");
    setTempo(120);
    setTimeSignature("4/4");
    actions.reset();
  }, [actions, audioUrl]);

  const isUploading = state.step === "uploading";
  const isExtracting = state.step === "extracting";
  const isConfiguring = state.step === "configuring";
  const isGenerating = state.step === "generating";
  const isComplete = state.step === "complete";
  const isError = state.step === "error";
  const isIdle = state.step === "idle";

  const canConfigure = isConfiguring || isComplete || isError;
  const canGenerate = canConfigure && chords.trim().length > 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link
            to="/"
            className="text-xl font-bold text-gray-900 hover:text-indigo-600 transition-colors"
          >
            AccompanAIment
          </Link>

          <nav className="flex items-center gap-4">
            <Link
              to="/history"
              className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              History
            </Link>
            <Link
              to="/feedback"
              className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              Feedback
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Generate Accompaniment
          </h1>
          <p className="mt-2 text-gray-600">
            Upload your song, configure the style, and generate a piano
            accompaniment.
          </p>
        </div>

        <div className="space-y-8">
          {/* Step 1: Upload */}
          <section>
            <h2 className="text-lg font-semibold text-gray-800 mb-3">
              Step 1: Upload Your Song
            </h2>
            <UploadArea
              onFileSelected={handleFileSelected}
              uploading={isUploading}
              disabled={!isIdle && !isError}
            />
          </section>

          {/* Waveform viewer (shown after upload) */}
          {audioUrl && (
            <section>
              <WaveformViewer audioUrl={audioUrl} />
            </section>
          )}

          {/* Step 2: Melody extraction results */}
          {(isExtracting || state.melody) && (
            <section>
              <h2 className="text-lg font-semibold text-gray-800 mb-3">
                Step 2: Melody Extraction
              </h2>
              <MelodyExtractor
                frames={state.melody?.frames ?? null}
                loading={isExtracting}
                error={isError && !state.melody ? state.error : null}
              />
            </section>
          )}

          {/* Step 3: Configuration (chords, style, tempo) */}
          {canConfigure && (
            <section>
              <h2 className="text-lg font-semibold text-gray-800 mb-3">
                Step 3: Configure Your Accompaniment
              </h2>

              <div className="space-y-6 p-6 bg-white border border-gray-200 rounded-lg">
                <ChordInput
                  value={chords}
                  onChordsChange={setChords}
                  disabled={isGenerating}
                />

                <StyleSelector
                  value={style}
                  onChange={setStyle}
                  disabled={isGenerating}
                />

                {/* Tempo and time signature */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label
                      htmlFor="tempo-input"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Tempo (BPM)
                    </label>
                    <input
                      id="tempo-input"
                      type="number"
                      min={40}
                      max={240}
                      value={tempo}
                      onChange={(e) =>
                        setTempo(
                          Math.max(40, Math.min(240, Number(e.target.value))),
                        )
                      }
                      disabled={isGenerating}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="time-sig-input"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Time Signature
                    </label>
                    <select
                      id="time-sig-input"
                      value={timeSignature}
                      onChange={(e) => setTimeSignature(e.target.value)}
                      disabled={isGenerating}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                      <option value="4/4">4/4</option>
                      <option value="3/4">3/4</option>
                      <option value="6/8">6/8</option>
                      <option value="2/4">2/4</option>
                      <option value="5/4">5/4</option>
                    </select>
                  </div>
                </div>

                {/* Generate button */}
                <div className="flex items-center gap-4">
                  <button
                    type="button"
                    disabled={!canGenerate || isGenerating}
                    onClick={handleGenerate}
                    className="px-6 py-3 text-sm font-medium text-white bg-indigo-600 rounded-lg shadow hover:bg-indigo-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isGenerating ? "Generating..." : "Generate Accompaniment"}
                  </button>

                  <button
                    type="button"
                    onClick={handleReset}
                    className="px-4 py-3 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300"
                  >
                    Start Over
                  </button>
                </div>
              </div>
            </section>
          )}

          {/* Step 4: Generation progress */}
          {(isGenerating || isComplete) && (
            <section>
              <h2 className="text-lg font-semibold text-gray-800 mb-3">
                Step 4: Generation
              </h2>
              <GenerationProgress
                progress={state.progress}
                step={state.step}
              />
            </section>
          )}

          {/* Step 5: Results (arrangement editor + downloads) */}
          {isComplete && state.generation && state.song && (
            <section>
              <h2 className="text-lg font-semibold text-gray-800 mb-3">
                Step 5: Your Accompaniment
              </h2>

              <div className="space-y-6">
                <ArrangementEditor
                  notes={[]}
                  totalDuration={0}
                />

                <DownloadPanel
                  songId={state.song.id}
                  generationId={state.generation.id}
                  ready={true}
                />
              </div>
            </section>
          )}

          {/* Error banner */}
          {isError && state.error && (
            <div
              className="p-4 bg-red-50 border border-red-200 rounded-lg"
              role="alert"
            >
              <h3 className="text-sm font-semibold text-red-800 mb-1">
                Something went wrong
              </h3>
              <p className="text-sm text-red-600">{state.error}</p>
              <button
                type="button"
                onClick={handleReset}
                className="mt-3 px-4 py-2 text-xs font-medium text-red-700 bg-red-100 rounded hover:bg-red-200 transition-colors"
              >
                Start Over
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
