"""Typed error hierarchy mirroring the `MEM-*` envelope (05-api-design.md).

Mirrors the category taxonomy in `backend/mip/core/errors.py` so client code
can catch `LifecycleError` etc. the same way server code does. Callers must
key on `.code`, never on `.message` (message text is not part of the contract).
"""

from __future__ import annotations

from typing import Any


class MIPAPIError(Exception):
    """Base of all typed API errors; carries the full structured envelope."""

    category: str = "Unknown"

    def __init__(
        self,
        *,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        recoverable: bool = False,
        documentation_url: str = "",
        http_status: int = 500,
        request_id: str | None = None,
    ) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable
        self.documentation_url = documentation_url
        self.http_status = http_status
        self.request_id = request_id


class ValidationError(MIPAPIError):
    category = "Validation"


class LifecycleError(MIPAPIError):
    category = "Lifecycle"


class IdentityError(MIPAPIError):
    category = "Identity"


class ConcurrencyError(MIPAPIError):
    category = "Concurrency"


class TrustError(MIPAPIError):
    category = "Trust"


class StorageError(MIPAPIError):
    category = "Storage"


class SyncError(MIPAPIError):
    category = "Sync"


class SecurityError(MIPAPIError):
    category = "Security"


class MIPConnectionError(Exception):
    """The server could not be reached at all (no HTTP response received)."""


_CATEGORY_TO_ERROR: dict[str, type[MIPAPIError]] = {
    "Validation": ValidationError,
    "Lifecycle": LifecycleError,
    "Identity": IdentityError,
    "Concurrency": ConcurrencyError,
    "Trust": TrustError,
    "Storage": StorageError,
    "Sync": SyncError,
    "Security": SecurityError,
}


def error_from_envelope(body: dict[str, Any], http_status: int) -> MIPAPIError:
    """Build the typed exception for a `{"error": {...}, "request_id": ...}` body."""
    error = body.get("error") or {}
    category = str(error.get("category", "Unknown"))
    error_cls = _CATEGORY_TO_ERROR.get(category, MIPAPIError)
    return error_cls(
        code=str(error.get("code", "MEM-0000")),
        message=str(error.get("message", "Unknown error")),
        details=error.get("details") or {},
        recoverable=bool(error.get("recoverable", False)),
        documentation_url=str(error.get("documentation_url", "")),
        http_status=http_status,
        request_id=body.get("request_id"),
    )
