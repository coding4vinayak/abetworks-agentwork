"""Task result types for agent execution."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


class ResultStatus(str, Enum):
    """Status of a task execution result."""

    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    PARTIAL = "partial"


class TaskResult(BaseModel):
    """Result of a task or tool execution.

    Captures the outcome, output data, error information, and execution metadata.
    Never raises on partial failure - always returns structured result.
    """

    status: ResultStatus = ResultStatus.SUCCESS
    output: Any = None
    error: Optional[str] = None
    error_details: Optional[Any] = None
    attempts: int = 1
    duration_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    partial_results: List[Any] = Field(default_factory=list)
    task_id: Optional[str] = None

    @property
    def success(self) -> bool:
        """Check if the result is a success."""
        return self.status == ResultStatus.SUCCESS

    @property
    def failed(self) -> bool:
        """Check if the result is a failure."""
        return self.status == ResultStatus.FAILURE

    @classmethod
    def ok(cls, output: Any = None, **kwargs: Any) -> TaskResult:
        """Create a successful result."""
        return cls(status=ResultStatus.SUCCESS, output=output, **kwargs)

    @classmethod
    def fail(
        cls, error: str, error_details: Optional[Any] = None, **kwargs: Any
    ) -> TaskResult:
        """Create a failure result."""
        return cls(
            status=ResultStatus.FAILURE,
            error=error,
            error_details=error_details,
            **kwargs,
        )

    @classmethod
    def partial(
        cls,
        output: Any = None,
        error: Optional[str] = None,
        partial_results: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> TaskResult:
        """Create a partial result (some steps succeeded, some failed)."""
        return cls(
            status=ResultStatus.PARTIAL,
            output=output,
            error=error,
            partial_results=partial_results or [],
            **kwargs,
        )
