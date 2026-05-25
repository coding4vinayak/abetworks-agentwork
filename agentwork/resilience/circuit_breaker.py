"""Circuit breaker pattern to prevent cascade failures."""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Any, Callable, Optional

from agentwork.core.exceptions import AgentError

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """State of the circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker that tracks failures and prevents cascade failures.

    - CLOSED: Normal operation, requests pass through.
    - OPEN: Too many failures, requests are rejected immediately.
    - HALF_OPEN: After cooldown, allow one request to test recovery.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: float = 60.0,
        success_threshold: int = 2,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.success_threshold = success_threshold
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None

    @property
    def state(self) -> CircuitState:
        """Get the current circuit state, checking for cooldown transition."""
        if self._state == CircuitState.OPEN:
            if (
                self._last_failure_time is not None
                and time.time() - self._last_failure_time >= self.cooldown_seconds
            ):
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                logger.info("Circuit breaker transitioned to HALF_OPEN")
        return self._state

    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute a function through the circuit breaker."""
        current_state = self.state

        if current_state == CircuitState.OPEN:
            raise AgentError(
                "Circuit breaker is OPEN - requests are being rejected",
                details={
                    "failure_count": self._failure_count,
                    "cooldown_remaining": self.cooldown_seconds
                    - (time.time() - (self._last_failure_time or 0)),
                },
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Record a successful execution."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info("Circuit breaker transitioned to CLOSED")
        else:
            self._failure_count = 0

    def _on_failure(self) -> None:
        """Record a failed execution."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning("Circuit breaker transitioned back to OPEN from HALF_OPEN")
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker transitioned to OPEN after %d failures",
                self._failure_count,
            )

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
