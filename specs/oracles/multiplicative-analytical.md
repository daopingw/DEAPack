# Multiplicative DEA: independent analytical oracle

**Method ID:** `static.multiplicative`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no  
**Production compiler reused:** no

This certificate validates both Charnes--Cooper--Seiford--Stutz source
variants with exact powers-of-two observations. The equation and
interpretation boundary is frozen in
`specs/source_protocols/charnes_etal_1982_1983_multiplicative.md`.

## Exact fixture

| Organization | $x$ | $y$ | $(\widehat x,\widehat y)$ |
|---|---:|---:|---:|
| A | 2 | 4 | $(L,2L)$ |
| B | 4 | 4 | $(2L,2L)$ |

where $L=\log2$.

### Invariant 1983 variant

The convexity constraint reduces every peer plan to
$\lambda_A+\lambda_B=1$. For B, eliminating its slacks gives

$$
s^-+s^+=L\lambda_A.
$$

The exact upper bound is therefore $L$, attained uniquely at
$\lambda_A=1$. Hence

$$
s^-=L,\qquad s^+=0,\qquad
(x_B^*,y_B^*)=(2,4),\qquad
D_B^{\mathrm{mult}}=L,\qquad
E_B^{\mathrm{mult}}=e^{-L}=\frac12.
$$

A can only attain the zero-slack self plan, so
$E_A^{\mathrm{mult}}=1$. With
$\delta=2$, the feasible plan and target do not change and
$E_B^{\mathrm{mult}}=e^{-2L}=1/4$.

### Original 1982 variant

For B, feasibility requires

$$
L\lambda_A+2L\lambda_B\leq2L,
\qquad
2L\lambda_A+2L\lambda_B\geq2L.
$$

Eliminating the slacks gives $s^-+s^+=L\lambda_A$. The input inequality
implies $\lambda_A\leq2-2\lambda_B\leq2$, so $2L$ is an exact upper bound.
It is attained uniquely at $\lambda_A=2,\lambda_B=0$. Therefore

$$
s^-=0,\qquad s^+=2L,\qquad
(x_B^*,y_B^*)=(4,16),qquad
D_B^{\mathrm{mult}}=2L,\qquad
E_B^{\mathrm{mult}}=\frac14.
$$

After the common unit change $x'=2x$, eliminating the original-variant
slacks gives $s^-+s^+=L(1-\lambda_B)$, whose upper bound is $L$.
Thus the original B score changes to $1/2$. The invariant programme remains
at $1/2$, with its input target co-scaling from 2 to 4. This is an exact
counterexample to unit invariance for the 1982 model and an exact unit-
invariance check for the 1983 model.

## Independent executable compiler

`tests/test_multiplicative_source_oracle.py` writes the dense variable vector
$[\lambda,s^-,s^+]$, log input/output balances, optional log-convexity row,
and source objective directly before calling `scipy.optimize.linprog`. The
primary certificate node is:

`tests/test_multiplicative_source_oracle.py::test_exact_two_dmu_source_variants`.

No production LP builder, sparse reference compiler, model method, log-
anchoring routine, solver wrapper, or registry helper is reused by that
independent compiler.

## Claim boundary

| Claim | Evidence | Certified scope |
|---|---|---|
| source-program transcription | exact upper bounds, attaining plans, independent dense LP | both source variants; two organizations; one input and one output |
| native score | exact $1,1/2,1/4$ values | named fixture and transformations above |
| operating account | exact log slacks, targets, and peer intensities | named fixture; no general target-uniqueness claim |
| unit behavior | exact common input-unit change | non-invariance for 1982; invariance for 1983 |
| exponent-floor behavior | exact $\delta=1$ and $\delta=2$ comparison | invariant variant on named fixture |

The certificate does not cover undesirable outputs, non-global references,
panels, network or dynamic technologies, productivity, price information,
uncertainty, causal interpretation, or published empirical replication.
