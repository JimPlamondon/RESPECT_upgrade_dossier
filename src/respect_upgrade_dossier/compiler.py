# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

"""Deterministic, content-bound RESPECT implementation-prompt compiler."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, Mapping

from .matrix import canonical_json, dependency_closure, requirement_index


PROTECTED_PATHS = [
    "src/respect_upgrade_dossier/data/matrix/upgrade_matrix.json",
    "tests/requirements",
]


def compile_prompt(
    matrix: Mapping[str, Any],
    requirement_ids: Iterable[str],
    *,
    dossier_commit: str,
    respect_revision: str,
) -> str:
    selected_ids = dependency_closure(matrix, requirement_ids)
    index = requirement_index(matrix)
    selected = [index[item] for item in selected_ids]
    for requirement in selected:
        if requirement.get("state") != "accepted":
            raise ValueError(
                "compiler refuses non-accepted requirement: "
                f"{requirement['requirement_id']}"
            )
        if requirement.get("implementation_ready") is not True:
            raise ValueError(
                "compiler refuses non-ready requirement: "
                f"{requirement['requirement_id']}"
            )
    binding: Dict[str, Any] = {
        "artifact_type": "respect_upgrade_implementation_prompt",
        "format_version": "1.0.0",
        "dossier_commit": dossier_commit,
        "matrix_id": matrix["matrix_id"],
        "matrix_semantic_hash": matrix["semantic_hash"],
        "respect_revision": respect_revision,
        "dependency_closure": selected_ids,
        "requirements": [
            {
                "requirement_id": item["requirement_id"],
                "statement": item["statement"],
                "target_versions": item["target_versions"],
                "dependencies": item["dependencies"],
                "tests": item["tests"],
                "evidence_contract": item["evidence_contract"],
                "allowed_scope": item["allowed_scope"],
                "non_goals": item["non_goals"],
            }
            for item in selected
        ],
        "protected_paths": PROTECTED_PATHS,
        "verification_commands": sorted(
            {
                test["candidate_command"]
                for item in selected
                for test in item["tests"]
            }
        ),
    }
    return (
        "# Implement accepted RESPECT Upgrade Matrix requirements\n\n"
        "The JSON contract below is authoritative for this implementation "
        "run. Do not edit protected requirements or acceptance tests.\n\n"
        "```json\n"
        + json.dumps(binding, indent=2, sort_keys=True)
        + "\n```\n\n"
        "Binding SHA-256: "
        + hashlib.sha256(canonical_json(binding)).hexdigest()
        + "\n"
    )
