# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

import ast
from pathlib import Path

from respect_upgrade_dossier.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_has_no_testkit_import():
    imports = set()
    for path in (ROOT / "src/respect_upgrade_dossier").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
    assert not any(
        name.startswith(("respect_compat", "respect_ification"))
        for name in imports
    )


def test_cli_validates_installed_canonical_matrix(capsys):
    assert main(["validate"]) == 0
    assert '"valid": true' in capsys.readouterr().out
