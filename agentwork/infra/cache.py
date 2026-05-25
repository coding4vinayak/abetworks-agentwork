"""TTL-based in-memory cache with LRU eviction and namespace support."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional


class CacheManager:
    """Thread-safe TTL-based in-memory cache with LRU eviction.

    Supports namespaces for isolating cache entries between agents.
    When max_size is exceeded, the least recently used entries are evicted.
    """

    def __init__(self, max_size: int = 10000) -> None:
        self._max_size = max_size
        self._lock = threading.Lock()
        # namespace -> OrderedDict[key, (value, expire_time)]
        self._stores: Dict[str, OrderedDict[str, tuple]] = {}

    def _get_store(self, namespace: str) -> OrderedDict:
        """Get or create the store for a namespace."""
        if namespace not in self._stores:
            self._stores[namespace] = OrderedDict()
        return self._stores[namespace]

    def _total_size(self) -> int:
        """Total number of entries across all namespaces."""
        return sum(len(store) for store in self._stores.values())

    def _evict_lru(self) -> None:
        """Evict the least recently used entry across all namespaces."""
        oldest_ns = None
        oldest_time = float("inf")

        for ns, store in self._stores.items():
            if store:
                # Peek at the first (oldest) item
                key = next(iter(store))
                _, expire_time = store[key]
                # Use insertion order as proxy for LRU (oldest first)
                # The item at the front is the least recently used
                if expire_time <= oldest_time:
                    oldest_time = expire_time
                    oldest_ns = ns

        if oldest_ns is not None and self._stores[oldest_ns]:
            self._stores[oldest_ns].popitem(last=False)

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 300,
        namespace: str = "default",
    ) -> None:
        """Store a value with TTL.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl_seconds: Time-to-live in seconds.
            namespace: Namespace to store under.
        """
        with self._lock:
            store = self._get_store(namespace)
            expire_time = time.time() + ttl_seconds

            # If key already exists, remove it first so it moves to end
            if key in store:
                del store[key]

            store[key] = (value, expire_time)
            store.move_to_end(key)

            # Evict if over capacity
            while self._total_size() > self._max_size:
                self._evict_lru()

    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Retrieve a cached value. Returns None if expired or missing.

        Args:
            key: Cache key.
            namespace: Namespace to look in.

        Returns:
            Cached value or None.
        """
        with self._lock:
            store = self._get_store(namespace)
            if key not in store:
                return None

            value, expire_time = store[key]
            if time.time() > expire_time:
                # Expired - clean up
                del store[key]
                return None

            # Move to end (most recently used)
            store.move_to_end(key)
            return value

    def delete(self, key: str, namespace: str = "default") -> None:
        """Remove an entry from the cache.

        Args:
            key: Cache key.
            namespace: Namespace to delete from.
        """
        with self._lock:
            store = self._get_store(namespace)
            if key in store:
                del store[key]

    def has(self, key: str, namespace: str = "default") -> bool:
        """Check if a key exists and is not expired.

        Args:
            key: Cache key.
            namespace: Namespace to check in.

        Returns:
            True if key exists and is not expired.
        """
        with self._lock:
            store = self._get_store(namespace)
            if key not in store:
                return False

            _, expire_time = store[key]
            if time.time() > expire_time:
                del store[key]
                return False
            return True

    def clear(self, namespace: Optional[str] = None) -> None:
        """Clear cache entries.

        Args:
            namespace: Specific namespace to clear, or None for all.
        """
        with self._lock:
            if namespace is None:
                self._stores.clear()
            elif namespace in self._stores:
                self._stores[namespace].clear()

    def size(self, namespace: Optional[str] = None) -> int:
        """Count cache entries.

        Args:
            namespace: Specific namespace to count, or None for all.

        Returns:
            Number of entries (including potentially expired ones).
        """
        with self._lock:
            if namespace is None:
                return self._total_size()
            store = self._stores.get(namespace)
            if store is None:
                return 0
            return len(store)
