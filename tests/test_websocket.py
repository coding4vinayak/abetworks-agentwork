"""Tests for the WebSocket manager."""

import pytest

from agentwork.server.websocket import WebSocketManager


class FakeWebSocket:
    """Fake WebSocket for testing."""

    def __init__(self, name: str = "ws"):
        self.name = name
        self.sent: list = []

    async def send_json(self, data: dict) -> None:
        self.sent.append(data)


class TestWebSocketManager:
    """Test WebSocketManager connect/disconnect/broadcast/send_to_task."""

    @pytest.fixture
    def manager(self):
        return WebSocketManager()

    @pytest.mark.asyncio
    async def test_connect_adds_to_all(self, manager):
        """connect without task_id subscribes to 'all'."""
        ws = FakeWebSocket("ws1")
        await manager.connect(ws)
        assert manager.active_connections == 1

    @pytest.mark.asyncio
    async def test_connect_with_task_id(self, manager):
        """connect with task_id subscribes to that task."""
        ws = FakeWebSocket("ws1")
        await manager.connect(ws, task_id="task-123")
        assert manager.active_connections == 1

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, manager):
        """disconnect removes the websocket from all lists."""
        ws = FakeWebSocket("ws1")
        await manager.connect(ws)
        await manager.connect(ws, task_id="task-123")
        await manager.disconnect(ws)
        assert manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self, manager):
        """broadcast sends event to all connected clients."""
        ws1 = FakeWebSocket("ws1")
        ws2 = FakeWebSocket("ws2")
        await manager.connect(ws1)
        await manager.connect(ws2)
        await manager.broadcast({"type": "test"})
        assert {"type": "test"} in ws1.sent
        assert {"type": "test"} in ws2.sent

    @pytest.mark.asyncio
    async def test_send_to_task_routes_correctly(self, manager):
        """send_to_task only sends to clients subscribed to that task."""
        ws1 = FakeWebSocket("ws1")
        ws2 = FakeWebSocket("ws2")
        await manager.connect(ws1, task_id="task-A")
        await manager.connect(ws2, task_id="task-B")
        await manager.send_to_task("task-A", {"data": "hello"})
        assert {"data": "hello"} in ws1.sent
        assert len(ws2.sent) == 0

    @pytest.mark.asyncio
    async def test_active_connections_count(self, manager):
        """active_connections returns total unique clients."""
        ws1 = FakeWebSocket("ws1")
        ws2 = FakeWebSocket("ws2")
        await manager.connect(ws1)
        await manager.connect(ws2, task_id="task-1")
        # ws1 in "all", ws2 in "task-1"
        assert manager.active_connections == 2

    @pytest.mark.asyncio
    async def test_multiple_subscriptions_counted_once(self, manager):
        """A client subscribed to multiple tasks counts as one connection."""
        ws = FakeWebSocket("ws1")
        await manager.connect(ws)
        await manager.connect(ws, task_id="task-1")
        # Same websocket in two lists, but active_connections counts unique
        assert manager.active_connections == 1

    @pytest.mark.asyncio
    async def test_send_to_task_no_subscribers(self, manager):
        """send_to_task with no subscribers does not raise."""
        await manager.send_to_task("nonexistent-task", {"data": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_with_failing_websocket(self, manager):
        """broadcast handles websocket send failures gracefully."""

        class FailingWS:
            async def send_json(self, data):
                raise RuntimeError("connection closed")

        ws_ok = FakeWebSocket("ws_ok")
        ws_fail = FailingWS()
        await manager.connect(ws_ok)
        await manager.connect(ws_fail)
        await manager.broadcast({"type": "event"})
        # The successful websocket should still receive it
        assert {"type": "event"} in ws_ok.sent
