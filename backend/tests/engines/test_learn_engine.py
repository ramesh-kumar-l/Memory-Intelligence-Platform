"""Learn (Phase 4 task 3, ADR-0006): derived semantics union non-destructively;
evidence matures through MemoryManager.update_memory only — Learn can never
touch anything Update itself couldn't reach.
"""

from __future__ import annotations

import pytest

from mip.core import errors
from mip.core.sections import Semantics, VerificationStatus
from mip.engines.learning.engine import LearnEngine
from mip.engines.memory_manager.engine import MemoryManager
from tests.factories import create_spec


def _create(manager: MemoryManager, **overrides: object) -> str:
    memory = manager.create_memory(create_spec(**overrides), request_id="r", trace_id="t")
    return memory.memory_id


def test_learn_unions_derived_semantics(manager: MemoryManager, learn_engine: LearnEngine) -> None:
    memory_id = _create(manager)
    original = manager.get_memory(memory_id)
    updated = learn_engine.learn(
        memory_id,
        derived=Semantics(concepts=("replication",), keywords=("sqlite",)),
        new_evidence=(),
        verifier=None,
        reason="pattern observed across memories",
        actor="learner",
        request_id="r1",
        trace_id="t1",
    )
    assert updated.version == original.version + 1
    assert "replication" in updated.semantics.concepts
    assert updated.semantics.keywords.count("sqlite") == 1  # union, never duplicated
    assert updated.audit.update_reason == "learn: pattern observed across memories"


def test_learn_matures_evidence_without_losing_prior_entries(
    manager: MemoryManager, learn_engine: LearnEngine
) -> None:
    memory_id = _create(manager)
    original = manager.get_memory(memory_id)
    assert original.trust.evidence == ()
    updated = learn_engine.learn(
        memory_id,
        derived=None,
        new_evidence=({"source": "doc-1"}, {"source": "doc-2"}),
        verifier="reviewer-1",
        reason="corroborating documents found",
        actor="learner",
        request_id="r1",
        trace_id="t1",
    )
    assert len(updated.trust.evidence) == 2
    assert updated.trust.source_count == original.trust.source_count + 2
    # default source_count starts at 1 (sections.py), so +2 evidence reaches the
    # Verified threshold (>= 3) directly.
    assert updated.trust.verification_status is VerificationStatus.VERIFIED

    again = learn_engine.learn(
        memory_id,
        derived=None,
        new_evidence=({"source": "doc-3"},),
        verifier="reviewer-2",
        reason="third source found",
        actor="learner",
        request_id="r2",
        trace_id="t2",
    )
    assert len(again.trust.evidence) == 3  # old evidence never dropped (INV-TRUST-003)
    assert again.trust.verification_status is VerificationStatus.VERIFIED


def test_learn_requires_derived_or_evidence(
    manager: MemoryManager, learn_engine: LearnEngine
) -> None:
    memory_id = _create(manager)
    with pytest.raises(errors.ValidationError):
        learn_engine.learn(
            memory_id,
            derived=None,
            new_evidence=(),
            verifier=None,
            reason="nothing to learn",
            actor="learner",
            request_id="r1",
            trace_id="t1",
        )


def test_learn_rejects_non_active_memory(manager: MemoryManager, learn_engine: LearnEngine) -> None:
    memory_id = _create(manager)
    manager.archive_memory(memory_id, actor="tester", trace_id="t")
    with pytest.raises(errors.LifecycleError):
        learn_engine.learn(
            memory_id,
            derived=Semantics(concepts=("x",)),
            new_evidence=(),
            verifier=None,
            reason="x",
            actor="learner",
            request_id="r1",
            trace_id="t1",
        )
