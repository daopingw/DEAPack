# Cooper--Park--Pastor (1999) range-adjusted measure source protocol

## Readiness record

| Field | State |
|---|---|
| Public method identity | `static.ram` |
| Source-qualified runtime profile | `cooper_park_pastor_1999_eq_17_18_20_23` |
| Primary source | complete author-uploaded article obtained and equation-checked |
| Published numerical reproduction | no numerical result table is claimed |
| Independent executable evidence | closed by a separately compiled dense VRS LP |
| Exact analytical evidence | closed for one four-DMU fixture with a unique target and peer |
| Source zero-range rule | omit the associated coordinate constraint and set its slack contribution to zero |
| Package extensions | global panel comparison |
| Deferred identities | CRS/NIRS/NDRS RAM, environmental/network/dynamic RAM, super-RAM, minimum-distance RAM, and alternative range populations |
| Last source audit | 2026-07-31 |

The defining source is W. W. Cooper, K. S. Park, and J. T. Pastor
(1999), “RAM: A Range Adjusted Measure of Inefficiency for Use with
Additive Models, and Relations to Other Models and Measures in DEA,”
*Journal of Productivity Analysis* 11(1), 5--42,
[DOI 10.1023/A:1007701304281](https://doi.org/10.1023/A:1007701304281).
The equation audit used the
[complete copy uploaded by coauthor Jesús T. Pastor](https://www.researchgate.net/publication/226323590_RAM_A_Range_Adjusted_Measure_of_Inefficiency_for_Use_with_Additive_Models_and_Relations_to_Other_Models_and_Measures_in_DEA).

RAM is the source's named normalization of a VRS additive operating
account. It is not an input-radial or output-radial model, and it is not a
monetary cost, revenue, profit, or welfare measure.

## Primary-source claim locators

| Source location | Claim frozen here |
|---|---|
| Section 8 opening | Negative inputs or outputs motivate a translation-invariant measure |
| Eq. (17) and Theorem 4 | The convexity identity $\sum_j\lambda_j=1$ supplies translation invariance |
| Eqs. (18.1)--(18.2) | Input excesses and desirable-output shortfalls enter one additive VRS account |
| Eq. (19) | Common coordinate translations leave the physical slacks unchanged |
| Eq. (20) | Each weight denominator is the observed maximum-minus-minimum range of that coordinate |
| Eq. (21) | The ranges are themselves translation invariant |
| Eq. (22) | RAM inefficiency is the equal mean of range-normalized optimal slacks |
| Eq. (23) | RAM efficiency is one minus RAM inefficiency |
| Eq. (24) and following discussion | Every normalized slack lies between zero and one under the self-inclusive VRS sample |
| Section 8, zero-range paragraph | A coordinate with zero observed range may be omitted and its associated slack is set to zero in the objective |
| Section 8, after Eq. (22) | Zero inefficiency is equivalent to all slacks being zero; the measure is unit invariant and presented as strongly monotonic |

## Source-qualified operating account

For organization $o$, let $x_o\in\mathbb R^m$ denote controllable
resources and $y_o\in\mathbb R^s$ desirable services. Quantities may be
signed. Each coordinate has a finite nonnegative range in the one
comparison population:

$$
R_i^x=\max_j x_{ij}-\min_j x_{ij}\geq0,
\qquad
R_r^y=\max_j y_{rj}-\min_j y_{rj}\geq0.
$$

For positive ranges, the source programme is

$$
\begin{aligned}
\max_{\lambda,s^-,s^+}\quad
&\delta_o^{RAM}
=
\frac{1}{m+s}
\left(
\sum_{i=1}^{m}\frac{s_i^-}{R_i^x}
+
\sum_{r=1}^{s}\frac{s_r^+}{R_r^y}
\right)\\
\text{s.t.}\quad
&X\lambda+s^-=x_o,\\
&Y\lambda-s^+=y_o,\\
&\mathbf1^\top\lambda=1,\\
&\lambda,s^-,s^+\geq0.
\end{aligned}
$$

The reported efficiency is

$$
\rho_o^{RAM}=1-\delta_o^{RAM}.
$$

The source also addresses a zero observed range: the associated coordinate
constraint may be omitted and its slack is set to zero in the objective.
DEAPack represents the same rule with a zero objective weight while
retaining the balance. When the range population and self-inclusive VRS
reference population are identical, every reference plan has the same
constant coordinate value, so the retained balance forces that slack to
zero. This is an algebraically equivalent implementation of the source rule,
not a package extension.

Higher $\rho_o^{RAM}$ is better and one denotes absence of every resource
excess and desirable-service shortfall recognized by the maintained VRS
technology. The companion $\delta_o^{RAM}$ is lower-is-better. Because the
evaluated organization remains eligible to benchmark itself, its own plan
is always feasible; because a VRS benchmark is a convex combination of
observed plans, each slack cannot exceed the corresponding full-sample
range. Hence both quantities lie in $[0,1]$ on the certified domain.

Economically, RAM gives every organization the same sample-defined ruler
for a given resource or service. A normalized input slack of $0.2$ says
that the benchmark releases one fifth of the full observed variation in
that resource. It does not say that expenditure falls by 20 percent. An
output term of $0.2$ says that the service shortfall is one fifth of that
service's observed range, not that revenue rises by 20 percent. Averaging
these accounts creates a dimensionless technical-and-mix performance
summary; it does not reveal prices, social values, causal effects, or
engineering limits outside the sample.

Multiplying one coordinate by a positive unit-conversion factor multiplies
its slack and range by the same factor. Adding a common constant to one
coordinate changes neither its range nor, under the VRS identity, its
feasible slacks. Those are the source reasons for unit and translation
invariance and for admitting signed observations.

## Independent exact four-DMU certificate

The analytical fixture used only for verification is:

| DMU | $x_1$ | $x_2$ | $y$ |
|---|---:|---:|---:|
| A | 7 | 8 | 20 |
| B | 1 | 2 | 5 |
| C | $3/2$ | $3/2$ | 1 |
| D | 10 | 10 | 1 |

Its ranges are

$$
R_1^x=9,\qquad R_2^x=\frac{17}{2},\qquad R^y=19.
$$

For focal D, every pure reference plan is feasible. The RAM distances
obtained from the four pure plans are:

| Reference plan | Input slacks | Output slack | RAM distance |
|---|---:|---:|---:|
| A | $(3,2)$ | $19$ | $80/153$ |
| B | $(9,8)$ | $4$ | $695/969$ |
| C | $(17/2,17/2)$ | $0$ | $35/54$ |
| D | $(0,0)$ | $0$ | $0$ |

After eliminating the slacks, the objective is linear in $\lambda$. Every
feasible VRS plan for D is a convex combination of the four rows above, so
its objective is the same convex combination of these four displayed
values. The largest value is attained uniquely by B. This proves, rather
than merely proposes, the upper bound:

$$
\delta_D^{RAM}=\frac{695}{969},
\qquad
\rho_D^{RAM}=\frac{274}{969},
$$

with target $(1,2;5)$, input slacks $(9,8)$, output slack $4$, and
$\lambda_B=1$. A, B, and C are strongly efficient: A alone can preserve
service 20, B alone can operate with $x_1\leq1$, and C alone can operate
with $x_2\leq3/2$. Thus the complete exact efficiency vector is

$$
\left(1,1,1,\frac{274}{969}\right).
$$

`tests/test_ram_source_oracle.py` compiles
$[\lambda,s^-,s^+]$ directly with dense NumPy matrices and
`scipy.optimize.linprog`. It imports no DEAPack production builder,
reference compiler, RTS helper, or internal RAM weight generator. It also
checks the exact unique target and peer, signed translations, positive unit
changes, source-profile metadata, and fail-closed postsolve behavior.
These are analytically derived results, not a claim that the 1999 article
printed this fixture.

## Evidence and interpretation boundary

The source-qualified runtime profile covers all and only:

- one cross section and one complete self-inclusive comparison population;
- the VRS convexity identity;
- finite signed resources and desirable services;
- the source zero-range rule: omit the inactive coordinate and set its slack
  contribution to zero, implemented equivalently by DEAPack as a zero
  objective weight plus the matched-population VRS balance;
- ordinary input and desirable-output disposal represented by the additive
  balances;
- equal influence for all $m+s$ range-normalized slack accounts;
- RAM distance, one-minus-distance efficiency, strong status, physical
  slacks, one solver-selected optimal target, and its peer intensities; and
- the independent exact fixture above.

The following remain transparent package behavior or
`deferred_to_next_version` and do not inherit the source-profile label:

- a panel pooled across periods, even when the analyst explicitly requests
  one global range and frontier;
- contemporaneous, sequential, biennial, rolling-window, external, or
  custom comparison populations;
- CRS, NIRS, NDRS, scale decomposition, super-efficiency, minimum-distance,
  closest-target, or alternate-target RAM;
- undesirable outputs, weak disposal, by-production, material balance,
  networks, dynamic links, nondiscretionary variables, integer targets,
  assurance regions, or price restrictions; and
- cost saving, revenue gain, profitability, welfare, causal, engineering,
  or statistical-inference claims.

RAM's common ruler is sample dependent. Changing the organizations in the
comparison may change both the frontier and every coordinate range. A
[subsequent comment by Steinmann and Zweifel (2001)](https://doi.org/10.1023/A:1007830622664)
challenged some maintained properties and raised a size-related ranking
concern; the original authors published a
[response](https://doi.org/10.1023/A:1007882606735).
DEAPack therefore presents RAM as a transparent sample-relative operating
account, not as an unquestionable cardinal measure of economic performance.
