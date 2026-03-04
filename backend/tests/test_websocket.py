"""Tests for WebSocket progress tracking and connection management."""

import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from src.main import app


@pytest.fixture
def client():
    """Synchronous test client for WebSocket testing."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# WebSocketManager unit tests
# ---------------------------------------------------------------------------


class TestWebSocketManagerConnectionStorage:
    """Test that WebSocketManager correctly stores and tracks connections."""

    def test_manager_starts_with_no_connections(self):
        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_connect_stores_connection(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)
        await manager.connect("song-1", ws)
        assert "song-1" in manager.active_connections
        assert ws in manager.active_connections["song-1"]

    @pytest.mark.asyncio
    async def test_connect_calls_accept(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)
        await manager.connect("song-1", ws)
        ws.accept.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_multiple_connections_same_song(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        await manager.connect("song-1", ws1)
        await manager.connect("song-1", ws2)
        assert len(manager.active_connections["song-1"]) == 2
        assert ws1 in manager.active_connections["song-1"]
        assert ws2 in manager.active_connections["song-1"]

    @pytest.mark.asyncio
    async def test_connections_for_different_songs_are_separate(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        await manager.connect("song-1", ws1)
        await manager.connect("song-2", ws2)
        assert len(manager.active_connections["song-1"]) == 1
        assert len(manager.active_connections["song-2"]) == 1


class TestWebSocketManagerDisconnect:
    """Test that disconnect properly removes connections."""

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)
        await manager.connect("song-1", ws)
        manager.disconnect("song-1", ws)
        assert ws not in manager.active_connections.get("song-1", [])

    @pytest.mark.asyncio
    async def test_disconnect_removes_empty_song_entry(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)
        await manager.connect("song-1", ws)
        manager.disconnect("song-1", ws)
        assert "song-1" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_keeps_other_connections_for_same_song(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        await manager.connect("song-1", ws1)
        await manager.connect("song-1", ws2)
        manager.disconnect("song-1", ws1)
        assert len(manager.active_connections["song-1"]) == 1
        assert ws2 in manager.active_connections["song-1"]

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_song_does_not_raise(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)
        # Should not raise
        manager.disconnect("nonexistent", ws)

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_ws_does_not_raise(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        await manager.connect("song-1", ws1)
        # Disconnecting a websocket that is not connected should not raise
        manager.disconnect("song-1", ws2)


class TestWebSocketManagerSendProgress:
    """Test that send_progress formats and sends messages correctly."""

    @pytest.mark.asyncio
    async def test_send_progress_sends_json_message(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)
        await manager.connect("song-1", ws)

        await manager.send_progress("song-1", progress=50, step="extracting_melody")

        ws.send_json.assert_awaited_once()
        sent_data = ws.send_json.call_args[0][0]
        assert sent_data["song_id"] == "song-1"
        assert sent_data["progress"] == 50
        assert sent_data["step"] == "extracting_melody"

    @pytest.mark.asyncio
    async def test_send_progress_includes_eta_seconds(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)
        await manager.connect("song-1", ws)

        await manager.send_progress(
            "song-1", progress=75, step="rendering_audio", eta_seconds=30
        )

        sent_data = ws.send_json.call_args[0][0]
        assert sent_data["eta_seconds"] == 30

    @pytest.mark.asyncio
    async def test_send_progress_eta_defaults_to_none(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)
        await manager.connect("song-1", ws)

        await manager.send_progress("song-1", progress=25, step="uploading")

        sent_data = ws.send_json.call_args[0][0]
        assert sent_data["eta_seconds"] is None

    @pytest.mark.asyncio
    async def test_send_progress_to_multiple_clients(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        await manager.connect("song-1", ws1)
        await manager.connect("song-1", ws2)

        await manager.send_progress("song-1", progress=100, step="complete")

        ws1.send_json.assert_awaited_once()
        ws2.send_json.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_progress_to_nonexistent_song_does_not_raise(self):
        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        # Should not raise
        await manager.send_progress("nonexistent", progress=50, step="test")

    @pytest.mark.asyncio
    async def test_send_progress_handles_broken_connection(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)
        ws.send_json.side_effect = Exception("Connection closed")
        await manager.connect("song-1", ws)

        # Should not raise despite the broken connection
        await manager.send_progress("song-1", progress=50, step="test")

    @pytest.mark.asyncio
    async def test_send_progress_removes_broken_connection(self):
        from unittest.mock import AsyncMock

        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)
        ws.send_json.side_effect = Exception("Connection closed")
        await manager.connect("song-1", ws)

        await manager.send_progress("song-1", progress=50, step="test")

        # Broken connection should have been removed
        assert ws not in manager.active_connections.get("song-1", [])


# ---------------------------------------------------------------------------
# WebSocket endpoint integration test
# ---------------------------------------------------------------------------


class TestWebSocketEndpoint:
    """Test the actual WebSocket /songs/{song_id}/status endpoint."""

    def test_websocket_connects_successfully(self, client):
        with client.websocket_connect("/songs/test-song-id/status") as ws:
            # Connection should be established; just verify no error
            pass

    def test_websocket_receives_connection_ack(self, client):
        with client.websocket_connect("/songs/test-song-id/status") as ws:
            data = ws.receive_json()
            assert data["type"] == "connection_established"
            assert data["song_id"] == "test-song-id"
