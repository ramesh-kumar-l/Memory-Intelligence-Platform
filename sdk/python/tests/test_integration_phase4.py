"""Phase 4 end-to-end check against the real FastAPI app (ADR-0006): graph
relationships, Consolidate, Learn, Export/Import round-trip.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

_BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from mip.api.app import create_app  # noqa: E402
from mip.config import MIPSettings  # noqa: E402

from mip_sdk.client import MIPClient  # noqa: E402
from mip_sdk.models.memory import RelationshipType, Semantics  # noqa: E402
from mip_sdk.models.requests import (  # noqa: E402
    ConsolidateRequest,
    CreateMemoryRequest,
    ExportRequest,
    LearnRequest,
    ProvenanceInput,
    RelationshipInput,
)


@pytest.fixture
def client(tmp_path: Path) -> Iterator[MIPClient]:
    settings = MIPSettings(db_path=tmp_path / "mip.db")
    app = create_app(settings)
    with TestClient(app) as test_client:
        sdk_client = MIPClient("http://testserver", http_client=test_client)
        yield sdk_client
        sdk_client.close()


def _create(
    client: MIPClient, title: str, *, relationships: tuple[RelationshipInput, ...] = ()
) -> str:
    memory = client.memories.create(
        CreateMemoryRequest(
            namespace="phase4",
            owner_id="user-1",
            title=title,
            semantics=Semantics(keywords=("phase4",)),
            provenance=ProvenanceInput(source="sdk-phase4-test"),
            relationships=relationships,
        )
    )
    return memory.memory_id


def test_graph_search_and_relationships(client: MIPClient) -> None:
    target = _create(client, "graph target")
    source = _create(
        client,
        "graph source",
        relationships=(
            RelationshipInput(target_memory_id=UUID(target), type=RelationshipType.REFERENCES),
        ),
    )

    results = client.search.search(query=source, mode="graph")
    assert results.items[0].memory_id == target

    edges = client.memories.relationships(source)
    assert edges.relationships[0].target_memory_id == target


def test_consolidate_merges_duplicate(client: MIPClient) -> None:
    primary = _create(client, "primary")
    duplicate = _create(client, "duplicate")
    merged = client.consolidate.consolidate(
        ConsolidateRequest(primary_memory_id=primary, duplicate_memory_ids=(duplicate,))
    )
    assert merged.lifecycle.consolidation_count == 1
    assert client.memories.get(duplicate).lifecycle.state.value == "Archived"


def test_learn_matures_evidence_and_derives_semantics(client: MIPClient) -> None:
    memory_id = _create(client, "learnable memory")
    updated = client.learn.learn(
        LearnRequest(
            memory_id=memory_id,
            derived=Semantics(concepts=("durability",)),
            new_evidence=({"source": "doc-1"}, {"source": "doc-2"}),
            reason="corroborating documents found",
        )
    )
    assert "durability" in updated.semantics.concepts
    assert updated.trust.source_count == 3
    assert updated.trust.verification_status.value == "Verified"


def test_export_import_round_trip(client: MIPClient) -> None:
    memory_id = _create(client, "export me")
    bundle = client.portability.export(ExportRequest(namespace="phase4"))
    assert bundle.memory_count >= 1

    report = client.portability.import_(bundle)
    assert memory_id in {skip.memory_id for skip in report.skipped}  # already present, skipped
    assert report.rejected == ()
