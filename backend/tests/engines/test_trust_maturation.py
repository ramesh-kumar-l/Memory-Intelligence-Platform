"""Trust maturation (Phase 4 task 5, ADR-0006): pure evidence-chain and
verification-status logic (INV-TRUST-003).
"""

from __future__ import annotations

from typing import Any

from mip.core.sections import Provenance, Trust, VerificationStatus
from mip.engines.trust.maturation import mature_evidence


def _trust(**overrides: Any) -> Trust:
    base: dict[str, Any] = {"confidence": 0.5, "provenance": Provenance(source="unit-test")}
    base.update(overrides)
    return Trust.model_validate(base)


def test_mature_evidence_appends_without_removing_existing() -> None:
    trust = _trust(evidence=({"source": "doc-1"},))
    matured = mature_evidence(trust, new_evidence=({"source": "doc-2"},), verifier=None)
    assert matured.evidence == ({"source": "doc-1"}, {"source": "doc-2"})


def test_mature_evidence_tags_verifier() -> None:
    trust = _trust()
    matured = mature_evidence(trust, new_evidence=({"source": "doc-1"},), verifier="reviewer-1")
    assert matured.evidence[0]["verifier"] == "reviewer-1"


def test_mature_evidence_does_not_overwrite_existing_verifier_tag() -> None:
    trust = _trust()
    matured = mature_evidence(
        trust, new_evidence=({"source": "doc-1", "verifier": "original"},), verifier="new-reviewer"
    )
    assert matured.evidence[0]["verifier"] == "original"


def test_mature_evidence_no_op_without_new_evidence() -> None:
    trust = _trust()
    matured = mature_evidence(trust, new_evidence=(), verifier="reviewer-1")
    assert matured == trust


def test_verification_status_upgrades_to_partially_verified_at_two_sources() -> None:
    trust = _trust(source_count=1, verification_status=VerificationStatus.UNVERIFIED)
    matured = mature_evidence(trust, new_evidence=({"source": "doc-2"},), verifier=None)
    assert matured.source_count == 2
    assert matured.verification_status is VerificationStatus.PARTIALLY_VERIFIED


def test_verification_status_upgrades_to_verified_at_three_sources() -> None:
    trust = _trust(source_count=2, verification_status=VerificationStatus.PARTIALLY_VERIFIED)
    matured = mature_evidence(trust, new_evidence=({"source": "doc-3"},), verifier=None)
    assert matured.verification_status is VerificationStatus.VERIFIED


def test_disputed_status_is_never_cleared_by_more_evidence() -> None:
    trust = _trust(source_count=1, verification_status=VerificationStatus.DISPUTED)
    matured = mature_evidence(
        trust, new_evidence=({"source": "doc-2"}, {"source": "doc-3"}), verifier=None
    )
    assert matured.verification_status is VerificationStatus.DISPUTED
