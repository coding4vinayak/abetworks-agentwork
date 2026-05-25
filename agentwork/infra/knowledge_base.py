"""Shared key-value knowledge base for inter-agent communication."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeEntry:
    """A single entry in the knowledge base."""

    key: str
    value: Any
    namespace: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class KnowledgeBase:
    """Thread-safe shared key-value store for agents.

    Supports namespaces for isolating entries, metadata per entry,
    and prefix-based search.

    Args:
        max_entries: Optional maximum number of total entries across all
            namespaces. When exceeded, the oldest entries (by created_at)
            are evicted. None means unlimited.
    """

    def __init__(self, max_entries: Optional[int] = None) -> None:
        self._lock = threading.RLock()
        # namespace -> key -> KnowledgeEntry
        self._entries: Dict[str, Dict[str, KnowledgeEntry]] = {}
        self._max_entries = max_entries

    def _get_namespace_store(self, namespace: str) -> Dict[str, KnowledgeEntry]:
        """Get or create the store for a namespace."""
        if namespace not in self._entries:
            self._entries[namespace] = {}
        return self._entries[namespace]

    def _total_entry_count(self) -> int:
        """Return the total number of entries across all namespaces."""
        return sum(len(store) for store in self._entries.values())

    def _evict_oldest(self) -> None:
        """Evict the oldest entry (by created_at) across all namespaces.

        Must be called while holding self._lock.
        """
        oldest_entry: Optional[KnowledgeEntry] = None
        oldest_ns: Optional[str] = None

        for ns, store in self._entries.items():
            for entry in store.values():
                if oldest_entry is None or entry.created_at < oldest_entry.created_at:
                    oldest_entry = entry
                    oldest_ns = ns

        if oldest_entry is not None and oldest_ns is not None:
            del self._entries[oldest_ns][oldest_entry.key]

    def store(
        self,
        key: str,
        value: Any,
        namespace: str = "shared",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store an entry in the knowledge base.

        Args:
            key: Entry key.
            value: Value to store.
            namespace: Namespace for the entry.
            metadata: Optional metadata dict (author, tags, etc.).
        """
        with self._lock:
            ns_store = self._get_namespace_store(namespace)
            now = time.time()

            if key in ns_store:
                entry = ns_store[key]
                entry.value = value
                entry.updated_at = now
                if metadata is not None:
                    entry.metadata = metadata
            else:
                ns_store[key] = KnowledgeEntry(
                    key=key,
                    value=value,
                    namespace=namespace,
                    metadata=metadata or {},
                    created_at=now,
                    updated_at=now,
                )
                # Evict oldest entries if over the limit
                if self._max_entries is not None:
                    while self._total_entry_count() > self._max_entries:
                        self._evict_oldest()

    def retrieve(self, key: str, namespace: str = "shared") -> Optional[KnowledgeEntry]:
        """Retrieve an entry from the knowledge base.

        Args:
            key: Entry key.
            namespace: Namespace to look in.

        Returns:
            KnowledgeEntry or None if not found.
        """
        with self._lock:
            ns_store = self._entries.get(namespace, {})
            return ns_store.get(key)

    def search(
        self, prefix: str, namespace: Optional[str] = None
    ) -> List[KnowledgeEntry]:
        """Search entries by key prefix.

        Args:
            prefix: Key prefix to match.
            namespace: Specific namespace to search, or None for all.

        Returns:
            List of matching entries.
        """
        with self._lock:
            results: List[KnowledgeEntry] = []
            namespaces = (
                [namespace] if namespace else list(self._entries.keys())
            )

            for ns in namespaces:
                ns_store = self._entries.get(ns, {})
                for key, entry in ns_store.items():
                    if key.startswith(prefix):
                        results.append(entry)

            return results

    def list_entries(self, namespace: Optional[str] = None) -> List[str]:
        """List all keys in the knowledge base.

        Args:
            namespace: Specific namespace to list, or None for all.

        Returns:
            List of keys.
        """
        with self._lock:
            keys: List[str] = []
            namespaces = (
                [namespace] if namespace else list(self._entries.keys())
            )

            for ns in namespaces:
                ns_store = self._entries.get(ns, {})
                keys.extend(ns_store.keys())

            return keys

    def delete(self, key: str, namespace: str = "shared") -> None:
        """Remove an entry from the knowledge base.

        Args:
            key: Entry key.
            namespace: Namespace to delete from.
        """
        with self._lock:
            ns_store = self._entries.get(namespace, {})
            if key in ns_store:
                del ns_store[key]

    def clear(self, namespace: Optional[str] = None) -> None:
        """Clear entries.

        Args:
            namespace: Specific namespace to clear, or None for all.
        """
        with self._lock:
            if namespace is None:
                self._entries.clear()
            elif namespace in self._entries:
                self._entries[namespace].clear()
