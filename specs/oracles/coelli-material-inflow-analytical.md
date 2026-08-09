# Coelli material-inflow efficiency: independent analytical oracle

**Method ID:** `environmental.material_inflow.coelli2007`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no  
**Production compiler reused:** no

This certificate validates the claim-scoped Coelli--Lauwers--Van
Huylenbroeck material-inflow account under CRS and VRS. It derives exact
$TE$, $EE$, physical-content $EAE$, material targets, and surplus accounts
from small synthetic technologies, then cross-checks them with a separately
compiled dense version of source equations (23)--(26). It does not reproduce
the source's 183-farm application because the unit-level observations are not
supplied.

## Source boundary

[Coelli, Lauwers, and Van Huylenbroeck
(2007)](https://doi.org/10.1007/s11123-007-0052-8) define environmental
efficiency through the minimum material entering with inputs while observed
desirable output is preserved. The complete equation audit uses the
[authors' CEPA Working Paper
06/2005](https://economics.uq.edu.au/files/5310/WP062005.pdf):

- equation (2): $z=a'x-b'y$;
- equation (23): input-radial technical efficiency;
- equation (24): minimum material inflow with explicit $x_o^e$;
- equations (25)--(26): $EE=a'x_o^e/a'x_o$ and $EAE=EE/TE$;
- footnote 6: the displayed programmes are CRS, and VRS adds
  $\mathbf 1'\lambda=1$ to both.

The certified package domain is a self-inclusive nonnegative cross-section,
one known common nonnegative material-content vector, positive observed
material inflow, fixed desirable output, and CRS or VRS. Prices, observed bad
outputs, explicit treatment, and causal or welfare claims are not part of
the account.

## Exact CRS fixture

Let $a=(1,3)$ and let one unit of desirable output retain two units of the
material:

| DMU | $x_1$ | $x_2$ | $y$ | observed inflow | observed surplus |
|---|---:|---:|---:|---:|---:|
| A | 1 | 3 | 1 | 10 | 8 |
| B | 3 | 1 | 1 | 6 | 4 |
| C | 8 | 8 | 2 | 32 | 28 |

For A and B, no proportional contraction can preserve their output, so
$TE_A=TE_B=1$. For C, the activity $\lambda_A=\lambda_B=1$ supplies output
2 with inputs $(4,4)=\tfrac12(8,8)$, hence $TE_C\le1/2$. Every CRS reference
activity satisfies

$$
x_1+x_2\ge4y.
$$

Therefore any plan supplying $y_C=2$ requires
$x_1+x_2\ge8$. A radial contraction of C has
$x_1+x_2=16\theta$, so $\theta\ge1/2$ and $TE_C=1/2$.

For material inflow, every observed activity satisfies

$$
x_1+3x_2\ge6y,
$$

and B attains equality. A plan preserving output $y_o$ therefore has minimum
inflow $6y_o$, attained with $\lambda_B=y_o$. This gives:

| DMU | $TE$ | minimum inflow | $EE$ | $EAE$ | material target | minimum surplus |
|---|---:|---:|---:|---:|---:|---:|
| A | $1$ | $6$ | $3/5$ | $3/5$ | $(3,1)$ | $4$ |
| B | $1$ | $6$ | $1$ | $1$ | $(3,1)$ | $4$ |
| C | $1/2$ | $12$ | $3/8$ | $3/4$ | $(6,2)$ | $8$ |

The exact decomposition for C is

$$
\frac{3}{8}=\frac12\times\frac34.
$$

Its technical radial target is $(4,4)$, while its minimum-material target is
$(6,2)$. The difference separates common resource saving from changing the
input mix.

## Exact VRS fixture

For the book case, all four plans produce $y=1$, $a=(1,3)$, and the output
retains one unit:

| DMU | $x_1$ | $x_2$ | inflow |
|---|---:|---:|---:|
| A | 1 | 3 | 10 |
| B | 3 | 1 | 6 |
| C | 2 | 2 | 8 |
| D | 4 | 4 | 16 |

A, B, and C form the VRS fixed-output frontier
$x_1+x_2=4$. Thus $TE_C=1$ and $TE_D=1/2$. Along that frontier,
$x_1+3x_2$ is minimized at B, so the minimum inflow for every observation is
6. Consequently,

$$
EE_C=EAE_C=\frac34,
$$

and

$$
EE_D=\frac38,\qquad
TE_D=\frac12,\qquad
EAE_D=\frac34.
$$

D's radial technical target is $(2,2)$ and its minimum-material target is
$(3,1)$. The two targets answer different management questions and neither
is a least-cost recommendation.

## Independent executable compiler

`tests/test_material_balance_independent_oracle.py` builds dense NumPy
matrices and calls `scipy.optimize.linprog` directly. It imports no DEAPack
reference compiler, RTS matrix builder, material problem builder, or
production solver wrapper.

Most importantly, the independent compiler preserves source equation (24)
with separate decision variables $(\lambda,x_o^e)$:

$$
\min a'x_o^e
\quad\text{s.t.}\quad
Y\lambda\ge y_o,\quad
X\lambda\le x_o^e,\quad
\lambda\ge0.
$$

Production code instead eliminates $x_o^e$ and minimizes
$a'X\lambda$. Agreement therefore checks the package's algebraic reduction
instead of repeating it. The same dense compiler adds
$\mathbf 1'\lambda=1$ only for the VRS cases.

The executable checks:

1. every CRS and VRS observation's independently compiled $TE$, minimum
   inflow, $EE$, $EAE$, and multiplicative identity against the public API;
2. all exact CRS scores, physical surpluses, radial/material targets, and
   stated peer intensities;
3. the VRS book case's distinct technical and material-mix targets;
4. coherent rescaling of one input and the desirable output together with
   reciprocal coefficient changes, including transformed targets; and
5. a zero-content-input case in which distinct plans have the same material
   objective, showing why the package cannot claim target uniqueness or
   generic Pareto--Koopmans efficiency.

Both paths use SciPy/HiGHS as the numerical optimizer, so this is independent
problem compilation and exact analytical validation, not an
independent-solver reproduction.

## Claim boundary

| Claim | Evidence | Certified scope |
|---|---|---|
| source programme transcription | equations (23)--(26), exact bounds, attaining plans, and independent dense LPs | one common nonnegative material vector; fixed output; self-inclusive cross-section; CRS and VRS |
| decomposition | exact $TE$, $EE$, $EAE$, and zero reconstruction residual | physical-content $EAE=EE/TE$; no price or valuation input |
| targets and peers | exact CRS peer portfolios and CRS/VRS input targets | one solver-selected optimum; uniqueness, closeness, least cost, and prescription not claimed |
| physical account | exact observed/minimum inflow and surplus | declared material boundary and known input/output contents |
| unit invariance | co-transformed quantities, coefficients, and targets | positive coherent changes of the exact fixture's input/output units |
| nonuniqueness boundary | two distinct feasible plans with identical material objective | zero-content inputs; native material efficiency only |

This certificate does **not** extend to:

- NIRS or NDRS;
- panel, window, leave-one-out, custom, or external-reference source
  equivalence;
- heterogeneous or estimated material coefficients;
- weighted multiple-material aggregation, although source equations
  (18)--(21) describe that extension;
- observed bad outputs, explicit treatment, inventory change, unmeasured
  loss, or stock pollution;
- unique, closest, least-cost, profit-maximizing, or Pareto--Koopmans
  targets;
- causal effects, realized emissions, environmental damage, welfare,
  compliance, or policy valuation; or
- farm-level or published-table reproduction of the Belgian application.

Those distinct claims remain `deferred_to_next_version` until their own
source and independent-oracle contracts close.
