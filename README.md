# RESPECT Upgrade Dossier

`RESPECT-upgrade-dossier` is the independent, Git-governed resource for
prescriptive requirements that future RESPECT Platform versions may implement.
It is not a CanApp compatibility test suite and has no runtime dependency on
the RESPECT TestKit.

The canonical authority is
`src/respect_upgrade_dossier/data/matrix/upgrade_matrix.json`. Imported
requirements begin as `proposed`; import does not accept them. Acceptance
requires an explicit recorded decision by Jim Plamondon or an authority he
delegates. Generated prompts and reports are derived artifacts.

Validate the installed canonical Matrix:

```text
respect-upgrade-dossier validate
```

Compile an implementation prompt only after named requirements are accepted
and implementation-ready:

```text
respect-upgrade-dossier compile UPG-EXAMPLE \
  --dossier-commit <commit> \
  --respect-revision <revision>
```

The compiler binds the Dossier commit, Matrix semantic hash, dependency
closure, registered test hashes and timeouts, supplied RESPECT revision,
allowed implementation scope, non-goals, protected paths, and verification
commands. It refuses imported, proposed, or otherwise non-ready requirements.

The initial Matrix was generated reproducibly from the TestKit commit recorded
in `provenance/import_manifest.json`. The exact source Matrix is preserved in
`provenance/import_snapshot/compatibility_matrix.json`.

This repository is deliberately local at creation time. Remote creation and
publication require a later owner action.
