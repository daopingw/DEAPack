# O'Donnell--Rao--Battese (2008) radial DEA metafrontier

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `heterogeneity.metafrontier.radial.odonnell_rao_battese_2008` |
| Source status | `source_frozen` |
| Implementation status | `implemented_and_tested` |
| Numerical-oracle status | `analytic_oracle_reproduced_and_independently_compiled`; published application data unavailable |
| Release disposition | `included_in_current_version`; published empirical reproduction deferred |
| Public API | `deapack.RadialMetafrontierDEA`; concise alias `deapack.MetafrontierDEA` |
| Registry status | registered as the candidate identifier above |
| Last source and oracle audit | 2026-07-30 |

The source gate passes for the radial DEA operator. The complete primary
article fixes the economic decomposition, the group and pooled
metafrontier programmes, the score transforms, the input- and
output-orientated variants, the CRS/VRS distinction, and the multiple-output
extension. Those programmes can be tested with an exact analytic oracle and
an independently compiled LP.

The article's country-level application cannot be reproduced exactly because
the 485 observation rows and the original DEAP control files are not
published with the article. That limits the empirical-reproduction claim; it
does not leave the DEA estimator ambiguous. DEAPack must therefore say that
it implements the source equations, not that it reproduces the article's
FAO application.

This decision is narrower than a general metafrontier family. It freezes the
paper's deterministic radial DEA construction. It does not freeze the
paper's stochastic-frontier branch, a nonconvex union estimator, a
directional or slack-based environmental metafrontier, or a metafrontier
productivity index.

## 1. Defining source and evidence boundary

Christopher J. O'Donnell, D. S. Prasada Rao, and George E. Battese (2008),
“Metafrontier frameworks for the study of firm-level efficiencies and
technology ratios,” *Empirical Economics*, 34(2), 231--255.
[DOI](https://doi.org/10.1007/s00181-007-0119-4);
[complete author final manuscript, dated 23 October 2006](https://file.pide.org.pk/pdf/Seminar/O_Donnell__Rao___Battese_EE_0447_final_version_23Oct06.pdf);
[UNE publication record](https://rune.une.edu.au/entities/publication/32e6e7b9-f9ec-40de-814a-8acb89157a19).

The equation freeze uses the published article and the complete author final
manuscript. The relevant source locations are:

- equations (1)--(6) for meta- and group technologies, output sets, and
  distance functions;
- equations (7)--(10) for meta efficiency, group efficiency, the
  metatechnology ratio, and the multiplicative decomposition;
- equation (17) and Section 3.1 for output-orientated VRS group DEA;
- the paragraph immediately after equation (17) for the pooled convex
  metafrontier and its nesting relation;
- equation (31) for multiple desirable outputs;
- equation (33) for input orientation; and
- Section 5.4 for obtaining CRS by deleting the convexity constraint.

The primary application uses 97 countries observed in 1986--1990: 27 in
Africa, 21 in the Americas, 26 in Asia, and 23 in Europe. It uses one
aggregate agricultural output and five inputs: land, machinery, labour,
fertiliser, and livestock. Table 2 reports selected-country and aggregate
summary statistics, not the complete input-output panel. Appendix A defines
the variables; Appendix B is SFA/SHazam code and refers to external data
files. Reconstructing the original data from current FAOSTAT vintages would
not be an exact reproduction.

The article does provide useful literature checkpoints:

- its scalar illustration has meta efficiency $0.60$, group efficiency
  $0.80$, and metatechnology ratio $0.75$;
- Figure 1 distinguishes a nonconvex conceptual metafrontier from a convex
  one and reports approximate ratios for both; and
- Table 2 reports published empirical summaries.

Those checkpoints verify terminology and score direction. They are not an
observation-level LP oracle.

## 2. Economic and managerial question

Organizations may perform the same broad mission while operating under
different regulatory, infrastructural, physical, or institutional
conditions. A score against only the organization's own group can therefore
mix two distinct questions:

1. how well does the organization use the opportunities available within
   its group; and
2. how far are those group opportunities from the broader opportunities
   represented by all groups?

The source decomposition separates these questions. Within-group technical
efficiency describes performance relative to the organization's restricted
operating environment. The metatechnology ratio describes the closeness of
that restricted opportunity frontier to the broader metafrontier at the
evaluated input-output mix. Meta efficiency combines both shortfalls.

This is an accounting decomposition, not a causal decomposition. A low
within-group score does not by itself identify managerial fault, and a low
metatechnology ratio does not prove that regulation, infrastructure, or any
other named condition caused the gap. Nor does it show that the organization
can adopt the meta benchmark without relocation, investment, policy change,
or other transition costs.

## 3. Frozen notation and technology construction

Let observation $o$ belong to exactly one ex ante group $g(o)=k$. It has
an input vector $x_o\in\mathbb{R}_+^m$ and a desirable-output vector
$y_o\in\mathbb{R}_+^s$.

Let $J_k$ be the eligible reference observations in group $k$, with
matrices

$$
X_k=[x_j]_{j\in J_k},\qquad
Y_k=[y_j]_{j\in J_k}.
$$

The pooled meta reference population is

$$
J_M=\bigcup_{k=1}^{K}J_k,\qquad
X_M=[x_j]_{j\in J_M},\qquad
Y_M=[y_j]_{j\in J_M}.
$$

For either reference level $S\in\{k,M\}$, the same observations, variable
roles, quantity units, orientation, returns-to-scale assumption, and temporal
information rule must be used. The only change between the two solves is the
comparison population: $J_k$ versus $J_M$.

For VRS, the empirical technology is the free-disposal convex hull:

$$
\lambda\ge 0,\qquad \mathbf 1^\top\lambda=1.
$$

For CRS, the empirical technology is the free-disposal cone:

$$
\lambda\ge 0,
$$

with no sum-of-intensities constraint. NIRS, NDRS, FDH, and other scale or
hull assumptions are not variants of this source leaf.

### Convexification boundary

At the theoretical level, the paper discusses the unrestricted technology
as the union of group technologies and explains that such a union can be
nonconvex. Its empirical DEA procedure then deliberately estimates a
**convex pooled metafrontier** by applying the same DEA model to all
observations.

The frozen construction is therefore:

```text
hull_construction = pooled_convex   # VRS
hull_construction = pooled_conic    # CRS
```

Under VRS, convex combinations may mix observations from different groups.
That is part of this estimator and must be visible in metadata. It is not
equal to the nonconvex union of estimated group hulls, and it may create a
virtual cross-group production plan that is not institutionally attainable.

## 4. Frozen output-orientated programme

For observation $o$ and reference level $S\in\{k,M\}$, solve

$$
\begin{aligned}
\phi_o^S=\max_{\phi,\lambda}\quad & \phi\\
\text{s.t.}\quad
&Y_S\lambda\ge \phi y_o,\\
&X_S\lambda\le x_o,\\
&\mathbf 1^\top\lambda=1
    &&\text{under VRS only},\\
&\lambda\ge0.
\end{aligned}
$$

This is equation (31), reducing to equation (17) for one output. The native
radial expansion factor is $\phi_o^S$. The package-facing
higher-is-better efficiency is

$$
E_{o,\mathrm{out}}^S=\frac{1}{\phi_o^S}.
$$

With source-style self inclusion and an optimal bounded solve,

$$
\phi_o^M\ge\phi_o^k\ge1,\qquad
0<E_{o,\mathrm{out}}^M\le E_{o,\mathrm{out}}^k\le1.
$$

Holding observed inputs fixed, $1-\phi^{-1}$ is the proportional output
shortfall as a share of frontier output. The native improvement factor is
$\phi-1$; these two percentages must not be interchanged.

## 5. Frozen input-orientated programme

For the same observation and matched reference level, solve the
input-orientated analogue in equation (33):

$$
\begin{aligned}
\theta_o^S=\min_{\theta,\lambda}\quad & \theta\\
\text{s.t.}\quad
&Y_S\lambda\ge y_o,\\
&X_S\lambda\le \theta x_o,\\
&\mathbf 1^\top\lambda=1
    &&\text{under VRS only},\\
&\lambda\ge0.
\end{aligned}
$$

The source reuses $\phi$ for this minimand. DEAPack must call it
$\theta$ so that an input contraction is not confused with an output
expansion. The reported higher-is-better efficiency is

$$
E_{o,\mathrm{in}}^S=\theta_o^S.
$$

With self inclusion and an optimal solve,

$$
0<\theta_o^M\le\theta_o^k\le1.
$$

Under CRS, matched input- and output-orientated radial efficiencies coincide.
Under VRS they need not. A result must always retain its orientation.

## 6. Metatechnology ratio and exact decomposition

For either orientation $q\in\{\mathrm{in},\mathrm{out}\}$, define

$$
\operatorname{MTR}_{o,q}
=
\frac{E_{o,q}^{M}}{E_{o,q}^{k}}.
$$

For output orientation this can also be computed as

$$
\operatorname{MTR}_{o,\mathrm{out}}
=\frac{\phi_o^k}{\phi_o^M}.
$$

For input orientation it is

$$
\operatorname{MTR}_{o,\mathrm{in}}
=\frac{\theta_o^M}{\theta_o^k}.
$$

The exact reconstruction identity is

$$
E_{o,q}^{M}
=
E_{o,q}^{k}\operatorname{MTR}_{o,q}.
$$

The source's canonical name is **metatechnology ratio**, because a larger
ratio means a smaller gap. “Technology gap ratio” is established earlier
terminology and may be accepted as a documented `TGR` alias. The stored
canonical field should nevertheless be `metatechnology_ratio`, with
`technology_gap_ratio`/`tgr` carrying explicit alias metadata. The package
must not relabel $1-\operatorname{MTR}$ as the source TGR.

For nested, certified solves,

$$
0<\operatorname{MTR}_{o,q}\le1.
$$

A ratio of one says that the group and meta frontiers coincide at the
evaluated radial projection. It does not say that all group technologies are
identical.

## 7. Frozen profiles and defaults

The source supports the following deterministic DEA profiles:

| Dimension | Frozen values |
|---|---|
| Orientation | `output`, `input` |
| Returns to scale | `vrs`, `crs` |
| Outputs | one or multiple desirable outputs |
| Group construction | ex ante, mutually exclusive group labels |
| Meta construction | all eligible group observations pooled in one DEA hull |
| Base cross section | all eligible rows in group versus all eligible rows pooled |
| Base panel | all periods pooled at both group and meta levels |

The source's empirical specification is output orientated and VRS. Those are
the appropriate API defaults for the exact source preset. Supporting the
other three orientation/RTS combinations is source-supported, not a
package-invented extrapolation.

Equation (17) pools all periods and thereby estimates a time-invariant
frontier. Section 5.1 also describes a cumulative period-$t$ construction
using observations from periods $1,\ldots,t$. That sequential
technological-change extension is source-supported, but it should be exposed
only when both group and meta reference plans use the identical cumulative
cutoff and a dedicated panel oracle has been added.

Contemporaneous, biennial, rolling-window, and arbitrary custom temporal
rules are not part of this exact source preset. They may later compose with
the general metafrontier family under separate identifiers and metadata.
“Meta” names the comparison population; “global” in DEAPack names a temporal
information policy. The terms must not be used as synonyms.

## 8. Data contract

An executable source leaf must require:

1. finite, nonnegative inputs and desirable outputs;
2. at least one strictly positive input and one strictly positive output for
   every evaluated observation;
3. two or more nonempty groups;
4. exactly one group label for every observation;
5. the evaluated observation included in its group and pooled reference sets;
6. identical input/output meanings, measurement units, and mission boundary
   across groups;
7. the same orientation, RTS, hull construction, and temporal information
   rule in the matched group and meta solves; and
8. no missing values in any active quantity or group field.

Groups are supplied ex ante. The source discusses statistical tools that
might help identify groups, but this DEA operator does not estimate group
membership, select the number of groups, or search for a partition that
maximizes the resulting scores.

Undesirable outputs are outside the frozen data contract. Section 5.4 notes
that directional distance functions can be useful for good and bad outputs;
it does not supply a complete undesirable-output metafrontier DEA programme.
Negative quantities, weak disposability, null-jointness, abatement
activities, and direction selection therefore belong to a separate
source-qualified environmental leaf.

## 9. Solver and reporting contract

Each observation requires two phase-one radial solves: one against its group
reference population and one against the pooled meta population. A
production implementation should group identical reference plans and reuse
compiled sparse matrices, but must not change the mathematical programme.

The mandatory observation-level result contains:

- `group_efficiency`;
- `meta_efficiency`;
- `metatechnology_ratio`;
- the orientation-specific native factors
  (`group_theta`/`meta_theta` or `group_phi`/`meta_phi`);
- group label, orientation, RTS, temporal policy, and hull construction;
- separate group and meta solver status and diagnostics; and
- decomposition residual
  $\lvert E^M-E^k\operatorname{MTR}\rvert$.

Targets and peers retain a `frontier_level` field with value `group` or
`metafrontier`; combining their intensities in one unlabelled table would
make the benchmark economically uninterpretable.

The source LP is a one-phase radial model. DEAPack may optionally apply its
generic lexicographic slack phase after fixing the radial optimum, but those
strong-efficiency, slack, and alternate-target results are package
extensions. They are not needed to compute the source MTR and must be
identified as such. Peer intensities can be nonunique even when every radial
score and target quantity is unique.

## 10. Failure and fail-closed rules

The operator must fail closed at the component level.

- If the group solve is not certified optimal, withhold group efficiency and
  MTR.
- If the meta solve is not certified optimal, withhold meta efficiency and
  MTR.
- If one component is available and the other is not, it may remain visible
  with its own diagnostic, but no decomposition may be reported.
- Reject a nonpositive or nonfinite native factor and any reciprocal that
  cannot be computed safely.
- Withhold MTR if a certified finite group efficiency is nonpositive. Solver
  feasibility tolerance is a residual threshold, not a lower bound on a
  multiplicative efficiency; every strictly positive group efficiency remains
  a valid denominator.
- If $E^M>E^k$ beyond tolerance, mark a nestedness violation and withhold
  MTR rather than clipping it to one.
- If MTR falls outside $(0,1]$ beyond tolerance, or if the reconstruction
  residual exceeds the declared tolerance, withhold the ratio and emit a
  decomposition diagnostic.
- Never repair an empty group, missing label, or mismatched group/meta
  reference policy by silently substituting the pooled sample.
- Never convert an unbounded, infeasible, time-limited, or numerical-error
  status into an efficiency score.

An MTR within the declared certificate tolerance of one may be normalized to
exactly one for display only after the raw value and residual diagnostics have
been retained. A strictly positive efficiency or MTR is never normalized to
zero. Zero cleanup is reserved for zero-benchmark residual and violation
diagnostics.

## 11. Exact analytic oracle

The following package-designed data are deliberately simple enough to prove
by inspection while still separating within-group performance from the
group opportunity gap:

| DMU | Group | Input $x$ | Output $y$ |
|---|---:|---:|---:|
| A | 1 | 2 | 2 |
| B | 1 | 4 | 4 |
| C | 1 | 4 | 2 |
| D | 2 | 1 | 2 |
| E | 2 | 2 | 4 |
| F | 2 | 4 | 8 |

The within-group best output/input ratio is one for group 1 and two for
group 2. The pooled best ratio is two. Matching observations at the relevant
input or output levels also make the same values exact under VRS.

For both CRS and VRS, and for both input and output orientation, the expected
higher-is-better results are:

| DMU | Group efficiency | Meta efficiency | MTR |
|---|---:|---:|---:|
| A | 1 | $1/2$ | $1/2$ |
| B | 1 | $1/2$ | $1/2$ |
| C | $1/2$ | $1/4$ | $1/2$ |
| D | 1 | 1 | 1 |
| E | 1 | 1 | 1 |
| F | 1 | 1 | 1 |

DMU C supplies the main decomposition oracle.

### Output orientation for C

$$
\phi_C^1=2,\qquad
\phi_C^M=4,
$$

so

$$
E_{C,\mathrm{out}}^1=\frac12,\qquad
E_{C,\mathrm{out}}^M=\frac14,\qquad
\operatorname{MTR}_{C,\mathrm{out}}=\frac12.
$$

Its radial group target is $(x,y)=(4,4)$, while its radial meta target is
$(4,8)$.

### Input orientation for C

$$
\theta_C^1=\frac12,\qquad
\theta_C^M=\frac14,
$$

so

$$
E_{C,\mathrm{in}}^1=\frac12,\qquad
E_{C,\mathrm{in}}^M=\frac14,\qquad
\operatorname{MTR}_{C,\mathrm{in}}=\frac12.
$$

Its radial group target is $(2,2)$, while its radial meta target is
$(1,2)$.

Both orientations must reconstruct

$$
\frac14=\frac12\times\frac12.
$$

Under CRS there may be alternate intensity vectors producing these targets;
tests must assert scores, target quantities, feasibility, and residuals, not
a unique peer vector.

## 12. Independent numerical cross-check

On 2026-07-30, the DMU C oracle was solved in two separately compiled
implementations:

1. the existing generic DEAPack `RadialDEA` engine, called once with the
   group-1 rows and once with all six rows; and
2. a direct `scipy.optimize.linprog` compiler that independently translated
   the displayed equations into constraint matrices without calling
   `RadialDEA`.

Using SciPy 1.18.0/HiGHS, both implementations returned:

| RTS | Orientation | Group native factor | Meta native factor | Group efficiency | Meta efficiency | MTR |
|---|---|---:|---:|---:|---:|---:|
| CRS | input | $0.5$ | $0.25$ | $0.5$ | $0.25$ | $0.5$ |
| CRS | output | $2$ | $4$ | $0.5$ | $0.25$ | $0.5$ |
| VRS | input | $0.5$ | $0.25$ | $0.5$ | $0.25$ | $0.5$ |
| VRS | output | $2$ | $4$ | $0.5$ | $0.25$ | $0.5$ |

The generic engine was also checked against every entry in the six-DMU
expected-score table for all four profiles; all 24 matched group/meta result
rows agreed.

This is a compiler-level cross-implementation check, supported independently
by the closed-form proof above. It is not a claim that two unrelated solver
libraries reproduced the paper's unpublished FAO rows. Before registration,
the implementation must commit this oracle as automated tests and retain the
direct equation compiler or an equivalent independent reference
implementation in the test suite.

Required property tests also include:

- meta efficiency never exceeds matched group efficiency;
- MTR lies in the unit interval and reconstructs meta efficiency;
- CRS input and output efficiencies coincide on the oracle;
- rescaling a common input or output unit across all groups leaves scores
  unchanged;
- row and group-label ordering do not change scores;
- a single common frontier gives MTR equal to one;
- group and meta failures propagate independently and suppress the ratio;
  and
- a deliberately mismatched reference plan triggers validation rather than
  a misleading decomposition.

## 13. Non-equivalence boundary

This source leaf is not an alias for:

- an ordinary pooled DEA score without a matched within-group solve;
- the nonconvex union of estimated group technologies;
- a convex hull constructed only from group-frontier projections;
- Charnes--Cooper--Rhodes programme-efficiency analysis;
- Asmild's global frontier-difference procedure;
- a latent-class, cluster-estimation, club-convergence, or conditional DEA
  model;
- the stochastic metafrontier estimators also discussed in the paper;
- SBM, additive, Russell, hyperbolic, or directional metafrontier measures;
- an undesirable-output or environmental metafrontier;
- a group/meta Malmquist, Hicks--Moorsteen, Färe--Primont, or other
  productivity decomposition; or
- a causal estimate of the effect of group membership or operating
  environment.

Different group/meta measures may reuse the comparison-population machinery,
but they require their own score identity, source freeze, oracle, and result
contract.

## 14. Current-version release gate

The missing original application rows are explicitly postponed; they should
be revisited only if a stable, authorized archive of the exact 1986--1990
data and aggregation procedure becomes available. No current-version effort
should attempt to reverse-engineer those rows from rounded Table 2 summaries.

The radial DEA operator itself may enter the current version after all of the
following are complete:

1. a thin group/meta orchestration layer reuses the certified radial kernel
   without duplicating its LP mathematics;
2. the analytic and independent-compiler tests in Sections 11--12 pass for
   all four orientation/RTS profiles;
3. nestedness, decomposition, component-failure, and metadata tests pass;
4. output and result schemas keep group and meta diagnostics separate;
5. the registry identifies the construction as
   `pooled_convex` or `pooled_conic`; and
6. documentation states that the source equations are implemented while the
   published agricultural application is not reproduced.

This evidence combination satisfies the current-version source gate because
the primary programme is complete and independently executable. It would not
be sufficient for a method whose defining equations, normalization, or score
account remained unavailable.

All six conditions above are satisfied by the current implementation,
registry record, analytic and independent-compiler tests, benchmark, book
chapter, and API documentation. The operator is therefore released in the
current version. Only the unavailable observation-level reproduction of the
paper's agricultural application remains deferred.
