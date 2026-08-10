# Tone (2001) non-oriented SBM: independent analytical oracle

**Method ID:** `static.sbm.nonoriented.tone2001`

**Validation kind:** `analytically_derived`

**Published reproduction:** no

**Production compiler reused:** no

This certificate validates the classic non-oriented slacks-based measure on a
strictly positive, cross-sectional, self-inclusive reference population. It
combines one exact VRS account with CRS/VRS programmes assembled directly as
dense arrays. The fixtures are synthetic; no published numerical table is
claimed as reproduced.

## Fractional account

For evaluated organization $o$, let $s^-$ and $s^+$ be the input-excess and
desirable-output shortfall vectors in

$$
X\lambda+s^-=x_o,
\qquad
Y\lambda-s^+=y_o,
\qquad
\lambda,s^-,s^+\geq0.
$$

The non-oriented Tone account is

$$
\rho_o=
\frac{1-\frac1m\sum_i s_i^-/x_{io}}
     {1+\frac1s\sum_r s_r^+/y_{ro}}.
$$

CRS imposes no intensity-sum restriction; VRS adds
$\boldsymbol 1^{\mathsf T}\lambda=1$.

## Exact VRS fixture

| Organization | $x_1$ | $x_2$ | $y_1$ | $y_2$ |
|---|---:|---:|---:|---:|
| A | 2 | 4 | 1 | 2 |
| B | 4 | 2 | 2 | 1 |
| O | 4 | 4 | 1 | 1 |

When O is evaluated, write its VRS intensities on A, B, and O as $a,b,c$.
Because $a+b+c=1$, the reference activity is

$$
X\lambda=(4-2a,4-2b),
\qquad
Y\lambda=(1+b,1+a).
$$

Put $z=a+b$. The average normalized input and output slacks are respectively
$z/4$ and $z/2$, so

$$
\rho_O(z)=\frac{1-z/4}{1+z/2},
\qquad 0\leq z\leq1.
$$

This expression is strictly decreasing on the feasible interval. Therefore
the lower bound is attained at $z=1$, for example by the feasible plan
$a=1,b=c=0$, and

$$
\rho_O=\frac12,
\qquad
\overline{s^-}=\frac14,
\qquad
\overline{s^+}=\frac12.
$$

The Charnes--Cooper scale is
$t=(1+\overline{s^+})^{-1}=2/3$. A must use A to maintain its second output
without exceeding its first input, and symmetrically B must use B. Hence the
exact score vector for (A, B, O) is $(1,1,1/2)$. This proof establishes an
optimum, not merely a feasible value.

The individual peer mix for O is not unique: every plan with $a+b=1$ attains
the same fractional account. The certificate therefore does not claim a
unique target or slack allocation.

## Independent dense compilation

`tests/test_nonoriented_sbm_independent_oracle.py` writes the transformed
programme from ordinary NumPy arrays. Its variables are transformed
intensities $\widehat\lambda$, normalized transformed slacks
$\widehat s^-,\widehat s^+$, and $t$. It imposes

$$
\frac{X\widehat\lambda}{x_o}+\widehat s^- -t\boldsymbol1=0,
\qquad
\frac{Y\widehat\lambda}{y_o}-\widehat s^+ -t\boldsymbol1=0,
$$

$$
t+\frac1s\boldsymbol1^{\mathsf T}\widehat s^+=1,
$$

plus $\boldsymbol1^{\mathsf T}\widehat\lambda=t$ for VRS, and minimizes

$$
t-\frac1m\boldsymbol1^{\mathsf T}\widehat s^-.
$$

The test builds every row itself and calls `scipy.optimize.linprog` for all
six organizations in a separate two-input/two-output fixture under CRS and
VRS. It then compares those independently compiled objective values with the
public `SBM.fit` scores. It imports neither DEAPack's SBM module nor its sparse
reference compiler, transformed-RTS helper, LP builder, or private fit path.
Using the same SciPy/HiGHS optimizer makes this independent problem
compilation, not an independent-solver reproduction.

## Claim boundary

The exact certificate covers the VRS score, the two average normalized-slack
accounts, the transform scale, and score validity for all three exact-fixture
organizations. The dense certificate covers only CRS/VRS public scores on the
six-organization fixture. Neither certificate covers NIRS/NDRS, weighted or
oriented SBM, undesirable outputs, zero or signed quantities, external or
non-global references, a unique optimum, dual values, sampling inference, or
published numerical reproduction.
