"""Health, version negotiation info, and projection rebuild (operational ops)."""

from __future__ import annotations

from typing import Any

from mip_sdk._http import Transport


class AdminResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def health(self) -> dict[str, Any]:
        result: dict[str, Any] = self._transport.request("GET", "/v1/health")
        return result

    def version(self) -> dict[str, Any]:
        result: dict[str, Any] = self._transport.request("GET", "/v1/version")
        return result

    def rebuild_projections(self) -> dict[str, Any]:
        result: dict[str, Any] = self._transport.request("POST", "/v1/admin/rebuild-projections")
        return result
