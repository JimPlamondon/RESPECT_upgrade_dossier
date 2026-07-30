# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

"""Content locks for accepted requirements and registered acceptance tests."""

from pathlib import Path
from typing import Any, Dict, Mapping

from .matrix import canonical_json, sha256_bytes


def accepted_content_lock(
    matrix: Mapping[str, Any], repository_root: Path
) -> Dict[str, Any]:
    requirements = [
        item for item in matrix["requirements"] if item["state"] == "accepted"
    ]
    tests = {}
    for requirement in requirements:
        for test in requirement["tests"]:
            path = repository_root / test["path"]
            tests[test["path"]] = sha256_bytes(path.read_bytes())
    return {
        "requirements_sha256": sha256_bytes(canonical_json(requirements)),
        "tests": dict(sorted(tests.items())),
    }


def verify_accepted_content_lock(
    matrix: Mapping[str, Any],
    repository_root: Path,
    lock: Mapping[str, Any],
) -> bool:
    return accepted_content_lock(matrix, repository_root) == lock
