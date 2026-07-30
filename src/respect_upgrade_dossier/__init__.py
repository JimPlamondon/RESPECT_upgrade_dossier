# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

"""Git-governed requirements and acceptance tooling for RESPECT upgrades."""

from .matrix import load_matrix, semantic_hash, validate_matrix

__all__ = ["load_matrix", "semantic_hash", "validate_matrix"]
__version__ = "0.1.0"
