# Contributing to DEAPack

DEAPack is developed as a coordinated software and package-Documentation
project. Contributions are welcome, but a new acronym or a
plausible optimization programme is not by itself a new supported method.
Code, economic meaning, notation, validation, and reader-facing material must
remain aligned.

## Contribution terms and component boundaries

The repository uses component-specific inbound terms. Every pull-request
commit must carry a DCO 1.1 `Signed-off-by` trailer; the protected DCO status
check verifies the exact pull-request commit range before merge. The terms apply
prospectively and do not infer ownership of existing material or retroactively
assign an earlier contribution.

- **Software code:** sign off under the
  [Developer's Certificate of Origin 1.1](DCO.txt) with
  `git commit --signoff`. The contribution is accepted under the same
  `GPL-3.0-only` terms used outbound (inbound = outbound). DEAPack does not
  require a separate code CLA at present.
- **Package Documentation:** original prose and original visual expression are
  contributed under `CC-BY-NC-SA-4.0`; executable examples, code blocks,
  snippets, and API signatures are contributed under `GPL-3.0-only`.
- **Dataset content:** a dataset confirmed to be wholly project-created may be
  accepted under `CC-BY-4.0` only after the contributor's identity, authority,
  origin declaration, attribution, and exact content mapping are reviewed.
  External and source-derived data follow their own terms and never inherit a
  DEAPack license. [DATA_LICENSES.md](DATA_LICENSES.md) records the exact
  fingerprint, attribution, and terms for every current dataset.

The complete outgoing boundary and official license-text locations are in
[COMPONENT_LICENSES.md](COMPONENT_LICENSES.md). A sign-off records the DCO
certification; it does not prove dataset clearance or establish authority on
behalf of an employer or co-owner.

English is the canonical source language for code, API names, and package
Documentation.

You do not need to arrive with finished code.  Questions, counterexamples,
literature leads, model proposals, data corrections, teaching cases,
visualization ideas, and documentation corrections are all useful
contributions.  Use the structured GitHub issue forms when possible so that a
suggestion can be evaluated without asking the contributor to learn the whole
repository first.

## Before opening a change

For a bug fix, documentation correction, dataset improvement, visualization,
or performance change, open an issue or pull request that states:

- the observable problem and the smallest affected public contract;
- whether scores, targets, peers, diagnostics, or only presentation changes;
- a reproducible example or fixture;
- the expected behavior and supporting source when the behavior is
  method-specific.

For a proposed method, begin with its economic or managerial question rather
than its historical acronym. Check the
[method universe](specs/METHOD_UNIVERSE.md), the
[canonical registry](specs/METHODS.md), and the
[source protocols](specs/source_protocols/README.md) first. Historically
different names may already be aliases, presets, parameterizations, or
non-equivalent uses of a shared numerical kernel.

The dedicated model-proposal form accepts an idea before an implementation
exists.  Maintainers will first decide whether it is a principal transferable
mechanism, an alias or parameterization of an existing family, a
Documentation-only specialization, or a source-deferred candidate.  That
classification is not a judgment about the value of the underlying research;
it keeps the package coherent and discoverable.

## Evidence gate for a new executable method

A literature-defined method can enter the public package only when all of the
following are available:

1. the complete defining primary source;
2. source-native equations, admissible data, technology, score convention,
   economic interpretation, and target policy frozen in a source protocol;
3. an independently reproducible numerical oracle, cross-implementation
   check, or exact independently derived analytical fixture;
4. fail-closed domain and compatibility rules;
5. public result, diagnostics, and metadata contracts;
6. tests covering the formulation, invariance domain, failure cases, and
   independent validation;
7. direct performance evidence proportional to the expected workload;
8. complete package Documentation that states the supported domain, result
   interpretation, limitations, and source-qualified identity.

If any of the first three items cannot be completed, record the candidate as
`deferred_to_next_version`. It may remain visible in the field map and retain
a source protocol that explains what is missing, but it must not receive a
guessed solver, public constructor, or machine method record. Missing original
application data prevents a claim of
empirical reproduction; it does not prevent a later theory release if the
complete source and an exact independent synthetic oracle are available.

The full promotion policy is specified in the
[coverage audit](specs/METHOD_COVERAGE_AUDIT.md) and
[roadmap](ROADMAP.md).

## Method contribution sequence

Use this order so that implementation choices cannot silently define the
theory:

1. create or update a source-freeze protocol;
2. locate the method in the eleven-axis unified framework;
3. state equivalence and non-equivalence boundaries;
4. freeze notation and result semantics;
5. add the numerical kernel or composition;
6. add analytical, property, failure, and independent-oracle tests;
7. add a direct `benchmarks/benchmark_*.py` execution contract;
8. add the machine method record and public catalog projection;
9. document the method in the API/model reference and method catalog.

A benchmark may be attached to a method only when it directly executes that
complete public API. Component benchmarks do not automatically certify a
composed method. See the [benchmark contract](benchmarks/README.md).

## Local checks

Install the development environment:

```bash
python -m pip install -e '.[dev,docs]'
```

Run the quality gates relevant to the change:

```bash
ruff format --check .
ruff check .
make test PYTHON=.venv/bin/python
sphinx-build -W --keep-going -E -a -b html docs docs/_build/html
```

Regenerate committed figures when their source changes and confirm that the
generated assets are reproducible. Do not commit solver logs, local build
directories, virtual environments, or machine-specific timing claims without
the environment information required by the benchmark contract.

## Pull-request scope

Keep each pull request centered on one method leaf, one shared kernel change,
or one coherent editorial correction. Preserve unrelated work in the
repository. A performance change must retain numerical agreement and
diagnostic completeness; a documentation-only change must not imply an
unsupported executable feature.

Every contribution should leave a future reader able to answer four
questions: what decision problem is being measured, under what production
possibilities, according to which source, and how the implementation was
independently checked.

## Credit, rights, and research integrity

Accepted contributions remain visible in Git history and are acknowledged in
release notes or the relevant source, dataset, example, figure, or translation
record when that is the most useful scholarly provenance.  A substantial
contribution can be discussed with the maintainers before submission so that
credit expectations are explicit. A contribution does not automatically
create software authorship or DOI metadata; those records follow the
contribution's nature and the policies of the eventual publication venue.

Only submit material that you are entitled to contribute.  Dataset and figure
contributions must identify their source, transformation, redistribution
status, and license; a citation alone is not permission to redistribute.
For an independently constructed theoretical or synthetic dataset, use the
[project-created dataset origin template](specs/dataset_candidates/ORIGIN_DECLARATION_TEMPLATE.md)
to record the management question, complete numerical recipe, contributors,
content license, oracle, and propagation checks. A passing numerical example
remains a candidate until that factual record and its release boundary are
approved.
Code contributions require DCO 1.1 sign-off and are accepted under
`GPL-3.0-only`. Original package Documentation prose is accepted under
`CC-BY-NC-SA-4.0`, with embedded code under GPL. Dataset contributions require
an affirmative dataset-to-license record; `CC-BY-4.0` is the adopted default
only for content confirmed to be wholly project-created.

For the first release candidate, the unresolved component and dataset
decisions are recorded explicitly in
[the rights review worksheet](specs/RELEASE_RIGHTS_REVIEW_2_0_RC1.md). That
worksheet is a maintainer decision record, not a claim that currently
uncleared material may be redistributed.

Please report security or result-integrity vulnerabilities through the private
route in [SECURITY.md](SECURITY.md), not through a public issue containing
exploit details.
