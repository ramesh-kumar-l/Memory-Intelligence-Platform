"""Injectable clock — tests never couple to wall-clock time (20-testing-strategy.md)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Current UTC time."""
        ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)
