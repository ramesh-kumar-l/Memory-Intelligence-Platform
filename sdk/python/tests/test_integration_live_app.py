"""End-to-end contract check: the SDK against the *real* FastAPI app (in-process
via Starlette's TestClient, no network) rather than a hand-written mock. Guards
against the SDK's request/response models silently drifting from the backend.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from mip.api.app import create_app  # noqa: E402
from mip.config import MIPSettings  # noqa: E402

from mip_sdk.client import MIPClient  # noqa: E402
from mip_sdk.models.memory import Semantics  # noqa: E402
from mip_sdk.models.requests import (  # noqa: E402
    CreateMemoryRequest,
    ProvenanceInput,
    UpdateMemoryRequest,
)


@pytest.fixture
def client(tmp_path: Path) -> Iterator[MIPClient]:
    settings = MIPSettings(db_path=tmp_path / "mip.db")
    app = create_app(settings)
    with TestClient(app) as test_client:
        sdk_client = MIPClient("http://testserver", http_client=test_client)
        yield sdk_client
        sdk_client.close()


def test_full_lifecycle_round_trip(client: MIPClient) -> None:
    created = client.memories.create(
        CreateMemoryRequest(
            namespace="demo",
            owner_id="user-1",
            title="Integration test memory",
            summary="Testing the SDK end to end.",
            semantics=Semantics(keywords=("integration", "sdk")),
            provenance=ProvenanceInput(source="sdk-integration-test"),
        )
    )
    assert created.lifecycle.state.value == "Active"
    assert created.lifecycle.version == 1

    fetched = client.memories.get(created.memory_id)
    assert fetched.memory_id == created.memory_id

    updated = client.memories.update(
        created.memory_id,
        UpdateMemoryRequest(title="Updated title"),
        expected_version=1,
    )
    assert updated.lifecycle.version == 2
    assert updated.content.title == "Updated title"

    page = client.memories.list(namespace="demo")
    assert any(record.memory_id == created.memory_id for record in page.items)
    assert next(r for r in page.items if r.memory_id == created.memory_id).title == "Updated title"

    versions = client.memories.list_versions(created.memory_id)
    assert [v.version for v in versions] == [1, 2]

    search_response = client.search.search(query="integration", mode="keyword")
    assert any(item.memory_id == created.memory_id for item in search_response.items)

    explanation = client.explain.explain(memory_id=created.memory_id, query="integration")
    assert 0.0 <= explanation.confidence <= 1.0
    assert explanation.ranking is not None and explanation.ranking.matched is True

    package = client.context.build(query="integration", namespace="demo")
    assert package.total_candidates >= 1

    archived = client.memories.archive(created.memory_id)
    assert archived.lifecycle.state.value == "Archived"
    restored = client.memories.restore(created.memory_id)
    assert restored.lifecycle.state.value == "Active"

    delete_result = client.memories.delete(created.memory_id)
    assert delete_result

    health = client.admin.health()
    assert health["status"] == "ok"

    report = client.admin.rebuild_projections()
    assert "indexed_memories" in report


def test_lifecycle_error_surfaces_as_typed_exception(client: MIPClient) -> None:
    from mip_sdk.errors import IdentityError

    with pytest.raises(IdentityError) as excinfo:
        client.memories.get("00000000-0000-0000-0000-000000000000")
    assert excinfo.value.code == "MEM-3001"


def test_version_conflict_surfaces_as_concurrency_error(client: MIPClient) -> None:
    from mip_sdk.errors import ConcurrencyError

    created = client.memories.create(
        CreateMemoryRequest(
            namespace="demo",
            owner_id="user-1",
            title="Conflict test",
            semantics=Semantics(keywords=("conflict",)),
            provenance=ProvenanceInput(source="sdk-integration-test"),
        )
    )
    with pytest.raises(ConcurrencyError) as excinfo:
        client.memories.update(
            created.memory_id,
            UpdateMemoryRequest(title="stale update"),
            expected_version=99,
        )
    assert excinfo.value.code == "MEM-4001"
