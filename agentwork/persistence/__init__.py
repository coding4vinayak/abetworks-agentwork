"""Persistence layer for storing task results and knowledge."""

from agentwork.persistence.backend import StorageBackend
from agentwork.persistence.sqlite_backend import SQLiteBackend

__all__ = ["StorageBackend", "SQLiteBackend"]
