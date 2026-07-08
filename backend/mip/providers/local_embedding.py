"""Default offline embedding provider: deterministic feature-hashed bag-of-words.

Not deep semantic understanding — a lexical stand-in that requires no model
download and no network (offline-first, ADR-0004). `hashlib` (not the builtin
`hash()`) is used so vectors are stable across processes regardless of
PYTHONHASHSEED, which is required for replay-identity.
"""

from __future__ import annotations

import hashlib
import math
import re

from mip.providers.embeddings import EmbeddingProviderABC, Vector

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


class LocalHashingEmbeddingProvider(EmbeddingProviderABC):
    """Feature-hashing embedder: each token hashes to a signed bucket in a
    fixed-width accumulator, which is then L2-normalized (the "hashing trick").
    """

    def __init__(self, dimensions: int = 256) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be >= 1")
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, text: str) -> Vector:
        accumulator = [0.0] * self._dimensions
        for token in _TOKEN_RE.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            bucket = value % self._dimensions
            sign = 1.0 if (value // self._dimensions) % 2 == 0 else -1.0
            accumulator[bucket] += sign
        norm = math.sqrt(sum(component * component for component in accumulator))
        if norm == 0.0:
            return tuple(accumulator)
        return tuple(component / norm for component in accumulator)
