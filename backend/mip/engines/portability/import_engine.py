"""Import (Phase 4 task 4, ADR-0006): materialize an Export bundle. Every
version of every memory is validated (schema + activation invariants) before
anything is written; each memory's version chain is written in one atomic
transaction, but memories are independent — one rejection never blocks the
rest of the bundle. A `memory_id` already present locally is skipped, never
overwritten (INV-ID-001: identity uniqueness; never clobber local history).
"""

from __future__ import annotations

from typing import Any

import pydantic

from mip.core import errors, invariants
from mip.core.clock import Clock
from mip.core.model import MemoryObject
from mip.events.projector import apply_event
from mip.events.types import consolidation_event, import_event, version_import_event
from mip.storage.interfaces import EventStoreABC, MemoryRepositoryABC, TransactionManagerABC


class ImportEngine:
    def __init__(
        self,
        *,
        event_store: EventStoreABC,
        repository: MemoryRepositoryABC,
        transactions: TransactionManagerABC,
        clock: Clock,
    ) -> None:
        self._events = event_store
        self._repo = repository
        self._tx = transactions
        self._clock = clock

    def import_bundle(self, bundle: dict[str, Any], *, actor: str, trace_id: str) -> dict[str, Any]:
        entries = bundle.get("memories")
        if not isinstance(entries, list):
            raise errors.import_bundle_invalid("'memories' must be a list")

        imported: list[str] = []
        skipped: list[dict[str, str]] = []
        rejected: list[dict[str, Any]] = []
        for entry in entries:
            memory_id = _entry_memory_id(entry)
            if memory_id is None:
                rejected.append({"memory_id": None, "violations": [{"message": "malformed entry"}]})
                continue
            if self._repo.get_record(memory_id) is not None:
                skipped.append({"memory_id": memory_id, "reason": "already exists"})
                continue
            try:
                versions = _parse_versions(entry)
            except (pydantic.ValidationError, TypeError, KeyError, ValueError) as exc:
                rejected.append({"memory_id": memory_id, "violations": [{"message": str(exc)}]})
                continue
            violations = _validate_versions(memory_id, versions)
            if violations:
                rejected.append({"memory_id": memory_id, "violations": violations})
                continue
            self._write_versions(memory_id, versions, actor=actor, trace_id=trace_id)
            imported.append(memory_id)
        return {"imported": imported, "skipped": skipped, "rejected": rejected}

    def _write_versions(
        self, memory_id: str, versions: list[MemoryObject], *, actor: str, trace_id: str
    ) -> None:
        with self._tx.transaction():
            first = versions[0]
            event = import_event(
                memory_id=memory_id,
                memory_json=first.model_dump(mode="json"),
                actor=actor,
                trace_id=trace_id,
                created_at=self._clock.now(),
            )
            self._events.append(event)
            apply_event(self._repo, event)
            previous_version = first.version
            for version_obj in versions[1:]:
                event = version_import_event(
                    memory_id=memory_id,
                    memory_json=version_obj.model_dump(mode="json"),
                    previous_version=previous_version,
                    actor=actor,
                    trace_id=trace_id,
                    created_at=self._clock.now(),
                )
                self._events.append(event)
                apply_event(self._repo, event)
                previous_version = version_obj.version
            # consolidation_count has no version of its own to carry it (it lives
            # on the live projection, not a version snapshot) — replay it via the
            # same event type Consolidate uses, so the counter stays event-sourced.
            # Use the exported updated_at (record_consolidation also stamps it) so
            # this synthetic replay doesn't overwrite it with the import time.
            final = versions[-1]
            consolidation_timestamp = final.lifecycle.updated_at or self._clock.now()
            for _ in range(final.lifecycle.consolidation_count):
                count_event = consolidation_event(
                    primary_memory_id=memory_id,
                    duplicate_memory_id="imported",
                    actor=actor,
                    trace_id=trace_id,
                    created_at=consolidation_timestamp,
                )
                self._events.append(count_event)
                apply_event(self._repo, count_event)


def _entry_memory_id(entry: Any) -> str | None:
    if not isinstance(entry, dict) or "memory_id" not in entry:
        return None
    return str(entry["memory_id"])


def _parse_versions(entry: dict[str, Any]) -> list[MemoryObject]:
    raw_versions = entry.get("versions")
    if not isinstance(raw_versions, list) or not raw_versions:
        raise ValueError("'versions' must be a non-empty list")
    return [MemoryObject.model_validate(v) for v in raw_versions]


def _validate_versions(memory_id: str, versions: list[MemoryObject]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    expected_version = 1
    for version_obj in versions:
        if str(version_obj.identity.memory_id) != memory_id:
            violations.append(
                {
                    "invariant": "INV-ID-001",
                    "field": "memory_id",
                    "message": "version's memory_id does not match the entry's memory_id",
                }
            )
        if version_obj.version != expected_version:
            violations.append(
                {
                    "invariant": "INV-VER-001",
                    "field": "version",
                    "message": f"expected version {expected_version}, got {version_obj.version}",
                }
            )
        expected_version += 1
        violations.extend(invariants.activation_violations(version_obj))
    return violations
