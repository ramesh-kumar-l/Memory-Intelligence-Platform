"""POST /v1/context contract tests (Phase 2 task 5)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.factories import create_payload


def test_build_context_returns_context_package(client: TestClient) -> None:
    client.post(
        "/v1/memories",
        json=create_payload(title="Quarterly revenue growth in the cloud division"),
    )
    response = client.post("/v1/context", json={"query": "revenue cloud", "mode": "hybrid"})
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["query"] == "revenue cloud"
    assert len(body["items"]) == 1
    assert "memory" in body["items"][0]
    assert body["complete"] is True
    assert body["continuation_token"] is None


def test_build_context_missing_query_and_token_rejected(client: TestClient) -> None:
    response = client.post("/v1/context", json={})
    assert response.status_code == 422


def test_build_context_pagination(client: TestClient) -> None:
    for i in range(3):
        client.post("/v1/memories", json=create_payload(title=f"Context page item {i}"))
    first = client.post(
        "/v1/context", json={"query": "context page item", "mode": "keyword", "limit": 2}
    ).json()["data"]
    assert first["complete"] is False
    assert first["continuation_token"] is not None
    second = client.post(
        "/v1/context", json={"continuation_token": first["continuation_token"], "mode": "keyword"}
    ).json()["data"]
    assert second["complete"] is True
