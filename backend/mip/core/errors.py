"""Structured error hierarchy bound to the append-only MEM-* code registry.

The registry (05-api-design.md) is append-only: codes are never renumbered or
removed. The API layer is the only place these become HTTP responses.
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


# --- Registry factories (append-only; keep codes stable forever) -----------------------------


def validation_failed(violations: list[dict[str, Any]]) -> ValidationError:
    return ValidationError(
        "MEM-1001",
        "Memory Object failed schema validation",
        details={"violations": violations},
        http_status=422,
    )


def missing_semantic_element() -> ValidationError:
    return ValidationError(
        "MEM-1003",
        "Memory Object must contain at least one semantic element (INV-SEM-001)",
        http_status=422,
    )


def invalid_request(violations: list[dict[str, Any]] | None = None) -> ValidationError:
    return ValidationError(
        "MEM-1004",
        "Request is malformed",
        details={"violations": violations or []},
        http_status=422,
    )


def unsupported_api_version(requested: str, supported: tuple[str, ...]) -> ValidationError:
    return ValidationError(
        "MEM-1005",
        "Requested API version is not supported",
        details={"requested": requested, "supported": list(supported)},
        http_status=400,
    )


def unsupported_search_mode(mode: str, supported: tuple[str, ...]) -> ValidationError:
    return ValidationError(
        "MEM-1007",
        "Requested search mode is not supported",
        details={"requested": mode, "supported": list(supported)},
        http_status=400,
    )


def unresolved_relationship_target(target_memory_id: str) -> ValidationError:
    return ValidationError(
        "MEM-1006",
        "Relationship target does not exist and is not marked unresolved (INV-REL-001)",
        details={"target_memory_id": target_memory_id},
        http_status=422,
    )


def illegal_transition(from_state: str, to_state: str) -> LifecycleError:
    return LifecycleError(
        "MEM-2001",
        "Illegal lifecycle transition (INV-STATE-002)",
        details={"from": from_state, "to": to_state},
        http_status=409,
    )


def operation_not_allowed(operation: str, state: str) -> LifecycleError:
    return LifecycleError(
        "MEM-2002",
        "Operation is not allowed in the current lifecycle state",
        details={"operation": operation, "state": state},
        http_status=409,
    )


def memory_deleted(memory_id: str, deleted_at: str | None) -> LifecycleError:
    return LifecycleError(
        "MEM-2003",
        "Memory Object is deleted; Deleted is terminal (INV-STATE-003)",
        details={"memory_id": memory_id, "deleted_at": deleted_at},
        http_status=410,
    )


def memory_not_found(memory_id: str) -> IdentityError:
    return IdentityError(
        "MEM-3001",
        "Memory Object not found",
        details={"memory_id": memory_id},
        http_status=404,
    )


def version_not_found(memory_id: str, version: int) -> IdentityError:
    return IdentityError(
        "MEM-3002",
        "Requested version does not exist",
        details={"memory_id": memory_id, "version": version},
        http_status=404,
    )


def duplicate_memory_id(memory_id: str) -> IdentityError:
    return IdentityError(
        "MEM-3003",
        "A Memory Object with this memory_id already exists (INV-ID-001)",
        details={"memory_id": memory_id},
        http_status=409,
    )


def version_conflict(expected: int, actual: int) -> ConcurrencyError:
    return ConcurrencyError(
        "MEM-4001",
        "Version conflict: If-Match does not match current version (INV-CONCUR-001)",
        details={"expected": expected, "actual": actual},
        recoverable=True,
        http_status=409,
    )


def missing_precondition(header: str) -> ConcurrencyError:
    return ConcurrencyError(
        "MEM-4002",
        "Missing required precondition header",
        details={"header": header},
        recoverable=True,
        http_status=428,
    )


def idempotency_key_reuse(key: str) -> ConcurrencyError:
    return ConcurrencyError(
        "MEM-4003",
        "Idempotency-Key was already used with a different request payload",
        details={"idempotency_key": key},
        http_status=409,
    )


def transition_in_progress(memory_id: str) -> ConcurrencyError:
    return ConcurrencyError(
        "MEM-4004",
        "Another lifecycle transition is in progress for this memory (INV-CONCUR-004)",
        details={"memory_id": memory_id},
        recoverable=True,
        http_status=409,
    )


def storage_failure(reason: str) -> StorageError:
    return StorageError(
        "MEM-6001",
        "Storage operation failed",
        details={"reason": reason},
        http_status=500,
    )


def internal_failure() -> StorageError:
    return StorageError(
        "MEM-6002",
        "Unexpected internal failure",
        http_status=500,
    )
