"""WebSocket support for real-time event streaming."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


class WebSocketManager:
    """Manages WebSocket connections and routes events by task_id.

    Enforces a maximum connection limit. New connections are rejected
    when max_connections is reached.
    """

    def __init__(self, max_connections: int = 1000) -> None:
        self._connections: Dict[str, List[Any]] = {}
        self._max_connections = max_connections

    async def connect(self, websocket: Any, task_id: Optional[str] = None) -> bool:
        """Add a WebSocket connection, optionally subscribing to a task_id.

        Returns True if the connection was accepted, False if rejected
        due to the connection limit being reached.
        """
        # Check limit only for truly new connections (not re-subscriptions)
        key = task_id if task_id else "all"
        is_new = not self._is_connected(websocket)
        if is_new and self.active_connections >= self._max_connections:
            return False

        if key not in self._connections:
            self._connections[key] = []
        if websocket not in self._connections[key]:
            self._connections[key].append(websocket)
        return True

    async def disconnect(self, websocket: Any) -> None:
        """Remove a WebSocket connection from all subscription lists."""
        for key in list(self._connections.keys()):
            if websocket in self._connections[key]:
                self._connections[key].remove(websocket)
            if not self._connections[key]:
                del self._connections[key]

    async def broadcast(self, event: dict) -> None:
        """Send an event to all connected clients."""
        all_websockets: set = set()
        for ws_list in self._connections.values():
            for ws in ws_list:
                all_websockets.add(ws)

        for ws in all_websockets:
            try:
                await ws.send_json(event)
            except Exception:
                pass

    async def send_to_task(self, task_id: str, event: dict) -> None:
        """Send an event only to clients subscribed to a specific task_id."""
        subscribers = self._connections.get(task_id, [])
        for ws in subscribers:
            try:
                await ws.send_json(event)
            except Exception:
                pass

    @property
    def active_connections(self) -> int:
        """Total number of connected clients."""
        all_websockets: set = set()
        for ws_list in self._connections.values():
            for ws in ws_list:
                all_websockets.add(ws)
        return len(all_websockets)

    def _is_connected(self, websocket: Any) -> bool:
        """Check if a websocket is already tracked in any subscription list."""
        for ws_list in self._connections.values():
            if websocket in ws_list:
                return True
        return False


def add_websocket_routes(app: Any, manager: WebSocketManager) -> None:
    """Add WebSocket endpoint to a FastAPI application."""
    if not HAS_FASTAPI:
        return

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    if "subscribe" in message:
                        task_id = message["subscribe"]
                        await manager.connect(websocket, task_id)
                except (json.JSONDecodeError, KeyError):
                    pass
        except WebSocketDisconnect:
            await manager.disconnect(websocket)
        except Exception:
            await manager.disconnect(websocket)
