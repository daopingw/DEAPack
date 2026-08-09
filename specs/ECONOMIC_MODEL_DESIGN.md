# Economic DEA model design contract

This document is normative for the first price-informed DEAPack models. It
defines the data, optimization, result, decomposition, and validation
contracts for cost, revenue, profit, Nerlovian, and profitability analysis.
The families remain distinct even when they reuse one linear-program compiler.

The primary theoretical references are
[Shephard](https://doi.org/10.1007/978-3-642-51578-1),
[Färe and Primont](https://doi.org/10.1007/978-94-011-0651-1),
[Chambers, Chung, and Färe](https://doi.org/10.1023/A:1022637501082),
[Färe, Grosskopf, and Zaim](https://doi.org/10.1016/S0377-2217(01)00022-4),
and
[Zofío and Prieto](https://doi.org/10.1007/s10108-006-9004-0).

## 1. Economic quantities and maintained technology

For observation $o$, let $x_o\in\mathbb{R}_+^m$ and
$y_o\in\mathbb{R}_+^s$, with input prices $w_o$ and output prices $p_o$.
The supplied-price quantities are

$$
C_o=w_o^\top x_o,\qquad R_o=p_o^\top y_o,\qquad
\Pi_o=R_o-C_o,\qquad \rho_o^{RTD}=R_o/C_o.
$$

All optimal values use the declared empirical technology, reference policy,
and returns-to-scale assumption. Market or administered prices are
valuations supplied by the user. Solver marginals are model-derived shadow
values and must never overwrite or be labeled as supplied prices.

The initial implementation supports ordinary nonnegative inputs and desirable
outputs, with at least one strictly positive input and desirable output for
each evaluated observation. Signed netputs, undesirable outcomes, incomplete prices, price
uncertainty, endogenous prices, and market power require separately registered
extensions.

## 2. Price data contract

Prices are valuation data, not DEA inputs or outputs. They therefore use an
immutable `PriceData` object separate from `DEAData`.

### 2.1 `PriceSpec`

`PriceSpec` records:

- `scope`: `common` or `by_observation`;
- `source`: `market`, `administered`, `accounting`, or another registered
  source;
- `currency`, `numeraire`, and optional `base_period`;
- `missing_policy`, initially fixed to `raise`;
- `sign_policy`, initially fixed to `strictly_positive`;
- denominator and monetary comparison tolerances.

Currency and base-period metadata are required for panel comparisons of
monetary values. DEAPack does not silently deflate, convert, or impute prices.

### 2.2 `PriceData`

`PriceData` must:

- map each price to an existing quantity variable by exact variable name;
- reject missing, extra, duplicate, nonfinite, zero, or negative prices in the
  initial implementation;
- align observation-specific prices by `(dmu_id, period)`, never row position;
- resolve common prices to read-only arrays of shape `(n, m)` and `(n, s)`
  without changing their declared scope;
- support input-only, output-only, or joint prices according to the requested
  economic model;
- expose a stable numerical signature for registry and cache metadata without
  storing confidential price payloads there.

Recommended constructors are:

- `PriceData.common(input_prices=..., output_prices=..., spec=...)`;
- `PriceData.from_frame(..., input_prices={quantity: price_column},
  output_prices={quantity: price_column}, dmu=..., period=..., spec=...)`.

`fit(data, prices)` must fail before optimization when names, observation
keys, periods, or required price sides do not match.

## 3. Method-specific optimization and results

Let $X$ and $Y$ denote one compiled reference set. The notation
$\lambda\in\Lambda_{\mathrm{RTS}}$ includes nonnegativity and the declared
RTS restriction.

### 3.1 Cost

$$
C_o^*=\min_{\lambda\in\Lambda_{\mathrm{RTS}}}
       w_o^\top X\lambda
\quad\text{s.t.}\quad Y\lambda\ge y_o .
$$

Cost analysis holds the observed output commitment and chooses a
cost-minimizing input plan. Its result must include:

- `observed_cost`, `minimum_cost`, and
  `cost_gap = observed_cost - minimum_cost`;
- `cost_efficiency = minimum_cost / observed_cost`;
- activity inputs $X\lambda^*$, reference intensities, and the maintained
  output commitment;
- solver status, residuals, and output-commitment marginals.

The public `score` and `efficiency` are `cost_efficiency`; higher is better.

### 3.2 Revenue

$$
R_o^*=\max_{\lambda\in\Lambda_{\mathrm{RTS}}}
       p_o^\top Y\lambda
\quad\text{s.t.}\quad X\lambda\le x_o .
$$

Revenue analysis holds available inputs and chooses a revenue-maximizing
output plan. Its result must include:

- `observed_revenue`, `maximum_revenue`, and
  `revenue_gap = maximum_revenue - observed_revenue`;
- source-native `revenue_expansion_ratio =
  maximum_revenue / observed_revenue`;
- canonical `revenue_efficiency =
  observed_revenue / maximum_revenue`;
- activity outputs $Y\lambda^*$, input use $X\lambda^*$, reference
  intensities, and input-capacity marginals.

The public `score` and `efficiency` are `revenue_efficiency`; higher is
better. The reciprocal expansion ratio is retained because the literature
uses both conventions.

### 3.3 Profit

$$
\Pi_o^*=\max_{\lambda\in\Lambda_{\mathrm{RTS}}}
        \left(p_o^\top Y\lambda-w_o^\top X\lambda\right).
$$

Profit analysis allows both inputs and outputs to change. Its result must
include:

- `observed_profit`, `maximum_profit`, and
  `profit_gap = maximum_profit - observed_profit`;
- the complete optimal activity plan and reference intensities;
- the finite-profit and shutdown-option policies.

Negative observed or maximum profit is valid. No generic
`observed_profit / maximum_profit` score is reported because it is undefined
or order-reversing at zero and negative values. Under certified membership
the public `score` is the nonnegative `profit_gap`,
`score_direction` is `lower_is_better`, and the generic `efficiency` field is
missing. An external-reference raw gap is retained, including a negative
value, but the score fails closed until membership is certified.

The public leaf is `economic.profit.maximum`. `economic.profit` is a
non-executable discovery family because the common maximum-profit numerator
also feeds several non-equivalent decompositions.

### 3.4 Nerlovian profit inefficiency

For the directional convention
$(x_o-\beta g_o^x,y_o+\beta g_o^y)$, define

$$
\nu_o=w_o^\top g_o^x+p_o^\top g_o^y>0,\qquad
NI_o=\frac{\Pi_o^*-\Pi_o}{\nu_o}.
$$

Nerlovian analysis composes the profit optimizer with a DDF fitted under the
same technology, RTS, reference, data, and direction. It must report:

- the raw profit gap and `direction_value = nu_o`;
- `nerlovian_inefficiency = NI_o`;
- DDF `technical_inefficiency = beta`;
- `allocative_inefficiency = NI_o - beta`;
- the DDF target and the profit-maximizing target as distinct plans.

The public `score` and `distance` are $NI_o$; lower is better. No arbitrary
$1/(1+NI_o)$ efficiency transformation is part of this method.

At least one direction component must be positive and $\nu_o$ must exceed the
declared denominator tolerance. Observation-specific directions or
normalizers must be marked as not directly comparable across observations
unless a common economic unit is established.

The first public leaf is `economic.nerlovian.ccf1998`. Its DDF phase-one
optimum supplies the technical component even when the optional slack
completion fails; in that case Pareto--Koopmans status is missing and the
result records that residual slacks were not certified. Profit-maximizing,
direct directional, and slack-completed plans have distinct `target_kind`
values.

The decomposition release gate consumes the explicit validity of both source
programmes. A backend `optimal` label is insufficient: the profit LP and price
account must certify, the DDF LP and directional production account must
certify, and the observation must be certified inside the matched reference
technology. A failure in either source withholds the Nerlovian headline and
both decomposition components for that observation. Optional DDF completion
failure may leave the already certified phase-one technical component intact,
but it withholds completion targets, slacks, peers, and their strong-efficiency
interpretation. All checks are postsolve and add no optimization tasks.

### 3.5 Profitability and return-to-dollar

$$
\Gamma(w_o,p_o)=
\max_{(x,y)\in T,\;w_o^\top x>0}\frac{p_o^\top y}{w_o^\top x},
\qquad
\rho_o^{RTD}=\frac{p_o^\top y_o}{w_o^\top x_o},
\qquad
PE_o=\frac{\rho_o^{RTD}}{\Gamma(w_o,p_o)}.
$$

`return_to_dollar` and `observed_profitability` are exact aliases for
$\rho_o^{RTD}$, the output revenue earned per unit of input expenditure.
Profitability efficiency is the separate relative value $PE_o$.
Neither is a profit ratio. The result includes:

- observed and maximum profitability;
- `profitability_efficiency = observed / maximum`;
- a feasible profitability-maximizing activity, with its scale policy;
- the source-qualified technical, scale, and allocative components only when
  a separately registered hyperbolic or generalized-distance composition is
  fitted.

The public `score` and `efficiency` are `profitability_efficiency`; higher is
better. The executable public leaf is
`economic.profitability.return_to_dollar`; `economic.profitability` remains a
non-executable umbrella.

For the ordinary DEA hull, define $a_{oj}=w_o^\top x_j>0$ and
$q_{oj}=p_o^\top y_j>0$. A reference combination's profitability is a
cost-weighted average of the reference ratios:

$$
\frac{\sum_j\lambda_jq_{oj}}{\sum_j\lambda_ja_{oj}}
=
\sum_j
\frac{\lambda_ja_{oj}}{\sum_k\lambda_ka_{ok}}
\frac{q_{oj}}{a_{oj}}.
$$

Consequently,

$$
\Gamma(w_o,p_o)=\max_{j\in R_o}\frac{q_{oj}}{a_{oj}}.
$$

The public implementation uses this exact extreme-ratio reduction, not a
nonlinear optimizer. It caches by reference set and joint price vector.
Charnes--Cooper remains an exact audit formulation: with
$z=t\lambda$, $w_o^\top Xz=1$; VRS additionally requires
$\mathbf{1}^\top z=t$, $t\ge0$, not $\mathbf 1^\top z=1$.

CRS and VRS therefore have the same maximum ratio on this ordinary
technology, although their reported target scales differ. VRS reports the
selected reference plan. CRS scales the selected profitability-maximizing
activity to the evaluated unit's observed input expenditure, making the
counterfactual read “revenue at the same current budget.” The CRS optimal
ray is otherwise scale-indeterminate.

An equal-profitability accounting point obtained by mechanically shrinking
the evaluated inputs and expanding its outputs need not belong to the
technology when allocation is inefficient. It is not the public target.
Likewise, a GDF proportional contract is a separate technically feasible
counterfactual returned by its own model or decomposition component.
Arbitrary generalized-distance decompositions must not be inferred from this
value optimizer.

### 3.6 Matched Chavas--Cox profitability decomposition

The public operator
`analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006`
internally fits the return-to-dollar benchmark and Chavas--Cox GDF under both
CRS and VRS. Every task uses the same quantities, reference policy, price
regime, bearing parameter $\alpha$, solver, and numerical tolerances. The
operator does not accept unrelated fitted component results.

For the frozen GDF convention,

$$
PE_o
=TE^{CRS}_{GDF,o}AE_{GDF,o}
=TE^{VRS}_{GDF,o}SE_{GDF,o}AE_{GDF,o},
$$

where

$$
SE_{GDF,o}
=\frac{TE^{CRS}_{GDF,o}}{TE^{VRS}_{GDF,o}},
\qquad
AE_{GDF,o}
=\frac{PE_o}{TE^{CRS}_{GDF,o}}.
$$

The public `score` and `efficiency` are $AE_{GDF}$, higher is better.
The overall profitability score, both technical components, and the scale
component remain separately named. Residuals audit both reconstruction
identities and the expected CRS--VRS ordering.

Under the ordinary CRS technology, $TE^{CRS}_{GDF}$ equals CRS
input-radial efficiency for every $\alpha$. Thus $PE$,
$TE^{CRS}_{GDF}$, and $AE_{GDF}$ are bearing-invariant. Under VRS,
$\alpha$ can change the technical score and peer mix, so
$TE^{VRS}_{GDF}$ and $SE_{GDF}$ can change while their product
reconstructs the same CRS component.

The result preserves `profitability_maximizing_activity`, `crs_gdf`, and
`vrs_gdf` as separate target components. Within each GDF component, the
algebraic contract, score-stage peer activity, and row-scaled
slack-completed target also remain distinct. `is_allocatively_efficient`
tests only the price-conditioned component; generic `is_efficient` remains
missing.

It follows that $PE_o\leq TE^{CRS}_{GDF,o}$. The reverse inequality
printed in some software prose conflicts with both the identity and its
numerical table.

## 4. Returns to scale and finite-value policy

The first supported combinations are:

| Method | Initial RTS support | Required finite-value checks |
|---|---|---|
| cost | CRS and VRS | feasible output commitment and positive observed cost |
| revenue | CRS and VRS | no positive-value zero-input production ray and positive observed revenue |
| profit | VRS | finite convex reference technology |
| Nerlovian | VRS | finite profit optimum and positive direction value |
| profitability value | CRS and VRS | strictly positive observed and candidate costs and revenues |
| GDF profitability decomposition | matched CRS and VRS GDF | the profitability domain plus positive defined GDF scores under both technologies and $\alpha\in[0,1]$ |

Under CRS, any feasible activity with positive profit can be scaled without
bound; if no activity has positive profit and shutdown is feasible, maximum
profit is normally zero. NDRS has the same potential positive-profit ray.
DEAPack must therefore return `unbounded` or `unsupported`, never a fabricated
profit score. NIRS, explicit capacity bounds, and quasi-fixed inputs require
their own audited extensions before public support.

Cost and revenue decompositions must use the same technology, RTS, reference,
and prices as their technical components. Merely changing the `rts` parameter
between the two solves invalidates the reported identity.

## 5. Shared LP compiler and caching

The internal economic compiler reuses the sparse `CompiledReference`,
reference planner, RTS blocks, solver interface, and result diagnostics. It is
not a public method family.

For one reference set, the lambda-only objective vectors are:

| Task | Minimization objective | Quantity constraint |
|---|---|---|
| cost | $X^\top w_o$ | $-Y\lambda\le-y_o$ |
| revenue | $-Y^\top p_o$ | $X\lambda\le x_o$ |
| profit | $X^\top w_o-Y^\top p_o$ | RTS and declared bounds only |

Matrices are cached by reference signature and RTS. Objective vectors may
additionally be cached by price signature. Cost and revenue retain
observation-specific right-hand sides. With common prices and references, a
profit optimum is reusable across observations.

All selected targets must reconstruct their reported economic value and
satisfy the same technology. Multiple optimum plans are possible. The initial
result may expose one solver-selected optimum, but metadata must state
`target_uniqueness = unknown` unless uniqueness has been tested; no arbitrary
slack objective may be described as economically preferred.

### 5.1 Certified release of direct price accounts

Cost, revenue, and profit claims require more than a backend `optimal` label.
The source LP must pass solver-neutral checks of primal rows, variable bounds,
objective reconstruction, dual feasibility, complementarity, and strong
duality. A second certificate must reconstruct the economically reported
account from the raw intensities, target quantities, supplied prices, and
observed quantities.

For cost, this includes observed and minimum cost, the output commitment, the
cost gap, and the cost-efficiency ratio. For revenue, it includes observed and
maximum revenue, input capacity, the gap, expansion ratio, reciprocal
efficiency, and the maximum-revenue denominator classification. For profit, a
certificate attached to each unique reference-and-price task reconstructs
target cost, target revenue, and maximum profit; an observation certificate
then reconstructs observed cost, revenue, profit, and the profit gap.

Release is atomic at the observation or cached-task boundary. If either
certificate fails, the affected derived score and economic semantic tables
are withheld, while directly observed monetary values, backend status, and raw
diagnostics remain available. Failures must not contaminate independent
observations or price/reference tasks. External cost and revenue comparisons
may retain certified unclipped ratios but withhold internal efficiency
classification; a certified external profit opportunity account retains its
target and values but has no public self-appraisal score.

`score_valid`, `target_valid`, `link_valid`, `carryover_valid`, `peer_valid`,
and `dual_valid` are separate claims whenever those accounts exist.
Thresholding a peer display is rechecked against the certified target and may
withhold intensities without invalidating the target or score. Network links
and dynamic carry-overs must close in original economic units as well as the
solver's scaled units. Dual rows require a complete expected published
account. All certificates are postsolve computations with
`additional_solver_calls = 0`. If a backend reports `optimal` but a required
certificate fails, the semantic result status is `numerical_error`; the raw
backend claim remains available in dedicated audit fields.

The account that is published must be the account that was certified. A
monetary or model tolerance may determine a nullable efficiency classification
or denominator status, but the implementation must not independently round,
clip, or zero an optimum, gap, or ratio after certification and thereby break
its public identities.

## 6. Legal allocative decompositions

The first public decompositions are limited to identities with a verified
economic interpretation:

$$
\begin{aligned}
CE_o &= TE_o^{I}\,AE_o^{C},\\
RE_o &= TE_o^{O}\,AE_o^{R},\\
NI_o &= \beta_o+AI_o^{N},\\
PE_o
&=TE^{CRS}_{GDF,o}AE_{GDF,o}\\
&=TE^{VRS}_{GDF,o}SE_{GDF,o}AE_{GDF,o}.
\end{aligned}
$$

Here $TE^I$ is input-radial efficiency in the package's $0$-to-$1$
convention, and $TE^O$ is the reciprocal of the native output expansion
factor. The profitability productive component is source-qualified. In the
public Chavas--Cox leaf, the native score is $\delta$; at
$\alpha=1/2$, conventional hyperbolic efficiency is
$h=\sqrt{\delta}$. The decomposition uses the matched GDF convention
rather than silently substituting $h$ or an arbitrary technical score.

`analysis.allocative_decomposition` must fail closed when method identity,
technology, RTS, reference membership, prices, orientation, direction, or
score convention differs. It records the reconstruction residual.

Residual decompositions based on another technical measure are not added
merely because subtraction or division is numerically possible. They require
a defining source, the correct normalization, and tests of the allocative
component's essential property. See
[Aparicio, Zofío, and Pastor](https://doi.org/10.1007/s10957-023-02188-2).

## 7. Public API and result boundary

The public classes are distinct:

- `CostEfficiency`;
- `RevenueEfficiency`;
- `ProfitEfficiency`, whose native performance field is `profit_gap`;
- `NerlovianProfitInefficiency`, with `NerlovianEfficiency` only as a
  discoverability alias if retained;
- `ReturnToDollarEfficiency`;
- `GDFProfitabilityDecomposition`, with `ProfitabilityDecomposition` as an
  exact discoverability alias;
- `AllocativeDecomposition` for the cost identity;
- `RevenueAllocativeDecomposition` for the revenue identity.

They use `fit(data, prices)` and return `DEAResult`. A single public
`EconomicDEA(kind=...)` switch is prohibited.

Every result records:

- the canonical method and decomposition leaf IDs;
- price scope, source, units, numeraire, base period, and numerical signature;
- native optimum, observed value, gap or ratio, and score direction;
- technology, RTS, reference, finite-value policy, and shutdown policy;
- activity targets, selected intensities, solver diagnostics, and
  source-labeled dual marginals;
- all denominator, identity-reconstruction, and target-feasibility
  diagnostics.

## 8. Published oracles and validation gates

The first cost oracle is Coelli's DEAP 2.1 Example 3. Under CRS with five
firms and input prices $(1,3)$, the published cost efficiencies are

$$
(0.353,\;0.857,\;0.750,\;0.667,\;1.000),
$$

with technical and allocative components and minimum-cost input quantities
also reported in the
[DEAP 2.1 guide](https://www.owlnet.rice.edu/~econ380/DEAP.PDF).

Revenue uses the published/book-backed eight-unit VRS example and its complete
revenue, technical, and allocative vectors in the
[BenchmarkingEconomicEfficiency documentation](https://javierbarbero.github.io/BenchmarkingEconomicEfficiency.jl/stable/revenue/revenue/).
It also reproduces the five-unit unequal-price CRS/VRS example exposed by
[DataEnvelopmentAnalysis.jl](https://javierbarbero.github.io/DataEnvelopmentAnalysis.jl/stable/economic/revenue/),
which prevents the all-unit-input VRS example from masking an RTS compiler
error and distinguishes a radial output plan from the revenue-maximizing
activity.
Profit, Nerlovian, and profitability validation uses the open data and
replication materials accompanying
[Barbero and Zofío](https://doi.org/10.1016/j.seps.2023.101656),
supplemented by the defining papers above. Profitability also checks the
source example of
[Zofío and Prieto](https://doi.org/10.1007/s10108-006-9004-0).

The profit and CCF Nerlovian implementations now reproduce the fixed
eight-unit public
[DataEnvelopmentAnalysis.jl oracle](https://github.com/javierbarbero/DataEnvelopmentAnalysis.jl/blob/ca17532cd4de4e47d159cee563c05d9a0db6a61c/test/deaprofit.jl#L12-L36):
profit gaps $(2,2,0,2,2,8,12,4)$, directional components
$(0,0,0,0,0,6,12,3)$, and allocative residuals
$(2,2,0,2,2,2,0,1)$ under a unit-valued monetary direction.

The return-to-dollar implementation and its matched GDF decomposition
reproduce the fixed five-unit
[profitability oracle](https://github.com/javierbarbero/DataEnvelopmentAnalysis.jl/blob/ca17532cd4de4e47d159cee563c05d9a0db6a61c/test/deaprofitability.jl#L4-L45).
Its observed costs are $(13,8,10,16,23)$, revenues are
$(29,46,44,23,21)$, maximum profitability is $46/8=5.75$, and
profitability-efficiency scores are
$(116/299,1,88/115,1/4,84/529)$. Independent tests also compare the direct
kernel with CRS and VRS Charnes--Cooper LPs. At $\alpha=1/2$, the matched
CRS GDF vector is $(7/11,1,1,1/4,6/23)$, and the VRS vector is
$((13-2\sqrt{30})/3,1,1,1/4,9/25)$. Tests reconstruct both profitability
identities and keep the value, CRS-GDF, and VRS-GDF targets separate.

No entry is promoted to public status until it has:

1. a published numerical oracle or independently reproduced source example;
2. hand-checkable tests for one efficient and one inefficient observation;
3. objective, target, and identity reconstruction tests;
4. matched radial or directional technical-component tests where applicable;
5. common positive price-scaling and quantity-unit conversion tests;
6. explicit zero-denominator, mismatched-price, infeasible, and unbounded
   failure tests;
7. primal/dual residual and multiple-optimum metadata tests;
8. performance evidence that shared reference matrices are compiled once.

## 9. Implementation order

1. Implement `PriceSpec`, `PriceData`, alignment, signatures, and the internal
   economic LP compiler.
2. Implement cost value optimization, cost results, input-radial allocative
   decomposition, and the DEAP oracle.
3. Implement the symmetric revenue value optimization, output-radial
   decomposition, and both public revenue oracles. **Implemented.**
4. Implement finite VRS profit optimization and raw profit-gap results.
   **Implemented.**
5. Compose VRS profit with the existing DDF for Nerlovian and additive
   allocative decomposition. **Implemented.**
6. Implement return-to-dollar value optimization. **Implemented with an
   exact extreme-ratio kernel and CRS/VRS target-scale policies.**
7. Implement Chavas--Cox GDF and its matched profitability decomposition
   after the technical measure, normalization transforms, and published
   identities pass their validation gates. **Implemented for CRS/VRS with
   the fixed Zofío--Prieto cross-implementation oracle.**
8. Add other hyperbolic and generalized-path profitability decompositions
   only after their distinct technical measures, transformations, and
   identities pass separate validation gates.
