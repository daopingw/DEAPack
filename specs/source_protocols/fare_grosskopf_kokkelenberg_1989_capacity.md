# Färe--Grosskopf--Kokkelenberg (1989) physical capacity: deferred release protocol

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `analysis.capacity.physical.fare_grosskopf_kokkelenberg_1989` |
| Source status | `defining_article_identified_full_text_not_obtained` |
| Implementation status | `prototype_internal_only` |
| Equation-freeze status | `review_level_reconstruction_only` |
| Numerical-oracle status | `candidate_property_check_not_primary_reproduction` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Registry status | retained non-public prototype |
| Last access audit | 2026-07-31 |

This protocol controls the evidence gate for DEAPack's proposed physical
capacity-utilization analysis. Prototype code may remain for inspection and
future source reconciliation. It does not establish current public support
for the defining 1989 method.

## 1. Defining source and access boundary

Rolf Färe, Shawna Grosskopf, and Edward C. Kokkelenberg (1989), “Measuring
Plant Capacity, Utilization and Technical Change: A Nonparametric Approach,”
*International Economic Review*. [DOI](https://doi.org/10.2307/2526781).

The bibliographic record identifies the defining article and its
electric-utility application. A complete, legally accessible copy of the
article was not obtained in the audited environment. DEAPack therefore has
not page-frozen the two technologies or programmes, the fixed/variable input
partition, scale and disposal assumptions, utilization identities, numerical
table, or interpretation stated in the defining source.

The prototype's matched two-program decomposition is a review-level
reconstruction. It must not be described as a verified transcription of
Färe--Grosskopf--Kokkelenberg (1989) until the complete source audit is
possible.

## 2. Boundary of the available secondary evidence

An open later review
([article](https://pmc.ncbi.nlm.nih.gov/articles/PMC9150390/)) supports the
general economic distinction among observed output, technically efficient
output, and output attainable when quasi-fixed plant remains binding but
variable resources do not. It is useful for terminology and interpretation,
but it cannot freeze the defining article's exact programmes or reproduce
its numerical application.

The
[deaR manual](https://mirrors.vcea.wsu.edu/r-cran/web/packages/deaR/deaR.pdf)
documents another software package and is retained only as secondary review
context. The present audit did not freeze a deaR version, function call,
option profile, source equations, fixture, and complete output that establish
exact equivalence to the proposed DEAPack contract. The manual is therefore
not classified as an independently audited implementation oracle.

Neither secondary source closes the missing-primary-text boundary.

## 3. Why the current tests are insufficient

The four-unit repository fixture and related tests verify internal properties
of the prototype: the two output factors can be solved on one declared
reference set, the utilization identity reconstructs, fixed and variable
inputs are partitioned, units rescale coherently, and management-facing
statuses propagate. They are not source reproduction because:

1. the fixture is analytically constructed property evidence rather than
   data and values transcribed from a published results table;
2. the expected decomposition follows the prototype contract and is not
   computed by a separately written compiler from page-frozen 1989
   equations;
3. the defining electric-utility results have not been reproduced; and
4. tests for package extensions such as panel or external-reference policies
   cannot demonstrate that those extensions belong to the defining method.

Benchmarks measure execution behavior only. They do not substitute for an
equation audit or an independent numerical oracle.

## 4. Items not yet source-frozen

The following details remain unresolved:

1. the exact definition of quasi-fixed and variable inputs and whether any
   other input categories appear;
2. the source-native technical-output and capacity programmes, including
   objectives, inequalities, intensity domains, convexity/conicity, and
   disposal assumptions;
3. the returns-to-scale assumption attached to each programme and any
   alternative specifications in the article;
4. the definitions, direction, and ranges of the technical-efficiency,
   observed-capacity-utilization, and technically adjusted
   capacity-utilization measures;
5. the exact decomposition identity and the conditions under which it holds;
6. the status of implied variable-input requirements, slacks, targets, and
   peers, including nonuniqueness;
7. rules for zero quantities, infeasibility, degeneracy, self-inclusion, and
   observations outside a supplied reference technology; and
8. the complete application data or a published numerical table sufficient
   to verify all reported factors and identities independently.

Physical capacity must meanwhile remain distinct from economic capacity,
cost or profit optimization, congestion, scale efficiency, and MPSS. Holding
plant fixed answers a different managerial question from choosing the
long-run productive scale.

## 5. Gate for the next version

The candidate may be reopened only after all of the following are available:

1. a complete, authorized copy of Färe--Grosskopf--Kokkelenberg (1989);
2. page-level transcription and independent review of the fixed/variable
   input definitions, both programmes, all transformations, assumptions, and
   economic interpretations;
3. a frozen source profile covering returns to scale, disposability,
   reference membership, output mix, target/slack policy, failure rules, and
   uniqueness claims;
4. reproduction of the defining electric-utility example, or an exact
   source-equation oracle implemented independently of the production
   compiler;
5. if deaR is used as cross-implementation evidence, a pinned version,
   source-matched options, complete fixture and outputs, and a documented
   proof that its implemented programme matches the frozen defining
   formulation;
6. tests separating the source method from DEAPack extensions such as panels,
   external/custom references, nullable claims, and reporting conveniences;
   and
7. reviewed management-language documentation explaining unused plant
   capacity, operating inefficiency, and the limits of the decomposition
   without implying demand, cost, profit, or investment optimality.

Only after this evidence gate passes may the record regain a public symbol,
catalog entry, and executable documentation. Until then,
`deferred_to_next_version` is the release disposition.
