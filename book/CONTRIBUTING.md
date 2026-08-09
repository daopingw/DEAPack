# Contributing to the Companion Book

The companion book is an English-source, research-grade introduction to efficiency and
productivity analysis, prepared for publication in English and Chinese. It is not an API manual and it
is not a catalogue of model acronyms. A chapter should help a new reader form a correct
mental model while giving an experienced researcher enough precision to audit the
technology, measure, and empirical interpretation.

## Rights gate before editorial work

Bilingual Handbook Preview 1 is an All Rights Reserved manuscript. Issue-based
error reports, source leads, terminology corrections, and concise suggestions are
welcome. Do not submit a pull request that adds, translates, or materially rewrites
Handbook expression at this stage.

The intended route for a substantive English or Chinese contribution is a written
copyright assignment that preserves credit while providing the rights needed for
coordinated editing, translation, and publication. No repository template is an
effective agreement: the parties, authority, governing law, consideration, moral
rights, warranties, scope, and signatures require applicable-law professional review,
and an assignment would take effect only when the final instrument is executed by all
required parties. See
[`HANDBOOK_CONTRIBUTION_POLICY.md`](HANDBOOK_CONTRIBUTION_POLICY.md).

This policy is prospective. It does not infer or retroactively transfer ownership of
existing manuscript, translation, catalog, or figure material whose provenance remains
pending. Software code and package Documentation use their separate contribution terms
in the root [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Editorial principles

### Establish the economic object before the estimator

Define the production process, variable roles, and comparison population before
introducing a DEA program. Readers should know what the decision-making units do,
which quantities are discretionary, and what “better performance” means. Then define
the technology or its relevant correspondence, state its assumptions, introduce the
distance or efficiency measure, and only then derive the finite-sample program.

The governing voice is production economics and management, not geometry. Begin with
the decision problem: which resources could be saved, which services could be expanded,
which operating practices form a credible benchmark, and which changes lie within
managerial control. A diagram may show the comparison, and an optimization program may
compute it, but neither substitutes for its economic meaning. Terms such as “ray,”
“arrow,” “movement,” and “projection” should appear only where they are technically
needed and should immediately be translated into an operating plan or counterfactual.

Productivity decompositions require the same discipline. Describe efficiency change as
a change in performance relative to the best-practice benchmark available in each
period, not merely as “catch-up.” Describe technical change as a change in the
industry's attainable input--output opportunities, not merely as a frontier “shift.”
Neither component identifies a cause: management reform, learning, investment,
regulation, demand, and sample composition require separate evidence.

Do not use “DEA model” as an undifferentiated label. Keep these objects distinct:

- the economic technology and its axioms;
- the empirical technology constructed from observations;
- the distance function or efficiency measure;
- the linear program used to compute it;
- the reported score, targets, slacks, peers, and diagnostics.

### Be accessible without becoming casual

Concrete examples and figures should reduce cognitive load, not replace precision.
Prefer direct scholarly prose. Avoid slogans, theatrical transitions, repeated
metaphors, rhetorical questions used as headings, and claims such as “obviously” or
“simply” when a result depends on assumptions. A metaphor such as a frontier moving
through time may introduce an idea once; the formal language should carry the rest of
the argument.

Use established terminology consistently. At first mention, give the formal term and
the historical name when it helps readers search the literature—for example,
“input-oriented radial efficiency under constant returns to scale (the envelopment
form of the CCR model).” Thereafter, organize equivalent formulations by mathematical
substance rather than multiplying acronyms.

### Build the argument in layers, not from a chapter template

Chapters do not have mandatory repeated headings. Their intellectual movement should,
however, remain visible:

1. motivate a production or measurement problem;
2. identify the benchmark and maintained assumptions;
3. develop the relevant technology and measure;
4. interpret the economic objective, managerial counterfactual, and constraints;
5. show what the estimator returns with a reproducible example;
6. discuss identification, diagnostics, sensitivity, and limits of interpretation.

These stages may be combined or reordered when the subject demands it. The goal is a
coherent argument, not six boxes filled in mechanically.

### Treat notation and sign conventions as part of the result

Use `specs/CONVENTIONS.md`. Introduce every symbol before use and preserve dimensions,
time superscripts, and the distinction between evaluated observations and reference
observations. For distance functions, state:

- whether the measure is input-, output-, graph-, or direction-oriented;
- whether larger or smaller values indicate better performance;
- the no-change or efficient value;
- whether cross-technology evaluations can be infeasible, exceed one, or be negative;
- the normalization and units of every direction vector.

After a mathematical program, explain the objective and each family of constraints in
sentences. A displayed formula should never be followed immediately by code as though
the economic interpretation were self-evident.

### Use citations to establish provenance and delimit claims

Consult the original contribution before describing a model. Cite it at the point
where the defining technology, measure, or decomposition is introduced. Use
authoritative monographs for synthesis and terminology, and methodological reviews to
map extensions; do not cite a recent application as the source of a classic result.

The working literature baseline is `specs/LITERATURE_BASELINE.md`. It begins with
Debreu, Koopmans, Farrell, CCR, BCC, Shephard distance functions, the production-theory
treatment of Färe, Grosskopf, and Lovell, and the productivity and environmental
extensions used in later parts. Contributors should expand that register when adding a
method family.

Paraphrase sources and derive equations independently. The book should synthesize the
field in its own voice, not imitate the wording or structure of any single textbook.

### Admit model families, not every published variation

The package is broader than the manuscript. Before proposing a chapter, section,
case, or appendix, apply the handbook admission gate in
`specs/BOOK_ARCHITECTURE.md`. The proposed topic must add a field-level,
transferable production, performance, organizational, temporal, valuation, or
inference idea. A paper-specific change in direction, weights, normalization,
variable labels, or industry setting remains a tested package preset documented
in the API; it does not become another book topic. Appendices follow the same
gate and are not a holding area for specialized studies.

When several historical names implement the same substantive mechanism, teach
the canonical family once and explain the names as provenance. When a variant
changes a maintained mechanism, state that difference explicitly and show why a
reader needs it before adding manuscript material.

### Make figures do analytical work

A figure is warranted when it clarifies a production set, operational benchmark,
resource-saving plan, output-expansion plan, slack, direction vector, returns-to-scale
region, reference window, decomposition, network, or pollution-generating
relationship. It must identify axes and units, distinguish feasible operating plans
from best observed practice, and explain the economic or managerial meaning of every
line, arrow, and shaded region in the text.

Figures are deterministic assets produced by the reviewed generators under
`book/figures/`; `make -C book figures` is the authoritative complete route. Use the
shared accessible palette, meaningful alt text, and captions that state the analytical
conclusion rather than repeat the title. Decorative images do not belong in the
manuscript.

### Let code reproduce a claim

Code appears after the estimand is understood. Every example must run against the
current public API and should expose the economic quantities needed to understand the
claim. Scores alone are rarely sufficient: include targets, slacks, peers,
decompositions, or continuity accounts when they bear on interpretation. In the
chapter, describe the substantive validity condition in ordinary language. Field-level
solver statuses, post-solve certificates, release gates, and failure schemas belong in
package Documentation rather than the teaching narrative.

Use small deterministic datasets to isolate theoretical properties and documented
empirical datasets to demonstrate research workflow. Do not hand-type numerical output
that can drift from the implementation. Complete signatures, parameter inventories,
exceptions, and compatibility tables belong in the package Documentation.

An unavailable or infeasible comparison must remain missing. Never replace it with
zero, and never let a finite backend value stand in for a valid efficiency or
productivity result. The reproducible generator or test may enforce detailed numerical
checks without exposing that internal pipeline in the reader-facing example.

### Report what makes an empirical conclusion valid

An applied discussion should make visible the comparability of DMUs, sample and time
coverage, variable definitions and units, zero or negative values, orientation,
returns to scale, disposability assumptions, reference technology, infeasibility
policy, and sensitivity analysis. DEA scores are conditional estimates of relative
performance; they are not causal effects, welfare rankings, or statistical certainty.
When sampling variation or second-stage inference matters, say so explicitly and point
to the relevant inference methods.

## Bilingual workflow

English Markdown is the canonical source. The Chinese Handbook is maintained through
Sphinx gettext catalogs and the reviewed terminology guide in
`specs/CHINESE_TRANSLATION_GUIDE.md`; it is not an independently drifting manuscript.
Translate arguments as idiomatic Chinese scholarly prose while preserving equations,
symbols, API identifiers, citations, code, cross-reference labels, and generated
values. Package Documentation remains English-only for the first public release.

Before submitting a book change, run:

```bash
make -C book figures
make -C book gettext
.venv/bin/python scripts/localize_handbook_math_labels.py --check
.venv/bin/python scripts/check_handbook_translations.py --require-complete \
  --template-root book/_build/gettext
.venv/bin/python book/figures/localize_handbook_figures_zh.py --check
make -C book html
make -C book html-zh
pytest -q
```

Mathematical statements, code, generated values, figures, and both language editions
must agree. A polished paragraph cannot compensate for a model or example that fails
this consistency check.
