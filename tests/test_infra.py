"""Tests for infrastructure modules: CacheManager, KnowledgeBase, TokenAuth."""

import time
import threading

import pytest

from agentwork.infra.cache import CacheManager
from agentwork.infra.knowledge_base import KnowledgeBase
from agentwork.infra.auth import TokenAuth, InvalidTokenError


# ============================================================
# CacheManager Tests
# ============================================================


class TestCacheManager:
    """Tests for CacheManager."""

    def test_set_and_get(self):
        cache = CacheManager()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self):
        cache = CacheManager()
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        cache = CacheManager()
        cache.set("key1", "value1", ttl_seconds=1)
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_has_existing_key(self):
        cache = CacheManager()
        cache.set("key1", "value1")
        assert cache.has("key1") is True

    def test_has_missing_key(self):
        cache = CacheManager()
        assert cache.has("nonexistent") is False

    def test_has_expired_key(self):
        cache = CacheManager()
        cache.set("key1", "value1", ttl_seconds=1)
        time.sleep(1.1)
        assert cache.has("key1") is False

    def test_delete(self):
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_delete_nonexistent(self):
        cache = CacheManager()
        # Should not raise
        cache.delete("nonexistent")

    def test_clear_all(self):
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key2", "value2", namespace="ns2")
        cache.clear()
        assert cache.size() == 0

    def test_clear_specific_namespace(self):
        cache = CacheManager()
        cache.set("key1", "value1", namespace="ns1")
        cache.set("key2", "value2", namespace="ns2")
        cache.clear(namespace="ns1")
        assert cache.get("key1", namespace="ns1") is None
        assert cache.get("key2", namespace="ns2") == "value2"

    def test_size(self):
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.size() == 2

    def test_size_with_namespace(self):
        cache = CacheManager()
        cache.set("key1", "value1", namespace="ns1")
        cache.set("key2", "value2", namespace="ns2")
        assert cache.size(namespace="ns1") == 1
        assert cache.size(namespace="ns2") == 1

    def test_lru_eviction(self):
        cache = CacheManager(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        # Adding a 4th should evict the oldest (key1)
        cache.set("key4", "value4")
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"

    def test_lru_access_updates_order(self):
        cache = CacheManager(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        # Access key1 to make it most recently used
        cache.get("key1")
        # Adding key4 should evict key2 (now the oldest)
        cache.set("key4", "value4")
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None

    def test_namespaces_isolation(self):
        cache = CacheManager()
        cache.set("key1", "value_a", namespace="ns_a")
        cache.set("key1", "value_b", namespace="ns_b")
        assert cache.get("key1", namespace="ns_a") == "value_a"
        assert cache.get("key1", namespace="ns_b") == "value_b"

    def test_overwrite_existing_key(self):
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        assert cache.get("key1") == "value2"

    def test_thread_safety(self):
        cache = CacheManager()
        errors = []

        def writer(prefix):
            try:
                for i in range(100):
                    cache.set(f"{prefix}_{i}", f"value_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(f"t{t}",)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert cache.size() == 500


# ============================================================
# KnowledgeBase Tests
# ============================================================


class TestKnowledgeBase:
    """Tests for KnowledgeBase."""

    def test_store_and_retrieve(self):
        kb = KnowledgeBase()
        kb.store("topic1", "data1")
        entry = kb.retrieve("topic1")
        assert entry is not None
        assert entry.value == "data1"

    def test_retrieve_missing(self):
        kb = KnowledgeBase()
        assert kb.retrieve("nonexistent") is None

    def test_store_with_metadata(self):
        kb = KnowledgeBase()
        kb.store("topic1", "data1", metadata={"author": "agent-1", "tags": ["test"]})
        entry = kb.retrieve("topic1")
        assert entry.metadata["author"] == "agent-1"
        assert entry.metadata["tags"] == ["test"]

    def test_namespaces(self):
        kb = KnowledgeBase()
        kb.store("key1", "shared_val", namespace="shared")
        kb.store("key1", "private_val", namespace="agent1")
        assert kb.retrieve("key1", namespace="shared").value == "shared_val"
        assert kb.retrieve("key1", namespace="agent1").value == "private_val"

    def test_search_by_prefix(self):
        kb = KnowledgeBase()
        kb.store("project:alpha", "data_a")
        kb.store("project:beta", "data_b")
        kb.store("task:gamma", "data_c")
        results = kb.search("project:")
        assert len(results) == 2

    def test_search_specific_namespace(self):
        kb = KnowledgeBase()
        kb.store("key:a", "val1", namespace="ns1")
        kb.store("key:b", "val2", namespace="ns2")
        results = kb.search("key:", namespace="ns1")
        assert len(results) == 1
        assert results[0].value == "val1"

    def test_list_entries_all(self):
        kb = KnowledgeBase()
        kb.store("k1", "v1", namespace="ns1")
        kb.store("k2", "v2", namespace="ns2")
        keys = kb.list_entries()
        assert "k1" in keys
        assert "k2" in keys

    def test_list_entries_namespace(self):
        kb = KnowledgeBase()
        kb.store("k1", "v1", namespace="ns1")
        kb.store("k2", "v2", namespace="ns2")
        keys = kb.list_entries(namespace="ns1")
        assert keys == ["k1"]

    def test_delete(self):
        kb = KnowledgeBase()
        kb.store("key1", "val1")
        kb.delete("key1")
        assert kb.retrieve("key1") is None

    def test_delete_nonexistent(self):
        kb = KnowledgeBase()
        # Should not raise
        kb.delete("nonexistent")

    def test_clear_all(self):
        kb = KnowledgeBase()
        kb.store("k1", "v1", namespace="ns1")
        kb.store("k2", "v2", namespace="ns2")
        kb.clear()
        assert kb.list_entries() == []

    def test_clear_specific_namespace(self):
        kb = KnowledgeBase()
        kb.store("k1", "v1", namespace="ns1")
        kb.store("k2", "v2", namespace="ns2")
        kb.clear(namespace="ns1")
        assert kb.retrieve("k1", namespace="ns1") is None
        assert kb.retrieve("k2", namespace="ns2") is not None

    def test_update_entry(self):
        kb = KnowledgeBase()
        kb.store("key1", "original")
        time.sleep(0.01)
        kb.store("key1", "updated")
        entry = kb.retrieve("key1")
        assert entry.value == "updated"
        assert entry.updated_at > entry.created_at

    def test_timestamps(self):
        kb = KnowledgeBase()
        before = time.time()
        kb.store("key1", "val1")
        after = time.time()
        entry = kb.retrieve("key1")
        assert before <= entry.created_at <= after
        assert before <= entry.updated_at <= after


# ============================================================
# TokenAuth Tests
# ============================================================


class TestTokenAuth:
    """Tests for TokenAuth."""

    def test_generate_and_validate(self):
        auth = TokenAuth(secret_key="test-secret")
        token = auth.generate_token("agent-1")
        result = auth.validate_token(token)
        assert result["subject"] == "agent-1"
        assert result["role"] == "agent"

    def test_custom_role(self):
        auth = TokenAuth(secret_key="test-secret")
        token = auth.generate_token("admin-user", role="admin")
        result = auth.validate_token(token)
        assert result["role"] == "admin"

    def test_readonly_role(self):
        auth = TokenAuth(secret_key="test-secret")
        token = auth.generate_token("viewer", role="readonly")
        result = auth.validate_token(token)
        assert result["role"] == "readonly"

    def test_invalid_role(self):
        auth = TokenAuth(secret_key="test-secret")
        with pytest.raises(InvalidTokenError):
            auth.generate_token("agent-1", role="superadmin")

    def test_token_expiration(self):
        auth = TokenAuth(secret_key="test-secret")
        token = auth.generate_token("agent-1", expires_in=1)
        time.sleep(1.1)
        with pytest.raises(InvalidTokenError, match="expired"):
            auth.validate_token(token)

    def test_token_revocation(self):
        auth = TokenAuth(secret_key="test-secret")
        token = auth.generate_token("agent-1")
        auth.revoke_token(token)
        assert auth.is_revoked(token) is True
        with pytest.raises(InvalidTokenError, match="revoked"):
            auth.validate_token(token)

    def test_is_revoked_false(self):
        auth = TokenAuth(secret_key="test-secret")
        token = auth.generate_token("agent-1")
        assert auth.is_revoked(token) is False

    def test_invalid_signature(self):
        auth = TokenAuth(secret_key="test-secret")
        token = auth.generate_token("agent-1")
        # Tamper with the signature
        parts = token.split(".")
        tampered = parts[0] + ".invalidsignature"
        with pytest.raises(InvalidTokenError, match="signature"):
            auth.validate_token(tampered)

    def test_malformed_token_no_dot(self):
        auth = TokenAuth(secret_key="test-secret")
        with pytest.raises(InvalidTokenError, match="Malformed"):
            auth.validate_token("nodottoken")

    def test_malformed_token_empty(self):
        auth = TokenAuth(secret_key="test-secret")
        with pytest.raises(InvalidTokenError, match="Malformed"):
            auth.validate_token("")

    def test_custom_claims(self):
        auth = TokenAuth(secret_key="test-secret")
        token = auth.generate_token("agent-1", claims={"team": "backend", "level": 5})
        result = auth.validate_token(token)
        assert result["claims"]["team"] == "backend"
        assert result["claims"]["level"] == 5

    def test_different_secrets_reject(self):
        auth1 = TokenAuth(secret_key="secret-1")
        auth2 = TokenAuth(secret_key="secret-2")
        token = auth1.generate_token("agent-1")
        with pytest.raises(InvalidTokenError):
            auth2.validate_token(token)

    def test_invalid_token_error_is_agent_error(self):
        from agentwork.core.exceptions import AgentError
        assert issubclass(InvalidTokenError, AgentError)
