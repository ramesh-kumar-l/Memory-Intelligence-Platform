"""Trust Engine: basic confidence/freshness derivation (Phase 2 task 7, ADR-0004).

Formulas are intentionally simple and documented — every score must be
explainable, never a black box (Constitution Law 6).
"""

from __future__ import annotations

from datetime import datetime

from mip.core.sections import Trust, VerificationStatus

#: Heuristic baseline confidence per verification status — explicit, not learned.
_STATUS_BASELINE: dict[VerificationStatus, float] = {
    VerificationStatus.VERIFIED: 0.95,
    VerificationStatus.PARTIALLY_VERIFIED: 0.7,
    VerificationStatus.UNKNOWN: 0.5,
    VerificationStatus.UNVERIFIED: 0.4,
    VerificationStatus.DISPUTED: 0.2,
}
_SOURCE_BONUS_PER_EXTRA_SOURCE = 0.05
_MAX_SOURCE_BONUS = 0.2


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class TrustEngine:
    def __init__(self, *, freshness_half_life_days: float = 30.0) -> None:
        if freshness_half_life_days <= 0:
            raise ValueError("freshness_half_life_days must be > 0")
        self._half_life_days = freshness_half_life_days

    def derive_confidence(self, trust: Trust) -> float:
        """Equal-weighted blend of the caller-supplied confidence and a
        heuristic from verification_status + corroborating source_count.
        """
        baseline = _STATUS_BASELINE[trust.verification_status]
        source_bonus = min(
            _MAX_SOURCE_BONUS, _SOURCE_BONUS_PER_EXTRA_SOURCE * max(0, trust.source_count - 1)
        )
        heuristic = _clamp(baseline + source_bonus)
        return round(_clamp(0.5 * trust.confidence + 0.5 * heuristic), 4)

    def dynamic_freshness(
        self, *, created_at: datetime, updated_at: datetime | None, now: datetime
    ) -> float:
        """Exponential half-life decay from the most recent content change.
        Computed at read time, never persisted — freshness is a function of
        wall-clock time and must never force a new version (ADR-0004).
        """
        reference = updated_at or created_at
        age_days = max(0.0, (now - reference).total_seconds() / 86400.0)
        return round(_clamp(0.5 ** (age_days / self._half_life_days)), 4)
