# Classic VRS additive DEA: independent analytical oracle

**Method ID:** `static.additive`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no  
**Production compiler reused:** no

This certificate validates the Charnes et al. (1985) direct VRS
unit-weight additive programme with one source-displayed example and one
independently derived discriminating fixture. Expected scores, slacks,
targets, and peers are obtained without DEAPack's production LP builder,
reference compiler, RTS helper, or solver wrapper.

The complete source boundary is frozen in
`specs/source_protocols/charnes_etal_1985_additive.md`. This is a
formulation-level analytical certificate, not a claim that the paper printed
the numerical results derived below.

## Source programme

For each evaluated observation $o$, the certified task is

$$
\begin{aligned}
\max_{\lambda,s^-,s^+}\quad
&\sum_i s_i^-+\sum_r s_r^+\\
\text{s.t.}\quad
&X\lambda+s^-=x_o,\\
&Y\lambda-s^+=y_o,\\
&\mathbf 1^\top\lambda=1,\\
&\lambda,s^-,s^+\geq0.
\end{aligned}
$$

Inputs are ordinary controllable resources, outputs are desirable services,
the comparison sample includes the evaluated observation, and no
undesirable-output or temporal-reference semantics are imported.

## Exact fixture 1: the source-displayed input excess

Charnes et al. display:

| DMU | $x_1$ | $x_2$ | $y$ |
|---|---:|---:|---:|
| A | 1 | 2 | 1 |
| B | 1 | 4 | 1 |

For B, every VRS reference plan is
$\lambda_A A+(1-\lambda_A)B$. Its only possible improvement is
$s_2^-=2\lambda_A$. Thus

$$
s_2^-\leq2,
$$

and $\lambda_A=1$ attains the bound. The exact result is

| Result component | B |
|---|---:|
| additive score/distance | $2$ |
| input slacks | $(0,2)$ |
| output slack | $0$ |
| target | $(1,2;1)$ |
| peer intensity | $\lambda_A=1$ |
| strong-efficiency status | false |

A's score is zero. This reconstructs a result from source-displayed
quantities; the paper does not print an additive result table, so published
reproduction remains false.

## Exact fixture 2: a unique management target

The independent separating fixture is:

| DMU | $x_1$ | $x_2$ | $y$ |
|---|---:|---:|---:|
| A | 7 | 8 | 20 |
| B | 1 | 2 | 5 |
| C | $3/2$ | $3/2$ | 1 |
| D | 10 | 10 | 1 |

For focal D, each of A, B, and C is individually feasible. The unit slack
sum at the four pure VRS reference activities is:

| Reference activity | Input saving | Service increase | Total |
|---|---:|---:|---:|
| A | $3+2$ | $19$ | $24$ |
| B | $9+8$ | $4$ | $21$ |
| C | $17/2+17/2$ | $0$ | $17$ |
| D | $0$ | $0$ | $0$ |

The objective of any convex combination is the same convex combination of
these four totals. It is therefore bounded above by 24, with equality only
at A. Consequently,

$$
\delta_D=24,\qquad
s_D^-=(3,2),\qquad
s_D^+=19,
$$

$$
(\widehat x_D,\widehat y_D)=(7,8;20),
\qquad
\lambda_A=1.
$$

A is efficient because a VRS plan preserving output 20 must place all
weight on A. B is efficient because it is the only activity using no more
than one unit of $x_1$. C is efficient because it is the only activity using
no more than $3/2$ units of $x_2$. The complete exact score vector is

$$
(\delta_A,\delta_B,\delta_C,\delta_D)=(0,0,0,24).
$$

This fixture separates the direct additive identity from other familiar
DEA summaries. For D, the VRS input-radial model selects C with
$\theta=3/20$, while the non-oriented VRS SBM selects B with
$\rho=3/100$. Agreement on one zero/nonzero status would therefore be
insufficient evidence; the distinct score, target, and peer close the model
identity.

## Independent executable compiler

`tests/test_additive_independent_oracle.py` constructs a dense variable
vector $[\lambda,s^-,s^+]$, writes the two balance blocks and VRS row
directly with NumPy, and calls `scipy.optimize.linprog`. It imports no
production problem builder or internal DEAPack compiler.

The source-certificate nodes are:

1. `test_source_displayed_two_dmu_case_recovers_the_pareto_shortfall`; and
2. `test_exact_vrs_additive_matches_independent_dense_source_program`.

Three additional tests are package-property evidence, not an expansion of
the 1985 source certificate:

- positive fixed weights change D's unique peer from A to B at the exact
  score 19;
- reciprocal quantity/weight changes preserve the score, peer, target, and
  weighted slack contributions; and
- the same fixture distinguishes additive, radial, and SBM identities.

Regression tests also protect the scale-aware numerical contract: small
common weights cannot turn a dominated observation into an efficient one,
an extreme reciprocal unit change preserves strong status, and a small
intensity is retained when it materially explains the reported target.

## Claim boundary

| Claim | Evidence | Certified scope |
|---|---|---|
| source-program transcription | Eq. (4.6), exact upper bounds, attaining plans, and independent dense LP | VRS; unit weights; self-inclusive cross-section |
| direct score and status | exact vectors $(0,2)$ and $(0,0,0,24)$ plus zero/nonzero strong status | ordinary nonnegative inputs and desirable outputs |
| physical operating account | exact input/output slacks, targets, and unique peers in both fixtures | source fixtures only; no general uniqueness claim |
| method identity | exact additive, radial, and SBM results differ on D | diagnostic fixture; does not certify the other models |
| numerical unit contract | row-scaled regression and reciprocal weight transformation | package extension evidence only |

The certificate does **not** extend to fixed non-unit weights,
CRS/NIRS/NDRS, panel or custom reference policies, equation (5.7), bad
outputs, signed data, unique/closest/least-cost targets, inference, or causal
management claims. A separately named leaf lacking its defining literature
or exact oracle remains `deferred_to_next_version`.
