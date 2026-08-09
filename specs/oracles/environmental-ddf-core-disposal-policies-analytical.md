# Environmental DDF core disposal policies: analytical oracle

**Method IDs:** `environmental.ddf.joint_production` (strong-disposal path)
and `environmental.ddf.weak_disposal.common_factor`  
**Validation kind:** `analytically_derived` with independent problem
compilation  
**Published reproduction:** no

This certificate checks two existing public environmental directional-distance
paths without creating another model identity. The quantities and exact values
below are synthetic consequences of the declared programmes; they are not
transcribed from a published application. The deprecated generic
`disposability="weak"` selector is expressly outside the certificate.

## Frozen primary programmes

For a nonnegative direction $(g^x,g^y,g^b)$, both paths maximize $\beta$ under

$$
X\lambda+\beta g^x\leq x_o,
\qquad
Y\lambda-\beta g^y\geq y_o,
\qquad
\lambda,\beta\geq0.
$$

The strong-disposal path adds

$$
B\lambda+\beta g^b\leq b_o,
$$

and permits CRS, VRS, NIRS, or NDRS intensity restrictions. The named
common-factor path instead adds

$$
B\lambda+\beta g^b=b_o
$$

under CRS. The latter equality is certified only as part of the named CRS
technology, not as the deprecated equality-only compatibility path under an
arbitrary scale assumption.

## Exact three-organization account

The primary fixture has one strictly positive resource, service, and residual:

| Organization | Resource $x$ | Service $y$ | Residual $b$ |
|---|---:|---:|---:|
| A | 3 | 4 | 2 |
| B | 5 | 2 | 3 |
| C | 5 | 6 | 4 |

Every organization is assessed against the pooled reference with
$(g^x,g^y,g^b)=(1,1,1)$. This is deliberately not the CFG output preset:
resources contract, and the service and residual directions are fixed at one
rather than copied from each assessed observation.

The exact strong-disposal distances and one attaining reference plan are:

| RTS | $\beta_A$; attaining $\lambda$ | $\beta_B$; attaining $\lambda$ | $\beta_C$; attaining $\lambda$ |
|---|---|---|---|
| CRS | $0$; $(1,0,0)$ | $4/3$; $(5/6,0,0)$ | $2/7$; $(11/7,0,0)$ |
| VRS | $0$; $(1,0,0)$ | $1$; $(1,0,0)$ | $0$; $(0,0,1)$ |
| NIRS | $0$; $(1,0,0)$ | $4/3$; $(5/6,0,0)$ | $0$; $(0,0,1)$ |
| NDRS | $0$; $(1,0,0)$ | $1$; $(1,0,0)$ | $2/7$; $(11/7,0,0)$ |

For the CRS common-factor equality, the exact distance vector is

$$
(\beta_A,\beta_B,\beta_C)=\left(0,\frac43,0\right),
$$

attained respectively by $(1,0,0)$, $(5/6,0,0)$, and $(0,0,1)$.

These are optima, not only feasible lower bounds. For the equivalent
minimization of $-\beta$, let inequality marginals follow SciPy's
$A_{ub}z\leq b_{ub}$ convention and hence be nonpositive. The following exact
row multipliers give the displayed dual objectives; the omitted lower-bound
marginals are the nonnegative reduced-cost residuals. Direct substitution
gives zero stationarity residual for $\beta$ and equality of each primal and
dual objective.

| Policy and case | Inequality marginals | Equality marginal | Dual objective |
|---|---|---|---:|
| strong CRS A | $(-4/7,-3/7,0)$ | -- | $0$ |
| strong CRS B | $(0,-1/3,-2/3)$ | -- | $-4/3$ |
| strong CRS C | $(-4/7,-3/7,0)$ | -- | $-2/7$ |
| strong VRS A | $(0,-1/3,-2/3)$ | $0$ | $0$ |
| strong VRS B | $(0,0,-1)$ | $2$ | $-1$ |
| strong VRS C | $(0,-1/2,-1/2)$ | $-1$ | $0$ |
| strong NIRS A, B | $(0,-1/3,-2/3,0)$ | -- | $0,-4/3$ |
| strong NIRS C | $(0,-1/2,-1/2,-1)$ | -- | $0$ |
| strong NDRS A | $(0,-1/3,-2/3,0)$ | -- | $0$ |
| strong NDRS B | $(0,0,-1,-2)$ | -- | $-1$ |
| strong NDRS C | $(-4/7,-3/7,0,0)$ | -- | $-2/7$ |
| common-factor CRS A | $(-4/7,-3/7)$ | $0$ | $0$ |
| common-factor CRS B | $(0,-1/3)$ | $-2/3$ | $-4/3$ |
| common-factor CRS C | $(-1,-1/2)$ | $1/2$ | $0$ |

The strong inequality rows are ordered input, desirable output, bad output,
and then the scale row where present. The common-factor inequality rows are
input and desirable output; its equality marginal belongs to the bad-output
row. The VRS equality marginal belongs to convexity. For NDRS the scale row is
$-\mathbf 1^\mathsf T\lambda\leq-1$.

## Exact strong-disposal slack completion

A separate two-organization fixture isolates the second-phase bad-output
account:

| Organization | Resource $x$ | Service $y$ | Residual $b$ |
|---|---:|---:|---:|
| Clean | 1 | 1 | 1 |
| Dirty | 1 | 1 | 2 |

Under VRS, strong disposal, and direction $(0,1,0)$, Dirty has primary
distance $\beta=0$. Once that value is fixed, row scales are $(1,1,2)$. The
scaled phase-two equations imply

$$
\lambda_C+\lambda_D=1,
\qquad
s_x=s_y=0,
\qquad
\frac{\lambda_C+2\lambda_D}{2}+\bar s_b=1.
$$

Thus $\bar s_b=\lambda_C/2\leq1/2$. The upper bound is attained uniquely at
$(\lambda_C,\lambda_D)=(1,0)$, so the physical bad-output slack is
$s_b=2\bar s_b=1$. The represented residual and reported target reconcile:

$$
B\lambda=1
=b_o-\beta g^b-s_b
=2-0-1.
$$

The exact phase-two vector in variable order
$(\lambda_C,\lambda_D,\bar s_x,\bar s_y,\bar s_b)$ is therefore
$(1,0,0,0,1/2)$.

## Independent executable check

`tests/test_environmental_ddf_core_policies_independent_oracle.py` builds
ordinary dense NumPy arrays directly from the equations above and calls
`scipy.optimize.linprog`. It does not call the production environmental
compiler, reference compiler, RTS helpers, row-scale helper, or private
problem builders. The tests compare every fixture observation with the
public APIs, cover all four strong-disposal RTS branches, and independently
assemble the exact strong-disposal phase-two programme.

The independent compiler and DEAPack's default backend both use SciPy/HiGHS.
This is therefore independent problem compilation and exact analytical
checking, not an independent-solver reproduction.

## Claim boundary

| Claim | Evidence | Scope |
|---|---|---|
| generic strong-disposal primary distance | exact primal plans, exact dual upper bounds, and independently compiled dense LPs | one positive three-organization fixture, global self-inclusive reference, direction $(1,1,1)$, CRS/VRS/NIRS/NDRS, nonnegative distances |
| generic common-factor primary distance beyond the CFG preset | exact primal plans, exact dual upper bounds, and independently compiled dense LPs | the same fixture and reference, CRS equality technology, direction $(1,1,1)$ |
| strong-disposal bad-output slack and target | exact scalar upper bound and independently compiled row-scaled phase two | one positive two-organization VRS fixture, direction $(0,1,0)$, Dirty only |

This certificate does **not** establish a published-data or published-table
reproduction. It does not certify the deprecated generic weak selector,
activity-specific or generalized weak disposal, arbitrary directions,
external or temporal references, negative distances, multidimensional or
zero-valued accounts, unique peers outside the exact phase-two case,
statistical inference, causal or cost interpretations, or any environmental
productivity operator.
