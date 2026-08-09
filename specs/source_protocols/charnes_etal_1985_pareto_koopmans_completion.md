# Charnes et al. (1985) Pareto--Koopmans target completion

## Readiness record

| Field | State |
|---|---|
| Public protocol identity | `evaluation.target_completion.pareto_koopmans` |
| Identifier role | embedded evaluation protocol; not a standalone method or solver |
| Current public compositions | `static.radial`, `static.directional_distance`, and `static.generalized_distance.chavas_cox` on the ordinary all-discretionary desirable-output domain described below |
| Public entry point | the base model's `compute_slacks=True`; there is no standalone target-completion class or function |
| Primary source | complete first-hand article obtained and equation-checked |
| Independent exact evidence | closed through the existing radial and directional dense-compilation certificates |
| Published numerical reproduction | not claimed |
| Alternate-target uniqueness | not claimed |
| Deferred extensions | environmental dominance; nondiscretionary variables; FDH, FCH, and FRH technologies |
| Last source audit | 2026-07-31 |

This protocol freezes a narrow claim. Pareto--Koopmans efficiency asks whether
an attainable plan can save at least one authorized input or increase at
least one desirable output without worsening any other authorized quantity.
It is not another radial or directional score. In DEAPack it is a secondary
evaluation protocol that preserves a compatible primary optimum and completes
the remaining ordinary input/output slacks before a generic strong-efficiency
status is reported.

The protocol is public only through compatible base models. Its shared ID
names the Pareto--Koopmans completion principle and the second-phase LP
layout; it does not assert identical alternate-optimum weights in every base
model. It creates no second machine method record, no new scalar measure, and
no standalone API.

## 1. Primary-source freeze

The defining article is A. Charnes, W. W. Cooper, B. Golany, L. Seiford, and
J. Stutz (1985), “Foundations of Data Envelopment Analysis for
Pareto-Koopmans Efficient Empirical Production Functions,” *Journal of
Econometrics* 30(1--2), 91--107,
[DOI 10.1016/0304-4076(85)90133-2](https://doi.org/10.1016/0304-4076(85)90133-2).
The equation audit used the
[Carnegie Mellon University archival scan](https://iiif.library.cmu.edu/file/Cooper_box00028_fld00020_bdl0001_doc0001/Cooper_box00028_fld00020_bdl0001_doc0001.pdf).

The relevant source boundaries are:

1. **Dominance order.** Equation (4.4) tests whether another empirical plan
   can weakly increase every output and weakly decrease every input.
2. **Direct Pareto test.** Equations (4.5)--(4.6) use a VRS convex empirical
   technology and maximize the ordinary input and output slacks. The optimum
   is zero if and only if the evaluated empirical plan is
   Pareto--Koopmans efficient.
3. **Radial priority.** Equation (5.3) places the CCR radial factor ahead of
   the input/output slacks through a non-Archimedean objective. Its economic
   content is lexicographic: estimate the radial performance factor first,
   then use the slacks without sacrificing that primary optimum.
4. **Projection.** Equation (5.5) reports the resource-saving and
   service-expansion plan obtained from the radial factor and the residual
   slacks.
5. **Unit normalization.** Equation (5.7) divides slacks by the evaluated
   plan's positive input and output quantities to construct a
   unit-invariant source measure.

The source establishes the Pareto test and the economic role of residual
slacks. It does **not** prove that one numerical slack weighting selects the
only legitimate management target. It also does not define DEAPack's
zero-safe row-scale formula.

## 2. DEAPack's public completion rule

Let $F_o^*$ be the feasible set left after a compatible base model's native
optimum has been fixed. For every eligible input and desirable output,
DEAPack writes

$$
X\lambda+s^-=\bar x_o,\qquad
Y\lambda-s^+=\bar y_o,\qquad
s^-,s^+\geq 0,
$$

where $(\bar x_o,\bar y_o)$ is the fixed primary path target. For radial DEA
and DDF this is the primary radial or directional path point. For GDF it is
the finite nonnegative path target implied by the already fitted
generalized-distance score. The completion phase certifies only the
second-stage target; it does not provide independent evidence for the GDF
first-stage formula or search.
The completion phase maximizes

$$
\sum_i \frac{s_i^-}{q_i^x}
+
\sum_r \frac{s_r^+}{q_r^y},
$$

with positive, coordinate-specific scales

$$
q_i^x=\max\!\left\{\max_{j\in R_o}x_{ji},\,|a^x_{oi}|\right\},
\qquad
q_r^y=\max\!\left\{\max_{j\in R_o}y_{jr},\,|a^y_{or}|\right\},
$$

and a scale of one for an all-zero coordinate. $R_o$ is the unchanged
reference population used by the primary fit. The anchor is
$(a^x_o,a^y_o)=(x_o,y_o)$ for radial DEA and DDF, preserving those models'
established evaluated-observation weighting policy. For GDF it is
$(a^x_o,a^y_o)=(\bar x_o,\bar y_o)$, the fixed finite nonnegative path target.

Every eligible slack therefore has a strictly positive weight. If an
attainable plan dominates a selected completion, it would remain compatible
with the fixed primary optimum and would strictly increase this secondary
objective. An optimal completion is consequently Pareto--Koopmans efficient
on the declared ordinary input/output domain. Zero optimal completion slack,
together with primary-measure efficiency of the evaluated plan, certifies its
strong-efficiency status.

The row scales are a **DEAPack alternate-optimum selection rule**. Under an
independent positive unit change, each physical slack and its scale change by
the same factor, so the normalized problem is unchanged. This is related to
the source's concern with unit invariance, but it is not equation (5.7), not a
claim of historical priority, and not a uniquely management-preferred target.
The two anchor policies preserve the same completion principle and strong
status. Their difference affects only which strongly efficient target and
peer representation can be selected when the fixed primary path admits
multiple eligible completions; it does not change the base model's
first-stage score.

## 3. Exact public domain

The reusable public identity is limited to all of the following:

- a black-box, continuous, convex DEA technology with ordinary free disposal;
- finite nonnegative inputs and desirable outputs, with positive
  observation-level input and output aggregates;
- every completed input is discretionary and may be reduced, and every
  completed output is desirable and may be increased;
- the same comparison population, temporal reference set, self-membership
  rule, and CRS/VRS/NIRS/NDRS restriction in both phases;
- one of these compatible public base models:
  - `static.radial` in input or output orientation;
  - `static.directional_distance` with nonnegative input-contraction and
    output-expansion directions and the nonnegative-distance policy; or
  - `static.generalized_distance.chavas_cox` under CRS or VRS, with a finite
    fitted score, positive observation-level input and output aggregates, and
    a fixed finite nonnegative path target;
- an exactly retained primary optimum, subject only to the declared solver
  tolerance;
- positive row-scale weights for every eligible component, anchored to the
  evaluated observation for radial DEA/DDF and to the fixed path target for
  GDF;
- an optimal completion solve and target reconstruction from the complete,
  unthresholded intensity vector; and
- generic `is_efficient` status only when the evaluated plan is inside the
  declared reference technology. A target can be completed for an external
  evaluation without turning the evaluated external plan into a certified
  member of that technology.

`static.additive` remains a separate direct performance measure. Its
VRS unit-weight profile is the source-native equation-(4.6) Pareto test.
DEAPack's fixed positive-weight and other-RTS configurations preserve the
same general slack logic as package extensions, but do not inherit that
historical certificate. None is relabelled as a secondary completion of some
other primary score. The direct additive evidence boundary is frozen in
`source_protocols/charnes_etal_1985_additive.md`.

## 4. Result and failure contract

A compatible result keeps four claims separate:

1. the base model's native score and measure-specific efficiency status;
2. the fixed primary path point;
3. the physical completion slacks and selected attainable target; and
4. nullable generic Pareto--Koopmans status.

The protocol fails closed when the primary solve fails, the completion solve
is absent or non-optimal, the target cannot be reconstructed, an eligible
weight is nonpositive, the reference/RTS contract changes between phases, or
the evaluated plan is outside the technology required for a status claim.
In those cases generic strong status is missing rather than inferred from a
radial factor of one or a directional distance of zero.

This protocol does not claim that the selected target is closest, furthest,
minimum-disruption, unique, causally attainable, or preferred by management.
Those are separate target-selection or decision-support questions.

## 5. Independent executable evidence

The public boundary is checked by independently compiled dense programmes,
not by reconstructing identities from the production solver's own outputs:

- `specs/oracles/radial-analytical.md` and
  `tests/test_radial_independent_oracle.py` verify exact CRS and VRS
  slack-completed targets, distinguish radial from strong efficiency, and
  cross-compile both phases over CRS, VRS, NIRS, and NDRS.
- `specs/oracles/directional-distance-analytical.md` and
  `tests/test_directional_independent_oracle.py` verify exact joint
  completion, physical slacks, targets, and strong status over all four RTS
  restrictions, plus an independent dense two-phase compiler.
- `tests/test_radial.py` and `tests/test_directional.py` verify score-only
  fail-closed status, unit changes, reference behavior, and solver-failure
  handling.
- `tests/test_target_completion_protocol.py` cross-checks the common
  second-phase layout against an independently compiled dense VRS programme
  and, at the exact $\alpha=0$ reduction, recovers the same completed target
  from radial DEA, input-only DDF, and GDF. A separate zero-component fixture
  checks the same three-model phase-two contract when individual path
  coordinates are zero but observation-level input and output aggregates
  remain positive. Metadata and unit-change checks distinguish the
  evaluated-observation anchor from GDF's fixed-path anchor.
- `tests/test_generalized_distance.py` separately checks an interior
  $\alpha=0.5$ path, keeps the fitted path target distinct from the selected
  peer activity and completed target, and verifies unit-covariant completion.

These are analytical synthetic oracles. They do not reproduce a numerical
table in Charnes et al. (1985), and they do not establish target uniqueness.
The $\alpha=0$ cross-model reduction certifies this phase-two composition
only; it is not evidence for GDF's interior first-stage formula or numerical
search. Charnes et al.'s equation (5.7) requires positive coordinate values
for its particular normalization; DEAPack's zero-safe row-scale selector is
a distinct package rule and does not import that restriction.

## 6. Deferred extensions

The following identities are `deferred_to_next_version`. Current
model-specific code paths, where present, do not inherit this reusable public
protocol claim.

| Deferred identity | Missing evidence before promotion |
|---|---|
| `evaluation.target_completion.pareto_koopmans.environmental` | A source-qualified dominance order for desirable and undesirable products under the selected strong/weak/by-production disposal technology, plus an independent exact completion oracle. |
| `evaluation.target_completion.pareto_koopmans.nondiscretionary` | A frozen variable-eligibility and equality/inequality contract for quantities that shape comparison but are not authorized management adjustments, plus an independent exact target oracle. Charnes et al. discuss equality restrictions for nondiscretionary inputs, but that discussion alone does not freeze every modern recipe. |
| `evaluation.target_completion.pareto_koopmans.fdh` | A source-qualified nonconvex completion theorem and independent exact oracle for the single-template/free-disposal technology and alternate-peer rule. |
| `evaluation.target_completion.pareto_koopmans.fch` | A source-qualified completion identity and independent exact oracle for the binary free-coordination technology and mixed-integer alternate optimum. |
| `evaluation.target_completion.pareto_koopmans.frh` | A source-qualified completion identity and independent exact oracle for integer replication activities and mixed-integer alternate targets. |

Promotion requires a complete source equation freeze, an independently
compiled discriminating fixture, unit/order invariance where claimed,
target-feasibility and strong-status proofs, alternate-optimum disclosure,
and fail-closed tests. Until then no extension receives a standalone API,
catalog identity, or machine method record.
