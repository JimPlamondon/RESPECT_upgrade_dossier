#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    arguments = parser.parse_args()
    errors = []
    with zipfile.ZipFile(arguments.wheel) as archive:
        names = archive.namelist()
        matrix = [
            name
            for name in names
            if name.endswith("/data/matrix/upgrade_matrix.json")
        ]
        if len(matrix) != 1:
            errors.append(f"canonical Upgrade Matrix count is {len(matrix)}")
        if any(name.startswith(("respect_compat/", "respect_ification/")) for name in names):
            errors.append("wheel contains TestKit packages")
        if any(
            name.lower().endswith((".apk", ".jks", ".keystore", ".env"))
            or "/.git/" in name
            for name in names
        ):
            errors.append("wheel contains forbidden private/generated material")
    print(json.dumps({"errors": errors, "valid": not errors}, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
