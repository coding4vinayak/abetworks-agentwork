"""Configurable retry policy with exponential backoff and jitter."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Optional, Tuple, Type

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    RetryError,
)

from agentwork.core.exceptions import RetryableError

logger = logging.getLogger(__name__)


class RetryPolicy:
    """Configurable retry policy using tenacity under the hood.

    Supports exponential backoff with jitter, configurable max attempts,
    and filtering by exception type.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        backoff_base: float = 1.0,
        backoff_max: float = 60.0,
        jitter: float = 1.0,
        retry_on: Optional[Tuple[Type[Exception], ...]] = None,
        on_retry: Optional[Callable[..., None]] = None,
    ) -> None:
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        self.jitter = jitter
        self.retry_on = retry_on or (Exception,)
        self.on_retry = on_retry

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute a function with retry logic applied.

        Returns the result of the function or raises if all retries exhausted.
        """

        @retry(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential_jitter(
                initial=self.backoff_base,
                max=self.backoff_max,
                jitter=self.jitter,
            ),
            retry=retry_if_exception_type(self.retry_on),
            reraise=False,
        )
        def _inner() -> Any:
            try:
                return func(*args, **kwargs)
            except self.retry_on as e:
                if self.on_retry:
                    self.on_retry(e)
                logger.warning(
                    "Retry triggered for %s: %s", func.__name__, str(e)
                )
                raise

        try:
            return _inner()
        except RetryError as e:
            last_exc = e.last_attempt.exception() if e.last_attempt else None
            raise RetryableError(
                f"All {self.max_attempts} retry attempts exhausted for {func.__name__}",
                attempts_remaining=0,
                details=str(last_exc),
            ) from e

    async def execute_async(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute an async function with retry logic applied."""
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                result = await func(*args, **kwargs)
                return result
            except self.retry_on as e:
                last_exception = e
                if self.on_retry:
                    self.on_retry(e)
                logger.warning(
                    "Async retry attempt %d/%d for %s: %s",
                    attempt,
                    self.max_attempts,
                    func.__name__,
                    str(e),
                )
                if attempt < self.max_attempts:
                    wait_time = min(
                        self.backoff_base * (2 ** (attempt - 1)),
                        self.backoff_max,
                    )
                    await asyncio.sleep(wait_time)

        raise RetryableError(
            f"All {self.max_attempts} async retry attempts exhausted for {func.__name__}",
            attempts_remaining=0,
            details=str(last_exception),
        )
