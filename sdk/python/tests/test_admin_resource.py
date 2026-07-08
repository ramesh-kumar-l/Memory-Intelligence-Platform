from __future__ import annotations

import httpx

from tests.conftest import MakeClient, envelope


def test_health_ok(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=envelope({"status": "ok", "storage": True}))

    client = make_client(handler)
    assert client.admin.health() == {"status": "ok", "storage": True}


def test_health_degraded_503_is_not_raised_as_error(make_client: MakeClient) -> None:
    """503 with a `data` envelope signals degraded state, not a MEM-* failure."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json=envelope({"status": "degraded", "storage": False}))

    client = make_client(handler)
    result = client.admin.health()
    assert result == {"status": "degraded", "storage": False}


def test_version(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=envelope(
                {"service_version": "0.1.0", "api_versions": ["1.0"], "schema_version": "1.0"}
            ),
        )

    client = make_client(handler)
    info = client.admin.version()
    assert info["service_version"] == "0.1.0"


def test_rebuild_projections(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/admin/rebuild-projections"
        return httpx.Response(200, json=envelope({"replayed_events": 3, "indexed_memories": 1}))

    client = make_client(handler)
    report = client.admin.rebuild_projections()
    assert report["indexed_memories"] == 1
