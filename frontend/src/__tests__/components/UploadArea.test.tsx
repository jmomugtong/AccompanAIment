import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { UploadArea } from "../../components/UploadArea";

describe("UploadArea", () => {
  it("renders the upload zone", () => {
    render(<UploadArea onFileSelected={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: /upload audio file/i }),
    ).toBeInTheDocument();
  });

  it("shows accepted file formats text", () => {
    render(<UploadArea onFileSelected={vi.fn()} />);
    expect(
      screen.getByText(/MP3, WAV, M4A, or FLAC/i),
    ).toBeInTheDocument();
  });

  it("calls onFileSelected when a valid file is selected", () => {
    const onFileSelected = vi.fn();
    render(<UploadArea onFileSelected={onFileSelected} />);

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    expect(input).not.toBeNull();

    const file = new File(["audio-data"], "song.mp3", {
      type: "audio/mpeg",
    });
    fireEvent.change(input, { target: { files: [file] } });

    expect(onFileSelected).toHaveBeenCalledWith(file);
  });

  it("rejects invalid file types and shows an error", () => {
    const onFileSelected = vi.fn();
    render(<UploadArea onFileSelected={onFileSelected} />);

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    const file = new File(["data"], "document.txt", {
      type: "text/plain",
    });
    fireEvent.change(input, { target: { files: [file] } });

    expect(onFileSelected).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/unsupported format/i);
  });
});
