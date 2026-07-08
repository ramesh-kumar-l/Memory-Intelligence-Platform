"""Embedding provider port (Constitution Law 8: model independence).

Engines depend only on this ABC; the concrete provider is chosen once, at
`create_app()`. Swapping in a real ML-backed provider never touches engine code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

#: A dense embedding vector, always L2-normalized by the provider.
Vector = tuple[float, ...]


class EmbeddingProviderABC(ABC):
    """Text-to-vector embedding port. Implementations must be deterministic:
    the same text SHALL always produce the same vector (replay-safety, ADR-0004).
    """

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Fixed output width; every vector this provider returns has this length."""

    @abstractmethod
    def embed(self, text: str) -> Vector:
        """Return a unit-length (L2-normalized) vector for the given text."""
