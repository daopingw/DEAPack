# Charnes--Cooper--Seiford--Stutz multiplicative DEA source protocol

## Readiness record

| Field | State |
|---|---|
| Public method identity | `static.multiplicative` |
| Public estimator | `MultiplicativeDEA` |
| Source variants | `original_1982`, `invariant_1983` |
| Source preset identities | `static.multiplicative.original.charnes_etal_1982`, `static.multiplicative.invariant.charnes_etal_1983` |
| Default variant | `invariant_1983` |
| Primary sources | both published notes obtained and equation-checked |
| Published numerical reproduction | no |
| Independent executable evidence | separate dense log-space LP |
| Exact analytical evidence | closed for a two-organization fixture |
| Last source audit | 2026-07-31 |

The sources are Charnes, Cooper, Seiford, and Stutz (1982), “A
Multiplicative Model for Efficiency Analysis,” *Socio-Economic Planning
Sciences* 16(5), 223--224,
[DOI 10.1016/0038-0121(82)90029-5](https://doi.org/10.1016/0038-0121(82)90029-5),
and Charnes, Cooper, Seiford, and Stutz (1983), “Invariant Multiplicative
Efficiency and Piecewise Cobb--Douglas Envelopments,” *Operations Research
Letters* 2(3), 101--103,
[DOI 10.1016/0167-6377(83)90014-7](https://doi.org/10.1016/0167-6377(83)90014-7).

The two papers define one historical development line. DEAPack therefore
uses one estimator with two explicit variants. It does not erase the
economically important difference between the original log-conic technology
and the later unit-invariant log-convex technology.

## What the model asks

Ordinary additive DEA compares weighted sums of services with weighted sums
of resources. Multiplicative DEA instead compares weighted products. Its
frontier permits different Cobb--Douglas-like trade-offs on different
facets. For a manager, the resulting account is proportional: input excesses
and output shortfalls are measured as log changes, then aggregated using
strictly positive exponents. The score is a relative operating-performance
index, not a production-function elasticity estimate, a causal effect, or a
price-based profit measure.

Let every input $x_{ij}$ and desirable output $y_{rj}$ be positive, and write
$\widehat x_{ij}=\log x_{ij}$ and $\widehat y_{rj}=\log y_{rj}$. The hats are
part of the maintained multiplicative technology. Fitting an ordinary DEA
model after an arbitrary log preprocessing step is not an equivalent
interpretation.

## 1982 original log-conic variant

The original source assumes every input and output is strictly greater than
one. For organization $o$, its multiplier programme is

$$
\begin{aligned}
\max_{\mu,v}\quad
  &\mu^\top\widehat y_o-v^\top\widehat x_o\\
\text{s.t.}\quad
  &\mu^\top\widehat y_j-v^\top\widehat x_j\leq0,
    &&j=1,\ldots,n,\\
  &\mu_r\geq1,&&r=1,\ldots,s,\\
  &v_i\geq1,&&i=1,\ldots,m.
\end{aligned}
$$

The equivalent source envelopment is

$$
\begin{aligned}
\max_{\lambda,s^-,s^+}\quad
  &\mathbf1^\top s^-+\mathbf1^\top s^+\\
\text{s.t.}\quad
  &\widehat X\lambda+s^-=\widehat x_o,\\
  &\widehat Y\lambda-s^+=\widehat y_o,\\
  &\lambda,s^-,s^+\geq0.
\end{aligned}
$$

There is no convexity equation. The benchmark is conic in log quantities,
so `crs` and `vrs` are misleading labels; DEAPack reports `log_conic`.
The native log efficiency is

$$
\ell_o=-\bigl(\mathbf1^\top s^-+\mathbf1^\top s^+\bigr)\leq0,
\qquad E_o=\exp(\ell_o)\in(0,1].
$$

Because changing a measurement unit translates a logged coordinate and the
model has neither an intercept nor $\mathbf1^\top\lambda=1$, the original
score is not invariant to unit changes. That limitation is retained and
tested rather than silently repaired.

## 1983 invariant log-convex variant

The 1983 paper introduces a free log intercept $\omega$ and a common
positive exponent floor $\delta$:

$$
\begin{aligned}
\max_{\mu,v,\omega}\quad
  &\mu^\top\widehat y_o-v^\top\widehat x_o+\omega\\
\text{s.t.}\quad
  &\mu^\top\widehat y_j-v^\top\widehat x_j+\omega\leq0,
    &&j=1,\ldots,n,\\
  &\mu_r\geq\delta>0,\qquad v_i\geq\delta.
\end{aligned}
$$

Its envelopment is

$$
\begin{aligned}
\max_{\lambda,s^-,s^+}\quad
  &\delta\left(\mathbf1^\top s^-+\mathbf1^\top s^+\right)\\
\text{s.t.}\quad
  &\widehat X\lambda+s^-=\widehat x_o,\\
  &\widehat Y\lambda-s^+=\widehat y_o,\\
  &\mathbf1^\top\lambda=1,\\
  &\lambda,s^-,s^+\geq0.
\end{aligned}
$$

DEAPack calls this technology `log_convex`, not VRS. The benchmark quantities
are peer-weighted geometric means:

$$
x_{io}^{*}=x_{io}\exp(-s_i^-)
             =\prod_j x_{ij}^{\lambda_j},
\qquad
y_{ro}^{*}=y_{ro}\exp(s_r^+)
             =\prod_j y_{rj}^{\lambda_j}.
$$

Thus $s_i^-=\log(x_{io}/x_{io}^{*})$ records proportional resource excess,
while $s_r^+=\log(y_{ro}^{*}/y_{ro})$ records proportional service shortfall.
The distance and efficiency reported by DEAPack are

$$
D_o^{\mathrm{mult}}=\delta\left(\sum_i s_i^-+\sum_r s_r^+\right),
\qquad
E_o^{\mathrm{mult}}=\exp(-D_o^{\mathrm{mult}}).
$$

At $\delta=1$, an input log slack of $\log 2$ means the selected benchmark
uses one half as much of that resource, holding the rest of the selected
operating account fixed. It does not by itself mean that expenditure halves:
prices and adjustment costs are absent. A different $\delta>0$ raises the
$\delta=1$ efficiency score to the power $\delta$; it leaves the feasible
peer plans, selected target set, and ranking unchanged. DEAPack defaults to
$\delta=1$ and labels other values as an explicit score-power convention.

The convexity identity makes common translations of a logged coordinate
cancel on both sides of every balance. Consequently, independent positive
rescalings of the original input and output units leave scores, intensities,
and proportional adjustments unchanged; targets rescale with their
coordinates.

## Independent exact certificate

The analytical fixture is deliberately small:

| Organization | input $x$ | output $y$ |
|---|---:|---:|
| A | 2 | 4 |
| B | 4 | 4 |

For the invariant 1983 variant with $\delta=1$, A is efficient. B chooses
$\lambda_A=1$, has $s^-=\log2$ and $s^+=0$, and therefore has target
$(2,4)$, distance $\log2$, and efficiency $1/2$.

For the original 1982 variant, B chooses $\lambda_A=2$, has $s^-=0$ and
$s^+=2\log2$, and therefore has one solver-independent target $(4,16)$,
distance $2\log2$, and efficiency $1/4$. Multiplying the input coordinate
of both organizations by two changes the original B score to $1/2$ but
leaves the invariant score at $1/2$. Setting $\delta=2$ in the invariant
variant retains B's peer and target while changing its score to $1/4$.

`tests/test_multiplicative_source_oracle.py` compiles the dense source
envelopment directly with NumPy and `scipy.optimize.linprog`; it imports no
production model builder, reference compiler, or private DEAPack helper.
These values are analytically derived and are not claimed to be a published
numerical table.

## Evidence and interpretation boundary

The source-qualified runtime profiles cover all and only:

- one self-inclusive cross section over ordinary resources and desirable
  services;
- strictly positive observations for 1983 and observations strictly greater
  than one for 1982;
- the exact log-conic or log-convex technology defined above;
- non-oriented multiplicative efficiency, log inefficiency, native log
  slacks, original-unit targets, peer intensities, and solver-selected
  exponents; and
- deterministic full-frontier estimation without prices or uncertainty.

Panel and non-global reference rules supported by the shared reference
infrastructure are transparent package extensions and do not receive a
source-profile match. Undesirable outputs, weak disposal, networks, dynamic
links, super-efficiency, productivity indexes, weight restrictions,
nondiscretionary variables, integer restrictions, statistical inference,
and causal, welfare, or profit interpretations remain distinct methods.
They are not implied by taking logarithms and are deferred until separately
source-qualified.
