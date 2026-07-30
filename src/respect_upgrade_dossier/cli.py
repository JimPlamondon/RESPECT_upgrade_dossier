# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

"""Command line interface for the standalone RESPECT Upgrade Dossier."""

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from .compiler import compile_prompt
from .matrix import load_matrix, validate_matrix


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="respect-upgrade-dossier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--matrix", type=Path)
    validate.add_argument("--repository-root", type=Path)

    compile_parser = subparsers.add_parser("compile")
    compile_parser.add_argument("requirement_ids", nargs="+")
    compile_parser.add_argument("--matrix", type=Path)
    compile_parser.add_argument("--dossier-commit", required=True)
    compile_parser.add_argument("--respect-revision", required=True)
    compile_parser.add_argument("--output", type=Path)

    arguments = parser.parse_args(argv)
    matrix = load_matrix(arguments.matrix)
    if arguments.command == "validate":
        errors = validate_matrix(matrix, arguments.repository_root)
        print(json.dumps({"errors": errors, "valid": not errors}, sort_keys=True))
        return 0 if not errors else 2

    prompt = compile_prompt(
        matrix,
        arguments.requirement_ids,
        dossier_commit=arguments.dossier_commit,
        respect_revision=arguments.respect_revision,
    )
    if arguments.output:
        arguments.output.write_text(prompt, encoding="utf-8")
    else:
        print(prompt, end="")
    return 0
