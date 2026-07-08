"""POST /v1/explain contract tests (Phase 2 task 4, FR-API-007)."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from tests.factories import create_payload


def test_explain_without_query_returns_trust_fields(client: TestClient) -> None:
    created = client.post("/v1/memories", json=create_payload()).json()["data"]
    response = client.post("/v1/explain", json={"memory_id": created["memory_id"]})
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["memory_id"] == created["memory_id"]
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["freshness"] == 1.0
    assert body["provenance"]["source"] == "api-test"
    assert body["ranking"] is None


def test_explain_with_query_includes_ranking_explanation(client: TestClient) -> None:
    created = client.post(
        "/v1/memories", json=create_payload(title="SQLite WAL mode enables concurrent readers")
    ).json()["data"]
    response = client.post(
        "/v1/explain",
        json={"memory_id": created["memory_id"], "query": "WAL concurrent", "mode": "keyword"},
    )
    assert response.status_code == 200
    ranking = response.json()["data"]["ranking"]
    assert ranking["matched"] is True
    assert ranking["mode"] == "keyword"
    assert ranking["score"] > 0.0


def test_explain_unknown_memory_returns_404(client: TestClient) -> None:
    response = client.post("/v1/explain", json={"memory_id": str(uuid.uuid4())})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MEM-3001"


def test_explain_deleted_memory_returns_410(client: TestClient) -> None:
    created = client.post("/v1/memories", json=create_payload()).json()["data"]
    memory_id = created["memory_id"]
    client.delete(f"/v1/memories/{memory_id}")
    response = client.post("/v1/explain", json={"memory_id": memory_id})
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "MEM-2003"
