"""Trust Engine: confidence blending and freshness decay (Phase 2 task 7, ADR-0004)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from mip.core.sections import Provenance, Trust, VerificationStatus
from mip.engines.trust.scoring import TrustEngine


@pytest.fixture
def trust_engine() -> TrustEngine:
    return TrustEngine(freshness_half_life_days=10.0)


def _trust(**overrides: object) -> Trust:
    base: dict[str, object] = {
        "confidence": 0.5,
        "provenance": Provenance(source="unit-test"),
        "verification_status": VerificationStatus.UNKNOWN,
        "source_count": 1,
    }
    base.update(overrides)
    return Trust.model_validate(base)


def test_verified_status_raises_confidence_above_unverified(trust_engine: TrustEngine) -> None:
    verified = trust_engine.derive_confidence(
        _trust(verification_status=VerificationStatus.VERIFIED)
    )
    unverified = trust_engine.derive_confidence(
        _trust(verification_status=VerificationStatus.UNVERIFIED)
    )
    assert verified > unverified


def test_disputed_status_yields_lowest_confidence(trust_engine: TrustEngine) -> None:
    disputed = trust_engine.derive_confidence(
        _trust(verification_status=VerificationStatus.DISPUTED)
    )
    unknown = trust_engine.derive_confidence(_trust(verification_status=VerificationStatus.UNKNOWN))
    assert disputed < unknown


def test_more_corroborating_sources_never_lowers_confidence(trust_engine: TrustEngine) -> None:
    few = trust_engine.derive_confidence(_trust(source_count=1))
    many = trust_engine.derive_confidence(_trust(source_count=10))
    assert many >= few


def test_confidence_always_bounded(trust_engine: TrustEngine) -> None:
    for confidence in (0.0, 1.0):
        for status in VerificationStatus:
            score = trust_engine.derive_confidence(
                _trust(confidence=confidence, verification_status=status, source_count=50)
            )
            assert 0.0 <= score <= 1.0


def test_freshness_is_one_at_zero_age(trust_engine: TrustEngine) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert trust_engine.dynamic_freshness(created_at=now, updated_at=None, now=now) == 1.0


def test_freshness_decays_over_time(trust_engine: TrustEngine) -> None:
    created = datetime(2026, 1, 1, tzinfo=UTC)
    at_half_life = trust_engine.dynamic_freshness(
        created_at=created, updated_at=None, now=created + timedelta(days=10)
    )
    at_two_half_lives = trust_engine.dynamic_freshness(
        created_at=created, updated_at=None, now=created + timedelta(days=20)
    )
    assert at_half_life == pytest.approx(0.5, abs=1e-6)
    assert at_two_half_lives == pytest.approx(0.25, abs=1e-6)
    assert at_two_half_lives < at_half_life


def test_freshness_uses_updated_at_when_present(trust_engine: TrustEngine) -> None:
    created = datetime(2026, 1, 1, tzinfo=UTC)
    updated = datetime(2026, 1, 20, tzinfo=UTC)
    now = datetime(2026, 1, 21, tzinfo=UTC)
    fresh_from_update = trust_engine.dynamic_freshness(
        created_at=created, updated_at=updated, now=now
    )
    stale_if_created_only = trust_engine.dynamic_freshness(
        created_at=created, updated_at=None, now=now
    )
    assert fresh_from_update > stale_if_created_only


def test_rejects_non_positive_half_life() -> None:
    with pytest.raises(ValueError, match="half_life"):
        TrustEngine(freshness_half_life_days=0)
