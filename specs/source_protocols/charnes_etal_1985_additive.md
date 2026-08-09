# Charnes et al. (1985) direct additive DEA source protocol

## Readiness record

| Field | State |
|---|---|
| Public method identity | `static.additive` |
| Source-qualified runtime profile | `charnes_etal_1985_eq_4_6` |
| Primary source | complete first-hand article obtained and equation-checked |
| Independent exact evidence | closed for VRS, unit weights, a self-inclusive cross-section, and ordinary inputs/desirable outputs |
| Published numerical reproduction | not claimed |
| Configurable package extensions | positive fixed slack weights, CRS/NIRS/NDRS, and non-source reference policies |
| Deferred source identities | equation (5.7) observation-specific normalization and any separately named weighted/RTS/temporal literature leaf |
| Last source audit | 2026-07-31 |

The defining source is A. Charnes, W. W. Cooper, B. Golany, L. Seiford, and
J. Stutz (1985), “Foundations of Data Envelopment Analysis for
Pareto-Koopmans Efficient Empirical Production Functions,” *Journal of
Econometrics* 30(1--2), 91--107,
[DOI 10.1016/0304-4076(85)90133-2](https://doi.org/10.1016/0304-4076(85)90133-2).
The equation audit used the
[Carnegie Mellon University archival scan](https://iiif.library.cmu.edu/file/Cooper_box00028_fld00020_bdl0001_doc0001/Cooper_box00028_fld00020_bdl0001_doc0001.pdf).

This protocol prevents one familiar name from lending its provenance to every
configuration accepted by a reusable solver. The current analytical
certificate covers the article's direct VRS unit-weight programme. Other
settings can remain transparent DEAPack sensitivity configurations, but they
do not inherit the 1985 historical identity or certificate.

## Primary-source claim locators

| Source location | Claim frozen here |
|---|---|
| Eq. (4.4) | An improvement weakly reduces every input and weakly increases every desirable output |
| Eqs. (4.5)--(4.6) | The direct empirical test uses a convexity equation, ordinary nonnegative slacks, and their unit sum |
| Text following Eq. (4.6) | The optimum is zero if and only if the evaluated observation is Pareto--Koopmans efficient |
| Eq. (5.6) | A direct additive projection replaces observed inputs by $x_o-s^{-*}$ and outputs by $y_o+s^{+*}$ |
| Eq. (5.7) | The article's unit-normalized functional divides each slack by the corresponding positive quantity of the evaluated observation |
| Two-DMU example preceding Eq. (5.6) | The displayed quantities are $(1,2;1)$ and $(1,4;1)$ and diagnose the second unit's unrevealed input excess |

The paper says that other empirical-set variations can be represented by
changing constraints on the intensity vector. That general observation is
not an equation-level source freeze for every modern CRS, NIRS, NDRS,
panel, window, custom-reference, or weighted-additive recipe.

## Source-qualified economic account

Let $x_o\in\mathbb R_+^m$ be the resources used by organization $o$ and
$y_o\in\mathbb R_+^s$ its desirable services or products. Let the columns of
$X$ and $Y$ be the complete comparison sample. The article's equation (4.6)
is equivalently

$$
\begin{aligned}
\max_{\lambda,s^-,s^+}\quad
&\mathbf 1^\top s^-+\mathbf 1^\top s^+\\
\text{s.t.}\quad
&X\lambda+s^-=x_o,\\
&Y\lambda-s^+=y_o,\\
&\mathbf 1^\top\lambda=1,\\
&\lambda,s^-,s^+\geq0.
\end{aligned}
$$

The convexity equation is part of the frozen source profile. Economically,
$s_i^-$ is an amount of resource $i$ that the represented comparison plan
does not need, and $s_r^+$ is additional desirable service $r$ represented
by that plan. The model evaluates both kinds of operating shortfall at once;
it is not input-oriented or output-oriented.

The unit sum

$$
\delta_o=\mathbf 1^\top s^{-*}+\mathbf 1^\top s^{+*}
$$

has zero as its best value. Under this source profile,
$\delta_o=0$ if and only if no represented comparison plan can improve at
least one ordinary resource or desirable service without worsening another.
A positive value diagnoses a Pareto--Koopmans inefficient observation.

The selected operating target is

$$
\widehat x_o=x_o-s^{-*}=X\lambda^*,
\qquad
\widehat y_o=y_o+s^{+*}=Y\lambda^*.
$$

Strictly positive slack weights preserve the strong-target argument as a
mathematical package extension, but different weights can select different
targets and peers. The 1985 unit-weight certificate therefore does not imply
that a target is unique, closest, least costly, preferred by management, or
causally attainable.

## Equation (5.7) is not arbitrary fixed user weighting

The article later proposes a different functional proportional to

$$
\sum_i\frac{s_i^-}{x_{io}}
+
\sum_r\frac{s_r^+}{y_{ro}},
$$

for positive observed coordinates. Its weights change with the evaluated
observation. The article suggests a factor $10/(m+s)$ and a logarithmic
“efficiency pH” interpretation.

`AdditiveDEA(input_weights=..., output_weights=...)` currently applies one
declared weight vector to the fitted comparison exercise. That general
configuration is useful for unit conversions, engineering coefficients, or
declared priorities, but it must not be described as equation (5.7).
A future observation-specific equation-(5.7) profile requires its own result
scale, positivity boundary, runtime API, and independent oracle. It is
`deferred_to_next_version` rather than inferred from the generic weight
arguments.

## Source-displayed two-DMU reconstruction

The article displays:

| DMU | $x_1$ | $x_2$ | $y$ |
|---|---:|---:|---:|
| A | 1 | 2 | 1 |
| B | 1 | 4 | 1 |

For B, let $\lambda_A=a$ and $\lambda_B=1-a$. The represented plan uses
$4-2a$ units of the second input and leaves every other account unchanged.
Its only positive slack is therefore

$$
s_2^-=4-(4-2a)=2a.
$$

Because $0\leq a\leq1$, the unit slack sum is at most two and is attained at
$a=1$. Hence B's exact additive result is

$$
\delta_B=2,\qquad
s_B^-=(0,2),\qquad
s_B^+=0,\qquad
(\widehat x_B,\widehat y_B)=(1,2;1).
$$

The article prints the data and explains the second unit's inefficiency, but
does not print this additive score, intensity, or target as a numerical
result table. DEAPack therefore calls this a source-displayed fixture
reconstruction, not a published numerical reproduction.

## Current evidence boundary

The current certificate covers all and only:

- VRS with $\mathbf 1^\top\lambda=1$;
- effective unit input and output slack weights, whether selected by the
  defaults or declared explicitly as all ones;
- one self-inclusive cross-section resolved to the complete global sample;
- finite nonnegative ordinary inputs and desirable outputs, with positive
  input and output aggregates for every observation;
- the direct additive score, physical slacks, target, peer intensity, and
  tolerance-aware strong-efficiency status; and
- one independent dense compiler that imports no DEAPack model, reference,
  RTS, LP-builder, or solver wrapper.

The following do not inherit this source certificate:

- arbitrary fixed positive non-unit user weights, whether supplied through
  `AdditiveDEA` or its `WeightedAdditiveDEA` discoverability alias;
- CRS, NIRS, or NDRS;
- panels and contemporaneous, sequential, biennial, window, custom, external,
  or leave-one-out reference policies;
- negative data, undesirable outputs, nondiscretionary quantities, network
  accounts, integer technologies, or statistical inference;
- equation (5.7)'s observation-specific normalization;
- target or peer uniqueness, minimum disruption, cost/profit optimality,
  preference, causality, or implementation feasibility; and
- a published numerical-table reproduction.

If one of those configurations is later given a separate historical name or
method identity, it must pass its own primary-source and independent-oracle
gate. If the required literature cannot be obtained, its release disposition
is `deferred_to_next_version`; the current version does not guess.
