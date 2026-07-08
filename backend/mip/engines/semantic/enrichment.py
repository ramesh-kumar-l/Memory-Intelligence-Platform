"""Deterministic keyword derivation from Memory Object text (FR-SEM enrichment).

Pure functions, no I/O — always augments the client-supplied `semantics.keywords`
with terms actually present in the content, so search recall never depends on
the caller having tagged the memory correctly.
"""

from __future__ import annotations

import re
from collections import Counter

from mip.core.sections import Content, Semantics

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_MAX_DERIVED_KEYWORDS = 20
_MIN_TOKEN_LENGTH = 3

_STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "are",
        "but",
        "not",
        "you",
        "all",
        "can",
        "her",
        "was",
        "one",
        "our",
        "out",
        "day",
        "get",
        "has",
        "him",
        "his",
        "how",
        "man",
        "new",
        "now",
        "old",
        "see",
        "two",
        "way",
        "who",
        "boy",
        "did",
        "its",
        "let",
        "put",
        "say",
        "she",
        "too",
        "use",
        "with",
        "this",
        "that",
        "from",
        "have",
        "were",
        "been",
        "will",
        "would",
        "there",
        "their",
        "what",
        "about",
        "which",
        "when",
    }
)


def derive_keywords(content: Content) -> tuple[str, ...]:
    """Rank tokens from title/summary/description by frequency (ties broken
    alphabetically for determinism), dropping stopwords and short tokens.
    """
    text = " ".join((content.title, content.summary, content.description))
    tokens = [
        token
        for token in (match.lower() for match in _TOKEN_RE.findall(text))
        if len(token) >= _MIN_TOKEN_LENGTH and token not in _STOPWORDS
    ]
    counts = Counter(tokens)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return tuple(token for token, _ in ranked[:_MAX_DERIVED_KEYWORDS])


def enrich_semantics(semantics: Semantics, content: Content) -> Semantics:
    """Union derived keywords into `semantics.keywords`, preserving order and
    never dropping explicit entities/concepts/etc. the caller supplied.
    """
    derived = derive_keywords(content)
    merged = list(semantics.keywords)
    seen = set(merged)
    for keyword in derived:
        if keyword not in seen:
            merged.append(keyword)
            seen.add(keyword)
    return semantics.model_copy(update={"keywords": tuple(merged)})
