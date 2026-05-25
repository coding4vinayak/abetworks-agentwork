"""SQLite-based storage backend using stdlib sqlite3."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agentwork.persistence.backend import StorageBackend


class SQLiteBackend(StorageBackend):
    """SQLite storage backend for task results and knowledge entries.

    Thread-safe: uses check_same_thread=False and a threading.Lock
    around all cursor operations.
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        """Create tables if they do not exist."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )"""
            )
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS task_results (
                    task_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS knowledge_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )
            # Record schema version
            cursor.execute("SELECT version FROM schema_version")
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (self.SCHEMA_VERSION,),
                )
            self._conn.commit()

    def migrate(self) -> None:
        """Check schema version and apply any needed migrations."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT version FROM schema_version")
            row = cursor.fetchone()
            current_version = row[0] if row else 0

            # Apply migrations in order
            if current_version < 1:
                self._init_tables()

            # Future migrations would go here:
            # if current_version < 2:
            #     cursor.execute("ALTER TABLE ...")
            #     cursor.execute("UPDATE schema_version SET version = 2")

            self._conn.commit()

    def save_result(self, task_id: str, result: dict) -> None:
        """Save a task result."""
        now = datetime.now(timezone.utc).isoformat()
        data = json.dumps(result)
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO task_results (task_id, data, created_at) VALUES (?, ?, ?)",
                (task_id, data, now),
            )
            self._conn.commit()

    def get_result(self, task_id: str) -> Optional[dict]:
        """Retrieve a task result by ID."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT data FROM task_results WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def list_results(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """List task results with pagination."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT task_id, data, created_at FROM task_results ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            rows = cursor.fetchall()
        results = []
        for row in rows:
            entry = json.loads(row[1])
            entry["task_id"] = row[0]
            entry["created_at"] = row[2]
            results.append(entry)
        return results

    def delete_result(self, task_id: str) -> bool:
        """Delete a task result. Returns True if a row was deleted."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM task_results WHERE task_id = ?", (task_id,))
            self._conn.commit()
            return cursor.rowcount > 0

    def save_knowledge(self, key: str, value: Any) -> None:
        """Save a knowledge entry."""
        now = datetime.now(timezone.utc).isoformat()
        data = json.dumps(value)
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO knowledge_entries (key, value, created_at) VALUES (?, ?, ?)",
                (key, data, now),
            )
            self._conn.commit()

    def get_knowledge(self, key: str) -> Optional[Any]:
        """Retrieve a knowledge entry by key."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT value FROM knowledge_entries WHERE key = ?", (key,))
            row = cursor.fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def delete_knowledge(self, key: str) -> bool:
        """Delete a knowledge entry. Returns True if a row was deleted."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM knowledge_entries WHERE key = ?", (key,))
            self._conn.commit()
            return cursor.rowcount > 0
