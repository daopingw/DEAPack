# RC1 public-source and ordinary-CI artifact boundary

Status: **fail-closed pending maintainer rights clearance**

This record defines what the ordinary GitHub validation workflows may do before
the DEAPack 2.0 RC1 rights review is complete. It is an engineering boundary,
not a legal determination and not a release approval.

## Public source boundary

The RC1 public repository excludes three classes of historical or generated
working material:

- `book/_archive/`;
- `docs/locale/`;
- `specs/archive/`.

The reader-facing Handbook localization catalog under `book/locale/` remains in
scope, as do the formal SVG figures used by the Handbook. Build outputs,
temporary review packets, and compiled message catalogs remain ignored under
the existing generated-file rules.

Ignoring a path only controls future Git additions. Before preparing a public
commit, the maintainer must also verify that no excluded path is already in the
Git index.

## Ordinary CI is validation-only

The `tests.yml`, `documentation.yml`, and `benchmarks.yml` workflows continue to
run their builds and checks on their configured refs. Their upload steps are
deliberately guarded by a literal false condition. Consequently, an ordinary
pull request, main-branch build, scheduled build, tag build, or manual
validation run cannot publish:

- wheel or source-distribution archives;
- rendered HTML sites;
- Handbook PDFs; or
- benchmark result bundles.

This design does not need a private approval key in pull-request jobs and does
not turn a rights blocker into a failed test suite. Logs still provide normal
development feedback, while generated files remain ephemeral on the runner.

## Publication route

Downloadable artifacts belong only to a separate protected publication path
that binds the reviewed bytes to the approved release tag and authorization
record. Enabling an upload in any ordinary workflow is therefore a policy
change requiring maintainer review, an updated regression test, and a renewed
rights audit. Replacing the literal-false condition with a branch, actor,
event-name, or filename check is not sufficient authorization.
