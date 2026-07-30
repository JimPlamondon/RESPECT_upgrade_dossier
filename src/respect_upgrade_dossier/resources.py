# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

import json
from importlib.resources import files
from typing import Any, Dict


def load_schema(name: str = "upgrade_matrix.schema.json") -> Dict[str, Any]:
    return json.loads(
        files("respect_upgrade_dossier")
        .joinpath("data", "schemas", name)
        .read_text(encoding="utf-8")
    )


def load_canonical_matrix() -> Dict[str, Any]:
    return json.loads(
        files("respect_upgrade_dossier")
        .joinpath("data", "matrix", "upgrade_matrix.json")
        .read_text(encoding="utf-8")
    )


def load_import_manifest() -> Dict[str, Any]:
    return json.loads(
        files("respect_upgrade_dossier")
        .joinpath("data", "provenance", "import_manifest.json")
        .read_text(encoding="utf-8")
    )
