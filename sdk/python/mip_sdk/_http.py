"""Low-level HTTP transport: envelope unwrapping, error translation, retries.

The only module allowed to import `httpx` directly (mirrors the backend rule
that SQL is confined to `storage/sqlite/` — here, transport is confined here).
"""

from __future__ import annotations

from typing import Any

import httpx

from mip_sdk.errors import MIPConnectionError, error_from_envelope

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_API_VERSION = "1.0"


class Transport:
    def __init__(
        self,
        base_url: str,
        *,
        api_version: str = DEFAULT_API_VERSION,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client: httpx.Client | None = None,
    ) -> None:
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"MIP-API-Version": api_version},
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Transport:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Send a request and return the unwrapped `data` payload on success."""
        try:
            response = self._client.request(method, path, json=json, params=params, headers=headers)
        except httpx.RequestError as exc:
            raise MIPConnectionError(f"Could not reach MIP API at {exc.request.url}") from exc
        body: dict[str, Any] = response.json() if response.content else {}
        # Keyed on the presence of an `error` envelope, not the HTTP status: some
        # endpoints (e.g. /v1/health) legitimately return a non-2xx status with a
        # normal `data` envelope to signal degraded state to infra, not a MEM-* error.
        if "error" in body:
            raise error_from_envelope(body, response.status_code)
        return body.get("data")
