"""MemoryManager.peek_namespace (ADR-0007): a raw namespace lookup that
bypasses the Active/Deleted lifecycle gate, used by auth/ownership checks
that must not disturb Delete/Archive/Restore's idempotent-on-tombstone paths.
"""

from __future__ import annotations

from mip.engines.memory_manager.engine import MemoryManager
from tests.factories import create_spec


def test_peek_namespace_returns_namespace_for_existing_memory(manager: MemoryManager) -> None:
    memory = manager.create_memory(create_spec(namespace="peek-ns"), request_id="r", trace_id="t")
    assert manager.peek_namespace(memory.memory_id) == "peek-ns"


def test_peek_namespace_returns_none_for_unknown_memory(manager: MemoryManager) -> None:
    assert manager.peek_namespace("does-not-exist") is None


def test_peek_namespace_still_resolves_after_delete(manager: MemoryManager) -> None:
    memory = manager.create_memory(create_spec(namespace="peek-ns-2"), request_id="r", trace_id="t")
    manager.delete_memory(memory.memory_id, actor="tester", trace_id="t")
    assert manager.peek_namespace(memory.memory_id) == "peek-ns-2"
