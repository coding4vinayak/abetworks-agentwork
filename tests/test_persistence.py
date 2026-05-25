"""Tests for the persistence module."""

import pytest

from agentwork.persistence.backend import StorageBackend
from agentwork.persistence.sqlite_backend import SQLiteBackend


class TestStorageBackendABC:
    """Test that StorageBackend cannot be instantiated directly."""

    def test_cannot_instantiate(self):
        """StorageBackend is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            StorageBackend()


class TestSQLiteBackendResults:
    """Test SQLiteBackend task result operations."""

    @pytest.fixture
    def backend(self):
        return SQLiteBackend(db_path=":memory:")

    def test_save_and_get_result(self, backend):
        """save_result then get_result retrieves the same data."""
        backend.save_result("task-1", {"status": "success", "output": "hello"})
        result = backend.get_result("task-1")
        assert result is not None
        assert result["status"] == "success"
        assert result["output"] == "hello"

    def test_get_result_nonexistent(self, backend):
        """get_result returns None for unknown task_id."""
        assert backend.get_result("nonexistent") is None

    def test_save_result_overwrites(self, backend):
        """save_result with same task_id overwrites previous."""
        backend.save_result("task-1", {"version": 1})
        backend.save_result("task-1", {"version": 2})
        result = backend.get_result("task-1")
        assert result["version"] == 2

    def test_list_results_empty(self, backend):
        """list_results returns empty list when no results saved."""
        assert backend.list_results() == []

    def test_list_results_with_data(self, backend):
        """list_results returns all saved results."""
        backend.save_result("task-1", {"a": 1})
        backend.save_result("task-2", {"b": 2})
        results = backend.list_results()
        assert len(results) == 2

    def test_list_results_limit(self, backend):
        """list_results respects limit parameter."""
        for i in range(5):
            backend.save_result(f"task-{i}", {"i": i})
        results = backend.list_results(limit=3)
        assert len(results) == 3

    def test_list_results_offset(self, backend):
        """list_results respects offset parameter."""
        for i in range(5):
            backend.save_result(f"task-{i}", {"i": i})
        results = backend.list_results(limit=10, offset=3)
        assert len(results) == 2

    def test_delete_result_existing(self, backend):
        """delete_result returns True when deleting existing result."""
        backend.save_result("task-1", {"data": "test"})
        assert backend.delete_result("task-1") is True
        assert backend.get_result("task-1") is None

    def test_delete_result_nonexistent(self, backend):
        """delete_result returns False for unknown task_id."""
        assert backend.delete_result("nonexistent") is False


class TestSQLiteBackendKnowledge:
    """Test SQLiteBackend knowledge entry operations."""

    @pytest.fixture
    def backend(self):
        return SQLiteBackend(db_path=":memory:")

    def test_save_and_get_knowledge(self, backend):
        """save_knowledge then get_knowledge retrieves same data."""
        backend.save_knowledge("key1", {"info": "value"})
        result = backend.get_knowledge("key1")
        assert result == {"info": "value"}

    def test_get_knowledge_nonexistent(self, backend):
        """get_knowledge returns None for unknown key."""
        assert backend.get_knowledge("unknown") is None

    def test_save_knowledge_overwrites(self, backend):
        """save_knowledge with same key overwrites previous."""
        backend.save_knowledge("key1", "first")
        backend.save_knowledge("key1", "second")
        assert backend.get_knowledge("key1") == "second"

    def test_delete_knowledge_existing(self, backend):
        """delete_knowledge returns True when deleting existing entry."""
        backend.save_knowledge("key1", "data")
        assert backend.delete_knowledge("key1") is True
        assert backend.get_knowledge("key1") is None

    def test_delete_knowledge_nonexistent(self, backend):
        """delete_knowledge returns False for unknown key."""
        assert backend.delete_knowledge("unknown") is False

    def test_knowledge_stores_various_types(self, backend):
        """Knowledge entries can store various JSON-serializable types."""
        backend.save_knowledge("str_key", "hello")
        backend.save_knowledge("int_key", 42)
        backend.save_knowledge("list_key", [1, 2, 3])
        assert backend.get_knowledge("str_key") == "hello"
        assert backend.get_knowledge("int_key") == 42
        assert backend.get_knowledge("list_key") == [1, 2, 3]


class TestSQLiteBackendMigration:
    """Test SQLiteBackend migration functionality."""

    def test_migrate_runs_without_error(self):
        """migrate() completes without raising."""
        backend = SQLiteBackend(db_path=":memory:")
        backend.migrate()

    def test_migrate_idempotent(self):
        """Multiple migrate() calls are safe."""
        backend = SQLiteBackend(db_path=":memory:")
        backend.migrate()
        backend.migrate()
        # Should still work
        backend.save_result("task-1", {"ok": True})
        assert backend.get_result("task-1") == {"ok": True}
