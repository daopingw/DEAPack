# Cost efficiency and input allocative decomposition: analytical oracle

**Method IDs:** `economic.cost`,
`analysis.allocative_decomposition.cost_input_radial`

**Validation kind:** `analytically_derived`

**Published reproduction:** no

**Production compiler reused:** no

This certificate validates minimum-cost efficiency and its matched
input-radial technical--allocative decomposition. It combines an exact
four-activity account with independently assembled dense cost and radial
programmes. The fixtures are synthetic and do not reproduce a published
numerical table.

## Exact four-activity account

Every activity produces one unit of the single desirable output. Input prices
are $w=(3,1)$.

| Organization | $x_1$ | $x_2$ | $y$ | Observed cost $w^{\mathsf T}x$ |
|---|---:|---:|---:|---:|
| A | 1 | 4 | 1 | 7 |
| B | 2 | 2 | 1 | 8 |
| C | 4 | 1 | 1 | 13 |
| O | 4 | 4 | 1 | 16 |

For both CRS and VRS, delivering O's output commitment requires
$\sum_j\lambda_j\geq1$; VRS sharpens this to equality. Every reference
activity costs at least seven, so any feasible reference plan satisfies

$$
w^{\mathsf T}X\lambda
=\sum_j (w^{\mathsf T}x_j)\lambda_j
\geq7\sum_j\lambda_j
\geq7.
$$

The plan $\lambda_A=1$ attains this bound. Thus O's minimum cost and cost
efficiency are

$$
C_O^*=7,
\qquad
CE_O=\frac{C_O^*}{w^{\mathsf T}x_O}=\frac7{16}.
$$

For O's matched input-radial programme, every reference activity has
$x_{1j}+x_{2j}\geq4$. Feasibility and the two input bounds imply

$$
4\leq
\sum_j(x_{1j}+x_{2j})\lambda_j
\leq 8\theta.
$$

Therefore $\theta\geq1/2$. The plan $\lambda_B=1$ attains the bound with
target $(2,2)$, under both CRS and VRS. Consequently

$$
TE_O^I=\frac12,
\qquad
AE_O^C=\frac{CE_O}{TE_O^I}=\frac78,
\qquad
CE_O=TE_O^I AE_O^C.
$$

The lower bounds and attaining plans prove the three component optima; the
identity is not used as a substitute for validating either underlying
programme.

## Independent dense compilation

`tests/test_cost_allocative_independent_oracle.py` uses a separate
six-organization, two-input/two-output fixture. For each evaluated
organization and common strictly positive input-price vector, it independently
assembles the minimum-cost programme

$$
\min_{\lambda\geq0} w^{\mathsf T}X\lambda
\quad\text{subject to}\quad
Y\lambda\geq y_o,
$$

and the input-radial technical programme

$$
\min_{\lambda\geq0,\theta\geq0}\theta
\quad\text{subject to}\quad
X\lambda\leq\theta x_o,
\quad Y\lambda\geq y_o.
$$

The VRS branch adds $\boldsymbol1^{\mathsf T}\lambda=1$ to each programme;
the CRS branch does not. The test constructs raw dense matrices, solves them
with `scipy.optimize.linprog`, and derives minimum cost, cost efficiency,
technical efficiency, allocative efficiency, and cost-minimizing targets. It
compares these values with the public `CostEfficiency.fit` and
`AllocativeDecomposition.fit` results for every fixture organization under
both CRS and VRS.

The oracle imports no DEAPack economic or radial compiler, template,
reference-plan helper, or private fit method. The shared SciPy/HiGHS optimizer
means the evidence is independent problem compilation rather than an
independent-solver reproduction.

## Claim boundary

The exact certificate covers the named O case under CRS/VRS with a common
strictly positive price vector: minimum cost, cost efficiency, input-radial
technical efficiency, cost allocative efficiency, and the multiplicative
identity. The dense certificate covers the same components for all six
organizations in its self-inclusive, global cross-sectional fixture, plus the
cost-minimizing target coordinates. It does not certify observation-specific
prices, nonpositive prices or cost denominators, restricted returns to scale,
external/custom/temporal references, undesirable outputs, target uniqueness,
dual values, sampling inference, or a published numerical reproduction.
