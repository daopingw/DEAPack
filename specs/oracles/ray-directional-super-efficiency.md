# Ray (2008) directional super-efficiency: independent analytical oracle

**Method ID:** `evaluation.super.directional.ray_2008`
**Validation kind:** `analytically_derived`
**Published reproduction:** no
**Production compiler reused:** no

The defining equation and interpretation boundary remain source-qualified in
`specs/source_protocols/ray_2008_directional_super_efficiency.md`. This
certificate uses exact synthetic cases rather than redistributing a published
table.

## Programme checked

For focal row $o$, the test uses variables $z=[\lambda_{-o},\beta]$ and the
source-shaped constraints

$$
\begin{bmatrix}
-Y_{-o}^{\mathsf T} & y_o\\
 X_{-o}^{\mathsf T} & x_o
\end{bmatrix}z
\leq
\begin{bmatrix}-y_o\\x_o\end{bmatrix},
\qquad
\begin{bmatrix}\mathbf1^{\mathsf T}&0\end{bmatrix}z=1,
$$

with $\lambda\geq0$ and unrestricted $\beta$. The source boundary and display
score are

$$
x_o^D=(1-\beta_o)x_o,
\qquad
y_o^D=(1+\beta_o)y_o,
\qquad
NL_o=1-\beta_o.
$$

`tests/test_ray_directional_super_independent_oracle.py` writes the dense
objective, inequality rows, convexity equation, self-exclusion bound, and
variable bounds directly with NumPy before calling SciPy/HiGHS. It imports no
DEAPack private helper, compiler, linear-program object, or solver wrapper.

## Exact two-unit certificate

For a VRS reference population containing only the other row, convexity fixes
$\lambda=1$. Every input coordinate implies
$\beta\leq1-x_{i,-o}/x_{io}$ and every output coordinate implies
$\beta\leq y_{r,-o}/y_{ro}-1$. The minimum of those upper bounds is feasible
and therefore is the exact optimum.

The analytical fixture is

| DMU | resource | service |
|---|---:|---:|
| A | 1 | 2 |
| B | 2 | 3 |

It gives:

| focal DMU | exact $\beta$ | exact $NL$ | input boundary | output boundary |
|---|---:|---:|---:|---:|
| A | -1 | 2 | 2 | 0 |
| B | -1/3 | 4/3 | 8/3 | 2 |

The test checks the public scalar and both target coordinates against these
closed-form values.

## Multivariate dense cross-check

An independent three-row, two-input, two-output compiler produces:

| focal DMU | exact $\beta$ | exact $NL$ | input boundary | output boundary |
|---|---:|---:|---|---|
| A | -1 | 2 | (2, 8) | (0, 0) |
| B | -1/4 | 5/4 | (2.5, 2.5) | (2.25, 2.25) |
| C | -1 | 2 | (8, 2) | (0, 0) |

The public API is compared with every independently optimized beta, score,
directional boundary, peer activity, and intensity. The small fixture makes
the attaining peer mixtures unique, so this check does not imply peer-plan
uniqueness for arbitrary data.

## Claim boundary

| Claim | Evidence | Certified scope |
|---|---|---|
| exact scalar and target boundary | two-unit primal upper bound and attaining plan | observed direction, VRS, leave-one-row-out |
| programme transcription | independent dense compiler | three-row, two-input, two-output fixture |
| native score and sign | exact scalar identity | `beta` and `NL=1-beta` |
| peer activity | independently reconstructed fixture accounts | no general peer-plan uniqueness claim |

The certificate does not cover published numerical reproduction, arbitrary
directions, other returns to scale, zero-input repairs, undesirable outputs,
general peer-plan uniqueness, networks, panels, productivity, prices,
uncertainty, or statistical outlier claims.
