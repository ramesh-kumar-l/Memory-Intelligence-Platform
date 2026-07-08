"""POST /v1/consolidate contract tests (Phase 4 task 2, ADR-0006)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.factories import create_payload


def _create(client: TestClient, **overrides: object) -> str:
    response = client.post("/v1/memories", json=create_payload(**overrides))
    return str(response.json()["data"]["memory_id"])


def test_consolidate_merges_duplicate(client: TestClient) -> None:
    primary = _create(client, title="primary")
    duplicate = _create(client, title="duplicate")
    response = client.post(
        "/v1/consolidate",
        json={"primary_memory_id": primary, "duplicate_memory_ids": [duplicate]},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["memory_id"] == primary
    assert data["lifecycle"]["consolidation_count"] == 1

    duplicate_response = client.get(f"/v1/memories/{duplicate}")
    assert duplicate_response.json()["data"]["lifecycle"]["state"] == "Archived"


def test_consolidate_self_merge_is_rejected(client: TestClient) -> None:
    primary = _create(client, title="primary")
    response = client.post(
        "/v1/consolidate",
        json={"primary_memory_id": primary, "duplicate_memory_ids": [primary]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MEM-1008"


def test_consolidate_empty_duplicates_rejected_by_schema(client: TestClient) -> None:
    primary = _create(client, title="primary")
    response = client.post(
        "/v1/consolidate", json={"primary_memory_id": primary, "duplicate_memory_ids": []}
    )
    assert response.status_code == 422


def test_consolidate_unknown_memory_is_404(client: TestClient) -> None:
    response = client.post(
        "/v1/consolidate",
        json={"primary_memory_id": "does-not-exist", "duplicate_memory_ids": ["also-missing"]},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MEM-3001"
