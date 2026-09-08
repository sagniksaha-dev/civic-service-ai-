from typing import Any, Dict, List, Optional
from fastapi import WebSocket
from app.core.logging import logger


class ConnectionManager:
    """Manages active WebSocket connections for real-time civic chat."""

    def __init__(self):
        # Map connection_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info("WebSocket connected: %s (total active: %d)", connection_id, len(self.active_connections))

    def disconnect(self, connection_id: str) -> None:
        """Remove a disconnected WebSocket."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info("WebSocket disconnected: %s (remaining: %d)", connection_id, len(self.active_connections))

    async def send_json(self, data: Dict[str, Any], connection_id: str) -> None:
        """Send JSON payload to a specific connection."""
        websocket = self.active_connections.get(connection_id)
        if websocket:
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.warning("Failed to send message to %s: %s", connection_id, e)
                self.disconnect(connection_id)

    async def broadcast(self, data: Dict[str, Any]) -> None:
        """Broadcast JSON message to all active connections."""
        for conn_id, ws in list(self.active_connections.items()):
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(conn_id)


connection_manager = ConnectionManager()
