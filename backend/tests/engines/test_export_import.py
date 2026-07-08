"""Export/Import (Phase 4 task 4, ADR-0006). Exit criterion: import of an
export round-trips losslessly. Fidelity is measured against what the public
API (GetMemory/ListVersions) already exposes, per ADR-0006 decision 8.
"""

from __future__ import annotations

import pytest

from mip.core import errors
from mip.core.specs import UpdateMemorySpec
from mip.core.states import MemoryState
from mip.engines.knowledge.consolidate import ConsolidateEngine
from mip.engines.memory_manager.engine import MemoryManager
from mip.engines.portability.export_engine import ExportEngine
from mip.engines.portability.import_engine import ImportEngine
from mip.storage.sqlite.memory_repository import SqliteMemoryRepository
from tests.factories import create_spec


def _create(manager: MemoryManager, **overrides: object) -> str:
    memory = manager.create_memory(create_spec(**overrides), request_id="r", trace_id="t")
    return memory.memory_id


def test_export_then_import_round_trips_losslessly(
    manager: MemoryManager,
    export_engine: ExportEngine,
    import_engine: ImportEngine,
    consolidate_engine: ConsolidateEngine,
    repo: SqliteMemoryRepository,
) -> None:
    m1 = _create(manager, title="first", namespace="rt")
    manager.update_memory(
        m1,
        UpdateMemorySpec(title="first revised"),
        expected_version=1,
        request_id="r2",
        trace_id="t2",
    )
    manager.archive_memory(m1, actor="tester", trace_id="t3")
    m2 = _create(manager, title="second", namespace="rt")
    m3 = _create(manager, title="consolidation target", namespace="rt")
    dup = _create(manager, title="dup of m3", namespace="rt")
    consolidate_engine.consolidate(
        primary_memory_id=m3, duplicate_memory_ids=(dup,), actor="t", request_id="r", trace_id="t"
    )

    bundle = export_engine.export(namespace="rt")
    assert bundle["memory_count"] == 4

    before = {
        m1: (manager.get_memory(m1, version=1), manager.get_memory(m1, version=2)),
        m2: (manager.get_memory(m2),),
        m3: (manager.get_memory(m3),),
    }
    before_m1_record = repo.get_record(m1)
    before_m3_record = repo.get_record(m3)
    assert before_m3_record is not None
    assert before_m3_record.consolidation_count == 1

    repo.clear_all()  # simulate restoring into a fresh store
    assert repo.get_record(m1) is None

    report = import_engine.import_bundle(bundle, actor="importer", trace_id="t4")
    assert set(report["imported"]) == {m1, m2, m3, dup}
    assert report["rejected"] == []
    assert report["skipped"] == []

    for memory_id, expected_versions in before.items():
        for expected in expected_versions:
            actual = manager.get_memory(memory_id, version=expected.version)
            assert actual.to_public_dict() == expected.to_public_dict()

    after_m1_record = repo.get_record(m1)
    assert after_m1_record is not None and before_m1_record is not None
    assert after_m1_record.state == before_m1_record.state == MemoryState.ARCHIVED
    assert after_m1_record.archived_at == before_m1_record.archived_at
    assert [v.version for v in manager.list_versions(m1)] == [1, 2]

    after_m3_record = repo.get_record(m3)
    assert after_m3_record is not None
    assert after_m3_record.consolidation_count == 1


def test_import_skips_already_existing_memory(
    manager: MemoryManager, export_engine: ExportEngine, import_engine: ImportEngine
) -> None:
    memory_id = _create(manager, title="already here", namespace="rt2")
    bundle = export_engine.export(namespace="rt2")
    report = import_engine.import_bundle(bundle, actor="importer", trace_id="t")
    assert report["imported"] == []
    assert report["skipped"] == [{"memory_id": memory_id, "reason": "already exists"}]


def test_import_rejects_invalid_memory_without_blocking_the_rest(
    manager: MemoryManager, export_engine: ExportEngine, import_engine: ImportEngine
) -> None:
    good_id = _create(manager, title="good memory", namespace="rt3")
    bundle = export_engine.export(namespace="rt3")
    bundle["memories"].append(
        {
            "memory_id": "bad-memory",
            "state": "Active",
            "versions": [{"not": "a valid memory object"}],
        }
    )
    report = import_engine.import_bundle(bundle, actor="importer", trace_id="t")
    assert good_id not in report["imported"]  # good_id already exists locally -> skipped
    assert report["skipped"] == [{"memory_id": good_id, "reason": "already exists"}]
    assert len(report["rejected"]) == 1
    assert report["rejected"][0]["memory_id"] == "bad-memory"


def test_import_bundle_missing_memories_field_is_rejected(import_engine: ImportEngine) -> None:
    with pytest.raises(errors.ValidationError) as exc_info:
        import_engine.import_bundle({}, actor="importer", trace_id="t")
    assert exc_info.value.code == "MEM-1009"


def test_import_rejects_entries_outside_allowed_namespaces(
    manager: MemoryManager,
    export_engine: ExportEngine,
    import_engine: ImportEngine,
    repo: SqliteMemoryRepository,
) -> None:
    """ADR-0007: a namespace outside the caller's allowed set is rejected like
    any other validation failure, not a whole-bundle failure."""
    allowed_id = _create(manager, title="in scope", namespace="allowed-ns")
    other_id = _create(manager, title="out of scope", namespace="other-ns")
    bundle = export_engine.export(namespace=None)
    assert {m["memory_id"] for m in bundle["memories"]} >= {allowed_id, other_id}

    repo.clear_all()  # simulate importing into a fresh store

    report = import_engine.import_bundle(
        {"memories": bundle["memories"]},
        actor="importer",
        trace_id="t",
        allowed_namespaces=("allowed-ns",),
    )
    assert allowed_id in report["imported"]
    rejected_ids = {entry["memory_id"] for entry in report["rejected"]}
    assert other_id in rejected_ids
    other_entry = next(entry for entry in report["rejected"] if entry["memory_id"] == other_id)
    assert other_entry["violations"][0]["code"] == "MEM-8003"
