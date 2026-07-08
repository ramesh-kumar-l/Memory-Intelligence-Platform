"""GET /v1/memories/{id}/relationships contract tests (Phase 4 task 1, ADR-0006)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.factories import create_payload


def _create(client: TestClient, **overrides: object) -> str:
    response = client.post("/v1/memories", json=create_payload(**overrides))
    return str(response.json()["data"]["memory_id"])


def test_relationships_lists_outbound_and_inbound_edges(client: TestClient) -> None:
    target = _create(client, title="target")
    source = _create(
        client,
        title="source",
        relationships=[{"target_memory_id": target, "type": "references"}],
    )
    source_edges = client.get(f"/v1/memories/{source}/relationships").json()["data"]
    assert source_edges["relationships"][0]["target_memory_id"] == target

    target_edges = client.get(f"/v1/memories/{target}/relationships").json()["data"]
    assert target_edges["relationships"][0]["source_memory_id"] == source


def test_relationships_of_unknown_memory_is_404(client: TestClient) -> None:
    response = client.get("/v1/memories/does-not-exist/relationships")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MEM-3001"
