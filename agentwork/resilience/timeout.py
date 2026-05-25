"""Timeout wrapper with configurable duration."""

from __future__ import annotations

import asyncio
import logging
import signal
import threading
from typing import Any, Callable, Optional

from agentwork.core.exceptions import TimeoutError

logger = logging.getLogger(__name__)


class Timeout:
    """Wraps function execution with a timeout.

    For sync execution, uses threading. For async, uses asyncio.wait_for.
    """

    def __init__(self, seconds: float) -> None:
        if seconds <= 0:
            raise ValueError("Timeout seconds must be positive")
        self.seconds = seconds

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute a function with a timeout (sync).

        Uses a thread to run the function and waits for the result.
        """
        result_container: dict[str, Any] = {}
        exception_container: dict[str, Optional[Exception]] = {"exc": None}

        def _target() -> None:
            try:
                result_container["result"] = func(*args, **kwargs)
            except Exception as e:
                exception_container["exc"] = e

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()
        thread.join(timeout=self.seconds)

        if thread.is_alive():
            logger.warning(
                "Timeout of %.1fs exceeded for %s",
                self.seconds,
                func.__name__ if hasattr(func, "__name__") else str(func),
            )
            raise TimeoutError(
                f"Operation timed out after {self.seconds}s",
                timeout_seconds=self.seconds,
            )

        if exception_container["exc"] is not None:
            raise exception_container["exc"]

        return result_container.get("result")

    async def execute_async(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute an async function with a timeout."""
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs), timeout=self.seconds
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(
                "Async timeout of %.1fs exceeded for %s",
                self.seconds,
                func.__name__ if hasattr(func, "__name__") else str(func),
            )
            raise TimeoutError(
                f"Async operation timed out after {self.seconds}s",
                timeout_seconds=self.seconds,
            )
