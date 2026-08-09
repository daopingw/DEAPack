# Portela--Thanassoulis--Simpson (2004) range directional measure

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `static.range_directional.portela_thanassoulis_simpson_2004` |
| Source status | `primary_source_equation_frozen` |
| Implementation status | `implemented_tested_released` |
| Numerical-oracle status | `exact_analytic_oracle_and_independent_compiler_passed` |
| Release disposition | `public_source_qualified_leaf` |
| Public API | `RangeDirectionalDEA`; concise alias `RDM` |
| Registry status | public method record and composition relation registered |
| Last release validation | 2026-07-30 |

This protocol freezes the evidence needed to implement the original range
directional measure (RDM) and records the boundary of the released leaf. The
release implements only the programmes and interpretations frozen here. It
does not authorize a reconstruction of adjacent signed-data methods from
similar names or secondary descriptions.

The pass decision rests on two independent items:

1. the complete author manuscript contains the generic directional programme,
   the ideal-point direction, the RDM programme, the score transformation,
   the invariance arguments, and a reported numerical illustration; and
2. Section 10 below gives a fully specified rational-data LP oracle whose
   optimum can be proved without relying on rounded software output.

## 1. Defining source and evidence boundary

Maria Conceicao A. Silva Portela, Emmanuel Thanassoulis, and Gary Simpson
(2004), "Negative data in DEA: a directional distance approach applied to
bank branches," *Journal of the Operational Research Society*, 55(10),
1111--1121.

- [DOI](https://doi.org/10.1057/palgrave.jors.2601768)
- [Aston University accepted manuscript](https://publications.aston.ac.uk/id/eprint/4099/1/Negative_data_in_DEA.PDF)
- [Aston University repository record](https://publications.aston.ac.uk/id/eprint/4099/)

The accepted manuscript is the complete primary text, not an abstract or a
secondary reconstruction. The following source items control this freeze:

| Source item | Frozen use |
|---|---|
| Equation (1) | VRS directional distance programme and orientation convention |
| Equation (2) | Focal-unit ranges from the observed coordinatewise ideal |
| Equation (3) | Original RDM programme |
| Text following equation (3) | Translation invariance under VRS and positive-units invariance |
| "Interpreting beta in model RDM" | Native inefficiency `beta` and reported efficiency `1 - beta` |
| "Pareto-efficiency" | Slack and weak-frontier limitation |
| Figure 2 discussion and Table 1 | Published target and score corroboration |
| Equation (4) and its discussion | Boundary between RDM and inverse RDM |

The bank-branch data are confidential and are not an executable public
fixture. Their presence is not used to claim empirical reproducibility.

## 2. Economic and managerial question

RDM asks:

> Given the best input and output levels observed in the comparison group,
> what common share of this unit's remaining observed improvement
> opportunities can be realized while staying within the VRS production
> possibility set?

The coordinatewise ideal combines the lowest observed level of every input
and the highest observed level of every output. It need not be an attainable
operating plan. It is an aspiration reference that records how much room for
improvement remains in each account.

For one unit of the common improvement factor `beta`, an input with a larger
gap from the best observed input is asked to fall by more in its own units,
and an output with a larger gap from the best observed output is asked to
rise by more. The source describes this as giving priority to factors on
which the unit performs worst relative to the observed best values. Thus RDM
is a target-priority rule as well as an efficiency measure.

Negative numbers are admitted because the model works with economically
directed differences rather than ratios to the observed level. The economic
roles do not change:

- an input is still an account for which less is preferred; and
- an output is still an account for which more is preferred.

A negative desirable output is therefore not an undesirable output. A bad
output requiring contraction has a different economic role and is outside
this source leaf.

## 3. Frozen notation and technology

Let:

- `J = {1, ..., n}` be the comparison population;
- `i = 1, ..., m` index inputs;
- `r = 1, ..., s` index desirable outputs;
- `o in J` be the focal DMU;
- `x_ij` be input `i` of DMU `j`; and
- `y_rj` be output `r` of DMU `j`.

All observations must be finite real numbers. Negative and zero observations
are allowed when their account meanings support the stated input or output
preference.

The source-qualified technology is the self-inclusive, free-disposal VRS
technology

```math
T_{\mathrm{VRS}}
=
\left\{
(x,y):
\sum_{j\in J}\lambda_j x_{ij}\le x_i,\quad
\sum_{j\in J}\lambda_j y_{rj}\ge y_r,\quad
\sum_{j\in J}\lambda_j=1,\quad
\lambda_j\ge0
\right\}.
```

The same comparison population `J` must be used:

1. to form the VRS technology;
2. to calculate every coordinatewise best value; and
3. to evaluate the focal member `o`.

Changing any one of these sets creates a different estimator and invalidates
the self-feasibility and bounded-score arguments below. Group, period, or
conditional frontiers may use a different `J`, but the extrema and the
technology must be rebuilt together and the focal observation must belong to
that exact set.

## 4. Ideal point and range direction

Define the coordinatewise observed best values

```math
x_i^{\min}=\min_{j\in J}x_{ij},
\qquad
y_r^{\max}=\max_{j\in J}y_{rj}.
```

For focal DMU `o`, equation (2) defines

```math
R^x_{io}=x_{io}-x_i^{\min}\ge0,
\qquad
R^y_{ro}=y_r^{\max}-y_{ro}\ge0.
```

The RDM direction is

```math
g_o=(R^x_o,R^y_o).
```

These are ranges of *possible improvement for the focal unit*. They are not
the full sample spreads `max x_i - min x_i` and
`max y_r - min y_r`. They are also not evidence that the coordinatewise
ideal is jointly feasible.

The direction is:

- focal-unit dependent;
- comparison-population dependent;
- nonnegative even when observed levels are negative; and
- endogenous to the declared data and reference policy, rather than a
  freely supplied generic DDF direction.

## 5. Frozen programmes

### 5.1 Non-oriented RDM: source equation (3)

```math
\begin{aligned}
\max_{\beta_o,\lambda}\quad & \beta_o \\
\text{s.t.}\quad
& \sum_{j\in J}\lambda_j y_{rj}
  \ge y_{ro}+\beta_o R^y_{ro},
  && r=1,\ldots,s,\\
& \sum_{j\in J}\lambda_j x_{ij}
  \le x_{io}-\beta_o R^x_{io},
  && i=1,\ldots,m,\\
& \sum_{j\in J}\lambda_j=1,\\
& \lambda_j\ge0,\qquad \beta_o\ge0.
\end{aligned}
```

The manuscript writes equation (3) as the RDM specialization of its
nonnegative-direction programme in equation (1). The nonnegativity of
`beta_o` is inherited from that programme; it should be explicit in an
implementation.

### 5.2 Input-oriented RDM

The source obtains an input orientation by setting the output-direction
components to zero:

```math
\begin{aligned}
\max_{\beta_o,\lambda}\quad & \beta_o \\
\text{s.t.}\quad
& \sum_j\lambda_j y_{rj}\ge y_{ro},
  && r=1,\ldots,s,\\
& \sum_j\lambda_j x_{ij}
  \le x_{io}-\beta_o R^x_{io},
  && i=1,\ldots,m,\\
& \sum_j\lambda_j=1,\quad
  \lambda_j\ge0,\quad\beta_o\ge0.
\end{aligned}
```

It measures the common share of the focal unit's remaining observed input
saving opportunities that can be achieved without reducing any output.

### 5.3 Output-oriented RDM

The source obtains an output orientation by setting the input-direction
components to zero:

```math
\begin{aligned}
\max_{\beta_o,\lambda}\quad & \beta_o \\
\text{s.t.}\quad
& \sum_j\lambda_j y_{rj}
  \ge y_{ro}+\beta_o R^y_{ro},
  && r=1,\ldots,s,\\
& \sum_j\lambda_j x_{ij}\le x_{io},
  && i=1,\ldots,m,\\
& \sum_j\lambda_j=1,\quad
  \lambda_j\ge0,\quad\beta_o\ge0.
\end{aligned}
```

It measures the common share of the focal unit's remaining observed output
growth opportunities that can be achieved without increasing any input.

For every orientation, "active direction" means only the range components
used by that programme. A positive output range does not bound an
input-oriented programme, and a positive input range does not bound an
output-oriented programme.

## 6. Score, targets, and slacks

The native optimum `beta_o^*` is an inefficiency measure: larger values mean
that a larger share of the observed improvement opportunities remains
realizable.

The source's reported efficiency is

```math
E_o^{\mathrm{RDM}}=1-\beta_o^*,
```

so higher is better.

Under the exact source contract - self-inclusion, VRS, the same `J` for
extrema and technology, and at least one positive active range -

```math
0\le\beta_o^*\le1
\qquad\text{and}\qquad
0\le E_o^{\mathrm{RDM}}\le1.
```

The lower bound follows because the focal observation makes `beta_o=0`
feasible. For any active input with positive range, a VRS convex combination
cannot use less than `x_i^min`, which implies `beta_o<=1`. The analogous
argument uses `y_r^max` for any active output with positive range.

The stage-one directional target is

```math
\widehat x_{io}=x_{io}-\beta_o^*R^x_{io},
\qquad
\widehat y_{ro}=y_{ro}+\beta_o^*R^y_{ro},
```

with the inactive side unchanged in an oriented model. A solver witness also
defines the peer activity

```math
x^\lambda_i=\sum_j\lambda_j^*x_{ij},
\qquad
y^\lambda_r=\sum_j\lambda_j^*y_{rj}.
```

The residual slacks are

```math
s^-_i=\widehat x_{io}-x^\lambda_i\ge0,
\qquad
s^+_r=y^\lambda_r-\widehat y_{ro}\ge0.
```

At least one positive-range directional constraint binds when the programme
is well posed, but other slacks can remain. Accordingly:

- `E=1` is necessary but not sufficient for Pareto efficiency;
- the basic score does not include every slack source of inefficiency; and
- a stage-one RDM target must not be advertised as Pareto efficient.

The paper discusses separate second-stage routes to Pareto-efficient targets.
Those routes are optional post-processing estimators and are not silently
part of equation (3). The paper's normalized ratio-of-norms calculation is
also not the basic RDM score.

`beta_o^*` is unique as the optimal scalar value, but optimal intensities and
peer targets can be non-unique. The source does not freeze a lexicographic
tie-break rule. An eventual implementation must distinguish the invariant
score from a solver witness and must not promise identical lambdas across
solvers.

## 7. Translation and unit properties

### 7.1 Translation invariance under VRS

Add a finite constant `v_i` to input `i` for every DMU and a finite constant
`k_r` to output `r` for every DMU. The extrema shift by the same constants,
so both range directions remain unchanged. In the envelopment constraints,

```math
\sum_j\lambda_j(x_{ij}+v_i)
=\sum_j\lambda_jx_{ij}+v_i\sum_j\lambda_j
=\sum_j\lambda_jx_{ij}+v_i,
```

and similarly for outputs. The constants cancel because
`sum_j lambda_j=1`. Thus `beta` and `E` are unchanged and targets shift by
the declared constants.

The source is explicit that this result is VRS-specific. A CRS programme
lacks the convexity identity and is not the source-qualified,
translation-invariant RDM leaf.

Translation invariance is a mathematical score property under common
coordinate shifts. It does not license changing an account's economic
meaning, shifting only selected DMUs, or applying different constants to the
extrema and the technology.

### 7.2 Positive-units invariance

If input `i` is multiplied for every DMU by `a_i>0` and output `r` by
`c_r>0`, their range components and target adjustments scale by the same
factors. Dividing each transformed constraint by its positive scale recovers
the original programme. `beta`, `E`, and the lambdas are therefore
unchanged, while level targets scale in their own units.

Zero or negative multipliers are not changes of measurement units and are
outside this property.

## 8. Zero ranges and failure domains

A zero range is meaningful: the focal unit already has the lowest observed
input or highest observed output in that coordinate. Its directional target
for that coordinate equals the observed level. The associated envelopment
inequality may still contain peer slack; "unchanged directional target" must
not be converted into a claim that every peer coordinate is equal.

There is a critical distinction:

- **some active ranges are zero, at least one is positive:** the model is
  bounded under the source contract and the zero components remain
  unchanged in the directional target;
- **all active ranges are zero:** `beta` occurs in no effective constraint,
  so the maximization programme is unbounded.

The second case is an algebraic edge case left implicit by the paper's
coordinatewise discussion. An implementation must fail closed with a
specific `zero_active_direction` or `unbounded_direction` diagnostic. It
must not impose an undocumented `beta<=1`, choose `beta=0`, or report
efficiency one merely to make the LP return a number.

The source-qualified leaf must also fail closed for:

1. empty data, missing dimensions, or non-finite observations;
2. a focal unit outside the exact comparison population;
3. extrema calculated from a set different from the technology set;
4. signed variables whose input/output preference is not economically
   declared;
5. undesirable outputs passed as ordinary desirable outputs;
6. CRS or another returns-to-scale rule presented as the 2004
   translation-invariant estimator;
7. solver infeasibility, unboundedness, limits, or numerical failure; and
8. any requested ratio interpretation whose binding range is zero.

Scores should be computed directly as `1 - beta`, not by dividing two nearly
zero coordinate gaps.

## 9. Non-equivalence boundary

RDM belongs in a unified directional-distance compiler, but it is a
source-qualified direction policy rather than an alias for every model that
can share that compiler.

- **Generic DDF:** a generic DDF accepts an externally chosen direction. RDM
  constructs a different focal- and sample-dependent direction from equation
  (2), fixes VRS, and reports `1 - beta`. Compiler reuse is valid; semantic
  aliasing is not.
- **Ordinary radial BCC after translating data:** the arbitrary translation
  changes radial ratios and can change targets after translating them back.
  The paper's illustration obtains different BCC targets after shifts of 5
  and 10, whereas RDM cancels common translations inside the VRS programme.
- **Range-adjusted measure (RAM):** sharing the word "range" and some
  invariance properties is not equivalence. RAM uses an additive,
  normalized-slack loss; RDM uses one common directional factor and
  focal-to-ideal gaps. RAM requires its own source protocol.
- **Semi-oriented radial measure (SORM):** this is a later signed-data
  estimator with a different defining source and score construction. It must
  not be exposed as an RDM option before a separate source freeze.
- **Inverse RDM (IRDM):** equation (4) replaces the ranges by inverse ranges.
  The paper treats it as a target-setting device, requires normalization for
  units invariance, and warns that its unit-specific implicit ideals make its
  scores unsuitable for ranking. It is not an orientation of RDM and is not
  passed by this protocol.
- **Data preprocessing by translation:** RDM invariance is a property of the
  complete VRS estimator, not an instruction to preprocess signed data and
  run an unrelated radial model.
- **Undesirable-output DDF:** a negative numerical value and a bad-output
  economic role are different concepts. RDM equation (3) expands every
  output; it does not encode contraction or weak disposability of pollution.

## 10. Executable exact oracle

The following synthetic fixture is deliberately small, signed, and rational.
It is not claimed to be the confidential bank data.

| DMU | input `x` | desirable output `y` |
|---|---:|---:|
| A | -2 | 2 |
| B | 2 | 6 |
| C | 2 | -2 |

Evaluate `C` against the self-inclusive VRS set `{A,B,C}`.

### 10.1 Non-oriented result

The ideal values and ranges are

```math
x^{\min}=-2,\quad y^{\max}=6,\quad
R^x_C=4,\quad R^y_C=8.
```

The exact optimum is

```math
\beta_C^*=\frac23,\qquad
E_C^{\mathrm{RDM}}=\frac13,
```

with one exact witness

```math
\lambda_A=\frac23,\qquad
\lambda_B=\frac13,\qquad
\lambda_C=0.
```

Both the directional target and peer activity equal

```math
\widehat x_C=x^\lambda=-\frac23,\qquad
\widehat y_C=y^\lambda=\frac{10}{3},
```

and both residual slacks are zero.

This is not merely a candidate solution. Let
`a=lambda_A`, `b=lambda_B`, and `c=lambda_C`. Convexity gives
`b=1-a-c`. The input constraint implies

```math
2-4a\le2-4\beta
\quad\Longrightarrow\quad
a\ge\beta.
```

The peer output is `6 - 4a - 8c`. Feasibility therefore requires

```math
-2+8\beta
\le6-4a-8c
\le6-4\beta,
```

so `beta<=2/3`. The displayed witness attains the bound and proves the
oracle exactly.

### 10.2 Orientation checks

On the same fixture:

- input-oriented RDM for `C` has `beta=1`, `E=0`, with `A` as a witness;
- output-oriented RDM for `C` has `beta=1`, `E=0`, with `B` as a witness.

These checks ensure that orientation is implemented by zeroing the inactive
side of the direction, not by changing signs or applying a radial ratio to
negative observations.

### 10.3 Metamorphic checks

An implementation must preserve the exact non-oriented result after:

- adding 10 to every input and subtracting 7 from every output; and
- multiplying every input by 3 and every output by 2.

The transformed level targets must shift or scale accordingly.

A separate one-DMU fixture has all active ranges equal to zero. Its LP is
unbounded in `beta` and must return the explicit failure described in
Section 8, not `E=1`.

### 10.4 Primary-source numerical corroboration

The paper's two-output illustration reports:

```text
observed U3       = (-4, 2)
coordinate ideal = ( 5, 6)
RDM target        = (1.07273, 4.25455)
```

Both coordinates give the same reported efficiency, subject to rounding:

```math
\frac{5-1.07273}{5-(-4)}
\approx
\frac{6-4.25455}{6-2}
\approx0.43636.
```

This corroborates the frozen `1 - beta` interpretation. Because the full
illustrative reference table is embedded in figures rather than supplied as
a machine-readable table, this rounded published result is a transcription
check; the rational fixture above is the executable solver oracle.

## 11. Release record and continuing boundary

The released implementation satisfies the gate because it:

1. compiles the three programmes in Section 5 exactly under VRS;
2. constructs directions per focal DMU from the exact reference population;
3. exposes native `beta` and higher-is-better `1 - beta` without ambiguity;
4. separates directional targets, peer activities, and residual slacks;
5. handles alternative peer optima honestly;
6. reproduces every exact and metamorphic check in Section 10;
7. fails explicitly for an all-zero active direction; and
8. proves non-equivalence at the public API and registry level.

The executable checks live in `tests/test_range_directional.py`. They include
the exact rational oracle, an independently compiled SciPy formulation for
all three orientations, common-translation and positive-unit transformations,
large-unit numerical scaling, reference-set preflight, solver failures, and
score-domain certification. The repeatable performance fixture lives in
`benchmarks/benchmark_range_directional.py`.

The public book and documentation use the synthetic
`range_directional_signed` dataset. The source bank-branch observations remain
confidential, so this release does not claim to reproduce the published
empirical application.

IRDM, RAM, SORM, undesirable-output models, Pareto-target second stages, CRS
variants, and productivity indexes remain outside this release. Each requires
its own evidence gate; if its defining literature or validation evidence
cannot be obtained, it is deferred to a later version rather than inferred.
