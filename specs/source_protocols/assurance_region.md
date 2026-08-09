# Thompson assurance-region weight restrictions

## Readiness record

| Field | State |
|---|---|
| Candidate identifiers | `valuation.weight_restriction.ar1`; `valuation.weight_restriction.ar2_cross_side` |
| Source status | `source_not_frozen` |
| Implementation status | `blocked_on_primary_source` |
| Numerical-oracle status | `not_located` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Registry status | do not register |
| Last access audit | 2026-07-30 |

This protocol is the controlling source-gate record for the proposed
Thompson assurance-region leaves. The accessible primary records establish
the managerial purpose of assurance regions and selected empirical outcomes,
but they do not expose the complete equations, restrictions, data, and
numerical results needed for an executable source freeze.

The current release must not reconstruct those missing details from a review,
textbook, later application, or generic weight-restriction formula. A future
version may reopen this gate after authorized access to the complete primary
articles and a reproducible numerical example is obtained.

## 1. Primary sources and access boundary

### Original siting application

Russell G. Thompson, F. D. Singleton, Robert M. Thrall, and Barton A. Smith
(1986), “Comparative Site Evaluations for Locating a High-Energy Physics Lab
in Texas,” *Interfaces*, 16(6), 35--49.
[DOI](https://doi.org/10.1287/inte.16.6.35);
[author and abstract record](https://ideas.repec.org/a/inm/orinte/v16y1986i6p35-49.html).

The authoritative abstract confirms all of the following:

- six feasible sites were evaluated;
- the decision account included project cost, user time delay, and
  environmental impact;
- price weights for time delay and environmental impact were studied after
  normalizing on project cost;
- arguments were used to bracket the price-weight pairs into an “assurance
  region”;
- South Dallas was preferred over a wide range of conditions; and
- North Houston was sensitive to the environmental-impact index.

The audited environment did not provide the article body. The publisher PDF
endpoint rejected retrieval, and no authorized open author manuscript was
located in the time-boxed audit. The abstract does not contain the full DEA
programme, exact bounds, site data, or score table.

### Formal multiplier-bounds treatment and farm application

Russell G. Thompson, Larry N. Langemeier, Chih-Tah Lee, Euntaik Lee, and
Robert M. Thrall (1990), “The Role of Multiplier Bounds in Efficiency
Analysis with Application to Kansas Farming,” *Journal of Econometrics*,
46(1--2), 93--108.
[DOI](https://doi.org/10.1016/0304-4076(90)90049-Y);
[publisher record](https://www.sciencedirect.com/science/article/pii/030440769090049Y).

The publisher abstract confirms all of the following:

- the economic assessment is intended to add price or cost information after
  technically efficient organizations have been identified;
- the assurance-region concept is defined for a linear production
  possibility set;
- the farm application uses a special case comprising separate linear
  homogeneous restrictions on input and output multipliers;
- the data concern 83 farms; and
- the restrictions reduce candidates for overall efficiency from 23 to 8 in
  the Ratio Model and from 44 to 13 in the Convex Model.

The full article is subscription restricted in the audited environment. The
abstract supplies neither the complete multiplier programmes nor the farm
data, bound matrices, observation-level scores, or target results.

These publisher and bibliographic records are primary discovery evidence.
They are not substitutes for equation- and table-level access to the
articles.

## 2. Economic and managerial problem that is source-supported

Unrestricted DEA allows each organization or site to select whichever
nonnegative implicit valuations make it look best. In the siting application,
technical efficiency alone left several serious candidates. Decision makers
also needed valuations of construction cost, user delay, and environmental
impact that remained within a substantively defensible range.

The assurance-region question supported by the primary abstracts is:

> Among technically efficient alternatives, which remain attractive when
> their implicit prices or costs are required to lie in a defensible region?

The restrictions are therefore preference or valuation information. The
accessible primary evidence does not show that they change observed
production quantities, estimate statistical uncertainty, or reveal market
prices. Bounds must not be described as objective prices unless their
provenance establishes that interpretation.

## 3. Items that are not source-frozen

The following details are required before either candidate can become an
executable leaf:

1. the exact Ratio Model and Convex Model objectives, constraints, multiplier
   signs, and score directions;
2. the normalization used in every model and whether project-cost
   normalization in the 1986 application is application-specific;
3. the exact matrices or pairwise inequalities defining the assurance
   region;
4. the primary-source definitions and names of AR-I and AR-II, including
   whether AR-II links input and output multiplier sides and under which
   numeraire;
5. the treatment of a free convex-model intercept and its interaction with
   weight restrictions;
6. the precise returns-to-scale and reference-population assumptions;
7. the multiplier-to-envelopment dual and the economic meaning of any
   resulting cone or production trade-off terms;
8. necessary and sufficient feasibility or consistency conditions for a
   declared set of bounds;
9. rules for zero input/output observations, zero denominators, unrestricted
   or negative multipliers, and infinite ratio bounds;
10. the exact bound provenance and units in the site and farm applications;
11. all raw observations needed by a published example; and
12. observation-level unrestricted and restricted scores, binding
    restrictions, multipliers, and any reported targets.

No default normalization, epsilon convention, zero policy, or infeasibility
repair may be inferred merely because it is common in later software.

## 4. Non-equivalence boundary still requiring primary confirmation

The repository review currently distinguishes three ideas:

- within-input-side or within-output-side multiplier-ratio restrictions,
  commonly labelled AR-I;
- restrictions linking an input multiplier to an output multiplier, commonly
  labelled AR-II or linked assurance regions; and
- Wong--Beasley bounds on an evaluated observation's virtual input or output
  shares.

That distinction is a useful discovery map, but the complete Thompson sources
were not available to certify the exact AR-I and AR-II equations, indexing,
normalization, or terminology. It must not yet be promoted into executable
aliases or a shared public `restrictions=` contract. In particular,
multiplier ratios and observation-specific virtual shares are not assumed to
be interchangeable, and a cross-side bound is not assumed to be
normalization-invariant.

The later source freeze for the Charnes--Cooper--Huang--Sun finite
polyhedral cone-ratio model does not reopen this gate. That distinct public leaf
accepts exogenous input and output cones directly in nonnegative sum form and
is restricted to input-oriented CRS. The 1990 cone-ratio article demonstrates
that some within-side pairwise ratio inequalities are special half-space
representations of polyhedral cones, but it does not freeze Thompson's full
Ratio Model, Convex Model, AR-I/AR-II terminology, cross-side normalization,
or farm example. See
`charnes_cooper_huang_sun_1990_polyhedral_cone_ratio.md` for the executable
boundary and its independently reproducible Example 2.

## 5. Numerical-oracle gate

No reproducible primary-source oracle has been obtained.

- The 1986 abstract reports a six-site decision outcome, but it omits the
  complete site data, assurance-region bounds, and unrestricted/restricted
  score vector.
- The 1990 abstract reports aggregate candidate counts for 83 farms, but it
  omits the farm-level data, exact Ratio/Convex programmes, bound matrices,
  and observation-level outputs.
- Counts such as “23 to 8” or “44 to 13” cannot certify score values,
  normalization, feasibility handling, binding bounds, or solver-selected
  multipliers.

A package-designed toy inequality would test generic linear programming, not
reproduce the Thompson method. It is therefore insufficient for the
literature-oracle release gate.

## 6. Conditions for reopening in a future version

The source gate may be reopened only when the following evidence is available:

1. complete, authorized copies of the 1986 and/or 1990 primary articles;
2. a page-by-page equation freeze covering the base DEA model,
   normalization, multiplier domains, and every assurance-region constraint;
3. a primary-source determination of the AR-I/AR-II relationship and its
   exact non-equivalence to virtual-share restrictions;
4. an explicit feasibility, unit, zero-data, and negative-weight domain
   contract; and
5. at least one primary numerical example whose data, bounds, score vector,
   and binding-restriction results can be independently recomputed.

Until then, the correct release action is
`deferred_to_next_version`: no implementation, catalog entry, registry record,
book claim of executable support, or public API.
