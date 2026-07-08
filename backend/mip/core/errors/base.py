"""The `MIPError` hierarchy and category taxonomy (05-api-design.md).

Split from `mip.core.errors` into `base.py` (classes) + `factories.py`
(registry) purely to keep each file under the 300-line modularity budget —
`mip.core.errors` (this package's `__init__.py`) re-exports both, so no
caller-visible import path changed.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, ClassVar

DOCUMENTATION_URL_BASE = (
    "https://github.com/mip-platform/memory-intelligence-platform/blob/main/docs/errors.md#"
)


class ErrorCategory(StrEnum):
    VALIDATION = "Validation"
    LIFECYCLE = "Lifecycle"
    IDENTITY = "Identity"
    CONCURRENCY = "Concurrency"
    TRUST = "Trust"
    STORAGE = "Storage"
    SYNC = "Sync"
    SECURITY = "Security"


class MIPError(Exception):
    """Base of all platform errors; carries the structured error envelope (INV-API-003)."""

    category: ClassVar[ErrorCategory]

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        recoverable: bool = False,
        http_status: int = 500,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details: dict[str, Any] = details or {}
        self.recoverable = recoverable
        self.http_status = http_status

    def to_error_dict(self) -> dict[str, Any]:
        """Body of the `error` field in the API error envelope."""
        return {
            "code": self.code,
            "category": self.category.value,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "documentation_url": f"{DOCUMENTATION_URL_BASE}{self.code}",
        }


class ValidationError(MIPError):
    category = ErrorCategory.VALIDATION


class LifecycleError(MIPError):
    category = ErrorCategory.LIFECYCLE


class IdentityError(MIPError):
    category = ErrorCategory.IDENTITY


class ConcurrencyError(MIPError):
    category = ErrorCategory.CONCURRENCY


class StorageError(MIPError):
    category = ErrorCategory.STORAGE


class SecurityError(MIPError):
    category = ErrorCategory.SECURITY
