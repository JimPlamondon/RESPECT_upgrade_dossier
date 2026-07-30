# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

"""TDD/CI receipt validation and dependency-aware CI selection."""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping

from .matrix import dependency_closure, requirement_index


def select_ci_requirements(
    matrix: Mapping[str, Any], changed_requirement_ids: Iterable[str]
) -> List[str]:
    changed = set(dependency_closure(matrix, changed_requirement_ids))
    index = requirement_index(matrix)
    advanced = True
    while advanced:
        advanced = False
        for requirement_id, requirement in index.items():
            if requirement_id in changed:
                continue
            if changed.intersection(requirement.get("dependencies", [])):
                changed.add(requirement_id)
                advanced = True
    return sorted(changed)


def validate_tdd_receipts(
    requirement: Mapping[str, Any], receipts: Mapping[str, Any]
) -> List[str]:
    errors: List[str] = []
    requirement_id = requirement.get("requirement_id", "<unknown>")
    expected = {
        "baseline": "fail",
        "candidate": "pass",
        "mutation": "fail",
    }
    timeout = max(
        (test.get("timeout_seconds", 0) for test in requirement["tests"]),
        default=0,
    )
    for name, result in expected.items():
        receipt = receipts.get(name)
        if not isinstance(receipt, Mapping):
            errors.append(f"{requirement_id}: missing {name} receipt")
            continue
        if receipt.get("result") != result:
            errors.append(
                f"{requirement_id}: {name} must be {result}, got "
                f"{receipt.get('result')}"
            )
        if not receipt.get("command") or not receipt.get("output_sha256"):
            errors.append(f"{requirement_id}: {name} receipt is not bound")
        if receipt.get("duration_seconds", timeout + 1) > timeout:
            errors.append(f"{requirement_id}: {name} exceeded timeout")
    return errors
