# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

import copy
import json
from pathlib import Path

import pytest

from respect_upgrade_dossier.compiler import compile_prompt
from respect_upgrade_dossier.harness import (
    select_ci_requirements,
    validate_tdd_receipts,
)
from respect_upgrade_dossier.matrix import (
    load_matrix,
    semantic_hash,
    sha256_bytes,
    validate_matrix,
)
from respect_upgrade_dossier.protection import (
    accepted_content_lock,
    verify_accepted_content_lock,
)


ROOT = Path(__file__).resolve().parents[1]


def accepted_matrix():
    matrix = copy.deepcopy(load_matrix())
    requirement = matrix["requirements"][0]
    positive = ROOT / "tests/requirements/synthetic_positive.py"
    negative = ROOT / "tests/requirements/synthetic_isolated_negative.py"
    requirement.update(
        {
            "allowed_scope": ["respect-server/src"],
            "decision": {
                "authority": "jim_plamondon",
                "approval_reference": "synthetic-fixture",
                "approved_at": "2026-07-30T00:00:00Z",
            },
            "evidence_contract": {
                "candidate_build": True,
                "independent": True,
            },
            "implementation_ready": True,
            "non_goals": ["Do not edit the TestKit."],
            "state": "accepted",
            "target_versions": {"first": "synthetic-next", "last": None},
            "tests": [
                {
                    "candidate_command": (
                        "python -m pytest -q tests/requirements"
                    ),
                    "ci_profile": "synthetic",
                    "path": positive.relative_to(ROOT).as_posix(),
                    "polarity": "positive",
                    "sha256": sha256_bytes(positive.read_bytes()),
                    "test_id": "SYNTHETIC-POSITIVE",
                    "timeout_seconds": 30,
                },
                {
                    "candidate_command": (
                        "python -m pytest -q tests/requirements"
                    ),
                    "ci_profile": "synthetic",
                    "path": negative.relative_to(ROOT).as_posix(),
                    "polarity": "isolated_negative",
                    "sha256": sha256_bytes(negative.read_bytes()),
                    "test_id": "SYNTHETIC-NEGATIVE",
                    "timeout_seconds": 30,
                },
            ],
        }
    )
    matrix["semantic_hash"] = semantic_hash(matrix)
    return matrix, requirement


def test_compiler_refuses_every_canonical_proposed_requirement():
    matrix = load_matrix()
    with pytest.raises(ValueError, match="non-accepted"):
        compile_prompt(
            matrix,
            [matrix["requirements"][0]["requirement_id"]],
            dossier_commit="d" * 40,
            respect_revision="respect-source-revision",
        )


def test_prompt_compiler_is_deterministic_and_content_bound():
    matrix, requirement = accepted_matrix()
    assert validate_matrix(matrix, ROOT) == []
    arguments = {
        "dossier_commit": "d" * 40,
        "respect_revision": "respect-source-revision",
    }
    first = compile_prompt(
        matrix, [requirement["requirement_id"]], **arguments
    )
    second = compile_prompt(
        matrix, [requirement["requirement_id"]], **arguments
    )
    assert first == second
    assert matrix["semantic_hash"] in first
    assert "tests/requirements" in first
    changed = compile_prompt(
        matrix,
        [requirement["requirement_id"]],
        dossier_commit="e" * 40,
        respect_revision="respect-source-revision",
    )
    assert changed != first


def test_synthetic_tdd_receipts_prove_red_green_mutation_red():
    _matrix, requirement = accepted_matrix()
    receipts = json.loads(
        (ROOT / "tests/fixtures/synthetic_tdd_receipts.json").read_text(
            encoding="utf-8"
        )
    )
    assert validate_tdd_receipts(requirement, receipts) == []
    receipts["mutation"]["result"] = "pass"
    assert any(
        "mutation must be fail" in item
        for item in validate_tdd_receipts(requirement, receipts)
    )


def test_ci_selection_includes_dependencies_and_dependents():
    matrix, requirement = accepted_matrix()
    dependency = copy.deepcopy(matrix["requirements"][1])
    requirement["dependencies"] = [dependency["requirement_id"]]
    matrix["semantic_hash"] = semantic_hash(matrix)
    assert select_ci_requirements(
        matrix, [dependency["requirement_id"]]
    ) == sorted(
        [dependency["requirement_id"], requirement["requirement_id"]]
    )


def test_accepted_content_lock_detects_test_mutation(tmp_path):
    matrix, requirement = accepted_matrix()
    for test in requirement["tests"]:
        source = ROOT / test["path"]
        destination = tmp_path / test["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    lock = accepted_content_lock(matrix, tmp_path)
    assert verify_accepted_content_lock(matrix, tmp_path, lock)
    path = tmp_path / requirement["tests"][0]["path"]
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert not verify_accepted_content_lock(matrix, tmp_path, lock)
