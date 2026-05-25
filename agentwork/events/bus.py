"""EventBus - pub/sub messaging with wildcard subscriptions, history, and replay."""

import asyncio
import logging
from collections import defaultdict
from fnmatch import fnmatch
from typing import Callable, Dict, List, Optional, Set

from agentwork.events.event_types import BaseEvent

logger = logging.getLogger(__name__)


class EventBus:
    """Pub/sub event bus with pattern matching, bounded history, and replay."""

    def __init__(self, max_history_size: int = 1000) -> None:
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._history: List[BaseEvent] = []
        self._max_history_size = max_history_size

    def subscribe(self, event_pattern: str, handler: Callable) -> None:
        """Register a handler for an event pattern (exact or wildcard)."""
        if handler not in self._subscribers[event_pattern]:
            self._subscribers[event_pattern].append(handler)

    def unsubscribe(self, event_pattern: str, handler: Callable) -> None:
        """Remove a handler from a pattern subscription."""
        handlers = self._subscribers.get(event_pattern, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: BaseEvent) -> None:
        """Publish an event synchronously. Errors in handlers are logged, never propagated."""
        self._store_event(event)
        handlers = self._matching_handlers(event.event_type)
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    # For async handlers in sync publish, attempt to run them
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None
                    if loop and loop.is_running():
                        # Schedule as fire-and-forget task on the running loop
                        loop.create_task(handler(event))
                    else:
                        asyncio.run(handler(event))
                else:
                    handler(event)
            except Exception as exc:
                logger.error(
                    "Handler %s raised for event %s: %s",
                    getattr(handler, "__name__", handler),
                    event.event_type,
                    exc,
                )

    async def publish_async(self, event: BaseEvent) -> None:
        """Publish an event asynchronously. Awaits async handlers, calls sync handlers normally."""
        self._store_event(event)
        handlers = self._matching_handlers(event.event_type)
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as exc:
                logger.error(
                    "Handler %s raised for event %s: %s",
                    getattr(handler, "__name__", handler),
                    event.event_type,
                    exc,
                )

    def get_history(self, event_pattern: Optional[str] = None) -> List[BaseEvent]:
        """Return events from history, optionally filtered by pattern."""
        if event_pattern is None:
            return list(self._history)
        return [e for e in self._history if fnmatch(e.event_type, event_pattern)]

    def replay(self, event_pattern: Optional[str] = None, handler: Callable = None) -> None:
        """Replay historical events matching a pattern to a handler."""
        if handler is None:
            return
        events = self.get_history(event_pattern)
        for event in events:
            try:
                if asyncio.iscoroutinefunction(handler):
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None
                    if loop and loop.is_running():
                        # Schedule as fire-and-forget task on the running loop
                        loop.create_task(handler(event))
                    else:
                        asyncio.run(handler(event))
                else:
                    handler(event)
            except Exception as exc:
                logger.error(
                    "Replay handler %s raised for event %s: %s",
                    getattr(handler, "__name__", handler),
                    event.event_type,
                    exc,
                )

    def clear(self) -> None:
        """Clear all subscriptions and history."""
        self._subscribers.clear()
        self._history.clear()

    def _store_event(self, event: BaseEvent) -> None:
        """Store event in bounded history."""
        self._history.append(event)
        if len(self._history) > self._max_history_size:
            self._history = self._history[-self._max_history_size:]

    def _matching_handlers(self, event_type: str) -> List[Callable]:
        """Get all handlers whose patterns match the given event_type."""
        matched: List[Callable] = []
        seen: Set[int] = set()
        for pattern, handlers in self._subscribers.items():
            if fnmatch(event_type, pattern):
                for handler in handlers:
                    handler_id = id(handler)
                    if handler_id not in seen:
                        seen.add(handler_id)
                        matched.append(handler)
        return matched
