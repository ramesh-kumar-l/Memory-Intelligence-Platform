from __future__ import annotations

import json

import httpx

from mip_sdk.models.memory import Semantics
from mip_sdk.models.requests import CreateMemoryRequest, ProvenanceInput, UpdateMemoryRequest
from tests.conftest import MakeClient, envelope
from tests.factories import MEMORY_ID, sample_memory_dict, sample_memory_record_dict


def test_create_memory_returns_typed_memory_object(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/memories"
        body = json.loads(request.content)
        assert body["title"] == "Sample memory"
        return httpx.Response(201, json=envelope(sample_memory_dict()))

    client = make_client(handler)
    request = CreateMemoryRequest(
        namespace="demo",
        owner_id="user-1",
        title="Sample memory",
        semantics=Semantics(keywords=("sample",)),
        provenance=ProvenanceInput(source="test-suite"),
    )
    memory = client.memories.create(request)
    assert memory.memory_id == MEMORY_ID
    assert memory.content.title == "Sample memory"
    assert memory.lifecycle.state.value == "Active"


def test_create_memory_sends_idempotency_key_header(make_client: MakeClient) -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(request.headers)
        return httpx.Response(201, json=envelope(sample_memory_dict()))

    client = make_client(handler)
    request = CreateMemoryRequest(
        namespace="demo",
        owner_id="user-1",
        title="Sample memory",
        semantics=Semantics(keywords=("sample",)),
        provenance=ProvenanceInput(source="test-suite"),
    )
    client.memories.create(request, idempotency_key="key-123")
    assert seen_headers["idempotency-key"] == "key-123"


def test_get_memory_with_version_query_param(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["version"] == "2"
        return httpx.Response(
            200,
            json=envelope(
                sample_memory_dict(
                    **{"lifecycle": {**sample_memory_dict()["lifecycle"], "version": 2}}
                )
            ),
        )

    client = make_client(handler)
    memory = client.memories.get(MEMORY_ID, version=2)
    assert memory.lifecycle.version == 2


def test_list_memories_returns_page(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/memories"
        return httpx.Response(
            200,
            json=envelope(
                {
                    "items": [sample_memory_record_dict()],
                    "complete": False,
                    "continuation_token": "mid:next",
                }
            ),
        )

    client = make_client(handler)
    page = client.memories.list(namespace="demo", limit=10)
    assert len(page.items) == 1
    assert page.items[0].memory_id == MEMORY_ID
    assert page.complete is False
    assert page.continuation_token == "mid:next"


def test_update_memory_sends_if_match_header(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["if-match"] == "1"
        body = json.loads(request.content)
        assert body["title"] == "New title"
        return httpx.Response(
            200,
            json=envelope(
                sample_memory_dict(
                    **{"content": {**sample_memory_dict()["content"], "title": "New title"}}
                )
            ),
        )

    client = make_client(handler)
    memory = client.memories.update(
        MEMORY_ID, UpdateMemoryRequest(title="New title"), expected_version=1
    )
    assert memory.content.title == "New title"


def test_delete_memory_is_idempotent_shaped_response(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        return httpx.Response(200, json=envelope({"memory_id": MEMORY_ID, "deleted": True}))

    client = make_client(handler)
    result = client.memories.delete(MEMORY_ID)
    assert result == {"memory_id": MEMORY_ID, "deleted": True}


def test_archive_and_restore(make_client: MakeClient) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        state = "Archived" if request.url.path.endswith("archive") else "Active"
        memory = sample_memory_dict()
        memory["lifecycle"] = {**memory["lifecycle"], "state": state}
        return httpx.Response(200, json=envelope(memory))

    client = make_client(handler)
    archived = client.memories.archive(MEMORY_ID)
    restored = client.memories.restore(MEMORY_ID)
    assert archived.lifecycle.state.value == "Archived"
    assert restored.lifecycle.state.value == "Active"
    assert calls == [f"/v1/memories/{MEMORY_ID}/archive", f"/v1/memories/{MEMORY_ID}/restore"]


def test_list_versions(make_client: MakeClient) -> None:
    version_info = {"version": 1, "previous_version": None, "created_at": "2026-07-08T00:00:00Z"}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=envelope({"memory_id": MEMORY_ID, "versions": [version_info]}),
        )

    client = make_client(handler)
    versions = client.memories.list_versions(MEMORY_ID)
    assert len(versions) == 1
    assert versions[0].version == 1
    assert versions[0].previous_version is None
