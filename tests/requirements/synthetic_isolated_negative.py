# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0

from .synthetic_positive import candidate_conforms


def test_isolated_mutation_is_rejected():
    assert not candidate_conforms("mutated-behavior")
