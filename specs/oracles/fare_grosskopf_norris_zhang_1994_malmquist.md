# Färe--Grosskopf--Norris--Zhang Malmquist: independent analytical oracle

**Method ID:** `productivity.malmquist.adjacent_geometric`  
**Preset ID:** `productivity.malmquist.decomposition.fgnz_core`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This certificate validates the existing output-oriented CRS adjacent
Malmquist core with an exact synthetic fixture and an independently compiled
dense LP. It does not reproduce the 17-country empirical results in Färe,
Grosskopf, Norris, and Zhang (1994), and it makes no claim about their
enhanced `PEFFCH × SCH` decomposition.

## Primary-source boundary

[Färe et al. (1994)](https://doi.org/10.2307/2117971) define the output
distance in equation (2) on page 69, the geometric Malmquist index in
equation (6) on page 70, and its efficiency-change times technical-change
rearrangement in equation (7) on page 71. Their CRS, strongly disposable
activity technology appears in equation (14) on page 73. Pages 74--75 state
the unit-invariance property and identify the four required distance tasks;
equations (16) and (17) on page 75 give the within-period and mixed-period
output LPs. The present oracle transcribes that four-task CRS core into its
own dense matrices.

The source also discusses an enhanced decomposition on pages 74--75. That
extension needs two VRS programmes and splits CRS efficiency change into pure
efficiency change and scale change. It is outside this certificate: no
`PEFFCH`, `SCH`, or six-programme claim is made here. Those claims are checked
independently in
[`fare_etal_1994_enhanced_fgnz.md`](fare_etal_1994_enhanced_fgnz.md).

## Economic account and four task roles

Let $D_o^r(x^q,y^q)$ be the output distance of an observation from period
$q$, evaluated against the production opportunities represented in period
$r$. For an activity feasible in the reference technology, the distance is
at most one; a smaller positive value means that more proportional output
expansion remains available. A cross-period distance may exceed one when the
evaluated activity is outside the other period's represented technology.

DEAPack's four diagnostic roles have the following source-level meanings:

| Diagnostic role | Distance |
|---|---|
| `base_on_base` | $D_o^0(x^0,y^0)$ |
| `comparison_on_base` | $D_o^0(x^1,y^1)$ |
| `base_on_comparison` | $D_o^1(x^0,y^0)$ |
| `comparison_on_comparison` | $D_o^1(x^1,y^1)$ |

For those four positive distances, the certified account is

$$
M_o =
\left[
\frac{D_o^0(x^1,y^1)}{D_o^0(x^0,y^0)}
\times
\frac{D_o^1(x^1,y^1)}{D_o^1(x^0,y^0)}
\right]^{1/2},
$$

$$
EC =
\frac{D_o^1(x^1,y^1)}{D_o^0(x^0,y^0)},
\qquad
TC =
\left[
\frac{D_o^0(x^1,y^1)}{D_o^1(x^1,y^1)}
\times
\frac{D_o^0(x^0,y^0)}{D_o^1(x^0,y^0)}
\right]^{1/2},
$$

so $M_o=EC\times TC$. `EC` records change in performance relative to each
period's represented best practice. `TC` records the reference-conditional
change in represented production opportunities. Neither component, by
itself, identifies a management intervention or an invention.

## Exact two-period fixture

The fixture has two organizations, two inputs, and two desirable outputs:

| Organization | Period | Staff | Capital | Service | Quality |
|---|---:|---:|---:|---:|---:|
| A | 0 | 2 | 6 | 2 | 2 |
| B | 0 | 1 | 3 | 2 | 2 |
| A | 1 | 4 | 12 | 9 | 9 |
| B | 1 | 2 | 6 | 6 | 6 |

Capital is three times staff and quality equals service in every row, so the
two input constraints and two output constraints each reduce to a common
resource or service bundle without changing the LP. In period 0 every
observation satisfies
$y\leq2x$, and B attains equality. In period 1 every observation satisfies
$y\leq3x$, and B again attains equality.

For period-$r$ frontier slope $a_r$, any CRS reference activity satisfies
$Y^r\lambda\leq a_rX^r\lambda$. The input commitment
$X^r\lambda\leq x_o$ and output requirement
$\phi y_o\leq Y^r\lambda$ therefore imply
$\phi\leq a_rx_o/y_o$, or

$$
D_o^r(x_o,y_o)\geq\frac{y_o}{a_rx_o}.
$$

Using B alone with intensity $x_o/x_B^r$ attains the bound. Because B is
the only activity attaining the maximum bundle productivity in each period,
that reference intensity is also unique. The exact distances and components
are:

| Organization | $D^0(z^0)$ | $D^0(z^1)$ | $D^1(z^0)$ | $D^1(z^1)$ | $M$ | $EC$ | $TC$ |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | $1/2$ | $9/8$ | $1/3$ | $3/4$ | $9/4$ | $3/2$ | $3/2$ |
| B | $1$ | $3/2$ | $2/3$ | $1$ | $3/2$ | $1$ | $3/2$ |

Every task uses B as its sole positive-intensity peer. In diagnostic-role
order, A's exact intensities are $(2,4,1,2)$, while B's are
$(1,2,1/2,1)$. The reference period is 0 for the first two roles and 1 for
the last two.

## Independent executable compiler

`tests/test_malmquist_independent_oracle.py` builds ordinary dense NumPy
matrices and calls `scipy.optimize.linprog` directly. For each evaluated
activity and reference period it solves

$$
\max_{\phi,\lambda\geq0}\ \phi
\quad\text{such that}\quad
X^r\lambda\leq x^q,\qquad
Y^r\lambda\geq\phi y^q.
$$

It neither imports nor calls DEAPack's production reference compiler,
returns-to-scale matrix builder, distance-problem builder, or task cache.
The dense cross-check uses the same SciPy/HiGHS optimizer family as the
default package backend, so it is an independent formulation check rather
than an independent-solver reproduction.

The executable checks:

1. recover all eight exact distances and both exact $M$, $EC$, and $TC$
   vectors through the independent compiler and public
   `FGNZMalmquistProductivityIndex` preset API;
2. recover each diagnostic task's evaluated/reference period, reciprocal
   radial factor, unique peer, reference period, and exact intensity;
3. rescale the two input and two output columns by four different positive
   constants and verify that every distance and component is unchanged;
4. use a three-period extension to show that 16 requested adjacent-role
   evaluations require 14 unique solves: each middle-period organization's
   own-period task is shared by its incoming and outgoing transition; and
5. construct an exact absent-output boundary in which the largest feasible
   cross-period radial factor is $\phi^*=0$, so its reciprocal output
   distance has no finite positive value, then verify that the package
   reports the responsible task and refuses to form a multiplicative
   productivity index.

## Claim boundary

| Claim | Evidence | Certified scope |
|---|---|---|
| four-distance transcription | analytical bounds, attaining plans, and independent dense LP compilation | output orientation, CRS, strong disposability, two periods, two organizations, two inputs, and two desirable outputs |
| adjacent geometric account | exact $M$, $EC$, $TC$, and zero reconstruction residual | the equation-(7) two-component identity only |
| task and peer semantics | unique analytical reference plans checked against diagnostics and public peers | four named roles and their evaluated/reference periods on the exact fixture |
| unit invariance | independent and public reruns after four column-specific positive rescalings | the exact fixture's distances, index, and two components |
| execution accounting | counting wrapper around the public solver plus result metadata | a three-period, two-organization extension; 16 requested role evaluations and 14 unique solves |
| undefined-distance failure | analytical zero radial factor plus independent dense LP | one absent-output mixed-period task; no finite positive distance, index, or component is reported |

This certificate does **not** extend to:

- input orientation, VRS, NIRS, NDRS, or an orientation-equivalence claim;
- the enhanced `TECHCH × PEFFCH × SCH` decomposition, Ray--Desli, Balk, or
  any other scale/mix decomposition;
- global, biennial, sequential, window, environmental, or non-radial
  productivity operators;
- unbalanced-panel matching, non-adjacent comparisons, custom reference
  populations, or alternative estimator families;
- dual multipliers, slack completion, counterfactual targets, or sampling
  inference; or
- reproduction of Färe et al.'s OECD data, preprocessing, published country
  table, or an independent software implementation.
