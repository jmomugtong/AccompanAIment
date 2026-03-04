import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { WaveformViewer } from "../../components/WaveformViewer";

describe("WaveformViewer", () => {
  it("renders without crashing", () => {
    render(<WaveformViewer audioUrl={null} />);
    expect(
      screen.getByRole("img", { name: /audio waveform display/i }),
    ).toBeInTheDocument();
  });

  it("shows 'No audio loaded' when audioUrl is null", () => {
    render(<WaveformViewer audioUrl={null} />);
    expect(screen.getByText("No audio loaded")).toBeInTheDocument();
  });
});
