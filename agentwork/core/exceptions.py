"""Exception hierarchy for the agent framework."""

from typing import Any, Optional


class AgentError(Exception):
    """Base exception for all agent framework errors."""

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ToolError(AgentError):
    """Raised when a tool execution fails."""

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, details)
        self.tool_name = tool_name


class RetryableError(AgentError):
    """Raised when an operation fails but can be retried."""

    def __init__(
        self,
        message: str,
        attempts_remaining: Optional[int] = None,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, details)
        self.attempts_remaining = attempts_remaining


class FatalError(AgentError):
    """Raised when an operation fails and should not be retried."""

    pass


class TimeoutError(AgentError):
    """Raised when an operation exceeds its time limit."""

    def __init__(
        self,
        message: str = "Operation timed out",
        timeout_seconds: Optional[float] = None,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, details)
        self.timeout_seconds = timeout_seconds
