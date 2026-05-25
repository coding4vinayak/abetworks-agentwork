"""Comprehensive tests for the EventBus and event types."""

import asyncio
from datetime import datetime, timezone

import pytest

from agentwork.events import (
    AgentHealthChanged,
    BaseEvent,
    CustomEvent,
    EventBus,
    TaskCompleted,
    TaskFailed,
    TaskStarted,
)


class TestBaseEvent:
    """Tests for BaseEvent and typed event creation."""

    def test_base_event_auto_generates_event_id(self):
        event = BaseEvent()
        assert event.event_id
        assert len(event.event_id) == 36  # UUID format

    def test_base_event_auto_generates_timestamp(self):
        event = BaseEvent()
        assert isinstance(event.timestamp, datetime)
        assert event.timestamp.tzinfo is not None

    def test_base_event_default_event_type(self):
        event = BaseEvent()
        assert event.event_type == "base"

    def test_task_started_event(self):
        event = TaskStarted(task_id="t1", agent_name="agent-a")
        assert event.event_type == "task.started"
        assert event.task_id == "t1"
        assert event.agent_name == "agent-a"

    def test_task_completed_event(self):
        event = TaskCompleted(task_id="t2", output={"result": 42})
        assert event.event_type == "task.completed"
        assert event.task_id == "t2"
        assert event.output == {"result": 42}
        assert event.agent_name == ""

    def test_task_failed_event(self):
        event = TaskFailed(task_id="t3", error="something broke")
        assert event.event_type == "task.failed"
        assert event.error == "something broke"

    def test_agent_health_changed_event(self):
        event = AgentHealthChanged(agent_name="worker-1", status="unhealthy")
        assert event.event_type == "agent.health_changed"
        assert event.agent_name == "worker-1"
        assert event.status == "unhealthy"

    def test_custom_event_configurable_type(self):
        event = CustomEvent(event_type="my.custom.event", data={"key": "value"})
        assert event.event_type == "my.custom.event"
        assert event.data == {"key": "value"}

    def test_events_have_unique_ids(self):
        e1 = BaseEvent()
        e2 = BaseEvent()
        assert e1.event_id != e2.event_id


class TestEventBus:
    """Tests for EventBus subscribe, publish, history, and replay."""

    def test_subscribe_and_publish_basic(self):
        bus = EventBus()
        received = []
        bus.subscribe("task.started", lambda e: received.append(e))
        event = TaskStarted(task_id="t1")
        bus.publish(event)
        assert len(received) == 1
        assert received[0].task_id == "t1"

    def test_wildcard_matching(self):
        bus = EventBus()
        received = []
        bus.subscribe("task.*", lambda e: received.append(e))
        bus.publish(TaskStarted(task_id="t1"))
        bus.publish(TaskCompleted(task_id="t2"))
        bus.publish(AgentHealthChanged(agent_name="a", status="ok"))
        assert len(received) == 2

    def test_star_matches_everything(self):
        bus = EventBus()
        received = []
        bus.subscribe("*", lambda e: received.append(e))
        bus.publish(TaskStarted(task_id="t1"))
        bus.publish(AgentHealthChanged(agent_name="a", status="ok"))
        assert len(received) == 2

    def test_multiple_subscribers_same_pattern(self):
        bus = EventBus()
        r1, r2 = [], []
        bus.subscribe("task.started", lambda e: r1.append(e))
        bus.subscribe("task.started", lambda e: r2.append(e))
        bus.publish(TaskStarted(task_id="t1"))
        assert len(r1) == 1
        assert len(r2) == 1

    def test_unsubscribe(self):
        bus = EventBus()
        received = []
        handler = lambda e: received.append(e)
        bus.subscribe("task.started", handler)
        bus.unsubscribe("task.started", handler)
        bus.publish(TaskStarted(task_id="t1"))
        assert len(received) == 0

    def test_unsubscribe_nonexistent_handler(self):
        bus = EventBus()
        # Should not raise
        bus.unsubscribe("task.started", lambda e: None)

    def test_handler_errors_are_caught(self):
        bus = EventBus()
        received = []

        def bad_handler(e):
            raise ValueError("oops")

        def good_handler(e):
            received.append(e)

        bus.subscribe("task.started", bad_handler)
        bus.subscribe("task.started", good_handler)
        bus.publish(TaskStarted(task_id="t1"))
        # Good handler still receives the event despite bad handler failing
        assert len(received) == 1

    def test_event_history_stores_events(self):
        bus = EventBus()
        bus.publish(TaskStarted(task_id="t1"))
        bus.publish(TaskCompleted(task_id="t2"))
        history = bus.get_history()
        assert len(history) == 2

    def test_event_history_bounded(self):
        bus = EventBus(max_history_size=5)
        for i in range(10):
            bus.publish(TaskStarted(task_id=f"t{i}"))
        history = bus.get_history()
        assert len(history) == 5
        # Should keep the most recent events
        assert history[0].task_id == "t5"
        assert history[-1].task_id == "t9"

    def test_history_filtering_by_pattern(self):
        bus = EventBus()
        bus.publish(TaskStarted(task_id="t1"))
        bus.publish(TaskCompleted(task_id="t2"))
        bus.publish(AgentHealthChanged(agent_name="a", status="ok"))
        history = bus.get_history("task.*")
        assert len(history) == 2

    def test_replay_events_to_handler(self):
        bus = EventBus()
        bus.publish(TaskStarted(task_id="t1"))
        bus.publish(TaskStarted(task_id="t2"))
        bus.publish(AgentHealthChanged(agent_name="a", status="ok"))

        replayed = []
        bus.replay("task.*", handler=lambda e: replayed.append(e))
        assert len(replayed) == 2

    def test_replay_all_events(self):
        bus = EventBus()
        bus.publish(TaskStarted(task_id="t1"))
        bus.publish(AgentHealthChanged(agent_name="a", status="ok"))

        replayed = []
        bus.replay(handler=lambda e: replayed.append(e))
        assert len(replayed) == 2

    def test_clear(self):
        bus = EventBus()
        bus.subscribe("task.*", lambda e: None)
        bus.publish(TaskStarted(task_id="t1"))
        bus.clear()
        assert bus.get_history() == []
        # After clear, publish should not fire old handlers
        received = []
        bus.publish(TaskStarted(task_id="t2"))
        # No subscribers, so nothing received, but history works again
        assert len(bus.get_history()) == 1

    @pytest.mark.asyncio
    async def test_publish_async_with_async_handler(self):
        bus = EventBus()
        received = []

        async def handler(e):
            received.append(e)

        bus.subscribe("task.started", handler)
        await bus.publish_async(TaskStarted(task_id="t1"))
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_publish_async_with_sync_handler(self):
        bus = EventBus()
        received = []
        bus.subscribe("task.started", lambda e: received.append(e))
        await bus.publish_async(TaskStarted(task_id="t1"))
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_publish_async_handler_error_caught(self):
        bus = EventBus()
        received = []

        async def bad_handler(e):
            raise RuntimeError("async fail")

        bus.subscribe("task.started", bad_handler)
        bus.subscribe("task.started", lambda e: received.append(e))
        await bus.publish_async(TaskStarted(task_id="t1"))
        assert len(received) == 1

    def test_exact_pattern_does_not_match_similar(self):
        bus = EventBus()
        received = []
        bus.subscribe("task.started", lambda e: received.append(e))
        bus.publish(TaskCompleted(task_id="t1"))
        assert len(received) == 0

    def test_no_duplicate_handler_registration(self):
        bus = EventBus()
        received = []
        handler = lambda e: received.append(e)
        bus.subscribe("task.started", handler)
        bus.subscribe("task.started", handler)
        bus.publish(TaskStarted(task_id="t1"))
        assert len(received) == 1
