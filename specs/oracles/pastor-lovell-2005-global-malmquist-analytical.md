# Pastor--Lovell (2005) Global Malmquist analytical oracle

**Method ID:** `productivity.global_malmquist`  
**Defining source:** Pastor and Lovell (2005),
[doi:10.1016/j.econlet.2005.02.013](https://doi.org/10.1016/j.econlet.2005.02.013)  
**Frozen protocol:**
`specs/source_protocols/pastor_lovell_2005_global_malmquist.md`
**Published reproduction:** no  

## Claim

This certificate validates the output-oriented CRS Global Malmquist account
under one fixed full-sample technology. It derives exact own-period and global
Farrell efficiency-form distances, the headline productivity ratios, the
efficiency-change and best-practice-change components, and fixed-vintage
circularity. It is not a published numerical-table reproduction.

## Exact three-period panel

Two organizations are observed in three periods:

| Organization | Period | Input $x$ | Output $y$ |
|---|---:|---:|---:|
| A | 0 | 2 | 1 |
| B | 0 | 1 | 1 |
| A | 1 | 1 | 1 |
| B | 1 | 1 | 2 |
| A | 2 | 1 | 3 |
| B | 2 | 1 | 4 |

All quantities are strictly positive. The maximum output/input ratios in the
three contemporaneous samples are $1$, $2$, and $4$. The global sample's
maximum ratio is $4$, represented uniquely by organization B in period 2.

## Exact radial-distance proof

For any reference sample whose observations satisfy $y_j\le kx_j$, every
feasible CRS output-oriented plan obeys

$$
\phi y_o
\le \sum_j\lambda_j y_j
\le k\sum_j\lambda_jx_j
\le kx_o.
$$

Thus $\phi\le kx_o/y_o$ and the efficiency-form distance satisfies
$d\ge y_o/(kx_o)$. In each contemporaneous sample, organization B lies on the
ray $y=kx$ and attains the bound with $\lambda=x_o$. In the global sample,
period-2 B lies on $y=4x$ and attains the corresponding global bound. These
feasible witnesses and upper bounds prove the exact optima:

| Organization, period | Own-period $d^\tau$ | Global $d^G$ | Own peer | Global peer |
|---|---:|---:|---|---|
| A, 0 | $1/2$ | $1/8$ | B, 0 | B, 2 |
| B, 0 | $1$ | $1/4$ | B, 0 | B, 2 |
| A, 1 | $1/2$ | $1/4$ | B, 1 | B, 2 |
| B, 1 | $1$ | $1/2$ | B, 1 | B, 2 |
| A, 2 | $3/4$ | $3/4$ | B, 2 | B, 2 |
| B, 2 | $1$ | $1$ | B, 2 | B, 2 |

The dense compiler independently recovers these values from the LP matrices;
it does not call DEAPack's reference builder, radial template, pooled task
engine, or result transformations.

## Exact productivity accounts

Using

$$
GM=\frac{d^G_1}{d^G_0},\quad
EC_G=\frac{d^1_1}{d^0_0},\quad
BPG^\tau=\frac{d^G_\tau}{d^\tau_\tau},\quad
BPC_G=\frac{BPG^1}{BPG^0},
$$

the four public adjacent accounts are:

| Organization, transition | $GM$ | $EC_G$ | $BPG^t$ | $BPG^{t+1}$ | $BPC_G$ |
|---|---:|---:|---:|---:|---:|
| A, 0 to 1 | $2$ | $1$ | $1/4$ | $1/2$ | $2$ |
| B, 0 to 1 | $2$ | $1$ | $1/4$ | $1/2$ | $2$ |
| A, 1 to 2 | $3$ | $3/2$ | $1/2$ | $1$ | $2$ |
| B, 1 to 2 | $2$ | $1$ | $1/2$ | $1$ | $2$ |

Every row closes $GM=EC_G\times BPC_G$ exactly. The A account distinguishes
operating-performance change from movement of contemporaneous best practice
toward the global benchmark: its second transition has both
$EC_G=3/2$ and $BPC_G=2$.

## Fixed-vintage circularity

For A,

$$
GM_A^{0,1}GM_A^{1,2}=2\times3=6
=\frac{3/4}{1/8}=GM_A^{0,2}.
$$

For B,

$$
GM_B^{0,1}GM_B^{1,2}=2\times2=4
=\frac{1}{1/4}=GM_B^{0,2}.
$$

The equalities telescope because every ratio uses the same frozen global
technology. They make no claim about chaining estimates from different
sample vintages.

## Executable mapping and boundary

- Production-free compiler:
  `tests/test_pastor_lovell_2005_global_malmquist_source.py`.
- Public result comparison:
  `tests/test_global_malmquist.py::test_public_api_matches_exact_pastor_lovell_three_period_oracle`.
- Certified result fields: `productivity_change`, `efficiency_change`,
  `best_practice_change`, both best-practice gaps, both global efficiencies,
  four diagnostic task roles, peer provenance, and the decomposition residual.

The certificate covers only the output-oriented CRS, ordinary desirable-output,
self-inclusive, fixed-global-vintage account. Input orientation, VRS, other
returns-to-scale assumptions, other temporal reference policies,
environmental production, inference, profitability, welfare, and the
published empirical application remain outside its claim.
