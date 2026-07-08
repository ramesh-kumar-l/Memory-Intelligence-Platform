"""Trust maturation (Phase 4 task 5, ADR-0006): append-only evidence chains,
source counting, and verification-status upgrades. Confidence itself is still
derived by `TrustEngine.derive_confidence` — this module only prepares inputs.
"""

from __future__ import annotations

from typing import Any

from mip.core.sections import Trust, VerificationStatus

#: Explicit, documented thresholds — not learned (Constitution Law 6: explainability).
_VERIFIED_SOURCE_THRESHOLD = 3
_PARTIALLY_VERIFIED_SOURCE_THRESHOLD = 2


def mature_evidence(
    trust: Trust, *, new_evidence: tuple[dict[str, Any], ...], verifier: str | None
) -> Trust:
    """Append new evidence (INV-TRUST-003: old evidence stays accessible), bump
    `source_count`, and upgrade `verification_status` by an explicit threshold
    table. Never downgrades a status the caller already escalated (a Disputed
    memory is never silently cleared just because more evidence arrived).
    """
    if not new_evidence:
        return trust
    tagged_evidence = tuple(
        {**entry, "verifier": verifier} if verifier and "verifier" not in entry else entry
        for entry in new_evidence
    )
    new_source_count = trust.source_count + len(new_evidence)
    return trust.model_copy(
        update={
            "evidence": trust.evidence + tagged_evidence,
            "source_count": new_source_count,
            "verification_status": _upgraded_status(trust.verification_status, new_source_count),
        }
    )


def _upgraded_status(current: VerificationStatus, source_count: int) -> VerificationStatus:
    if current is VerificationStatus.DISPUTED:
        return current
    if source_count >= _VERIFIED_SOURCE_THRESHOLD:
        return VerificationStatus.VERIFIED
    if source_count >= _PARTIALLY_VERIFIED_SOURCE_THRESHOLD and current in (
        VerificationStatus.UNKNOWN,
        VerificationStatus.UNVERIFIED,
    ):
        return VerificationStatus.PARTIALLY_VERIFIED
    return current
