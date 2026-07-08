"""POST /v1/export + /v1/import contract tests (Phase 4 task 4, ADR-0006).
Exit criterion: import of an export round-trips losslessly.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.factories import create_payload


def _create(client: TestClient, **overrides: object) -> str:
    response = client.post("/v1/memories", json=create_payload(**overrides))
    return str(response.json()["data"]["memory_id"])


def test_export_returns_bundle(client: TestClient) -> None:
    _create(client, namespace="export-ns", title="exportable memory")
    response = client.post("/v1/export", json={"namespace": "export-ns"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["memory_count"] == 1
    assert data["memories"][0]["versions"][0]["content"]["title"] == "exportable memory"


def test_import_round_trips_export_bundle(client: TestClient) -> None:
    memory_id = _create(client, namespace="rt-api", title="round trip memory")
    client.patch(
        f"/v1/memories/{memory_id}",
        json={"title": "round trip memory revised"},
        headers={"If-Match": "1"},
    )
    before = client.get(f"/v1/memories/{memory_id}").json()["data"]
    bundle = client.post("/v1/export", json={"namespace": "rt-api"}).json()["data"]

    import_response = client.post("/v1/import", json=bundle)
    assert import_response.status_code == 200
    report = import_response.json()["data"]
    assert report["imported"] == []  # already present locally -> skipped, never overwritten
    assert report["skipped"] == [{"memory_id": memory_id, "reason": "already exists"}]

    after = client.get(f"/v1/memories/{memory_id}").json()["data"]
    assert after == before


def test_import_rejects_malformed_bundle(client: TestClient) -> None:
    response = client.post(
        "/v1/import",
        json={"memories": [{"memory_id": "bad", "versions": [{"not": "valid"}]}]},
    )
    assert response.status_code == 200
    report = response.json()["data"]
    assert report["rejected"][0]["memory_id"] == "bad"


def test_import_missing_memories_field_defaults_to_empty(client: TestClient) -> None:
    response = client.post("/v1/import", json={})
    assert response.status_code == 200
    assert response.json()["data"] == {"imported": [], "skipped": [], "rejected": []}
