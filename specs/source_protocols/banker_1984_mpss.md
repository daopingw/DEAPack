# Banker (1984) most productive scale size: deferred release protocol

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `analysis.mpss.banker_1984` |
| Source status | `defining_article_identified_full_text_not_obtained` |
| Implementation status | `prototype_internal_only` |
| Equation-freeze status | `later_source_reconstruction_only` |
| Numerical-oracle status | `candidate_derived_checks_not_primary_reproduction` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Registry status | retained non-public prototype |
| Last access audit | 2026-07-31 |

This protocol is the controlling evidence boundary for DEAPack's proposed
Banker fixed-mix most productive scale size (MPSS) analysis. Prototype code
and tests may remain in the repository so that the formulation can be
audited, but they are not current-release evidence for a public catalog
method, public symbol, or executable book recipe.

## 1. Defining source and access boundary

Rajiv D. Banker (1984), “Estimating Most Productive Scale Size Using Data
Envelopment Analysis,” *European Journal of Operational Research*, 17(1),
35--44. [DOI](https://doi.org/10.1016/0377-2217(84)90006-7).

The bibliographic record and publisher metadata identify this article as the
defining source. A complete, legally accessible copy of the article was not
obtained in the audited environment. Consequently, DEAPack has not
page-frozen the source's programmes, normalizations, assumptions, endpoint
rules, numerical illustration, or managerial interpretation. Familiarity
with the MPSS literature cannot substitute for that primary-source audit.

The current prototype therefore must not imply that its three-program
construction, endpoint conventions, or result fields have been verified
against every detail of Banker (1984).

## 2. What later literature currently supports

Later literature provides useful but bounded support:

- Ray's 2010 UConn working paper
  ([PDF](https://media.economics.uconn.edu/working/2010-07.pdf)) supplies a
  later mathematical route to a fixed-mix MPSS calculation. Its displayed
  primary programme and the minimum/maximum intensity-sum programmes support
  the prototype's three-solve structure.
- Banker, Chang, and Cooper (1996)
  ([DOI](https://doi.org/10.1016/0377-2217(95)00044-5)) provide a later
  five-observation production-set example. The A--E fixture used in the
  repository is analytically derived from those displayed data, including
  the B--C MPSS interval; it is not a transcription of a published MPSS
  output table from Banker (1984).
- Zhu (2000)
  ([DOI](https://doi.org/10.1057/palgrave.jors.2600893)) supplies later
  support for distinguishing smallest and largest MPSS targets.

These sources help explain and test a plausible later formulation. They do
not prove the exact contents of the unavailable 1984 article, and they do not
authorize attribution of every prototype convention to Banker (1984).

## 3. Why the current tests are insufficient

The repository tests establish useful internal properties: the primary and
endpoint programmes resolve together, derived fixtures recover expected
interval behavior, targets remain feasible under the declared technology,
unit changes are coherent, and failure states propagate. Those checks still
fall short of a release oracle because:

1. the A--E expected results are derived from later source data rather than
   reproduced from a source-native numerical-results table;
2. the tests execute the production prototype instead of a separately
   written compiler transcribed from frozen defining-source equations;
3. the provenance and exact source role of the
   Førsund--Hjalmarsson seven-DMU fixture have not been frozen; and
4. no test can confirm the 1984 article's terminology, score convention,
   normalization, endpoint semantics, or edge-case policy without the full
   defining text.

Execution coverage and benchmarks show that prototype code runs; they do not
close the literature-evidence gate.

## 4. Items not yet source-frozen

The following matters remain open:

1. the source-native definition of productivity and its economic units;
2. the exact CRS and VRS programmes, objectives, constraints, and
   normalizations used to locate MPSS;
3. the conditions under which MPSS is a point or an interval and the precise
   rule for its smallest and largest endpoints;
4. the relationship among the optimal productivity ratio, intensity sums,
   normalized peer weights, proportional input/output plans, and any slacks;
5. returns-to-scale, free-disposal, positivity, zero-data, self-inclusion,
   infeasibility, degeneracy, and nonuniqueness assumptions;
6. which targets or peer activities, if any, the defining source treats as
   economically meaningful and whether they are unique; and
7. a defining-source numerical example with enough data and printed results
   for independent recomputation.

Until these items are frozen, MPSS must also remain distinct from local
returns-to-scale classification, radial scale efficiency, scale elasticity,
and physical capacity utilization. Similar managerial language about “best
scale” is not an equivalence proof.

## 5. Gate for the next version

The candidate may be reconsidered only after all of the following are
available:

1. a complete, authorized copy of Banker (1984);
2. page-level transcription and independent review of every programme,
   transformation, assumption, and interpretation used by the implementation;
3. an explicit reconciliation of the defining formulation with the later
   Ray, Banker--Chang--Cooper, and Zhu formulations, including every
   difference in score, normalization, technology, and endpoint convention;
4. one complete defining-source numerical reproduction, or an exact
   synthetic oracle evaluated by a separately written source-equation
   compiler that does not call the production LP builder;
5. documented provenance for every retained test fixture and expected value;
6. regression tests for point and interval MPSS, unit changes, zero and
   boundary data, nonunique peers/targets, external references, and solver
   failure; and
7. a reviewed economic interpretation that states what operating at MPSS
   means for managers without conflating global average productivity with
   local scale returns or capacity use.

Only after this gate passes may the record regain a public API identity and
current executable documentation. Until then,
`deferred_to_next_version` is the release disposition.
