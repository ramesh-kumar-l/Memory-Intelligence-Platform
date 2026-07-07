"""Projection rebuild over HTTP: replay must report identical state."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.factories import create_payload


def test_rebuild_projections_reports_identical(client: TestClient) -> None:
    created = client.post("/v1/memories", json=create_payload()).json()["data"]
    memory_id = created["memory_id"]
    client.patch(f"/v1/memories/{memory_id}", json={"title": "v2"}, headers={"If-Match": "1"})
    client.post(f"/v1/memories/{memory_id}/archive")

    response = client.post("/v1/admin/rebuild-projections")
    assert response.status_code == 200
    report = response.json()["data"]
    assert report["identical"] is True
    assert report["memories"] == 1
    assert report["events_replayed"] > 0

    # State fully intact after rebuild.
    memory = client.get(f"/v1/memories/{memory_id}").json()["data"]
    assert memory["lifecycle"]["state"] == "Archived"
    assert memory["lifecycle"]["version"] == 2
