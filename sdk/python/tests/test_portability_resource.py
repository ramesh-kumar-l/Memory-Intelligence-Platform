"""Export/Import resource tests (Phase 4 task 4, mock transport)."""

from __future__ import annotations

import httpx

from mip_sdk.models.requests import ExportRequest
from tests.conftest import MakeClient, envelope


def _bundle_dict() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "exported_at": "2026-07-08T00:00:00Z",
        "namespace": "demo",
        "memory_count": 0,
        "memories": [],
    }


def test_export_returns_typed_bundle(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/export"
        return httpx.Response(200, json=envelope(_bundle_dict()))

    client = make_client(handler)
    bundle = client.portability.export(ExportRequest(namespace="demo"))
    assert bundle.namespace == "demo"
    assert bundle.memory_count == 0


def test_import_accepts_export_bundle_object(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/export":
            return httpx.Response(200, json=envelope(_bundle_dict()))
        assert request.url.path == "/v1/import"
        return httpx.Response(200, json=envelope({"imported": [], "skipped": [], "rejected": []}))

    client = make_client(handler)
    bundle = client.portability.export(ExportRequest(namespace="demo"))
    report = client.portability.import_(bundle)
    assert report.imported == ()
    assert report.skipped == ()
    assert report.rejected == ()
