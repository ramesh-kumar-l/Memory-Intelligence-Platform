"""Version invariant suite (INV-VER-*): monotonic versions, immutable history,
one current version, predecessor links.
"""

from __future__ import annotations

from mip.core.specs import UpdateMemorySpec
from mip.engines.memory_manager.engine import MemoryManager
from mip.storage.sqlite.memory_repository import SqliteMemoryRepository
from tests.factories import create_spec


def _update(manager: MemoryManager, memory_id: str, version: int, title: str) -> None:
    manager.update_memory(
        memory_id,
        UpdateMemorySpec(title=title),
        expected_version=version,
        request_id=f"r{version}",
        trace_id=f"t{version}",
    )


def test_inv_ver_001_versions_increase_monotonically(manager: MemoryManager) -> None:
    memory = manager.create_memory(create_spec(title="v1"), request_id="r", trace_id="t")
    _update(manager, memory.memory_id, 1, "v2")
    _update(manager, memory.memory_id, 2, "v3")
    versions = [info.version for info in manager.list_versions(memory.memory_id)]
    assert versions == [1, 2, 3]
    assert manager.get_memory(memory.memory_id).version == 3


def test_inv_ver_002_historical_versions_immutable(manager: MemoryManager) -> None:
    memory = manager.create_memory(create_spec(title="original"), request_id="r", trace_id="t")
    _update(manager, memory.memory_id, 1, "revised")
    v1 = manager.get_memory(memory.memory_id, version=1)
    assert v1.content.title == "original"
    assert v1.version == 1


def test_inv_ver_003_exactly_one_current_version(
    manager: MemoryManager, repo: SqliteMemoryRepository
) -> None:
    memory = manager.create_memory(create_spec(), request_id="r", trace_id="t")
    _update(manager, memory.memory_id, 1, "second")
    record = repo.get_record(memory.memory_id)
    assert record is not None
    assert record.current_version == 2
    current = manager.get_memory(memory.memory_id)
    assert current.version == record.current_version


def test_inv_ver_004_every_version_links_to_predecessor(manager: MemoryManager) -> None:
    memory = manager.create_memory(create_spec(), request_id="r", trace_id="t")
    _update(manager, memory.memory_id, 1, "second")
    _update(manager, memory.memory_id, 2, "third")
    chain = {
        info.version: info.previous_version for info in manager.list_versions(memory.memory_id)
    }
    assert chain == {1: None, 2: 1, 3: 2}
