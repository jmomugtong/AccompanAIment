import React, { useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { submitFeedback, type FeedbackRequest } from "../services/api";

/**
 * Rating dimensions presented to the user.
 */
interface RatingDimension {
  key: keyof Pick<
    FeedbackRequest,
    "overall_rating" | "harmony_rating" | "rhythm_rating" | "style_rating"
  >;
  label: string;
  description: string;
}

const DIMENSIONS: RatingDimension[] = [
  {
    key: "overall_rating",
    label: "Overall Quality",
    description: "How good is the accompaniment as a whole?",
  },
  {
    key: "harmony_rating",
    label: "Harmony",
    description: "Are the chord voicings and harmonic choices appropriate?",
  },
  {
    key: "rhythm_rating",
    label: "Rhythm",
    description: "Is the rhythmic pattern musical and well-suited to the style?",
  },
  {
    key: "style_rating",
    label: "Style Accuracy",
    description: "Does the accompaniment faithfully represent the chosen style?",
  },
];

/**
 * Feedback page with a multi-dimensional star rating interface.
 * Users rate a specific generation across four dimensions (overall,
 * harmony, rhythm, style) on a 1-5 scale with optional comments.
 */
export function Feedback(): React.ReactElement {
  const [generationId, setGenerationId] = useState("");
  const [ratings, setRatings] = useState<Record<string, number>>({
    overall_rating: 0,
    harmony_rating: 0,
    rhythm_rating: 0,
    style_rating: 0,
  });
  const [comments, setComments] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRatingChange = useCallback((key: string, value: number) => {
    setRatings((prev) => ({ ...prev, [key]: value }));
  }, []);

  const canSubmit =
    generationId.trim().length > 0 &&
    Object.values(ratings).every((r) => r >= 1) &&
    !submitting;

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!canSubmit) return;

      setSubmitting(true);
      setError(null);

      try {
        const feedback: FeedbackRequest = {
          overall_rating: ratings.overall_rating,
          harmony_rating: ratings.harmony_rating,
          rhythm_rating: ratings.rhythm_rating,
          style_rating: ratings.style_rating,
          comments: comments.trim() || undefined,
        };

        await submitFeedback(generationId.trim(), feedback);
        setSubmitted(true);
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Failed to submit feedback. Please try again.";
        setError(message);
      } finally {
        setSubmitting(false);
      }
    },
    [canSubmit, generationId, ratings, comments],
  );

  const handleReset = useCallback(() => {
    setGenerationId("");
    setRatings({
      overall_rating: 0,
      harmony_rating: 0,
      rhythm_rating: 0,
      style_rating: 0,
    });
    setComments("");
    setSubmitted(false);
    setError(null);
  }, []);

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
              to="/history"
              className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              History
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Rate Your Accompaniment
          </h1>
          <p className="mt-2 text-gray-600">
            Help us improve by rating the quality of your generated
            accompaniment across multiple dimensions.
          </p>
        </div>

        {submitted ? (
          <div className="p-8 bg-white border border-gray-200 rounded-lg text-center">
            <div className="w-16 h-16 mx-auto mb-4 flex items-center justify-center rounded-full bg-green-100">
              <svg
                className="h-8 w-8 text-green-600"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Thank you for your feedback!
            </h2>
            <p className="text-gray-600 mb-6">
              Your ratings help us improve the quality of generated
              accompaniments.
            </p>
            <button
              type="button"
              onClick={handleReset}
              className="px-6 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
            >
              Submit Another Rating
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Generation ID input */}
            <div className="p-6 bg-white border border-gray-200 rounded-lg">
              <label
                htmlFor="generation-id"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Generation ID
              </label>
              <input
                id="generation-id"
                type="text"
                value={generationId}
                onChange={(e) => setGenerationId(e.target.value)}
                placeholder="Enter the generation ID to rate"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <p className="mt-1 text-xs text-gray-400">
                You can find this on the generation history page.
              </p>
            </div>

            {/* Rating dimensions */}
            <div className="p-6 bg-white border border-gray-200 rounded-lg space-y-6">
              {DIMENSIONS.map((dim) => (
                <div key={dim.key}>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-sm font-medium text-gray-700">
                      {dim.label}
                    </label>
                    <span className="text-xs text-gray-400">
                      {ratings[dim.key] > 0
                        ? `${ratings[dim.key]} / 5`
                        : "Not rated"}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mb-2">
                    {dim.description}
                  </p>
                  <StarRating
                    value={ratings[dim.key]}
                    onChange={(val) => handleRatingChange(dim.key, val)}
                    disabled={submitting}
                  />
                </div>
              ))}
            </div>

            {/* Comments */}
            <div className="p-6 bg-white border border-gray-200 rounded-lg">
              <label
                htmlFor="feedback-comments"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Comments (optional)
              </label>
              <textarea
                id="feedback-comments"
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="Any additional thoughts on the accompaniment quality, style accuracy, or suggestions for improvement..."
                rows={4}
                disabled={submitting}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
              />
            </div>

            {/* Submit button */}
            <div className="flex items-center gap-4">
              <button
                type="submit"
                disabled={!canSubmit}
                className="px-6 py-3 text-sm font-medium text-white bg-indigo-600 rounded-lg shadow hover:bg-indigo-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? "Submitting..." : "Submit Feedback"}
              </button>

              <button
                type="button"
                onClick={handleReset}
                className="px-4 py-3 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Clear
              </button>
            </div>

            {error && (
              <p className="text-sm text-red-600" role="alert">
                {error}
              </p>
            )}
          </form>
        )}
      </main>
    </div>
  );
}

// -- Star rating sub-component -------------------------------------------

interface StarRatingProps {
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}

function StarRating({
  value,
  onChange,
  disabled = false,
}: StarRatingProps): React.ReactElement {
  const [hovered, setHovered] = useState(0);

  return (
    <div className="flex items-center gap-1" role="radiogroup" aria-label="Rating">
      {[1, 2, 3, 4, 5].map((star) => {
        const filled = star <= (hovered || value);

        return (
          <button
            key={star}
            type="button"
            disabled={disabled}
            onClick={() => onChange(star)}
            onMouseEnter={() => setHovered(star)}
            onMouseLeave={() => setHovered(0)}
            className={`p-0.5 transition-colors ${disabled ? "cursor-not-allowed" : "cursor-pointer"}`}
            role="radio"
            aria-checked={star === value}
            aria-label={`${star} star${star !== 1 ? "s" : ""}`}
          >
            <svg
              className={`h-7 w-7 transition-colors ${
                filled ? "text-yellow-400" : "text-gray-300"
              }`}
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.007 5.404.433c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.433 2.082-5.006z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        );
      })}
    </div>
  );
}
