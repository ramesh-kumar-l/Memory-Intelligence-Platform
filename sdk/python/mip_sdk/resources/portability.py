"""Export/Import — Phase 4 task 4 (ADR-0006)."""

from __future__ import annotations

from typing import Any

from mip_sdk._http import Transport
from mip_sdk.models.intelligence import ExportBundle, ImportReport
from mip_sdk.models.requests import ExportRequest


class PortabilityResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def export(self, request: ExportRequest | None = None, **kwargs: Any) -> ExportBundle:
        request = request or ExportRequest(**kwargs)
        data = self._transport.request(
            "POST", "/v1/export", json=request.model_dump(mode="json", exclude_none=True)
        )
        return ExportBundle.model_validate(data)

    def import_(self, bundle: ExportBundle | dict[str, Any]) -> ImportReport:
        """Named `import_` — `import` is a Python reserved word."""
        body = bundle.model_dump(mode="json") if isinstance(bundle, ExportBundle) else bundle
        data = self._transport.request("POST", "/v1/import", json=body)
        return ImportReport.model_validate(data)
