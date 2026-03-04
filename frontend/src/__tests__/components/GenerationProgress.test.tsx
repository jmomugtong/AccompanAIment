import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { GenerationProgress } from "../../components/GenerationProgress";

describe("GenerationProgress", () => {
  it("renders the progress bar", () => {
    render(
      <GenerationProgress
        progress={{ step: "generating", percent: 50, message: "Generating piano accompaniment", eta_seconds: null }}
        step="generating"
      />,
    );

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("shows the step text", () => {
    render(
      <GenerationProgress
        progress={{ step: "extracting", percent: 30, message: "Extracting melody with CREPE", eta_seconds: null }}
        step="extracting"
      />,
    );

    expect(
      screen.getByText("Extracting melody with CREPE"),
    ).toBeInTheDocument();
  });

  it("shows the completion state", () => {
    render(
      <GenerationProgress
        progress={{ step: "complete", percent: 100, message: "Generation complete", eta_seconds: null }}
        step="complete"
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Generation complete");
    // Progress bar should show 100%
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "100");
  });
});
