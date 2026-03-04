/**
 * Supported audio file extensions for upload.
 */
export const SUPPORTED_FORMATS = [".mp3", ".wav", ".m4a", ".flac"] as const;

/**
 * Format a duration in seconds as a "m:ss" string.
 *
 * @param seconds - Total duration in seconds.
 * @returns Formatted string, e.g. 125 -> "2:05".
 */
export function formatDuration(seconds: number): string {
  const totalSeconds = Math.max(0, Math.floor(seconds));
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

/**
 * Format a file size in bytes to a human-readable string.
 *
 * @param bytes - File size in bytes.
 * @returns Formatted string, e.g. 1048576 -> "1.0 MB".
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 0) {
    return "0 B";
  }

  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

/**
 * Check whether a filename has a supported audio format extension.
 *
 * @param filename - The filename to validate.
 * @returns True if the extension is one of the supported audio formats.
 */
export function isValidAudioFormat(filename: string): boolean {
  const lower = filename.toLowerCase();
  return SUPPORTED_FORMATS.some((ext) => lower.endsWith(ext));
}
