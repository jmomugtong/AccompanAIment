import React from "react";
import { Link } from "react-router-dom";

/**
 * Landing page with hero section introducing AccompanAIment.
 */
export function Home(): React.ReactElement {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center px-4 py-20 bg-gradient-to-b from-indigo-50 to-white">
        <div className="max-w-3xl text-center">
          <h1 className="text-5xl font-bold text-gray-900 tracking-tight sm:text-6xl">
            AccompanAIment
          </h1>
          <p className="mt-4 text-xl text-indigo-600 font-medium">
            AI-Powered Piano Accompaniment for Singer-Songwriters
          </p>
          <p className="mt-6 text-lg text-gray-600 leading-relaxed">
            Upload your song, specify your chord progression, and let our AI
            generate beautiful piano accompaniments in multiple styles. Get
            professional-quality MIDI, audio, and sheet music -- all powered by
            open-source technology with zero API costs.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/generate"
              className="inline-flex items-center px-8 py-3 text-base font-medium text-white bg-indigo-600 rounded-lg shadow hover:bg-indigo-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              Start Creating
              <svg
                className="ml-2 h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M13 7l5 5m0 0l-5 5m5-5H6"
                />
              </svg>
            </Link>

            <Link
              to="/history"
              className="inline-flex items-center px-8 py-3 text-base font-medium text-indigo-600 bg-white border-2 border-indigo-200 rounded-lg hover:bg-indigo-50 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              View Past Generations
            </Link>
          </div>
        </div>
      </section>

      {/* Feature highlights */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-12">
            How It Works
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard
              step="1"
              title="Upload Your Song"
              description="Upload any audio file (MP3, WAV, M4A, FLAC). Our CREPE-based
                melody extraction identifies the vocal melody automatically."
            />
            <FeatureCard
              step="2"
              title="Configure Your Style"
              description="Enter your chord progression and choose from five styles: Jazz,
                Soulful, R&B, Pop, or Classical. Set your tempo and time
                signature."
            />
            <FeatureCard
              step="3"
              title="Download Results"
              description="Our LLM agent generates style-appropriate voicings. Download
                your accompaniment as MIDI, rendered audio (WAV), or engraved
                sheet music (PDF)."
            />
          </div>
        </div>
      </section>

      {/* Technology section */}
      <section className="py-16 px-4 bg-gray-50">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            100% Open Source
          </h2>
          <p className="text-gray-600 leading-relaxed">
            AccompanAIment runs entirely on open-source technology. Melody
            extraction uses CREPE, music theory is handled by music21, audio
            rendering uses FluidSynth, and the AI agent runs locally via Ollama.
            No external API keys required. No usage fees. Your music stays on
            your machine.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 bg-white border-t border-gray-200">
        <div className="max-w-5xl mx-auto text-center text-sm text-gray-400">
          AccompanAIment -- Open-source AI piano accompaniment generator
        </div>
      </footer>
    </div>
  );
}

interface FeatureCardProps {
  step: string;
  title: string;
  description: string;
}

function FeatureCard({
  step,
  title,
  description,
}: FeatureCardProps): React.ReactElement {
  return (
    <div className="flex flex-col items-center text-center p-6 bg-gray-50 rounded-xl">
      <div className="w-10 h-10 flex items-center justify-center rounded-full bg-indigo-600 text-white font-bold text-sm mb-4">
        {step}
      </div>
      <h3 className="text-lg font-semibold text-gray-800 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  );
}
