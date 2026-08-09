# Chung--Färe--Grosskopf environmental output DDF: analytical oracle

**Method ID:** `environmental.ddf.output.chung_fare_grosskopf_1997`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This certificate validates the source-qualified, fixed-input,
constant-returns-to-scale environmental output directional distance function
exposed as `ChungFareGrosskopfDDF`. It combines a small exact synthetic
example with linear programmes compiled directly in the test module. The
numbers below are not transcribed from the Swedish pulp-and-paper application,
and no published numerical reproduction is claimed.

## Source-edition note

The [1997 journal article](https://doi.org/10.1006/jema.1997.0146) defines an
output set $P(x)$, holds $x$ as the resource commitment, and selects the
signed output direction $g=(y,-b)$: desirable output increases while the
undesirable residual decreases. Its printed equation (3.14), however, places
$(1-\beta)x$ on the right-hand side of the input constraint. That term
would contract inputs even though the defining set and direction hold them
fixed.

Chung and Färe's [1995 working-paper version, equation
(2.14)](https://econwpa.ub.uni-muenchen.de/econ-wp/mic/papers/9511/9511002.pdf)
prints the input restriction as $X\lambda\leq x$. It is consistent with
the output-set definition, the chosen $g=(y,-b)$, and the surrounding
economic interpretation. This certificate therefore tests the fixed-input
programme. The note records an internal edition inconsistency; it does not
claim that a formal publisher erratum was issued.

## The operating question

For organization $o$, let $x_o$ denote resources, $y_o$ desirable
services, and $b_o$ undesirable residuals. The score asks:

> With the observed resources held available, by what common proportion can
> services rise and residuals fall before the plan reaches what the reference
> organizations have demonstrated?

Under the Chung--Färe--Grosskopf common-factor CRS technology, the answer is

$$
\begin{aligned}
\max_{\lambda,\beta}\quad &\beta\\
\text{s.t.}\quad
&X\lambda\leq x_o,\\
&Y\lambda\geq(1+\beta)y_o,\\
&B\lambda=(1-\beta)b_o,\\
&\lambda\geq0.
\end{aligned}
$$

There is no intensity-sum equation: nonnegative intensities define the CRS
technology. Equality in the bad-output account and CRS scaling implement the
common proportional weak-disposal construction. Null jointness remains a
separate data requirement.

For a self-inclusive feasible organization, $\beta\geq0$. A positive value
is a joint operating-and-environmental improvement opportunity. For example,
$\beta=0.2$ means a feasible benchmark combines 20% more desirable output
with 20% less undesirable output, relative to the assessed organization's
observed output levels. The package's bounded convenience report is
$1/(1+\beta)$ only on this nonnegative domain.

An external or cross-period reference need not contain the assessed plan.
Then $\beta<0$ can be economically meaningful: the selected reference
technology cannot reproduce the assessed combination of high desirable
output and low pollution without giving back some service and accepting more
residual. It is neither a negative efficiency nor a data-error code, so
DEAPack retains the distance and leaves the convenience efficiency and
efficiency flags missing.

## Exact two-organization account

The deterministic teaching fixture contains one resource, one desirable
service, and one undesirable residual:

| Organization | Resource $x$ | Service $y$ | Residual $b$ |
|---|---:|---:|---:|
| Old | 1 | 1 | 2 |
| New | 1 | 2 | 1 |

Write $a$ and $n$ for the CRS intensities on Old and New.

### Old assessed against the pooled reference

For Old, the bad-output equality gives

$$
2a+n=2(1-\beta),
\qquad
\beta=1-a-\frac{n}{2}.
$$

The desirable-output requirement becomes

$$
a+2n\geq1+\beta
\quad\Longleftrightarrow\quad
2a+\frac{5}{2}n\geq2.
$$

Maximizing $\beta$ means meeting this service requirement with the smallest
$a+n/2$. New supplies more service per unit of that account, so the bound is
attained by $a=0$, $n=4/5$. The resource restriction is satisfied because
$a+n=4/5\leq1$. Hence

$$
\beta_{\mathrm{Old}}=\frac35.
$$

The demonstrated management target uses $4/5$ of the resource to supply
$8/5$ units of service and $4/5$ units of residual. The unused-resource
slack is $1/5$.

### New assessed against the pooled reference

For New,

$$
2a+n=1-\beta,
\qquad
\beta=1-2a-n,
$$

and the service account reduces to

$$
5a+4n\geq4.
$$

The least costly way to meet this condition in the score account is
$a=0,n=1$, the organization's own observed plan. Therefore

$$
\beta_{\mathrm{New}}=0.
$$

The exact pooled score vector in the order (Old, New) is

$$
\left(\frac35,\;0\right).
$$

### New assessed against Old only

Now remove New from the eligible reference set. With only intensity $a$ on
Old, the bad-output account gives

$$
2a=1-\beta,
\qquad
a=\frac{1-\beta}{2}.
$$

The service requirement is

$$
a\geq2(1+\beta).
$$

Combining the two accounts yields $\beta\leq-3/5$. Equality is feasible at
$a=4/5$, so

$$
\beta_{\mathrm{New}\mid\mathrm{Old}}=-\frac35.
$$

In management terms, the old-only technology can match the newer
organization only at a comparison target with $4/5$ unit of service and
$8/5$ units of residual, while using $4/5$ of the resource. The negative
distance records that technological mismatch; it is not transformed into an
efficiency score. Old remains at zero against its own reference, giving the
external-reference vector

$$
\left(0,\;-\frac35\right).
$$

## Independent compilation

`tests/test_cfg_environmental_ddf_independent_oracle.py` builds dense
`scipy.optimize.linprog` arrays directly from the fixture. For every assessed
organization it creates:

- input inequalities $X\lambda\leq x_o$;
- desirable-output inequalities
  $-Y\lambda+\beta y_o\leq-y_o$;
- bad-output equalities $B\lambda+\beta b_o=b_o$; and
- nonnegative intensity bounds with an unrestricted $\beta$.

The test does not call the environmental production compiler, reference
compiler, RTS helpers, or a production fit routine to construct these LPs.
It uses SciPy/HiGHS, as does the default package configuration, so this is
independent problem compilation rather than an independent-solver
reproduction.

The public checks cover:

1. the exact pooled scores $(3/5,0)$, bounded nonnegative-domain reports,
   management targets, slack account, and source-preset identity;
2. the exact old-only score vector $(0,-3/5)$, its targets, and missing
   efficiency claims for the negative external comparison;
3. explicit infeasibility, rather than clipping to zero, when the same
   old-only comparison disallows negative distance;
4. equality of full and score-only public runs with the independently
   compiled dense programmes for both reference policies;
5. actual phase-one, phase-two, total-solve, and reference-compilation
   accounting; and
6. score and normalized slack-completion invariance when resource, service,
   and residual units are independently rescaled.

## Claim boundary

| Claim | Evidence | Scope |
|---|---|---|
| fixed-input CFG score | exact inequalities plus attaining intensity plans | one positive one-input, one-good-output, one-bad-output synthetic fixture under CRS common-factor weak disposal |
| independent LP compilation | separately constructed dense SciPy/HiGHS programmes | pooled self-inclusive and old-only custom references; $\beta$, solver status, and execution accounting |
| negative distance semantics | exact old-only comparison | raw $\beta=-3/5$, target accounts, and missing convenience efficiency/status claims |
| unit invariance | independent positive rescaling of all three data roles | observed good/bad direction, score, and row-scaled slack completion on this fixture |

This certificate does **not** extend to:

- a reproduction of the article's confidential Swedish mill observations or
  published productivity table; that evidence has not been located and is
  deferred to a later version;
- the journal equation (3.14) input-contraction term, which is outside the
  fixed-input output-direction formulation justified above;
- VRS activity-specific weak disposal, strong bad-output disposal, or the
  legacy unidentified directional-equality spelling;
- arbitrary user-supplied directions, multiple dimensions, zero or signed
  data, or non-CRS technologies;
- the four-distance Malmquist--Luenberger productivity operator, a global
  Malmquist--Luenberger index, or any claim that changing one reference
  option alone constructs either index;
- unique peers or slack allocations beyond this nondegenerate fixture; or
- dual values, shadow prices, sampling inference, uncertainty
  quantification, or causal and cost interpretations.
