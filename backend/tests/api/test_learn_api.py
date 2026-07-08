"""POST /v1/learn contract tests (Phase 4 task 3, ADR-0006). Idempotency-Key
semantics mirror Create/Update (05-api-design.md).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.factories import create_payload


def _create(client: TestClient, **overrides: object) -> str:
    response = client.post("/v1/memories", json=create_payload(**overrides))
    return str(response.json()["data"]["memory_id"])


def test_learn_adds_derived_concepts(client: TestClient) -> None:
    memory_id = _create(client)
    response = client.post(
        "/v1/learn",
        json={
            "memory_id": memory_id,
            "derived": {"concepts": ["durability-guarantees"]},
            "reason": "pattern observed",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "durability-guarantees" in data["semantics"]["concepts"]
    assert data["lifecycle"]["version"] == 2


def test_learn_matures_evidence(client: TestClient) -> None:
    memory_id = _create(client)
    response = client.post(
        "/v1/learn",
        json={
            "memory_id": memory_id,
            "new_evidence": [{"source": "doc-1"}, {"source": "doc-2"}],
            "verifier": "reviewer-1",
            "reason": "corroborating documents",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["trust"]["evidence"]) == 2
    assert data["trust"]["source_count"] == 3


def test_learn_requires_derived_or_evidence(client: TestClient) -> None:
    memory_id = _create(client)
    response = client.post("/v1/learn", json={"memory_id": memory_id, "reason": "nothing"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MEM-1004"


def test_learn_repeated_idempotency_key_returns_original_result(client: TestClient) -> None:
    memory_id = _create(client)
    payload = {
        "memory_id": memory_id,
        "derived": {"concepts": ["x"]},
        "reason": "same request twice",
    }
    headers = {"Idempotency-Key": "learn-key-1"}
    first = client.post("/v1/learn", json=payload, headers=headers)
    second = client.post("/v1/learn", json=payload, headers=headers)
    assert first.status_code == second.status_code == 200
    assert first.json()["data"] == second.json()["data"]
    assert first.json()["data"]["lifecycle"]["version"] == 2  # not applied twice
