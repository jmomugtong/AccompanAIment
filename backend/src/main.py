"""FastAPI application entrypoint."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.api.websocket import manager
from src.config import settings

app = FastAPI(
    title="AccompanAIment",
    description="AI-Powered Piano Accompaniment Generator",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routes
app.include_router(router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.websocket("/songs/{song_id}/status")
async def websocket_status(websocket: WebSocket, song_id: str) -> None:
    """WebSocket endpoint for real-time song processing progress.

    Clients connect to receive progress updates for a specific song.
    Sends a connection_established message on connect, then forwards
    progress updates as they arrive from the processing pipeline.
    """
    await manager.connect(song_id, websocket)
    try:
        await websocket.send_json(
            {"type": "connection_established", "song_id": song_id}
        )
        while True:
            # Keep connection alive; wait for client messages (e.g. ping)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(song_id, websocket)
