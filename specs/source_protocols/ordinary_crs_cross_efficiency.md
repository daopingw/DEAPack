# Ordinary CRS cross-efficiency: deferred release protocol

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `evaluation.cross.crs` |
| Defining-source status | `identified_full_text_not_obtained` |
| Secondary-goal source status | `identified_full_text_not_obtained` |
| Implementation status | `prototype_internal_only` |
| Equation-freeze status | `later_primary_source_only` |
| Numerical-oracle status | `later_source_profiles_not_current_raw_matrix_oracle` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Registry status | retained non-public prototype |
| Last access audit | 2026-07-31 |

This protocol is the controlling evidence boundary for DEAPack's proposed
ordinary CRS cross-efficiency method. Prototype code and property tests may
remain in the repository so that the formulation, solver behavior, and
reporting contract can be audited. They are not current-release evidence for
a public catalog method, public symbol, source-qualified ranking, or
source-native numerical reproduction.

The independently source-frozen Liang--Wu--Cook--Zhu game cross-efficiency
protocol is outside this deferment. It retains its separate method identity,
public API, and literature oracle.

## 1. Defining sources and access boundary

The defining source is Thomas R. Sexton, Richard H. Silkman, and Andrew J.
Hogan (1986), “Data Envelopment Analysis: Critique and Extensions,” in
Richard H. Silkman (ed.), *Measuring Efficiency: An Assessment of Data
Envelopment Analysis*, *New Directions for Program Evaluation*, 32, 73--105
([DOI](https://doi.org/10.1002/ev.1441)).

Publisher metadata and limited search snippets identify the chapter and
confirm that it discusses appraiser-by-evaluatee cross-efficiencies, row and
column summaries, arbitrary primary optimal weights, and secondary selection
on the primary optimal face. A complete, legally accessible copy was not
obtained in the audited environment. Search snippets are not a substitute for
page-level verification of the chapter's complete programmes, assumptions,
aggregation rules, edge cases, and numerical tables.

The principal secondary-goal source is John Doyle and Rodney Green (1994),
“Efficiency and Cross-Efficiency in DEA: Derivations, Meanings and Uses,”
*Journal of the Operational Research Society*, 45(5), 567--578
([DOI](https://doi.org/10.1057/jors.1994.84)). Publisher metadata confirms
that the paper distinguishes several aggressive and benevolent
implementations. A complete copy was not obtained, so DEAPack has not frozen
the exact Method I, II, and III programmes, their equivalence boundaries, or
their original numerical results.

Consequently, the repository must not attribute its current solver-selected
raw prototype, strict-positive-input rule, self-exclusion option, maverick
index, or failure policy to either defining source.

## 2. What the complete later source supports

Liang, Wu, Cook, and Zhu (2008), “Alternative Secondary Goals in DEA
Cross-Efficiency Evaluation,” *Operations Research*, 56(4), 1055--1065
([DOI](https://doi.org/10.1287/opre.1070.0487)) is available as a complete
primary article. Its equations (1)--(3) support the following later account:

1. each organization solves an input-normalized CCR multiplier programme;
2. one selected multiplier system is carried across all evaluatees in that
   appraiser's row;
3. the ordinary aggregate is an equal arithmetic column mean including the
   diagonal; and
4. alternate primary optima can change raw cross-appraisals even when the
   diagonal CCR scores are unchanged.

Its five-organization example supplies published CCR scores and arbitrary,
aggressive, benevolent, and game aggregate profiles. The arbitrary profile
is produced by one unspecified primary optimum selected by the source's
software. It is not a unique oracle for DEAPack's solver-selected prototype:
another certified primary optimum may yield a different off-diagonal matrix
and column means. The aggressive and benevolent profiles are not oracles for
an ordinary raw implementation because they depend on distinct secondary
programmes that the prototype does not implement.

This later source provides important mathematical and behavioral evidence.
It does not close the exact historical definition or the Doyle--Green
secondary-goal boundary.

## 3. Current prototype boundary

The internal `CRSCrossEfficiency` / `CrossEfficiency` implementation currently
uses one certified, solver-selected primary CCR optimum per appraiser. It
forms an appraiser-by-evaluatee matrix and reports an equal column mean. Its
default includes self-appraisal; `include_self=False` is an explicit package
extension. It labels multiplier and score uniqueness as unassessed and
attaches no aggressive, benevolent, neutral, or game interpretation.

The prototype adds engineering safeguards that are useful but not yet
source-frozen:

- every input component must be strictly positive;
- every organization must have positive aggregate desirable output;
- every virtual-input denominator and postprocessed ratio must be valid;
- primal feasibility, dual optimality, and the duality gap must be certified;
- a failed appraiser prevents publication of a complete score vector; and
- the optional maverick index compares self-efficiency with the peer-only
  mean using a package-defined denominator.

These rules describe current code behavior only. They must not be presented
as universal cross-efficiency requirements or historical source conventions.

## 4. Why the present tests do not close the gate

The repository tests establish useful prototype properties: the one-input,
one-output case is analytically transparent; the Liang data reproduce the
published CCR diagonal; equal means agree with the materialized matrix;
streamed and stored summaries agree; unit changes are coherent in a simple
case; malformed, uncertified, and dimensionally invalid solutions fail
closed; and two certified primary optima can preserve the diagonal while
changing the peer matrix and ranking.

Those tests remain insufficient for release because:

1. they execute the production prototype rather than a separately written
   compiler transcribed from frozen defining-source equations;
2. the published arbitrary matrix is not unique and therefore cannot certify
   the solver-selected raw result;
3. no complete Sexton--Silkman--Hogan numerical table has been independently
   reproduced;
4. no complete Doyle--Green Method II or Method III numerical table has been
   independently reproduced; and
5. property checks cannot establish unobserved source conventions for zeros,
   epsilon or delta values, self-inclusion, aggregation, degeneracy, or
   alternate optima.

Benchmarks demonstrate computational behavior, not literature identity.

## 5. Items not yet source-frozen

The following matters remain open:

1. the complete Sexton--Silkman--Hogan primary and secondary programmes,
   normalizations, multiplier bounds, and tie-breaking sequence;
2. the source-native definitions and intended uses of row means, column
   means, the grand mean, and any maverick or disagreement statistic;
3. whether each summary includes its diagonal and how missing or invalid
   appraisals are handled;
4. admissible zero input/output observations, zero multiplier weights,
   virtual-input denominators, and any positive epsilon or delta convention;
5. all Doyle--Green Method I, II, and III aggressive and benevolent
   programmes, including ratio-of-sums versus sum-of-ratios distinctions;
6. the interpretation and uniqueness status of rankings under alternate
   primary and secondary optima;
7. a complete source-native nursing-home or department example with input and
   output data, multiplier selections, appraisal matrix, and summaries; and
8. exact boundaries between ordinary raw, aggressive, benevolent, neutral,
   common-weight, interval/robust, VRS, and game cross-efficiency methods.

The four proposed Doyle--Green Method II/III aggressive/benevolent identifiers
remain literature-review inventory only. They have no machine record and no
current API.

## 6. Gate for the next version

The candidate may be reconsidered only after all of the following are
available:

1. complete, authorized copies of Sexton--Silkman--Hogan (1986) and
   Doyle--Green (1994);
2. page-level transcription and independent review of every programme,
   normalization, assumption, aggregation rule, and interpretation used by
   each proposed implementation;
3. an explicit reconciliation with Liang--Wu--Cook--Zhu (2008), including
   every difference in primary selection and summary construction;
4. separately named source leaves for every materially different ordinary,
   aggressive, benevolent, or neutral protocol rather than one overloaded
   switch;
5. one complete source-native numerical reproduction for the ordinary method
   and one for each secondary leaf, or an exact synthetic oracle evaluated by
   a separately written source-equation compiler;
6. regression tests for self-inclusion, row/column/grand summaries, zeros,
   epsilon/delta policies, invalid denominators, degeneracy, alternate
   optima, unit changes, and solver failure; and
7. reviewed economic and managerial interpretations that do not present a
   solver-selected ranking as uniquely determined peer consensus.

Only after this gate passes may `evaluation.cross.crs` regain a public API
identity and executable current-release documentation. Until then,
`deferred_to_next_version` is the release disposition.
