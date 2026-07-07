"""Per-memory advisory locks: one lifecycle transition at a time (INV-CONCUR-004)."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

from mip.core import errors


class LockRegistry:
    def __init__(self) -> None:
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()

    def _lock_for(self, memory_id: str) -> threading.Lock:
        with self._guard:
            return self._locks.setdefault(memory_id, threading.Lock())

    @contextmanager
    def acquire(self, memory_id: str, timeout: float) -> Iterator[None]:
        """Hold the memory's transition lock; MEM-4004 if another transition runs."""
        lock = self._lock_for(memory_id)
        if not lock.acquire(timeout=timeout):
            raise errors.transition_in_progress(memory_id)
        try:
            yield
        finally:
            lock.release()
