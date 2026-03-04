"""WebSocket manager for real-time progress tracking."""

from fastapi import WebSocket


class WebSocketManager:
    """Manages WebSocket connections for song processing progress updates.

    Tracks active connections per song_id, allowing multiple clients to
    receive real-time progress updates for the same song. Handles
    connection cleanup on disconnect and broken connections.
    """

    def __init__(self) -> None:
        """Initialize the manager with an empty connection store."""
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, song_id: str, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection for a song.

        Args:
            song_id: The song identifier to associate with this connection.
            websocket: The WebSocket connection to register.
        """
        await websocket.accept()
        if song_id not in self.active_connections:
            self.active_connections[song_id] = []
        self.active_connections[song_id].append(websocket)

    def disconnect(self, song_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection for a song.

        Safely handles the case where the song_id or websocket is not found.
        Cleans up the song_id entry if no connections remain.

        Args:
            song_id: The song identifier associated with the connection.
            websocket: The WebSocket connection to remove.
        """
        if song_id not in self.active_connections:
            return
        connections = self.active_connections[song_id]
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            del self.active_connections[song_id]

    async def send_progress(
        self,
        song_id: str,
        progress: int,
        step: str,
        eta_seconds: int | None = None,
    ) -> None:
        """Send a progress update to all connected clients for a song.

        Sends a JSON message with song_id, progress percentage, current step,
        and optional ETA. Automatically removes broken connections.

        Args:
            song_id: The song identifier to send progress for.
            progress: Progress percentage (0-100).
            step: Current processing step name.
            eta_seconds: Estimated seconds remaining (optional).
        """
        if song_id not in self.active_connections:
            return

        message = {
            "song_id": song_id,
            "progress": progress,
            "step": step,
            "eta_seconds": eta_seconds,
        }

        broken: list[WebSocket] = []
        for ws in self.active_connections[song_id]:
            try:
                await ws.send_json(message)
            except Exception:
                broken.append(ws)

        for ws in broken:
            self.disconnect(song_id, ws)


# Module-level manager instance shared across the application
manager = WebSocketManager()
