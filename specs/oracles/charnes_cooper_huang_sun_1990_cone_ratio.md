# Polyhedral cone-ratio DEA: 1990 published Example 2 oracle

**Candidate identity:**
`valuation.weight_restriction.cone_ratio.polyhedral_crs.charnes_etal_1990`  
**Controlled oracle status:** `reproduced`  
**Numerical audit:** `published_example_independently_reproduced`  
**Repository automation:** `complete`  
**Production compiler reused:** no  
**Defining source:** Charnes, Cooper, Huang, and Sun (1990), journal
pp. 83--85, Example 2, Table 1, and the displayed block matrix on p. 84  
**Certified scope:** one output, two inputs, 17 organizations, input-oriented
CRS, and the printed nonnegative sum-form generators

The controlled status is `reproduced`. The source data, exact certificate,
and two independently assembled LP forms are automated in
`tests/test_polyhedral_cone_ratio_source_oracle.py`. That test imports no
production transformation, compiler, solver wrapper, or result helper.

The equation and interpretation boundary is frozen in
`specs/source_protocols/charnes_cooper_huang_sun_1990_polyhedral_cone_ratio.md`.

## 1. Primary-source fixture

Table 1 of Charnes et al. (1990) reports the following observations. Every
organization produces the same desirable output $y=2$.

| Organization | $y$ | $x_1$ | $x_2$ |
|---|---:|---:|---:|
| DMU1 | 2 | 10 | 10 |
| DMU2 | 2 | 20 | 5 |
| DMU3 | 2 | 30 | 4 |
| DMU4 | 2 | 27 | 9 |
| DMU5 | 2 | 14 | 8 |
| DMU6 | 2 | 5 | 20 |
| DMU7 | 2 | 4 | 20 |
| DMU8 | 2 | 12 | 18 |
| DMU9 | 2 | 8 | 12 |
| DMU10 | 2 | 4 | 30 |
| DMU11 | 2 | 6 | 15 |
| DMU12 | 2 | 25 | 4 |
| DMU13 | 2 | 7 | 13 |
| DMU14 | 2 | 40 | 5 |
| DMU15 | 2 | 20.5 | 4.9 |
| DMU16 | 2 | 4.1 | 19.5 |
| DMU17 | 2 | 5 | 15 |

Example 2 supplies the finite-generator transformation

$$
\begin{bmatrix}B&0\\0&A\end{bmatrix}
=
\begin{bmatrix}
1&0&0\\
0&1&0.01\\
0&0.01&1
\end{bmatrix},
$$

so

$$
B=[1],
\qquad
A=\begin{bmatrix}1&0.01\\0.01&1\end{bmatrix}.
$$

The source reports that the transformed-data cone-ratio scores of DMU3 and
DMU10 are, respectively,

$$
0.9884
\qquad\text{and}\qquad
0.9767.
$$

## 2. Independently assembled envelopment oracle

Let $X$ contain the two input rows above and let
$Y=(2,\ldots,2)$. The transformed observations are

$$
X'=AX,
\qquad
Y'=BY=Y.
$$

For every focal organization $o$, the audit directly assembled the dense LP

$$
\begin{aligned}
\min_{\lambda,\theta}\quad &\theta\\
\text{s.t.}\quad
&X'\lambda-\theta x'_o\le0,\\
&-Y'\lambda\le-y'_o,\\
&\lambda\ge0,\quad\theta\ge0.
\end{aligned}
\tag{E}
$$

The variable vector was $[\lambda_1,\ldots,\lambda_{17},\theta]$. No
DEAPack model, reference compiler, sparse template, solver wrapper, result
object, or registry helper was imported.

## 3. Independently assembled multiplier oracle

The second audit form did not dualize the matrix generated for (E). It
independently transcribed the source multiplier programme with variables
$[\alpha_1,\alpha_2,\gamma]$:

$$
\begin{aligned}
\max_{\alpha,\gamma}\quad &\gamma By_o\\
\text{s.t.}\quad
&\gamma By_j-\alpha^\top Ax_j\le0,
&&j=1,\ldots,17,\\
&\alpha^\top Ax_o=1,\\
&\alpha\ge0,\quad\gamma\ge0.
\end{aligned}
\tag{M}
$$

Both dense programmes were solved by `scipy.optimize.linprog` with HiGHS
under SciPy 1.18.0. Across all 17 focal organizations, the maximum absolute
difference between their objective values was

$$
9.55\times10^{-15}.
$$

This is an independent cross-form transcription audit. The same separation is
enforced in the automated source-only test and compared with the public API in
a separate production-facing test.

## 4. Exact DMU3 certificate

For DMU3,

$$
x_3=(30,4)^\top,
\qquad
Ax_3=(30.04,4.30)^\top.
$$

DMU12 has

$$
x_{12}=(25,4)^\top,
\qquad
Ax_{12}=(25.04,4.25)^\top.
$$

Because all outputs equal 2, $\lambda_{12}=1$ satisfies the transformed
output constraint. Its required radial factor is

$$
\max\left\{
\frac{25.04}{30.04},
\frac{4.25}{4.30}
\right\}
=
\max\left\{
\frac{626}{751},
\frac{85}{86}
\right\}
=\frac{85}{86}.
$$

The dense LP certifies that no feasible reference combination has a lower
factor. Thus

$$
\theta_3=\frac{85}{86}
=0.9883720930\ldots,
\qquad
\lambda_{12}=1,
$$

which rounds to the source value `0.9884`.

In ordinary input coordinates DMU12 directly reduces $x_1$ and holds $x_2$.
That observation is specific to this fixture. The general cone-ratio model
certifies transformed inequalities and does not imply componentwise original-
quantity dominance for every dataset.

## 5. Exact DMU10 certificate

For DMU10,

$$
x_{10}=(4,30)^\top,
\qquad
Ax_{10}=(4.30,30.04)^\top.
$$

DMU7 has

$$
x_7=(4,20)^\top,
\qquad
Ax_7=(4.20,20.04)^\top.
$$

Again the common output makes $\lambda_7=1$ output-feasible. Its radial
factor is

$$
\max\left\{
\frac{4.20}{4.30},
\frac{20.04}{30.04}
\right\}
=
\max\left\{
\frac{42}{43},
\frac{501}{751}
\right\}
=\frac{42}{43}.
$$

The dense LP certifies the matching lower bound, so

$$
\theta_{10}=\frac{42}{43}
=0.9767441860\ldots,
\qquad
\lambda_7=1,
$$

which rounds to the source value `0.9767`.

## 6. Identity-cone reduction

The source programme gives an exact implementation property independent of
the published fixture. Setting

$$
A=I_m,
\qquad
B=I_s
$$

makes (E)--(M) ordinary input-oriented CRS DEA. The automated oracle
compares a separately compiled cone-ratio LP with a separately compiled
ordinary CCR LP over deterministic and randomized nonnegative fixtures. This
is an exact reduction, not a tolerance-based approximation.

## 7. Unit-covariance certificate

Holding $A$ fixed while changing an input measurement unit changes the
declared valuation cone. The audit multiplied the first input row by 100.
For DMU3:

| Account | Score |
|---|---:|
| original quantities and $A$ | 0.9883720930 |
| $x_1$ multiplied by 100; numerical $A$ unchanged | 0.5882352941 |
| $x_1$ multiplied by 100; first column of $A$ divided by 100 | 0.9883720930 |

In general, for positive diagonal input and output recodings $C,D$, the
covariant generator update is

$$
\widetilde A=AC^{-1},
\qquad
\widetilde B=BD^{-1}.
$$

An automated release oracle must verify both the covariant invariance and a
counterexample showing that holding numerical generators fixed represents a
different restriction.

## 8. Example 3/Table 2 is not an oracle

The next source example reuses the same 17 observations and prints

$$
B=\begin{bmatrix}1\\1\end{bmatrix},
\qquad
A=\begin{bmatrix}0.125&0.025\\0.05&0.05\end{bmatrix}.
$$

The independent programmes (E) and (M) agree numerically and reproduce 15 of
the 17 Table 2 entries after four-decimal rounding. Two entries conflict:

| Organization | Printed Table 2 | Independent result |
|---|---:|---:|
| DMU3 | 0.1923 | 0.5882 |
| DMU10 | 0.3333 | 0.8000 |

The discrepancy is not a multiplier/envelopment duality gap, a matrix-
transpose choice, or solver tolerance: the two independent source forms
agree on `0.5882` and `0.8000`. No primary erratum was located. The complete
Table 2 vector is therefore an unresolved source anomaly and must not be
copied into a test expectation, silently corrected, or represented as a
published reproduction.

The anomaly does not affect the independently reproduced Example 2 values or
the equations defining the finite sum-form model.

## 9. Automated release oracle

The source-only and public-contract tests now:

1. encode the 17 printed observations directly in the test;
2. compile (E) and (M) independently without production helpers;
3. reproduce $85/86$ and $42/43$ to source rounding;
4. compare both forms over all 17 rows;
5. verify the identity-cone CCR reduction;
6. verify covariant unit recoding and the fixed-generator counterexample;
7. corrupt an apparently optimal incumbent and require fail-closed
   certification; and
8. retain the Example 3 conflict as documentation, not a passing expected
   score vector.

These checks close the `reproduced` oracle status without extending the
source identity beyond the finite input-oriented CRS sum-form programme.

## 10. Claim boundary

| Claim | Evidence | Certified scope |
|---|---|---|
| source-program transcription | 1990 equations (5)--(6), direct multiplier/envelopment agreement | finite nonnegative sum-form input/output cones; input CRS |
| published numerical values | exact $85/86$ and $42/43$ certificates | Example 2 DMU3 and DMU10 |
| full-sample cross-form equivalence | maximum audit gap $9.55\times10^{-15}$ | all 17 Example 2 observations |
| peer account | exact single peers DMU12 and DMU7 | the two certified focal rows only |
| unit behavior | positive diagonal recoding audit | Example 2 input 1; general algebraic covariance identity |
| complete Example 3 reproduction | contradicted by source audit | **not certified** |

This oracle does not certify AR-I or AR-II, common weights, virtual shares,
half-space conversion, VRS, output orientation, undesirable outputs, panel or
non-global references, strong Pareto targets, generator elicitation from
expert DMUs, inference, or any empirical banking table.
