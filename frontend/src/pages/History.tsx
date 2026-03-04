import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { getGenerations, type Generation } from "../services/api";

/**
 * Status badge colors for generation states.
 */
const STATUS_STYLES: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  processing: "bg-blue-100 text-blue-700",
  complete: "bg-green-100 text-green-700",
  error: "bg-red-100 text-red-700",
};

/**
 * History page listing all past generations.
 * Fetches generation records from the API and displays them as cards
 * with status, style, chord progression, and creation date.
 */
export function History(): React.ReactElement {
  const [generations, setGenerations] = useState<Generation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getGenerations();
      setGenerations(data);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to load generation history.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

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
              to="/generate"
              className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              Generate
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
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Generation History
            </h1>
            <p className="mt-2 text-gray-600">
              View and manage your past accompaniment generations.
            </p>
          </div>

          <button
            type="button"
            onClick={fetchHistory}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-indigo-600 bg-white border border-indigo-200 rounded-lg hover:bg-indigo-50 transition-colors disabled:opacity-50"
          >
            Refresh
          </button>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <svg
              className="animate-spin h-8 w-8 text-indigo-500"
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
            <span className="ml-3 text-gray-500">Loading history...</span>
          </div>
        )}

        {/* Error state */}
        {error && !loading && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg" role="alert">
            <p className="text-sm text-red-600">{error}</p>
            <button
              type="button"
              onClick={fetchHistory}
              className="mt-2 text-xs font-medium text-red-700 hover:text-red-800"
            >
              Try again
            </button>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && generations.length === 0 && (
          <div className="text-center py-16">
            <p className="text-gray-500 mb-4">
              No generations yet. Create your first accompaniment to see it
              here.
            </p>
            <Link
              to="/generate"
              className="inline-flex items-center px-6 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Create Your First Accompaniment
            </Link>
          </div>
        )}

        {/* Generations list */}
        {!loading && generations.length > 0 && (
          <div className="space-y-4">
            {generations.map((gen) => (
              <div
                key={gen.id}
                className="p-5 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[gen.status] ?? "bg-gray-100 text-gray-700"}`}
                      >
                        {gen.status}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(gen.created_at).toLocaleString()}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm">
                      <div>
                        <span className="text-gray-500">Style: </span>
                        <span className="text-gray-800 font-medium capitalize">
                          {gen.style}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Tempo: </span>
                        <span className="text-gray-800">
                          {gen.tempo} BPM
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Time: </span>
                        <span className="text-gray-800">
                          {gen.time_signature}
                        </span>
                      </div>
                    </div>

                    <p className="mt-2 text-sm text-gray-600 font-mono">
                      {gen.chord_progression}
                    </p>

                    {gen.error_message && (
                      <p className="mt-2 text-xs text-red-500">
                        {gen.error_message}
                      </p>
                    )}
                  </div>

                  <div className="ml-4 flex-shrink-0">
                    <span className="text-xs text-gray-400 font-mono">
                      {gen.id.slice(0, 8)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
