"""LocalHashingEmbeddingProvider: determinism and replay-safety (ADR-0004)."""

from __future__ import annotations

import math

import pytest

from mip.providers.local_embedding import LocalHashingEmbeddingProvider


@pytest.fixture
def provider() -> LocalHashingEmbeddingProvider:
    return LocalHashingEmbeddingProvider(dimensions=64)


def test_dimensions_reported(provider: LocalHashingEmbeddingProvider) -> None:
    assert provider.dimensions == 64
    assert len(provider.embed("hello world")) == 64


def test_deterministic_across_instances() -> None:
    first = LocalHashingEmbeddingProvider(dimensions=32).embed("revenue grew in the cloud division")
    second = LocalHashingEmbeddingProvider(dimensions=32).embed(
        "revenue grew in the cloud division"
    )
    assert first == second


def test_unit_length_normalized(provider: LocalHashingEmbeddingProvider) -> None:
    vector = provider.embed("quarterly revenue report for the cloud division")
    norm = math.sqrt(sum(component * component for component in vector))
    assert norm == pytest.approx(1.0, abs=1e-9)


def test_empty_text_is_zero_vector(provider: LocalHashingEmbeddingProvider) -> None:
    assert provider.embed("") == (0.0,) * 64


def test_similar_text_is_closer_than_unrelated(provider: LocalHashingEmbeddingProvider) -> None:
    def distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)))

    base = provider.embed("revenue grew due to strong enterprise cloud sales")
    similar = provider.embed("revenue grew due to strong enterprise cloud sales this quarter")
    unrelated = provider.embed("the cat sat quietly on a warm windowsill")
    assert distance(base, similar) < distance(base, unrelated)


def test_rejects_non_positive_dimensions() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        LocalHashingEmbeddingProvider(dimensions=0)
