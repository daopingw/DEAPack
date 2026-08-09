# Activity-specific weak-disposal DDF: independent analytical oracle

**Method ID:** `environmental.ddf.weak_disposal.activity_specific`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This certificate validates the public VRS activity-specific weak-disposal
directional distance function on a small exact production account. The
fixture and its expected values are synthetic consequences of the frozen
Kuosmanen technology; they are not a transcription of a published empirical
table.

## Frozen programme

For evaluated activity $(x_o,y_o,b_o)$ and nonnegative direction
$(g^x,g^y,g^b)$, the programme uses nonnegative active intensities $\mu$ and
complementary curtailed intensities $\eta$:

$$
\begin{aligned}
\max_{\mu,\eta,\beta}\quad &\beta\\
\text{subject to}\quad
&X(\mu+\eta)+\beta g^x\le x_o,\\
&Y\mu-\beta g^y\ge y_o,\\
&B\mu+\beta g^b=b_o,\\
&\mathbf1^\mathsf T(\mu+\eta)=1,\\
&\mu,\eta,\beta\ge0.
\end{aligned}
$$

The complement is denoted by $\eta$ here so that $\tau$ remains available for
a reference period in the shared book notation. The public result field
`abatement_tau` is a stable software name for this mathematical complement;
it is not a time index or an observed abatement cost.

## Exact three-activity fixture

| Activity | input $x$ | desirable output $y$ | residual $b$ |
|---|---:|---:|---:|
| A | $1$ | $1$ | $1$ |
| B | $2$ | $3/2$ | $4/5$ |
| C | $3/2$ | $6/5$ | $9/10$ |

The default public direction is $(g^x,g^y,g^b)=(0,y_o,b_o)$. Self-inclusion
and the nonnegative-distance policy give zero distance for A and B. For C, the
following exact activity account is feasible:

$$
\mu_A=\frac{67}{140},\qquad
\mu_B=\frac12,\qquad
\eta_A=\frac{3}{140},\qquad
\beta=\frac1{42},
$$

with all other $\mu$ and $\eta$ equal to zero. Total intensity is one, the
input account binds at $3/2$, and the represented output and residual are

$$
Y\mu=\frac{43}{35}
=\frac65\left(1+\frac1{42}\right),
\qquad
B\mu=\frac{123}{140}
=\frac9{10}\left(1-\frac1{42}\right).
$$

An exact dual certificate is obtained for the equivalent minimization of
$-\beta$. The input and desirable-output inequality multipliers are
$(-1/3,-10/21)$; the residual-equality and VRS-equality multipliers are
$(-10/21,1/3)$. In variable order
$(\mu_A,\mu_B,\mu_C,\eta_A,\eta_B,\eta_C,\beta)$, the resulting reduced costs
are

$$
\left(0,0,\frac1{42},0,\frac13,\frac16,0\right),
$$

which are nonnegative. The primal and dual minimization objectives both equal
$-1/42$, proving that C's maximum directional distance is $1/42$ rather than
merely exhibiting a feasible improvement.

The corresponding public display efficiency is $42/43$. Its directional
target is $(x^*,y^*,b^*)=(3/2,43/35,123/140)$.

## Independent executable check

The automated oracle assembles the dense phase-one arrays directly from the
equations above and solves them with SciPy/HiGHS. It does not call the
production sparse compiler, private problem builders, or production result
post-processing. A second test compares the independent distances for every
fixture activity with the public API and checks C's exact target.

## Claim boundary

The certificate covers one self-inclusive, cross-sectional VRS technology,
nonnegative quantities, one input, one desirable output, one residual, the
observation-scaled $(0,y_o,b_o)$ direction, and the nonnegative-distance
policy. It does not certify generalized weak disposal, common-factor CRS,
strong disposal, null jointness, custom or temporal references, alternative
directions, statistical inference, or environmental productivity operators.
