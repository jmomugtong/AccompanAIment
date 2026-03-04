import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ArrangementEditor } from "../../components/ArrangementEditor";

describe("ArrangementEditor", () => {
  it("renders without crashing", () => {
    render(<ArrangementEditor notes={[]} totalDuration={0} />);
    expect(screen.getByText("Arrangement Editor")).toBeInTheDocument();
  });

  it("shows placeholder when no notes are provided", () => {
    render(<ArrangementEditor notes={[]} totalDuration={0} />);
    expect(
      screen.getByText(/no arrangement data/i),
    ).toBeInTheDocument();
  });
});
