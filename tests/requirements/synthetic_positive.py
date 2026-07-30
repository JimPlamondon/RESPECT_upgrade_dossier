# SPDX-FileCopyrightText: 2026 Jim Plamondon
# SPDX-License-Identifier: Apache-2.0


def candidate_conforms(value):
    return value == "required-behavior"


def test_candidate_exhibits_required_behavior():
    assert candidate_conforms("required-behavior")
