import axios, { AxiosInstance, AxiosResponse } from "axios";

/**
 * Shape of an uploaded song record returned by the API.
 */
export interface Song {
  id: string;
  filename: string;
  duration_seconds: number;
  sample_rate: number;
  created_at: string;
}

/**
 * A single pitch frame from CREPE melody extraction.
 */
export interface MelodyFrame {
  time: number;
  frequency: number;
  confidence: number;
  note_name: string;
}

/**
 * Full melody extraction result.
 */
export interface MelodyData {
  song_id: string;
  frames: MelodyFrame[];
  average_confidence: number;
}

/**
 * Parameters required to trigger piano accompaniment generation.
 */
export interface GeneratePianoRequest {
  chord_progression: string;
  style: string;
  tempo?: number;
  time_signature?: string;
}

/**
 * A generation record returned by the API.
 */
export interface Generation {
  id: string;
  song_id: string;
  status: "pending" | "processing" | "complete" | "error";
  style: string;
  chord_progression: string;
  tempo: number;
  time_signature: string;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}

/**
 * Feedback submission payload.
 */
export interface FeedbackRequest {
  overall_rating: number;
  harmony_rating: number;
  rhythm_rating: number;
  style_rating: number;
  comments?: string;
}

/**
 * Feedback record returned by the API.
 */
export interface FeedbackResponse {
  id: string;
  generation_id: string;
  overall_rating: number;
  harmony_rating: number;
  rhythm_rating: number;
  style_rating: number;
  comments: string | null;
  created_at: string;
}

/**
 * Available download formats for a generation.
 */
export type DownloadFormat = "midi" | "audio" | "sheet";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

/**
 * Create a configured Axios instance pointing at the AccompanAIment API.
 */
function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      "Content-Type": "application/json",
    },
  });

  // Attach JWT token to every request when available.
  client.interceptors.request.use((config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Intercept 401 responses and clear stale tokens.
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        localStorage.removeItem("auth_token");
      }
      return Promise.reject(error);
    },
  );

  return client;
}

const apiClient = createApiClient();

/**
 * Upload an audio file (MP3, WAV, M4A, FLAC).
 * Max size enforced server-side: 100 MB.
 */
export async function uploadSong(file: File): Promise<Song> {
  const formData = new FormData();
  formData.append("file", file);

  const response: AxiosResponse<Song> = await apiClient.post(
    "/songs/upload",
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000, // uploads may be large
    },
  );
  return response.data;
}

/**
 * Retrieve extracted melody data for a song.
 */
export async function getMelody(songId: string): Promise<MelodyData> {
  const response: AxiosResponse<MelodyData> = await apiClient.get(
    `/songs/${songId}/melody`,
  );
  return response.data;
}

/**
 * Trigger piano accompaniment generation.
 * Returns 202 Accepted with a Generation record.
 */
export async function generatePiano(
  songId: string,
  params: GeneratePianoRequest,
): Promise<Generation> {
  const response: AxiosResponse<Generation> = await apiClient.post(
    `/songs/${songId}/generate-piano`,
    params,
  );
  return response.data;
}

/**
 * Get all generations for a song, or all generations if no songId is provided.
 */
export async function getGenerations(songId?: string): Promise<Generation[]> {
  const url = songId ? `/songs/${songId}/generations` : "/generations";
  const response: AxiosResponse<Generation[]> = await apiClient.get(url);
  return response.data;
}

/**
 * Download a generation artifact in the specified format.
 * Returns a Blob suitable for saving via the browser.
 */
export async function downloadGeneration(
  songId: string,
  generationId: string,
  format: DownloadFormat,
): Promise<Blob> {
  const response = await apiClient.get(
    `/songs/${songId}/generations/${generationId}/download`,
    {
      params: { format },
      responseType: "blob",
    },
  );
  return response.data as Blob;
}

/**
 * Submit multi-dimensional feedback for a generation.
 */
export async function submitFeedback(
  generationId: string,
  feedback: FeedbackRequest,
): Promise<FeedbackResponse> {
  const response: AxiosResponse<FeedbackResponse> = await apiClient.post(
    `/generations/${generationId}/feedback`,
    feedback,
  );
  return response.data;
}

export { apiClient };
