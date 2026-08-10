# Tone (2002) super-SBM: independent analytical oracle

**Method ID:** `evaluation.super.sbm.tone_2002`
**Validation kind:** `analytically_derived`
**Published reproduction:** no
**Production compiler reused:** no

This certificate is deliberately narrower than the complete public method.
It validates the VRS, non-oriented, strictly positive, desirable-output-only
score and replacement-target account. It does not redistribute or claim to
reproduce a numerical table from Tone (2002).

## Source programme and independent transformation

For focal row $o$, the leave-one-out VRS programme chooses peer intensities
$\lambda$, an input replacement plan $\bar x$, and an output replacement plan
$\bar y$. Its fractional objective is

$$
\rho_o
=
\frac{m^{-1}\sum_i \bar x_i/x_{io}}
     {s^{-1}\sum_r \bar y_r/y_{ro}},
$$

subject to

$$
X_{-o}\lambda\leq\bar x,
\qquad
Y_{-o}\lambda\geq\bar y,
\qquad
\bar x\geq x_o,
\qquad
\bar y\leq y_o,
\qquad
\mathbf 1^{\mathsf T}\lambda=1,
\qquad
\lambda\geq0.
$$

The independent test compiler sets
$t=(s^{-1}\sum_r\bar y_r/y_{ro})^{-1}$ and introduces
$(\Lambda,U,V)=(t\lambda,t\bar x,t\bar y)$. It minimizes
$m^{-1}\sum_iU_i/x_{io}$ under the dense linear constraints

$$
X_{-o}\Lambda\leq U,
\quad
Y_{-o}\Lambda\geq V,
\quad
U\geq tx_o,
\quad
V\leq ty_o,
\quad
\frac1s\sum_r\frac{V_r}{y_{ro}}=1,
\quad
\mathbf1^{\mathsf T}\Lambda=t.
$$

`tests/test_tone_super_sbm_independent_oracle.py` builds these dense arrays
directly and calls SciPy/HiGHS. It imports no DEAPack private helper, compiler,
linear-program object, or solver wrapper.

## Exact two-unit certificate

The analytical fixture is

| DMU | resource | service |
|---|---:|---:|
| A | 1 | 1 |
| B | 2 | 3 |

Both rows are strongly SBM-efficient under VRS: A has the smaller resource
bundle and B has the larger service bundle. After row-level self-exclusion,
the only remaining peer has intensity one. Therefore the optimal replacement
plan is componentwise $\bar x=\max(x_o,x_{-o})$ and
$\bar y=\min(y_o,y_{-o})$. This gives

| focal DMU | input target | output target | exact score |
|---|---:|---:|---:|
| A | 2 | 1 | 2 |
| B | 2 | 1 | 3 |

The feasible plan attains each value. The lower bound follows because every
feasible plan must keep the sole peer, satisfy the input floor, and satisfy
the output ceiling. The values are therefore exact optima, not frozen output
copied from the production implementation.

## Multivariate dense cross-check

The second fixture has three rows, two inputs, and two desirable outputs. All
three rows pass the ordinary strong-efficiency screen. The independent dense
compiler obtains:

| focal DMU | input target | output target | exact score |
|---|---|---|---:|
| A | (2, 4) | (1, 2) | 1.8 |
| B | (2.5, 2.5) | (2, 2) | 1.25 |
| C | (4, 2) | (2, 1) | 1.8 |

The public API is compared with these independently optimized scores,
replacement targets, and peer intensities for every fixture row.

## Claim boundary

This evidence certifies only the VRS non-oriented score and its
solver-selected source replacement account on the named positive fixtures.
It does not certify CRS, input- or output-oriented programmes, zero or signed
data, undesirable outputs, alternate optima in general, statistical outlier
claims, or a published numerical reproduction.
