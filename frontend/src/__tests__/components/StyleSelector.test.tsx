import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { StyleSelector } from "../../components/StyleSelector";

describe("StyleSelector", () => {
  const styles = ["Jazz", "Soulful", "R&B", "Pop", "Classical"];

  it("renders all 5 style options", () => {
    render(<StyleSelector value="" onChange={vi.fn()} />);

    for (const style of styles) {
      expect(screen.getByText(style)).toBeInTheDocument();
    }
  });

  it("calls onChange when a style is clicked", () => {
    const onChange = vi.fn();
    render(<StyleSelector value="" onChange={onChange} />);

    fireEvent.click(screen.getByText("Jazz"));
    expect(onChange).toHaveBeenCalledWith("jazz");
  });

  it("highlights the selected style", () => {
    render(<StyleSelector value="pop" onChange={vi.fn()} />);

    const popButton = screen.getByRole("button", {
      name: /select pop style/i,
    });
    expect(popButton).toHaveAttribute("aria-pressed", "true");

    const jazzButton = screen.getByRole("button", {
      name: /select jazz style/i,
    });
    expect(jazzButton).toHaveAttribute("aria-pressed", "false");
  });
});
