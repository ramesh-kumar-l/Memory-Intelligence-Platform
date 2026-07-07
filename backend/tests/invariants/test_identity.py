"""Identity invariant suite (INV-ID-*): one immutable memory_id, immutable
ownership and creation timestamp, identity survives every operation.
"""

from __future__ import annotations

import pytest

from mip.core.errors import IdentityError
from mip.core.specs import UpdateMemorySpec
from mip.engines.memory_manager.engine import MemoryManager
from mip.engines.validation.engine import ValidationEngine
from mip.storage.sqlite.database import Database
from mip.storage.sqlite.memory_repository import SqliteMemoryRepository
from tests.factories import create_spec


def test_inv_id_001_memory_id_is_unique(
    repo: SqliteMemoryRepository, validation: ValidationEngine, db: Database
) -> None:
    memory = validation.build_memory(create_spec(), request_id="r", trace_id="t")
    with db.transaction():
        repo.create(memory)
    with pytest.raises(IdentityError) as exc_info, db.transaction():
        repo.create(memory)
    assert exc_info.value.code == "MEM-3003"


def test_inv_id_003_creation_timestamp_immutable(manager: MemoryManager) -> None:
    created = manager.create_memory(create_spec(), request_id="r", trace_id="t")
    updated = manager.update_memory(
        created.memory_id,
        UpdateMemorySpec(title="new title"),
        expected_version=1,
        request_id="r2",
        trace_id="t2",
    )
    assert updated.lifecycle.created_at == created.lifecycle.created_at


def test_inv_id_004_identity_survives_update_archive_restore(manager: MemoryManager) -> None:
    created = manager.create_memory(create_spec(), request_id="r", trace_id="t")
    manager.update_memory(
        created.memory_id,
        UpdateMemorySpec(summary="revised"),
        expected_version=1,
        request_id="r2",
        trace_id="t2",
    )
    manager.archive_memory(created.memory_id, actor="a", trace_id="t3")
    restored = manager.restore_memory(created.memory_id, actor="a", trace_id="t4")
    assert restored.memory_id == created.memory_id
    assert restored.identity.namespace == created.identity.namespace
    assert restored.identity.owner_id == created.identity.owner_id  # INV-ID-002
