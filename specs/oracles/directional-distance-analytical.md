# Directional distance DEA: independent analytical oracle

**Method ID:** `static.directional_distance`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This record validates a bounded part of DEAPack's desirable-output
directional distance function with an exact fixture derived independently of
the production compiler. It is not a transcription of a published numerical
table and makes no published-reproduction claim.

## Estimand and fixture

For organization $o$, DEAPack's native directional score is

$$
\beta_o=\max_{\beta,\lambda}\{\beta:
X\lambda\leq x_o-\beta g_o^x,\quad
Y\lambda\geq y_o+\beta g_o^y,\quad
\lambda\text{ satisfies the declared RTS restriction}\}.
$$

The direction describes the operating improvement programme: $g_o^x$
specifies the input reductions associated with one unit of $\beta$, while
$g_o^y$ specifies the desirable-output increases. The certificate uses one
input and one desirable output:

| Organization | Input $x$ | Desirable output $y$ |
|---|---:|---:|
| A | $1$ | $1$ |
| B | $2$ | $1$ |
| C | $1$ | $1/2$ |

All three observations belong to the reference set. The data are
cross-sectional and nonnegative, and the default `auto` reference request
resolves to the self-inclusive `global` reference.

Every observed activity satisfies $y_j\leq x_j$. Therefore every feasible
conical or convex reference activity satisfies

$$
Y\lambda\leq X\lambda.
$$

This simple production inequality, together with the relevant scale
restriction, supplies analytical bounds on every optimum below. The displayed
intensities supply matching feasible plans.

## Exact phase-one scores

### Joint proportional input saving and output expansion

Set $g_o^x=x_o$ and $g_o^y=y_o$. Feasibility requires

$$
y_o(1+\beta)\leq Y\lambda
\leq X\lambda\leq x_o(1-\beta),
$$

so

$$
\beta\leq\frac{x_o-y_o}{x_o+y_o}.
$$

Under CRS, placing
$\lambda_A=2x_oy_o/(x_o+y_o)$ on A attains the bound. VRS imposes
$\sum_j\lambda_j=1$; NIRS imposes
$\sum_j\lambda_j\leq1$; and NDRS imposes
$\sum_j\lambda_j\geq1$. Because every reference output is at most one,
NIRS adds $y_o(1+\beta)\leq1$. Because every reference input is at least
one, NDRS adds $x_o(1-\beta)\geq1$. VRS imposes both bounds.

| RTS | A | B | C | Attaining reference intensity |
|---|---:|---:|---:|---|
| CRS | $0$ | $1/3$ | $1/3$ | $\lambda_A=(1,4/3,2/3)$ |
| VRS | $0$ | $0$ | $0$ | $\lambda_A=1$ for each organization |
| NIRS | $0$ | $0$ | $1/3$ | A, B, and $\lambda_A=2/3$, respectively |
| NDRS | $0$ | $1/3$ | $0$ | A, $\lambda_A=4/3$, and A, respectively |

Here and in the two tables below, a named organization denotes unit intensity
on that observed activity.

### Proportional input saving only

Set $g_o^x=x_o$ and $g_o^y=0$. Then

$$
y_o\leq Y\lambda\leq X\lambda\leq x_o(1-\beta),
\qquad
\beta\leq1-\frac{y_o}{x_o}.
$$

Under CRS, $\lambda_A=y_o$ attains this bound. The lower-scale restriction
in VRS and NDRS additionally requires $X\lambda\geq1$, hence
$\beta\leq1-1/x_o$. NIRS does not tighten the CRS bound on this fixture.

| RTS | A | B | C | Attaining reference intensity |
|---|---:|---:|---:|---|
| CRS | $0$ | $1/2$ | $1/2$ | $\lambda_A=(1,1,1/2)$ |
| VRS | $0$ | $1/2$ | $0$ | $\lambda_A=1$ for each organization |
| NIRS | $0$ | $1/2$ | $1/2$ | $\lambda_A=(1,1,1/2)$ |
| NDRS | $0$ | $1/2$ | $0$ | $\lambda_A=1$ for each organization |

For this observed input-only direction, the associated Farrell input
contraction factor is

$$
\theta_o=1-\beta_o.
$$

This identity does not turn the generic DDF compatibility field into a
Farrell input score.

### Proportional desirable-output expansion only

Set $g_o^x=0$ and $g_o^y=y_o$. Then

$$
y_o(1+\beta)\leq Y\lambda\leq X\lambda\leq x_o,
\qquad
\beta\leq\frac{x_o}{y_o}-1.
$$

Under CRS, $\lambda_A=x_o$ attains the bound. VRS and NIRS also require
$\sum_j\lambda_j\leq1$. Since every reference output is at most one, this
adds $y_o(1+\beta)\leq1$. NDRS does not tighten the CRS bound on this
fixture.

| RTS | A | B | C | Attaining reference intensity |
|---|---:|---:|---:|---|
| CRS | $0$ | $1$ | $1$ | $\lambda_A=(1,2,1)$ |
| VRS | $0$ | $0$ | $1$ | $\lambda_A=1$ for each organization |
| NIRS | $0$ | $0$ | $1$ | $\lambda_A=1$ for each organization |
| NDRS | $0$ | $1$ | $1$ | $\lambda_A=(1,2,1)$ |

For this observed output-only direction, the associated Farrell output
expansion factor is

$$
\phi_o=1+\beta_o.
$$

## Compatibility transform

The package reports `score = distance = beta` as the native result. For
nonnegative $\beta$, its `efficiency` column is only the compatibility
transform

$$
\text{efficiency}_o=\frac{1}{1+\beta_o}.
$$

It is not an invariant economic efficiency measure across direction choices.
In particular, the pure observed input programme has
$\theta_o=1-\beta_o$, whereas the pure observed output programme has
$\phi_o=1+\beta_o$. The executable exact checks therefore validate both
the native distance and the package's stated compatibility transform without
conflating them.

## Exact observed-joint slack completion

Holding each observed-joint phase-one optimum fixed, the package maximizes
the sum of row-scaled slacks. For each quantity row, the positive scale is
the larger of the evaluated quantity's magnitude and the corresponding
reference-column maximum, with an all-zero row assigned scale one. The
reported slacks and targets remain in physical units. This completion rule
prevents a mere change from, for example, tonnes to kilograms from changing
the selected target.

The fixture gives the following exact second-stage results. A target is
written as (input, desirable output); slacks are written as (input slack,
output slack).

| RTS | Organization | $\beta$ | Target | Slacks | Directionally efficient? | Strongly efficient? |
|---|---|---:|---|---|---|---|
| CRS | A | $0$ | $(1,1)$ | $(0,0)$ | yes | yes |
| CRS | B | $1/3$ | $(4/3,4/3)$ | $(0,0)$ | no | no |
| CRS | C | $1/3$ | $(2/3,2/3)$ | $(0,0)$ | no | no |
| VRS | A | $0$ | $(1,1)$ | $(0,0)$ | yes | yes |
| VRS | B | $0$ | $(1,1)$ | $(1,0)$ | yes | no |
| VRS | C | $0$ | $(1,1)$ | $(0,1/2)$ | yes | no |
| NIRS | A | $0$ | $(1,1)$ | $(0,0)$ | yes | yes |
| NIRS | B | $0$ | $(1,1)$ | $(1,0)$ | yes | no |
| NIRS | C | $1/3$ | $(2/3,2/3)$ | $(0,0)$ | no | no |
| NDRS | A | $0$ | $(1,1)$ | $(0,0)$ | yes | yes |
| NDRS | B | $1/3$ | $(4/3,4/3)$ | $(0,0)$ | no | no |
| NDRS | C | $0$ | $(1,1)$ | $(0,1/2)$ | yes | no |

The positive-distance CRS targets, the NIRS target for C, and the NDRS
target for B all lie on $x=y$. If their fixed post-direction coordinates
are denoted by $(u,v)$, then $u=v$, and phase-two feasibility gives

$$
s^x+s^y
=(u-X\lambda)+(Y\lambda-v)
=-(X\lambda-Y\lambda)\leq0.
$$

Nonnegative slacks must therefore both be zero. A has the same conclusion
with $u=v=1$.

For B under VRS or NIRS, the fixed phase-one commitments are input two and
output one. Replacing B by A is permitted under either scale restriction and
produces the same output with input one, so input slack is one and output
slack is zero. More generally,

$$
(2-X\lambda)+(Y\lambda-1)
=1-(X\lambda-Y\lambda)\leq1,
$$

and A attains the bound.

For C under VRS or NDRS, the fixed input commitment is one. Every observed
input is at least one. VRS requires intensities to sum to one, while NDRS
requires their sum to be at least one; in either case feasibility forces
reference input to equal one and input slack to be zero. No permitted
reference at that input produces more than the sample maximum output one.
A attains that maximum, giving output slack $1-1/2=1/2$.

Consequently A alone is strongly efficient under every RTS assumption.
The full table validates exact phase-two slack, target, directional-status,
and strong-status semantics without asserting a unique peer basis.

## Executable checks

`tests/test_directional_independent_oracle.py` performs three distinct checks:

1. it compares the twelve exact score vectors above—three economically
   distinct observed-direction programmes under CRS, VRS, NIRS, and
   NDRS—with the public `DirectionalDistanceDEA` API;
2. it verifies the exact observed-joint completion table for A, B, and C
   under all four RTS assumptions; and
3. on a separate six-organization, two-input, two-output fixture, it
   hand-compiles dense phase-one and phase-two equations directly for four
   fixed direction profiles, all four RTS assumptions, and both score-only
   and slack-completion execution.

The independent dense compiler uses `scipy.optimize.linprog` with the
SciPy/HiGHS optimizer class, which is also the optimizer class used by the
package configuration under test. Its constraint matrices, objective vectors,
RTS rows, and target accounting are formulated separately from DEAPack's
sparse reference compiler and private DDF problem builders. It is therefore
an independent formulation cross-check, not an independent-solver
reproduction. The four fixed profiles are observed joint, observed
input-only, observed output-only, and one fixed global two-input/two-output
vector.

## Claim boundary

The evidence has deliberately limited reach:

| Claim | Exact or cross-check? | Parameter and result scope |
|---|---|---|
| phase-one optimum | exact feasible witness plus analytical bound | native $\beta$, compatibility transform, and directional-efficiency status for the three observed-direction programmes under CRS, VRS, NIRS, and NDRS |
| phase-two semantics | exact analytical cases | observed-joint A, B, and C under CRS, VRS, NIRS, and NDRS; physical component slacks, targets, and strong status (native score and directional status are covered by the phase-one claim) |
| dense two-phase compilation | separately hand-compiled numerical cross-check using the same SciPy/HiGHS optimizer class | four fixed direction profiles, four RTS assumptions, and score-only/slack-completion modes on one six-organization, two-input, two-output fixture; native score, compatibility transform, status, optimal row-scaled slack sum, maximum scaled slack, target accounting, and RTS intensity sums |

All certified runs are cross-sectional, nonnegative, desirable-output-only,
self-inclusive, and evaluated against the full eligible sample through
`auto`, resolved to `global`. They use
`allow_negative_distance=False`.

The certificate does **not** extend to:

- undesirable outputs or an environmental disposability technology;
- `allow_negative_distance=True` or any negative-distance result;
- external or custom reference populations, leave-one-out appraisal, or
  panel reference policies;
- direction resolver branches not exercised by the four fixed profiles,
  including mean, ones, scalar, mapping, and by-observation resolution;
- dual values, shadow prices, peer uniqueness, or component-level uniqueness
  under alternate optima outside the exact observed-joint completion table;
  or
- sampling inference, uncertainty quantification, productivity operators, or
  any other method that happens to use a directional-distance kernel.
