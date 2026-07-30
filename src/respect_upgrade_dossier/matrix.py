# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

"""Canonical Upgrade Matrix loading, hashing, closure, and validation."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set

from jsonschema import Draft202012Validator

from .lifecycle import acceptance_decision_is_qualifying
from .resources import load_canonical_matrix, load_schema


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def semantic_hash(matrix: Mapping[str, Any]) -> str:
    candidate = copy.deepcopy(dict(matrix))
    candidate.pop("semantic_hash", None)
    return sha256_bytes(canonical_json(candidate))


def verify_import_provenance(
    matrix: Mapping[str, Any],
    manifest: Mapping[str, Any],
    snapshot_bytes: bytes,
) -> List[str]:
    errors: List[str] = []
    snapshot_hash = sha256_bytes(snapshot_bytes)
    source_import = matrix.get("source_import", {})
    if snapshot_hash != source_import.get("snapshot_sha256"):
        errors.append("source snapshot hash mismatch")
    if snapshot_hash != manifest.get("snapshot_sha256"):
        errors.append("import manifest snapshot hash mismatch")
    if manifest.get("source_commit") != source_import.get("source_commit"):
        errors.append("source commit provenance mismatch")
    if manifest.get("matrix_semantic_hash") != matrix.get("semantic_hash"):
        errors.append("import manifest Matrix hash mismatch")
    if manifest.get("closure_sha256") != sha256_bytes(
        canonical_json(source_import.get("closure", {}))
    ):
        errors.append("import closure hash mismatch")
    try:
        snapshot = json.loads(snapshot_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        errors.append("source snapshot is not valid JSON")
        return errors
    snapshot_candidate = copy.deepcopy(snapshot)
    claimed = snapshot_candidate.pop("semantic_hash", None)
    if claimed != sha256_bytes(canonical_json(snapshot_candidate)):
        errors.append("source snapshot semantic hash mismatch")
    if claimed != source_import.get("source_matrix_semantic_hash"):
        errors.append("source Matrix semantic provenance mismatch")
    return sorted(set(errors))


def load_matrix(path: Optional[Path] = None) -> Dict[str, Any]:
    if path is None:
        return load_canonical_matrix()
    return json.loads(path.read_text(encoding="utf-8"))


def requirement_index(matrix: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item["requirement_id"]): dict(item)
        for item in matrix.get("requirements", [])
    }


def dependency_closure(
    matrix: Mapping[str, Any], requirement_ids: Iterable[str]
) -> List[str]:
    index = requirement_index(matrix)
    pending = list(requirement_ids)
    selected: Set[str] = set()
    while pending:
        requirement_id = pending.pop()
        if requirement_id in selected:
            continue
        if requirement_id not in index:
            raise ValueError(f"unknown requirement dependency: {requirement_id}")
        selected.add(requirement_id)
        pending.extend(index[requirement_id].get("dependencies", []))
    return sorted(selected)


def _cycle_errors(index: Mapping[str, Mapping[str, Any]]) -> List[str]:
    errors: List[str] = []
    visiting: Set[str] = set()
    visited: Set[str] = set()

    def visit(requirement_id: str) -> None:
        if requirement_id in visiting:
            errors.append(f"dependency cycle includes {requirement_id}")
            return
        if requirement_id in visited:
            return
        visiting.add(requirement_id)
        for dependency in index[requirement_id].get("dependencies", []):
            if dependency in index:
                visit(dependency)
        visiting.remove(requirement_id)
        visited.add(requirement_id)

    for requirement_id in index:
        visit(requirement_id)
    return errors


def _implementation_ready_errors(
    requirement: Mapping[str, Any], base_path: Optional[Path]
) -> List[str]:
    errors: List[str] = []
    requirement_id = requirement.get("requirement_id")
    tests = requirement.get("tests", [])
    polarities = {test.get("polarity") for test in tests}
    if not {"positive", "isolated_negative"}.issubset(polarities):
        errors.append(
            f"{requirement_id}: implementation-ready requirement needs "
            "positive and isolated_negative tests"
        )
    if not requirement.get("target_versions", {}).get("first"):
        errors.append(f"{requirement_id}: target version is required")
    if not requirement.get("evidence_contract"):
        errors.append(f"{requirement_id}: evidence contract is required")
    if not requirement.get("allowed_scope"):
        errors.append(f"{requirement_id}: allowed scope is required")
    protected = {
        "src/respect_upgrade_dossier/data/matrix/upgrade_matrix.json",
        "tests/requirements",
    }
    if protected.intersection(requirement.get("allowed_scope", [])):
        errors.append(f"{requirement_id}: allowed scope includes protected paths")
    for test in tests:
        if not test.get("sha256") or not test.get("ci_profile"):
            errors.append(f"{requirement_id}: test binding is incomplete")
        if not isinstance(test.get("timeout_seconds"), int):
            errors.append(f"{requirement_id}: test timeout is required")
        if base_path is not None and test.get("path"):
            path = base_path / str(test["path"])
            if not path.is_file():
                errors.append(f"{requirement_id}: test path is missing: {path}")
            elif sha256_bytes(path.read_bytes()) != test.get("sha256"):
                errors.append(f"{requirement_id}: test hash mismatch: {path}")
    return errors


def validate_matrix(
    matrix: Mapping[str, Any], base_path: Optional[Path] = None
) -> List[str]:
    errors = [
        error.message
        for error in Draft202012Validator(load_schema()).iter_errors(matrix)
    ]
    if matrix.get("semantic_hash") != semantic_hash(matrix):
        errors.append("Upgrade Matrix semantic hash mismatch")
    requirements = list(matrix.get("requirements", []))
    ids = [item.get("requirement_id") for item in requirements]
    if len(ids) != len(set(ids)):
        errors.append("requirement IDs are not unique")
    index = requirement_index(matrix)
    for requirement in requirements:
        requirement_id = str(requirement.get("requirement_id"))
        for dependency in requirement.get("dependencies", []):
            if dependency not in index:
                errors.append(
                    f"{requirement_id}: missing dependency {dependency}"
                )
        state = requirement.get("state")
        decision = requirement.get("decision")
        if state == "accepted":
            if not acceptance_decision_is_qualifying(decision or {}):
                errors.append(
                    f"{requirement_id}: accepted without authorized decision"
                )
            if requirement.get("implementation_ready") is not True:
                errors.append(
                    f"{requirement_id}: accepted requirement is not "
                    "implementation-ready"
                )
        elif decision is not None:
            errors.append(
                f"{requirement_id}: non-accepted requirement carries decision"
            )
        if requirement.get("implementation_ready"):
            errors.extend(_implementation_ready_errors(requirement, base_path))
    errors.extend(_cycle_errors(index))
    source_import = matrix.get("source_import", {})
    closure = source_import.get("closure", {})
    counts = source_import.get("closure_counts", {})
    for key in (
        "features",
        "rows",
        "profiles",
        "bindings",
        "semantic_contracts",
        "interface_families",
        "source_locks",
    ):
        if counts.get(key) != len(closure.get(key, [])):
            errors.append(f"source import closure count mismatch: {key}")
    return sorted(set(errors))
