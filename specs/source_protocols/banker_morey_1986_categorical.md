# Banker--Morey (1986) categorical variables

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `static.radial.categorical.banker_morey_1986` (provisional umbrella; final leaf split unresolved) |
| Source status | `primary_metadata_and_abstract_located_full_text_not_obtained` |
| Implementation status | `deferred_source_audit` |
| Equation-freeze status | `not_frozen` |
| Dataset status | `or_library_dea3_located_raw_69x6_unlabelled_requires_source_tables` |
| Numerical-oracle status | `not_located` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Registry status | do not register |
| Last access audit | 2026-08-04 |

This is the controlling source-gate record for the proposed Banker--Morey
categorical-variable leaf. The current release must not implement, register,
or document the candidate as executable Banker--Morey support. The candidate
identifier is only a discovery label: the defining article may require
separate controllable and uncontrollable leaves after its equations are
frozen.

## 1. Defining source and access boundary

Rajiv D. Banker and Richard C. Morey (1986), “The Use of Categorical
Variables in Data Envelopment Analysis,” *Management Science*, 32(12),
1613--1627. [DOI](https://doi.org/10.1287/mnsc.32.12.1613);
[INFORMS record](https://pubsonline.informs.org/doi/10.1287/mnsc.32.12.1613).

The publisher abstract establishes that categorical information is used in
constructing comparison groups, that the article considers manager-controllable
and uncontrollable categorical variables, and that it discusses technical and
scale inefficiency. It does not expose the defining programmes, domains,
targets, category coding, numerical tables, or complete results. A complete,
legally accessible copy of pages 1613--1627 was not obtained in the audited
environment. An inaccessible URL or publisher metadata is not an equation
freeze.

The [OR-Library DEA data
record](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/deainfo.html) identifies
`dea3` as data associated with the article and says that its format is apparent
from the paper's tables. The retrieved file contains 69 rows and six unlabelled
numeric fields; it provides no DMU identifiers, headings, units, variable
roles, category coding, or expected results. Its audited SHA-256 is
`69cbe5296ee7016f1d042686bf4c63f62b6ffe27c49d12f8c5633d8a25d5852e`.
It is therefore an uninterpreted source-data candidate, not a numerical oracle.
No threshold, ordering, or categorical role may be guessed from its columns.

## 2. Items not yet source-frozen

The following details remain unresolved:

1. the complete primal and multiplier programmes for the uncontrollable
   categorical case, including the peer-eligibility relation, direction of
   category order where applicable, and self-inclusion rule;
2. the complete controllable categorical-output programme, objective,
   descriptor construction, integrality requirements, and solver form;
3. the equations and returns-to-scale conditions for technical and scale
   inefficiency and any decomposition relating them;
4. orientation, native score, slack or lexicographic stages, targets, and the
   interpretation of fitted intensities;
5. whether the article supports binary, nominal, ordered, hierarchical,
   single-category, or multiple-category information in each formulation;
6. source-native behaviour for ties, unknown labels, empty or singleton
   admissible populations, zero quantities, infeasibility, and non-unique
   optima, or an explicit record that the article is silent;
7. the boundary between the original controllable formulation and later
   corrections or revisions, including the Kamakura discussion reported in
   the literature;
8. the six `dea3` columns' names, production roles, units, DMU order, and
   categorical thresholds or codes from the source tables;
9. the complete published technical-efficiency, scale-efficiency,
   admissibility, intensity, categorical-improvement, and returns-to-scale
   results; and
10. an independently written source-equation oracle that reproduces those
    results without calling the production compiler.

Until these items are frozen, no categorical data role, source-named compiler,
convenience preset, catalog row, machine registry record, Handbook recipe, or
public class should claim the 1986 method.

## 3. Non-equivalence boundary

The proposed method must not be reconstructed by:

- one-hot encoding category labels as ordinary inputs or outputs;
- estimating an independent ordinary DEA model within each category;
- guessing an ordinal rule from the values in `dea3`;
- using a generic row filter or observation-specific comparison-population
  object and relabelling the result as Banker--Morey; or
- merging manager-controllable categorical outputs, uncontrollable comparison
  restrictions, nominal groups, and ordered groups into one untyped switch.

DEAPack provides source-neutral comparison-population infrastructure only on
`RadialDEA`, `CCR`, and `BCC`. It intersects an observation-specific declared
candidate population with the base `ReferenceSpec` and carries its own
provenance. That study-design mechanism infers no categorical interpretation
and neither proves nor implements the source equations named here.

## 4. Gate for the next version

The candidate may be reopened only after all of the following are available:

1. an authorized complete copy of the defining article;
2. a page-by-page transcription and independent review of all relevant
   equations, definitions, domains, and result tables;
3. an explicit split, if required, between controllable and uncontrollable
   formulations and between original and later-corrected variants;
4. a source-matched schema for `dea3`, including every label, role, unit,
   category code, and observation key;
5. at least one complete primary numerical reproduction through an independent
   oracle; and
6. fail-closed tests distinguishing the source leaf from ordinary filtering,
   separate-group DEA, one-hot encoding, and generic comparison eligibility.

Until that gate closes, `deferred_to_next_version` is the final release
disposition.
