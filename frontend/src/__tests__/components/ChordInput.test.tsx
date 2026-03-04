import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ChordInput } from "../../components/ChordInput";

describe("ChordInput", () => {
  it("renders a textarea", () => {
    render(<ChordInput onChordsChange={vi.fn()} value="" />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("calls onChordsChange with the input value", () => {
    const onChordsChange = vi.fn();
    render(<ChordInput onChordsChange={onChordsChange} value="" />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Am F C G" } });

    expect(onChordsChange).toHaveBeenCalledWith("Am F C G");
  });

  it("shows validation feedback for valid chords", () => {
    const onChordsChange = vi.fn();
    render(<ChordInput onChordsChange={onChordsChange} value="" />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Am F C G" } });

    expect(screen.getByRole("status")).toHaveTextContent(/4 chord\(s\) recognized/);
  });

  it("shows validation feedback for invalid chords", () => {
    const onChordsChange = vi.fn();
    render(<ChordInput onChordsChange={onChordsChange} value="" />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Xz99" } });

    expect(screen.getByRole("alert")).toHaveTextContent(/unrecognized chord/i);
  });
});
