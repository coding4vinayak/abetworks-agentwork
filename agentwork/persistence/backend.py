"""Abstract storage backend for persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save_result(self, task_id: str, result: dict) -> None:
        """Save a task result."""
        ...

    @abstractmethod
    def get_result(self, task_id: str) -> Optional[dict]:
        """Retrieve a task result by ID."""
        ...

    @abstractmethod
    def list_results(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """List task results with pagination."""
        ...

    @abstractmethod
    def delete_result(self, task_id: str) -> bool:
        """Delete a task result. Returns True if deleted."""
        ...

    @abstractmethod
    def save_knowledge(self, key: str, value: Any) -> None:
        """Save a knowledge entry."""
        ...

    @abstractmethod
    def get_knowledge(self, key: str) -> Optional[Any]:
        """Retrieve a knowledge entry by key."""
        ...

    @abstractmethod
    def delete_knowledge(self, key: str) -> bool:
        """Delete a knowledge entry. Returns True if deleted."""
        ...
