# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

"""Legal lifecycle transitions for canonical Upgrade Matrix requirements."""

from enum import Enum
from typing import Any, Mapping, Optional


class RequirementState(str, Enum):
    IMPORTED = "imported"
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    IN_IMPLEMENTATION = "in_implementation"
    CANDIDATE_READY = "candidate_ready"
    INDEPENDENTLY_VERIFIED = "independently_verified"
    CLOSED = "closed"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


LINEAR_TRANSITIONS = {
    RequirementState.IMPORTED: RequirementState.PROPOSED,
    RequirementState.PROPOSED: RequirementState.ACCEPTED,
    RequirementState.ACCEPTED: RequirementState.IN_IMPLEMENTATION,
    RequirementState.IN_IMPLEMENTATION: RequirementState.CANDIDATE_READY,
    RequirementState.CANDIDATE_READY: RequirementState.INDEPENDENTLY_VERIFIED,
}
TERMINAL_STATES = {
    RequirementState.CLOSED,
    RequirementState.SUPERSEDED,
    RequirementState.REJECTED,
}


def acceptance_decision_is_qualifying(decision: Mapping[str, Any]) -> bool:
    authority = str(decision.get("authority", ""))
    return bool(
        authority == "jim_plamondon" or authority.startswith("delegated:")
    ) and bool(decision.get("approval_reference")) and bool(
        decision.get("approved_at")
    )


def transition(
    current: RequirementState,
    requested: RequirementState,
    *,
    decision: Optional[Mapping[str, Any]] = None,
    acceptance_evidence: Optional[Mapping[str, Any]] = None,
) -> RequirementState:
    if current in TERMINAL_STATES:
        raise ValueError(
            f"terminal requirement state cannot transition: {current.value}"
        )
    if requested in {RequirementState.SUPERSEDED, RequirementState.REJECTED}:
        return requested
    if requested == RequirementState.ACCEPTED:
        if current != RequirementState.PROPOSED:
            raise ValueError("only a proposed requirement can be accepted")
        if decision is None or not acceptance_decision_is_qualifying(decision):
            raise ValueError("acceptance requires an authorized recorded decision")
    if requested == RequirementState.CLOSED:
        if current != RequirementState.INDEPENDENTLY_VERIFIED:
            raise ValueError("closure requires independently_verified state")
        if (
            acceptance_evidence is None
            or acceptance_evidence.get("candidate_result") != "pass"
            or acceptance_evidence.get("independent") is not True
            or not acceptance_evidence.get("evidence_hash")
        ):
            raise ValueError(
                "closure requires independently preserved candidate evidence"
            )
        return requested
    if LINEAR_TRANSITIONS.get(current) != requested:
        raise ValueError(
            f"non-normative requirement transition: {current.value} -> "
            f"{requested.value}"
        )
    return requested
