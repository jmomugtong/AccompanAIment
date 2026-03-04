import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MelodyExtractor } from "../../components/MelodyExtractor";

describe("MelodyExtractor", () => {
  it("renders note data when provided", () => {
    const frames = [
      { time: 0.0, frequency: 440.0, confidence: 0.9, note_name: "A4" },
      { time: 0.1, frequency: 493.88, confidence: 0.85, note_name: "B4" },
      { time: 0.2, frequency: 523.25, confidence: 0.92, note_name: "C5" },
    ];

    render(<MelodyExtractor frames={frames} />);

    expect(screen.getByText("A4")).toBeInTheDocument();
    expect(screen.getByText("B4")).toBeInTheDocument();
    expect(screen.getByText("C5")).toBeInTheDocument();
    expect(screen.getByText("Frames")).toBeInTheDocument();
    expect(screen.getByText("Unique Notes")).toBeInTheDocument();
  });

  it("shows empty state when no data is provided", () => {
    render(<MelodyExtractor frames={null} />);

    expect(
      screen.getByText(/no melody data available/i),
    ).toBeInTheDocument();
  });
});
