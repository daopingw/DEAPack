# Contributing

DEAPack welcomes questions, model proposals, bug reports, code, datasets,
teaching cases, visualizations, and documentation improvements. A
contributor does not need to implement a method before suggesting it.

Start with the repository's complete
[contribution guide](https://github.com/daopingw/DEAPack/blob/main/CONTRIBUTING.md).
GitHub provides structured forms for a
[model proposal](https://github.com/daopingw/DEAPack/issues/new?template=model-proposal.yml),
[bug or numerical discrepancy](https://github.com/daopingw/DEAPack/issues/new?template=bug-report.yml),
and an
[editorial or translation suggestion](https://github.com/daopingw/DEAPack/issues/new?template=documentation-translation.yml).
Blank issues remain available when none of those forms fits.

Software commits require a DCO 1.1 `Signed-off-by` line and are contributed
under `GPL-3.0-only` (inbound = outbound). Project-owned original package
Documentation prose is contributed under `CC-BY-NC-SA-4.0`, while executable
examples and code blocks remain GPL software. Dataset content requires a
separate approved rights mapping. The root guide contains the complete
component boundary.

## How a model proposal is classified

A familiar name is not assumed to require another solver class.  Review first
locates the proposal in the unified framework and asks whether it is:

- an alias, preset, or parameterization of an existing mechanism;
- a source-qualified specialization that belongs in package Documentation;
- a principal transferable mechanism that expands an existing family;
- or a candidate that must be deferred until its defining source or an
  independent numerical check is available.

This classification keeps historical provenance while avoiding a catalogue of
duplicate acronyms.  The executable evidence gate requires the complete
primary source, a frozen formulation and result convention, an independent
oracle, fail-closed domain rules, tests, direct performance evidence, and
aligned package Documentation.  See {doc}`extending` for the implementation
boundaries.

## Other useful contributions

Small corrections matter.  Particularly useful contributions include a
minimal numerical counterexample, a clearer economic interpretation, an
accessible deterministic figure, a synthetic teaching dataset, a documented
performance case or a missing primary-source location. Dataset and figure proposals must
state source, transformations, redistribution status, and license; a citation
does not by itself grant redistribution permission.

Accepted work remains traceable in Git history and is acknowledged in the
most relevant release, source, dataset, figure, or translation record.
Authorship and persistent-identifier metadata are separate scholarly
decisions, not automatic consequences of a pull request.
