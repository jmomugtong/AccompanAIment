/**
 * WebSocket client for receiving real-time generation progress updates.
 *
 * Connects to the backend WebSocket endpoint at /songs/{id}/status
 * and dispatches typed progress events to registered listeners.
 */

export interface ProgressUpdate {
  /** Current pipeline step (e.g. "uploading", "extracting", "generating", "rendering", "complete", "error"). */
  step: string;
  /** Completion percentage for the current step (0-100). */
  percent: number;
  /** Human-readable description of what is happening now. */
  message: string;
  /** Estimated seconds remaining, or null if unknown. */
  eta_seconds: number | null;
  /** Error detail when step is "error". */
  error?: string;
}

export type ProgressListener = (update: ProgressUpdate) => void;

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:8000";

/**
 * Manages a WebSocket connection for a single song's generation progress.
 *
 * Usage:
 *   const ws = new GenerationWebSocket(songId);
 *   ws.onProgress((update) => { ... });
 *   ws.connect();
 *   // later:
 *   ws.disconnect();
 */
export class GenerationWebSocket {
  private songId: string;
  private socket: WebSocket | null = null;
  private listeners: ProgressListener[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;

  constructor(songId: string) {
    this.songId = songId;
  }

  /**
   * Register a callback that fires on every progress update.
   * Returns an unsubscribe function.
   */
  onProgress(listener: ProgressListener): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  /**
   * Open the WebSocket connection to the server.
   */
  connect(): void {
    this.intentionalClose = false;
    this.reconnectAttempts = 0;
    this.openSocket();
  }

  /**
   * Gracefully close the connection. No automatic reconnect will occur.
   */
  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  /** Whether the socket is currently open. */
  get connected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  // -- private helpers ---------------------------------------------------

  private openSocket(): void {
    const url = `${WS_BASE_URL}/songs/${this.songId}/status`;
    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event: MessageEvent) => {
      try {
        const update: ProgressUpdate = JSON.parse(event.data as string);
        this.dispatch(update);
      } catch {
        // Non-JSON message; ignore.
      }
    };

    this.socket.onerror = () => {
      // The close handler takes care of reconnection.
    };

    this.socket.onclose = () => {
      this.socket = null;
      if (!this.intentionalClose) {
        this.scheduleReconnect();
      }
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.dispatch({
        step: "error",
        percent: 0,
        message: "Lost connection to server. Please refresh the page.",
        eta_seconds: null,
        error: "WebSocket reconnection failed after maximum attempts.",
      });
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts += 1;

    this.reconnectTimer = setTimeout(() => {
      this.openSocket();
    }, delay);
  }

  private dispatch(update: ProgressUpdate): void {
    for (const listener of this.listeners) {
      try {
        listener(update);
      } catch {
        // Listener errors must not break the dispatch loop.
      }
    }
  }
}
