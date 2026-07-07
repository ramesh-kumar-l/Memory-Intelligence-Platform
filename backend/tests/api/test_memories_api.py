"""API contract suite: success envelope shape, error envelope shape, lifecycle
semantics over HTTP (05-api-design.md). Never allowed to be red or skipped.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from tests.factories import create_payload


def _assert_success_envelope(body: dict[str, Any]) -> None:
    for field in ("data", "request_id", "schema_version", "processing_time_ms"):
        assert field in body


def _assert_error_envelope(body: dict[str, Any], code: str) -> None:
    assert body["error"]["code"] == code
    for field in ("category", "message", "details", "recoverable", "documentation_url"):
        assert field in body["error"]
    assert "request_id" in body


def _create(client: TestClient, **overrides: Any) -> dict[str, Any]:
    response = client.post("/v1/memories", json=create_payload(**overrides))
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()["data"]
    return data


class TestCreateMemory:
    def test_create_returns_201_active_memory(self, client: TestClient) -> None:
        response = client.post("/v1/memories", json=create_payload())
        assert response.status_code == 201
        body = response.json()
        _assert_success_envelope(body)
        assert body["data"]["lifecycle"]["state"] == "Active"
        assert body["data"]["lifecycle"]["version"] == 1
        assert "storage" not in body["data"]  # Section 9 never exposed
        assert response.headers["X-Request-Id"] == body["request_id"]

    def test_missing_title_rejected(self, client: TestClient) -> None:
        payload = create_payload()
        del payload["title"]
        response = client.post("/v1/memories", json=payload)
        assert response.status_code == 422
        _assert_error_envelope(response.json(), "MEM-1004")

    def test_memory_without_semantics_rejected(self, client: TestClient) -> None:
        response = client.post("/v1/memories", json=create_payload(semantics={}))
        assert response.status_code == 422
        _assert_error_envelope(response.json(), "MEM-1003")

    def test_confidence_out_of_range_rejected(self, client: TestClient) -> None:
        response = client.post("/v1/memories", json=create_payload(confidence=1.5))
        assert response.status_code == 422
        _assert_error_envelope(response.json(), "MEM-1004")

    def test_relationship_to_existing_memory(self, client: TestClient) -> None:
        target = _create(client, title="target")
        data = _create(
            client,
            title="source",
            relationships=[{"target_memory_id": target["memory_id"], "type": "references"}],
        )
        assert data["relationships"][0]["target_memory_id"] == target["memory_id"]

    def test_relationship_to_missing_target_rejected(self, client: TestClient) -> None:
        payload = create_payload(
            relationships=[
                {
                    "target_memory_id": "00000000-0000-0000-0000-000000000000",
                    "type": "references",
                }
            ]
        )
        response = client.post("/v1/memories", json=payload)
        assert response.status_code == 422
        _assert_error_envelope(response.json(), "MEM-1006")

    def test_unresolved_relationship_target_allowed(self, client: TestClient) -> None:
        data = _create(
            client,
            relationships=[
                {
                    "target_memory_id": "00000000-0000-0000-0000-000000000000",
                    "type": "references",
                    "unresolved": True,
                }
            ],
        )
        assert data["relationships"][0]["unresolved"] is True


class TestGetMemory:
    def test_get_returns_current_version(self, client: TestClient) -> None:
        created = _create(client)
        response = client.get(f"/v1/memories/{created['memory_id']}")
        assert response.status_code == 200
        _assert_success_envelope(response.json())
        assert response.json()["data"]["memory_id"] == created["memory_id"]

    def test_get_unknown_memory_is_404(self, client: TestClient) -> None:
        response = client.get("/v1/memories/does-not-exist")
        assert response.status_code == 404
        _assert_error_envelope(response.json(), "MEM-3001")

    def test_get_historical_version(self, client: TestClient) -> None:
        created = _create(client, title="first title")
        client.patch(
            f"/v1/memories/{created['memory_id']}",
            json={"title": "second title"},
            headers={"If-Match": "1"},
        )
        response = client.get(f"/v1/memories/{created['memory_id']}", params={"version": 1})
        assert response.json()["data"]["content"]["title"] == "first title"

    def test_get_missing_version_is_404(self, client: TestClient) -> None:
        created = _create(client)
        response = client.get(f"/v1/memories/{created['memory_id']}", params={"version": 9})
        assert response.status_code == 404
        _assert_error_envelope(response.json(), "MEM-3002")

    def test_versions_listing(self, client: TestClient) -> None:
        created = _create(client)
        client.patch(
            f"/v1/memories/{created['memory_id']}",
            json={"summary": "updated"},
            headers={"If-Match": "1"},
        )
        response = client.get(f"/v1/memories/{created['memory_id']}/versions")
        versions = response.json()["data"]["versions"]
        assert [(v["version"], v["previous_version"]) for v in versions] == [(1, None), (2, 1)]


class TestUpdateMemory:
    def test_update_creates_version_two(self, client: TestClient) -> None:
        created = _create(client)
        response = client.patch(
            f"/v1/memories/{created['memory_id']}",
            json={"title": "revised", "update_reason": "clarity"},
            headers={"If-Match": "1"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["lifecycle"]["version"] == 2
        assert data["content"]["title"] == "revised"
        assert data["audit"]["update_reason"] == "clarity"

    def test_update_without_if_match_is_428(self, client: TestClient) -> None:
        created = _create(client)
        response = client.patch(f"/v1/memories/{created['memory_id']}", json={"title": "x"})
        assert response.status_code == 428
        _assert_error_envelope(response.json(), "MEM-4002")

    def test_update_with_stale_if_match_is_409(self, client: TestClient) -> None:
        created = _create(client)
        response = client.patch(
            f"/v1/memories/{created['memory_id']}",
            json={"title": "x"},
            headers={"If-Match": "7"},
        )
        assert response.status_code == 409
        _assert_error_envelope(response.json(), "MEM-4001")

    def test_update_with_malformed_if_match_is_422(self, client: TestClient) -> None:
        created = _create(client)
        response = client.patch(
            f"/v1/memories/{created['memory_id']}",
            json={"title": "x"},
            headers={"If-Match": "abc"},
        )
        assert response.status_code == 422
        _assert_error_envelope(response.json(), "MEM-1004")

    def test_update_archived_memory_is_409(self, client: TestClient) -> None:
        created = _create(client)
        client.post(f"/v1/memories/{created['memory_id']}/archive")
        response = client.patch(
            f"/v1/memories/{created['memory_id']}",
            json={"title": "x"},
            headers={"If-Match": "1"},
        )
        assert response.status_code == 409
        _assert_error_envelope(response.json(), "MEM-2002")


class TestArchiveRestoreDelete:
    def test_archive_then_restore(self, client: TestClient) -> None:
        created = _create(client)
        archived = client.post(f"/v1/memories/{created['memory_id']}/archive")
        assert archived.json()["data"]["lifecycle"]["state"] == "Archived"
        restored = client.post(f"/v1/memories/{created['memory_id']}/restore")
        assert restored.json()["data"]["lifecycle"]["state"] == "Active"

    def test_archive_and_restore_are_idempotent(self, client: TestClient) -> None:
        created = _create(client)
        client.post(f"/v1/memories/{created['memory_id']}/archive")
        again = client.post(f"/v1/memories/{created['memory_id']}/archive")
        assert again.status_code == 200
        assert again.json()["data"]["lifecycle"]["state"] == "Archived"
        client.post(f"/v1/memories/{created['memory_id']}/restore")
        again = client.post(f"/v1/memories/{created['memory_id']}/restore")
        assert again.status_code == 200
        assert again.json()["data"]["lifecycle"]["state"] == "Active"

    def test_delete_is_idempotent(self, client: TestClient) -> None:
        created = _create(client)
        first = client.delete(f"/v1/memories/{created['memory_id']}")
        assert first.status_code == 200
        assert first.json()["data"]["state"] == "Deleted"
        second = client.delete(f"/v1/memories/{created['memory_id']}")
        assert second.status_code == 200  # FR-API-005

    def test_get_after_delete_is_410(self, client: TestClient) -> None:
        created = _create(client)
        client.delete(f"/v1/memories/{created['memory_id']}")
        response = client.get(f"/v1/memories/{created['memory_id']}")
        assert response.status_code == 410
        _assert_error_envelope(response.json(), "MEM-2003")

    def test_delete_archived_memory_is_illegal(self, client: TestClient) -> None:
        created = _create(client)
        client.post(f"/v1/memories/{created['memory_id']}/archive")
        response = client.delete(f"/v1/memories/{created['memory_id']}")
        assert response.status_code == 409
        _assert_error_envelope(response.json(), "MEM-2001")  # only Active → Deleted is legal


class TestListMemories:
    def test_pagination_with_continuation_token(self, client: TestClient) -> None:
        for index in range(3):
            _create(client, namespace="paging", title=f"memory {index}")
        first_page = client.get("/v1/memories", params={"namespace": "paging", "limit": 2})
        body = first_page.json()["data"]
        assert len(body["items"]) == 2
        assert body["complete"] is False
        assert body["continuation_token"]
        second_page = client.get(
            "/v1/memories",
            params={
                "namespace": "paging",
                "limit": 2,
                "continuation_token": body["continuation_token"],
            },
        )
        second_body = second_page.json()["data"]
        assert len(second_body["items"]) == 1
        assert second_body["complete"] is True
        assert second_body["continuation_token"] is None
        all_ids = {item["memory_id"] for item in body["items"] + second_body["items"]}
        assert len(all_ids) == 3  # no duplicates, no gaps

    def test_deleted_memories_hidden_unless_filtered(self, client: TestClient) -> None:
        kept = _create(client, namespace="tombstones", title="kept")
        gone = _create(client, namespace="tombstones", title="gone")
        client.delete(f"/v1/memories/{gone['memory_id']}")
        default = client.get("/v1/memories", params={"namespace": "tombstones"})
        ids = [item["memory_id"] for item in default.json()["data"]["items"]]
        assert ids == [kept["memory_id"]] or set(ids) == {kept["memory_id"]}
        deleted = client.get("/v1/memories", params={"namespace": "tombstones", "state": "Deleted"})
        deleted_ids = [item["memory_id"] for item in deleted.json()["data"]["items"]]
        assert deleted_ids == [gone["memory_id"]]

    def test_unknown_state_filter_rejected(self, client: TestClient) -> None:
        response = client.get("/v1/memories", params={"state": "Bogus"})
        assert response.status_code == 422
        _assert_error_envelope(response.json(), "MEM-1004")

    def test_malformed_continuation_token_rejected(self, client: TestClient) -> None:
        response = client.get("/v1/memories", params={"continuation_token": "not-a-token"})
        assert response.status_code == 422
        _assert_error_envelope(response.json(), "MEM-1004")


class TestOperationalEndpoints:
    def test_health(self, client: TestClient) -> None:
        response = client.get("/v1/health")
        assert response.status_code == 200
        assert response.json()["data"] == {"status": "ok", "storage": True}

    def test_version(self, client: TestClient) -> None:
        response = client.get("/v1/version")
        data = response.json()["data"]
        assert "1.0" in data["api_versions"]
        assert data["schema_version"] == "1.0"

    def test_unsupported_api_version_negotiation(self, client: TestClient) -> None:
        response = client.get("/v1/health", headers={"MIP-API-Version": "9.9"})
        assert response.status_code == 400
        _assert_error_envelope(response.json(), "MEM-1005")

    def test_supported_api_version_accepted(self, client: TestClient) -> None:
        response = client.get("/v1/health", headers={"MIP-API-Version": "1.0"})
        assert response.status_code == 200
