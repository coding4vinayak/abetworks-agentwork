"""Base Tool class - a unit of work an agent can perform."""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import Any, Callable, Optional, Tuple, Type

from pydantic import BaseModel, ConfigDict, Field

from agentwork.core.exceptions import ToolError
from agentwork.core.result import TaskResult
from agentwork.resilience.retry import RetryPolicy

logger = logging.getLogger(__name__)


class Tool(BaseModel):
    """A unit of work that an agent can perform.

    Wraps a callable function with metadata, validation, retry policy,
    and fallback behavior. Execution always returns a TaskResult.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str = ""
    function: Callable[..., Any] = Field(exclude=True)
    retry_policy: Optional[RetryPolicy] = Field(default=None, exclude=True)
    fallback: Optional[Callable[..., Any]] = Field(default=None, exclude=True)
    tags: list[str] = Field(default_factory=list)
    timeout_seconds: Optional[float] = None

    def execute(self, *args: Any, **kwargs: Any) -> TaskResult:
        """Execute the tool with retry and fallback.

        Never raises - always returns a TaskResult.
        """
        start_time = time.time()
        attempts = 0

        try:
            if self.retry_policy:
                attempts = self.retry_policy.max_attempts
                result = self.retry_policy.execute(self.function, *args, **kwargs)
            else:
                attempts = 1
                result = self.function(*args, **kwargs)

            duration_ms = (time.time() - start_time) * 1000
            return TaskResult.ok(output=result, attempts=attempts, duration_ms=duration_ms)

        except Exception as e:
            logger.warning("Tool '%s' failed: %s", self.name, str(e))

            # Try fallback
            if self.fallback is not None:
                try:
                    fallback_result = self.fallback(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    return TaskResult.ok(
                        output=fallback_result,
                        attempts=attempts,
                        duration_ms=duration_ms,
                        metadata={"used_fallback": True},
                    )
                except Exception as fallback_err:
                    logger.error(
                        "Tool '%s' fallback also failed: %s",
                        self.name,
                        str(fallback_err),
                    )

            duration_ms = (time.time() - start_time) * 1000
            return TaskResult.fail(
                error=str(e),
                error_details={"tool": self.name, "exception_type": type(e).__name__},
                attempts=attempts,
                duration_ms=duration_ms,
            )

    async def execute_async(self, *args: Any, **kwargs: Any) -> TaskResult:
        """Execute the tool asynchronously."""
        start_time = time.time()
        attempts = 1

        try:
            if asyncio.iscoroutinefunction(self.function):
                if self.retry_policy:
                    attempts = self.retry_policy.max_attempts
                    result = await self.retry_policy.execute_async(
                        self.function, *args, **kwargs
                    )
                else:
                    result = await self.function(*args, **kwargs)
            else:
                if self.retry_policy:
                    attempts = self.retry_policy.max_attempts
                    result = self.retry_policy.execute(self.function, *args, **kwargs)
                else:
                    result = self.function(*args, **kwargs)

            duration_ms = (time.time() - start_time) * 1000
            return TaskResult.ok(output=result, attempts=attempts, duration_ms=duration_ms)

        except Exception as e:
            logger.warning("Tool '%s' async execution failed: %s", self.name, str(e))

            if self.fallback is not None:
                try:
                    if asyncio.iscoroutinefunction(self.fallback):
                        fallback_result = await self.fallback(*args, **kwargs)
                    else:
                        fallback_result = self.fallback(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    return TaskResult.ok(
                        output=fallback_result,
                        attempts=attempts,
                        duration_ms=duration_ms,
                        metadata={"used_fallback": True},
                    )
                except Exception as fallback_err:
                    logger.error(
                        "Tool '%s' async fallback failed: %s",
                        self.name,
                        str(fallback_err),
                    )

            duration_ms = (time.time() - start_time) * 1000
            return TaskResult.fail(
                error=str(e),
                error_details={"tool": self.name, "exception_type": type(e).__name__},
                attempts=attempts,
                duration_ms=duration_ms,
            )
