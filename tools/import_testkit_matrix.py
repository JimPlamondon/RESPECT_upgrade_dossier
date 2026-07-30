#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

"""Deterministically seed the Upgrade Matrix from a TestKit Matrix snapshot."""

import argparse
import copy
import hashlib
import json
from pathlib import Path


def encoded(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def selected_feature(feature):
    guidance = feature.get("respect_upgrade_guidance", "")
    return (
        not guidance.startswith("No RESPECT platform work is authorized")
        or feature.get("feature_work_unit") is not None
    )


def by_ids(values, field, selected):
    return [
        copy.deepcopy(value)
        for value in values
        if value.get(field) in selected
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-matrix", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--extraction-commit", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    arguments = parser.parse_args()

    source_bytes = arguments.source_matrix.read_bytes()
    source = json.loads(source_bytes)
    features = [
        copy.deepcopy(feature)
        for feature in source["features"]
        if selected_feature(feature)
    ]
    feature_ids = {feature["feature_id"] for feature in features}
    row_ids = {
        row["row_id"]
        for row in source["rows"]
        if row.get("platform_gap_eligible")
        or row.get("dossier_acceptance_test")
        or row.get("feature_id") in feature_ids
    }
    rows = by_ids(source["rows"], "row_id", row_ids)

    profile_ids = {
        item
        for value in features + rows
        for item in value.get("profile_ids", [])
    }
    profiles = by_ids(source["profiles"], "profile_id", profile_ids)
    interface_family_ids = {
        feature["interface_family_id"] for feature in features
    }
    interface_family_ids.update(
        item
        for profile in profiles
        for item in profile.get("interface_family_ids", [])
    )
    interface_families = by_ids(
        source["interface_families"],
        "interface_family_id",
        interface_family_ids,
    )
    binding_ids = {
        row["binding_id"] for row in rows if row.get("binding_id")
    }
    bindings = by_ids(source["bindings"], "binding_id", binding_ids)
    semantic_contract_ids = {
        row["semantic_contract_id"]
        for row in rows
        if row.get("semantic_contract_id")
    }
    semantic_contract_ids.update(
        item
        for feature in features
        for item in feature.get("semantic_contract_ids", [])
    )
    semantic_contract_ids.update(
        item
        for binding in bindings
        for item in binding.get("semantic_contract_ids", [])
    )
    semantic_contracts = by_ids(
        source["semantic_contracts"],
        "semantic_contract_id",
        semantic_contract_ids,
    )
    closure = {
        "bindings": bindings,
        "features": features,
        "interface_families": interface_families,
        "profiles": profiles,
        "rows": rows,
        "semantic_contracts": semantic_contracts,
        "source_locks": copy.deepcopy(source["source_locks"]),
    }
    closure_counts = {
        key: len(value) for key, value in closure.items()
    }

    requirements = []
    rows_by_feature = {}
    for row in rows:
        rows_by_feature.setdefault(row["feature_id"], []).append(row["row_id"])
    for feature in sorted(features, key=lambda item: item["feature_id"]):
        feature_id = feature["feature_id"]
        requirements.append(
            {
                "allowed_scope": [],
                "decision": None,
                "dependencies": [],
                "evidence_contract": {},
                "implementation_ready": False,
                "kind": "upgrade_requirement",
                "non_goals": [
                    "No implementation is authorized until explicit acceptance."
                ],
                "requirement_id": "UPG-" + feature_id.removeprefix("RCF-"),
                "source_feature_id": feature_id,
                "source_row_ids": sorted(rows_by_feature.get(feature_id, [])),
                "state": "proposed",
                "statement": feature["respect_upgrade_guidance"],
                "target_versions": {
                    "first": feature.get("first_applicable_respect_version"),
                    "last": feature.get("last_applicable_respect_version"),
                },
                "tests": [],
            }
        )

    snapshot_sha256 = digest(source_bytes)
    matrix = {
        "artifact_type": "respect_upgrade_matrix",
        "authority": "this_matrix_under_git",
        "format_version": "1.0.0",
        "matrix_id": "respect-upgrade-matrix-v1",
        "requirements": requirements,
        "source_import": {
            "closure": closure,
            "closure_counts": closure_counts,
            "selection_rule": (
                "affirmative upgrade guidance or feature work unit or "
                "platform-gap eligibility or Dossier acceptance, plus "
                "referenced dependency closure"
            ),
            "snapshot_sha256": snapshot_sha256,
            "source_commit": arguments.source_commit,
            "source_matrix_id": source["matrix_id"],
            "source_matrix_semantic_hash": source["semantic_hash"],
            "source_matrix_version": source["matrix_version"],
            "source_repository": (
                "https://github.com/JimPlamondon/RESPECT_testkit.git"
            ),
        },
        "semantic_hash": "pending",
    }
    matrix["semantic_hash"] = digest(
        encoded({key: value for key, value in matrix.items() if key != "semantic_hash"})
    )
    manifest = {
        "artifact_type": "respect_upgrade_import_manifest",
        "closure_counts": closure_counts,
        "closure_sha256": digest(encoded(closure)),
        "extraction_commit": arguments.extraction_commit,
        "extraction_method": (
            "git subtree split --prefix=src/respect_upgrade_dossier"
        ),
        "format_version": "1.0.0",
        "matrix_semantic_hash": matrix["semantic_hash"],
        "requirements_imported": len(requirements),
        "requirements_state": {"accepted": 0, "proposed": len(requirements)},
        "snapshot_sha256": snapshot_sha256,
        "source_commit": arguments.source_commit,
        "source_matrix_semantic_hash": source["semantic_hash"],
    }
    root = arguments.repository_root
    snapshot_path = (
        root / "provenance/import_snapshot/compatibility_matrix.json"
    )
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_bytes(source_bytes)
    write_json(root / "provenance/import_manifest.json", manifest)
    write_json(
        root
        / "src/respect_upgrade_dossier/data/provenance/import_manifest.json",
        manifest,
    )
    write_json(
        root / "src/respect_upgrade_dossier/data/matrix/upgrade_matrix.json",
        matrix,
    )


if __name__ == "__main__":
    main()
