# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

import copy
import json
from pathlib import Path

from respect_upgrade_dossier.matrix import (
    load_matrix,
    semantic_hash,
    validate_matrix,
    verify_import_provenance,
)
from respect_upgrade_dossier.resources import load_import_manifest


ROOT = Path(__file__).resolve().parents[1]


def test_canonical_matrix_is_one_valid_unaccepted_authority():
    matrix = load_matrix()
    assert validate_matrix(matrix) == []
    assert matrix["authority"] == "this_matrix_under_git"
    assert len(matrix["requirements"]) == 21
    assert {item["state"] for item in matrix["requirements"]} == {"proposed"}
    assert matrix["source_import"]["closure_counts"] == {
        "bindings": 4,
        "features": 21,
        "interface_families": 23,
        "profiles": 3,
        "rows": 20,
        "semantic_contracts": 12,
        "source_locks": 16,
    }


def test_import_snapshot_and_closure_are_content_bound():
    matrix = load_matrix()
    manifest = load_import_manifest()
    snapshot = (
        ROOT / "provenance/import_snapshot/compatibility_matrix.json"
    ).read_bytes()
    assert verify_import_provenance(matrix, manifest, snapshot) == []
    assert verify_import_provenance(
        matrix, manifest, snapshot + b"\n"
    ) == [
        "import manifest snapshot hash mismatch",
        "source snapshot hash mismatch",
    ]


def test_matrix_semantic_mutation_is_detected():
    matrix = load_matrix()
    matrix["requirements"][0]["statement"] += " mutation"
    assert "Upgrade Matrix semantic hash mismatch" in validate_matrix(matrix)


def test_acceptance_without_owner_decision_is_rejected():
    matrix = load_matrix()
    requirement = matrix["requirements"][0]
    requirement["state"] = "accepted"
    requirement["implementation_ready"] = True
    matrix["semantic_hash"] = semantic_hash(matrix)
    errors = validate_matrix(matrix)
    assert any("accepted without authorized decision" in item for item in errors)


def test_import_generation_is_reproducible(tmp_path):
    source = ROOT / "provenance/import_snapshot/compatibility_matrix.json"
    script = ROOT / "tools/import_testkit_matrix.py"
    import subprocess
    import sys

    subprocess.run(
        [
            sys.executable,
            str(script),
            "--source-matrix",
            str(source),
            "--source-commit",
            "3417dd40e69039a5dfb26d18aec6e823b18f8b19",
            "--extraction-commit",
            "b32dac9290842d6cbe63f911c415e5357ed71d2b",
            "--repository-root",
            str(tmp_path),
        ],
        check=True,
    )
    regenerated = json.loads(
        (
            tmp_path
            / "src/respect_upgrade_dossier/data/matrix/upgrade_matrix.json"
        ).read_text(encoding="utf-8")
    )
    assert regenerated == load_matrix()
