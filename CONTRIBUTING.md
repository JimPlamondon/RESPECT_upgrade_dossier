# Contributing

Anyone may propose an Upgrade Matrix change through a Git branch or fork.
Proposal does not confer acceptance. Only Jim Plamondon, or a governance
authority he explicitly delegates, may move a requirement to `accepted`.

Accepted requirements and their registered tests are protected inputs to
implementation work. Implementation agents must work only within each row's
`allowed_scope` and must not modify the canonical Matrix or acceptance tests.

Use signed-off commits (`git commit -s`). Do not commit secrets, private
CanApp material, device data, generated prompts, or candidate-build evidence
that contains private information.
