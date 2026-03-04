import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DownloadPanel } from "../../components/DownloadPanel";

describe("DownloadPanel", () => {
  it("renders download buttons for MIDI, Audio, and Sheet Music", () => {
    render(
      <DownloadPanel songId="song-1" generationId="gen-1" ready={true} />,
    );

    expect(
      screen.getByRole("button", { name: /download midi/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /download audio/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /download sheet music/i }),
    ).toBeInTheDocument();
  });

  it("buttons have correct labels", () => {
    render(
      <DownloadPanel songId="song-1" generationId="gen-1" ready={true} />,
    );

    expect(screen.getByText("MIDI")).toBeInTheDocument();
    expect(screen.getByText("Audio (WAV)")).toBeInTheDocument();
    expect(screen.getByText("Sheet Music (PDF)")).toBeInTheDocument();
  });
});
