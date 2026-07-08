"""POST /v1/search contract tests (Phase 2 tasks 1-3, FR-API-007)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.factories import create_payload


def _create(client: TestClient, **overrides: object) -> str:
    response = client.post("/v1/memories", json=create_payload(**overrides))
    return str(response.json()["data"]["memory_id"])


def test_keyword_search_finds_created_memory(client: TestClient) -> None:
    memory_id = _create(client, title="SQLite WAL mode enables concurrent readers")
    response = client.post("/v1/search", json={"query": "WAL concurrent", "mode": "keyword"})
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["items"][0]["memory_id"] == memory_id
    assert body["items"][0]["explanation"]["mode"] == "keyword"
    assert body["complete"] is True


def test_semantic_and_hybrid_modes_return_200(client: TestClient) -> None:
    _create(client, title="Revenue grew due to strong enterprise cloud sales")
    for mode in ("semantic", "hybrid"):
        response = client.post("/v1/search", json={"query": "revenue cloud sales", "mode": mode})
        assert response.status_code == 200, mode


def test_unsupported_mode_returns_mem_1007(client: TestClient) -> None:
    response = client.post("/v1/search", json={"query": "anything", "mode": "graph"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MEM-1007"


def test_missing_query_and_no_continuation_token_is_rejected(client: TestClient) -> None:
    response = client.post("/v1/search", json={"mode": "keyword"})
    assert response.status_code == 422


def test_continuation_token_resumes_the_same_query(client: TestClient) -> None:
    for i in range(3):
        _create(client, title=f"Paginated widget number {i}", namespace=f"ns-page-{i}")
    first = client.post(
        "/v1/search", json={"query": "widget", "mode": "keyword", "limit": 2}
    ).json()["data"]
    assert first["complete"] is False
    token = first["continuation_token"]
    assert token is not None
    second = client.post(
        "/v1/search", json={"continuation_token": token, "mode": "keyword"}
    ).json()["data"]
    assert second["complete"] is True
    first_ids = {item["memory_id"] for item in first["items"]}
    second_ids = {item["memory_id"] for item in second["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_malformed_continuation_token_is_rejected(client: TestClient) -> None:
    response = client.post("/v1/search", json={"continuation_token": "not-a-real-token"})
    assert response.status_code == 422
