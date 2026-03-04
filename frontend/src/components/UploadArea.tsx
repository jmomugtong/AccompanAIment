import React, { useState, useRef, useCallback } from "react";

/**
 * Accepted audio MIME types and their file extensions.
 */
const ACCEPTED_FORMATS: Record<string, string> = {
  "audio/mpeg": ".mp3",
  "audio/wav": ".wav",
  "audio/x-wav": ".wav",
  "audio/mp4": ".m4a",
  "audio/x-m4a": ".m4a",
  "audio/flac": ".flac",
};

const ACCEPTED_EXTENSIONS = [".mp3", ".wav", ".m4a", ".flac"];
const MAX_FILE_SIZE_MB = 100;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export interface UploadAreaProps {
  /** Called with the selected file once validation passes. */
  onFileSelected: (file: File) => void;
  /** Whether an upload is currently in progress. */
  uploading?: boolean;
  /** Whether the component is disabled (e.g. while processing). */
  disabled?: boolean;
}

/**
 * Drag-and-drop file upload area with format and size validation.
 * Accepts MP3, WAV, M4A, and FLAC files up to 100 MB.
 */
export function UploadArea({
  onFileSelected,
  uploading = false,
  disabled = false,
}: UploadAreaProps): React.ReactElement {
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    // Check file extension.
    const name = file.name.toLowerCase();
    const hasValidExtension = ACCEPTED_EXTENSIONS.some((ext) =>
      name.endsWith(ext),
    );
    const hasValidMime = Object.keys(ACCEPTED_FORMATS).includes(file.type);

    if (!hasValidExtension && !hasValidMime) {
      return `Unsupported format. Please upload one of: ${ACCEPTED_EXTENSIONS.join(", ")}`;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum size is ${MAX_FILE_SIZE_MB} MB.`;
    }

    return null;
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      const error = validateFile(file);
      if (error) {
        setValidationError(error);
        return;
      }
      setValidationError(null);
      onFileSelected(file);
    },
    [validateFile, onFileSelected],
  );

  const handleDragEnter = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (!disabled) setDragActive(true);
    },
    [disabled],
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (!disabled) setDragActive(true);
    },
    [disabled],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (disabled || uploading) return;

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFile(files[0]);
      }
    },
    [disabled, uploading, handleFile],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
      // Reset so the same file can be re-selected.
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
    [handleFile],
  );

  const handleClick = useCallback(() => {
    if (!disabled && !uploading) {
      fileInputRef.current?.click();
    }
  }, [disabled, uploading]);

  const borderColor = dragActive
    ? "border-indigo-500 bg-indigo-50"
    : "border-gray-300 bg-white";

  const cursorStyle = disabled || uploading ? "cursor-not-allowed opacity-50" : "cursor-pointer";

  return (
    <div className="w-full">
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload audio file"
        className={`relative flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-lg transition-colors ${borderColor} ${cursorStyle} hover:border-indigo-400 hover:bg-indigo-50`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            handleClick();
          }
        }}
      >
        {uploading ? (
          <div className="flex flex-col items-center gap-2">
            <svg
              className="animate-spin h-8 w-8 text-indigo-600"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            <p className="text-sm text-gray-600">Uploading...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <svg
              className="h-10 w-10 text-gray-400"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
              />
            </svg>
            <p className="text-sm text-gray-600">
              <span className="font-semibold text-indigo-600">
                Click to upload
              </span>{" "}
              or drag and drop
            </p>
            <p className="text-xs text-gray-400">
              MP3, WAV, M4A, or FLAC (max {MAX_FILE_SIZE_MB} MB)
            </p>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(",")}
          onChange={handleInputChange}
          className="hidden"
          aria-hidden="true"
        />
      </div>

      {validationError && (
        <p className="mt-2 text-sm text-red-600" role="alert">
          {validationError}
        </p>
      )}
    </div>
  );
}
