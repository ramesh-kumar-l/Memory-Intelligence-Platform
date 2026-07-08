"""API-key auth + namespace/ownership enforcement contract tests (ADR-0007).
Auth is opt-in — see `test_auth_disabled_by_default_requires_no_key` and
`22-deployment.md`.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mip.api.app import create_app
from mip.config import MIPSettings
from tests.factories import create_payload


@pytest.fixture
def auth_client(tmp_path: Path) -> Iterator[TestClient]:
    settings = MIPSettings(
        db_path=tmp_path / "auth.db",
        auth_enabled=True,
        api_keys={
            "scoped-key": ("team-a",),
            "multi-key": ("team-a", "team-b"),
            "admin-key": ("*",),
        },
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def _headers(key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {key}"}


def test_missing_api_key_is_rejected(auth_client: TestClient) -> None:
    response = auth_client.post("/v1/memories", json=create_payload(namespace="team-a"))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MEM-8001"


def test_invalid_api_key_is_rejected(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/v1/memories", json=create_payload(namespace="team-a"), headers=_headers("nope")
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MEM-8002"


def test_health_and_version_stay_public(auth_client: TestClient) -> None:
    assert auth_client.get("/v1/health").status_code == 200
    assert auth_client.get("/v1/version").status_code == 200


def test_admin_rebuild_requires_api_key(auth_client: TestClient) -> None:
    assert auth_client.post("/v1/admin/rebuild-projections").status_code == 401


def test_scoped_key_can_create_in_its_namespace(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/v1/memories", json=create_payload(namespace="team-a"), headers=_headers("scoped-key")
    )
    assert response.status_code == 201


def test_scoped_key_forbidden_cross_namespace_create(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/v1/memories", json=create_payload(namespace="team-b"), headers=_headers("scoped-key")
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "MEM-8003"


def test_scoped_key_cannot_read_foreign_namespace_memory(auth_client: TestClient) -> None:
    memory_id = auth_client.post(
        "/v1/memories", json=create_payload(namespace="team-b"), headers=_headers("admin-key")
    ).json()["data"]["memory_id"]
    response = auth_client.get(f"/v1/memories/{memory_id}", headers=_headers("scoped-key"))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "MEM-8003"


def test_delete_stays_idempotent_after_namespace_check(auth_client: TestClient) -> None:
    memory_id = auth_client.post(
        "/v1/memories", json=create_payload(namespace="team-a"), headers=_headers("admin-key")
    ).json()["data"]["memory_id"]
    first = auth_client.delete(f"/v1/memories/{memory_id}", headers=_headers("scoped-key"))
    second = auth_client.delete(f"/v1/memories/{memory_id}", headers=_headers("scoped-key"))
    assert first.status_code == 200
    assert second.status_code == 200


def test_multi_namespace_key_must_specify_namespace_on_list(auth_client: TestClient) -> None:
    response = auth_client.get("/v1/memories", headers=_headers("multi-key"))
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MEM-8004"


def test_single_namespace_key_list_defaults_to_its_namespace(auth_client: TestClient) -> None:
    auth_client.post(
        "/v1/memories", json=create_payload(namespace="team-a"), headers=_headers("scoped-key")
    )
    response = auth_client.get("/v1/memories", headers=_headers("scoped-key"))
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert items and all(item["namespace"] == "team-a" for item in items)


def test_learn_forbidden_cross_namespace(auth_client: TestClient) -> None:
    memory_id = auth_client.post(
        "/v1/memories", json=create_payload(namespace="team-b"), headers=_headers("admin-key")
    ).json()["data"]["memory_id"]
    response = auth_client.post(
        "/v1/learn",
        json={"memory_id": memory_id, "reason": "test"},
        headers=_headers("scoped-key"),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "MEM-8003"


def test_consolidate_forbidden_cross_namespace(auth_client: TestClient) -> None:
    admin = _headers("admin-key")
    primary = auth_client.post(
        "/v1/memories", json=create_payload(namespace="team-a"), headers=admin
    ).json()["data"]["memory_id"]
    duplicate = auth_client.post(
        "/v1/memories", json=create_payload(namespace="team-b"), headers=admin
    ).json()["data"]["memory_id"]
    response = auth_client.post(
        "/v1/consolidate",
        json={"primary_memory_id": primary, "duplicate_memory_ids": [duplicate]},
        headers=_headers("scoped-key"),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "MEM-8003"


def test_export_scoped_key_defaults_to_its_namespace(auth_client: TestClient) -> None:
    auth_client.post(
        "/v1/memories", json=create_payload(namespace="team-a"), headers=_headers("scoped-key")
    )
    response = auth_client.post("/v1/export", json={}, headers=_headers("scoped-key"))
    assert response.status_code == 200
    assert response.json()["data"]["namespace"] == "team-a"


def test_auth_disabled_by_default_requires_no_key(client: TestClient) -> None:
    response = client.post("/v1/memories", json=create_payload())
    assert response.status_code == 201
