# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

import pytest

from respect_upgrade_dossier.lifecycle import RequirementState, transition


DECISION = {
    "authority": "jim_plamondon",
    "approval_reference": "owner-decision:test",
    "approved_at": "2026-07-30T00:00:00Z",
}


def test_imported_work_requires_proposal_then_explicit_acceptance():
    assert transition(
        RequirementState.IMPORTED, RequirementState.PROPOSED
    ) == RequirementState.PROPOSED
    with pytest.raises(ValueError, match="authorized recorded decision"):
        transition(RequirementState.PROPOSED, RequirementState.ACCEPTED)
    assert transition(
        RequirementState.PROPOSED,
        RequirementState.ACCEPTED,
        decision=DECISION,
    ) == RequirementState.ACCEPTED


def test_lifecycle_is_linear_and_closure_is_evidence_gated():
    with pytest.raises(ValueError, match="non-normative"):
        transition(
            RequirementState.ACCEPTED,
            RequirementState.CANDIDATE_READY,
        )
    with pytest.raises(ValueError, match="independently preserved"):
        transition(
            RequirementState.INDEPENDENTLY_VERIFIED,
            RequirementState.CLOSED,
        )
    assert transition(
        RequirementState.INDEPENDENTLY_VERIFIED,
        RequirementState.CLOSED,
        acceptance_evidence={
            "candidate_result": "pass",
            "independent": True,
            "evidence_hash": "a" * 64,
        },
    ) == RequirementState.CLOSED
