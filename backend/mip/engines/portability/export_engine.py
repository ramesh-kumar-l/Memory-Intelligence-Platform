"""Export (Phase 4 task 4, ADR-0006): dump every version of every in-scope
memory exactly as the public API already exposes it (GetMemory/ListVersions)
— fidelity is defined against the public contract, not internal storage layout.
Deleted tombstones are excluded by default, matching ListMemories' own default.
"""

from __future__ import annotations

from typing import Any

from mip.core.clock import Clock
from mip.engines.memory_manager.engine import MemoryManager

_PAGE_SIZE = 200


class ExportEngine:
    def __init__(self, *, manager: MemoryManager, clock: Clock, schema_version: str) -> None:
        self._manager = manager
        self._clock = clock
        self._schema_version = schema_version

    def export(self, *, namespace: str | None) -> dict[str, Any]:
        memories: list[dict[str, Any]] = []
        after: str | None = None
        while True:
            records, has_more = self._manager.list_memories(
                namespace=namespace, state=None, limit=_PAGE_SIZE, after_memory_id=after
            )
            for record in records:
                versions = self._manager.list_versions(record.memory_id)
                memories.append(
                    {
                        "memory_id": record.memory_id,
                        "state": record.state.value,
                        "versions": [
                            self._manager.get_memory(
                                record.memory_id, info.version
                            ).to_public_dict()
                            for info in versions
                        ],
                    }
                )
            if not records or not has_more:
                break
            after = records[-1].memory_id
        return {
            "schema_version": self._schema_version,
            "exported_at": self._clock.now().isoformat(),
            "namespace": namespace,
            "memory_count": len(memories),
            "memories": memories,
        }
