"""Idempotency-Key contract: repeated key returns the original result; same
key with a different payload is rejected (05-api-design.md).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.factories import create_payload


def test_repeated_create_returns_original_result(client: TestClient) -> None:
    headers = {"Idempotency-Key": "create-key-1"}
    first = client.post("/v1/memories", json=create_payload(), headers=headers)
    second = client.post("/v1/memories", json=create_payload(), headers=headers)
    assert first.status_code == second.status_code == 201
    assert second.json() == first.json()  # byte-identical replay, same memory_id

    listing = client.get("/v1/memories", params={"namespace": "default"})
    assert len(listing.json()["data"]["items"]) == 1  # only one memory was created


def test_key_reuse_with_different_payload_is_409(client: TestClient) -> None:
    headers = {"Idempotency-Key": "create-key-2"}
    client.post("/v1/memories", json=create_payload(title="one"), headers=headers)
    conflict = client.post("/v1/memories", json=create_payload(title="two"), headers=headers)
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "MEM-4003"


def test_repeated_update_does_not_create_extra_versions(client: TestClient) -> None:
    created = client.post("/v1/memories", json=create_payload()).json()["data"]
    memory_id = created["memory_id"]
    headers = {"If-Match": "1", "Idempotency-Key": "update-key-1"}
    first = client.patch(f"/v1/memories/{memory_id}", json={"title": "v2"}, headers=headers)
    second = client.patch(f"/v1/memories/{memory_id}", json={"title": "v2"}, headers=headers)
    assert first.status_code == second.status_code == 200
    assert second.json() == first.json()
    current = client.get(f"/v1/memories/{memory_id}").json()["data"]
    assert current["lifecycle"]["version"] == 2  # not 3 — replay, not re-execution
