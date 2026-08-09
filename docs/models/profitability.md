# Return-to-dollar profitability efficiency

```{eval-rst}
.. currentmodule:: deapack
```

`ReturnToDollarEfficiency` asks how much desirable-output revenue an
organization earns per unit of input expenditure, and compares that ratio
with the best ratio available from its declared reference set.
`ProfitabilityEfficiency` is an exact API alias for the same model.

For evaluated prices $w_o,p_o$,

$$
\rho_o=\frac{p_o^\top y_o}{w_o^\top x_o},
\qquad
\Gamma_o^*=
\max_{(x,y)\in T,\;w_o^\top x>0}\frac{p_o^\top y}{w_o^\top x},
\qquad
PE_o=\frac{\rho_o}{\Gamma_o^*}.
$$

`return_to_dollar` and `observed_profitability` both contain $\rho_o$.
`maximum_profitability` contains $\Gamma_o^*$, while `score`,
`efficiency`, and `profitability_efficiency` contain $PE_o$. Higher is
better, and one is best under a self-inclusive reference.

This is not a profit ratio. It never divides observed net profit by maximum
net profit; negative or zero profit therefore does not create a sign reversal.
The input-cost and output-revenue totals used in the profitability ratio must
nevertheless be strictly positive.

## Example

```python
from deapack import (
    DEAData,
    PriceData,
    ReturnToDollarEfficiency,
    load_dataset,
)

frame = load_dataset("revenue_5x2")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["input_1", "input_2"],
    outputs=["output_1", "output_2"],
)
prices = PriceData.common(
    input_prices={"input_1": 2.0, "input_2": 1.0},
    output_prices={"output_1": 3.0, "output_2": 2.0},
)

result = ReturnToDollarEfficiency(
    returns_to_scale="crs",
).fit(data, prices)

result.summary()[[
    "dmu_id",
    "observed_cost",
    "observed_revenue",
    "return_to_dollar",
    "maximum_profitability",
    "profitability_efficiency",
]]
```

The five observed costs are $13,8,10,16,23$, and revenues are
$29,46,44,23,21$. Unit 2 earns $46/8=5.75$ per unit of expenditure, the
largest reference ratio. The efficiency scores are

$$
\left(
\frac{116}{299},\,
1,\,
\frac{88}{115},\,
\frac14,\,
\frac{84}{529}
\right).
$$

These values reproduce the public Zofío--Prieto cross-implementation oracle.

## Exact solver-free reduction

Let $a_j=w_o^\top x_j>0$, $q_j=p_o^\top y_j>0$, and
$r_j=q_j/a_j$. For any nonnegative reference intensities,

$$
\frac{\sum_j\lambda_jq_j}{\sum_j\lambda_ja_j}
=
\sum_j
\frac{\lambda_ja_j}{\sum_k\lambda_ka_k}r_j.
$$

The combined profitability is a cost-weighted average of the reference
ratios. It cannot exceed their maximum. DEAPack therefore evaluates the
reference ratios directly and selects the first maximizer in stable reference
order. This exact algorithm needs no nonlinear optimizer and is cached by the
joint price vector and reference set.

The equivalent Charnes--Cooper formulation uses $z=t\lambda$ and
$w_o^\top Xz=1$. Under VRS the transformed convexity restriction is
$\mathbf 1^\top z=t$, not $\mathbf 1^\top z=1$. Automated tests compare the direct
kernel with both CRS and VRS transformed LPs.

## CRS and VRS target scale

The maximum ratio is identical under the ordinary CRS cone and VRS convex
hull because scaling an activity changes revenue and cost by the same factor.
The target scale is not identical:

- Under VRS, `profitability_maximizing_activity` is the selected reference
  activity with intensity one.
- Under CRS, the selected activity is scaled so its input expenditure equals
  the evaluated unit's observed cost. The target then answers: “At the same
  total resource budget, what revenue would the best return-to-dollar
  operating recipe earn?”

The CRS optimum is a ray, so this same-budget convention is a reporting
normalization rather than a uniquely identified operating scale.
`target_scale_policy` records `observed_cost` or `vrs_reference_plan`.
`maximizer_count` and `target_uniqueness` disclose tied best ratios.

An accounting point created by mechanically shrinking the current inputs and
expanding the current outputs until its ratio reaches the maximum may be
technologically infeasible. DEAPack does not present that point as a target.
The separately fitted
{doc}`Chavas--Cox generalized-distance model <generalized-distance>` keeps its
technically feasible proportional contract distinct from the
profitability-maximizing activity.

## External references and efficiency flags

With a self-inclusive reference, `profitability_efficiency` lies in
$(0,1]$ up to tolerance. Equality sets
`is_profitability_efficient=True`. Complete strictly positive prices then
provide positive evidence of Pareto--Koopmans efficiency: a strict dominator
would have a larger revenue-cost ratio. A score below one does not prove
technical inefficiency, so generic `is_efficient` remains missing.

With an external reference, the ratio is retained without clipping and may
exceed one. `score_status="defined_external_comparison"` marks this as a
benchmark-relative comparison; both efficiency flags are missing.

## Admissible data

The public leaf requires:

- nonnegative input and desirable-output quantities;
- at least one positive input and one positive desirable output per
  observation;
- complete, finite, strictly positive input and output prices;
- observed and reference costs and revenues above
  `PriceSpec.denominator_tolerance`; and
- CRS or VRS.

Zero-cost candidates, shutdown at the origin, undesirable outputs, negative
prices or quantities, and restricted-returns fractional technologies require
separate model contracts. The closed-form backend returns no fabricated
duals; `duals_available=False` explains why.

The GDF technical, scale, and allocative decomposition is not part of this
value optimizer. Use
{doc}`GDFProfitabilityDecomposition
<../analysis/profitability-decomposition>` to fit the separately registered
composition with its own bearing parameter, feasible technical targets,
numerical method, and identity checks.

```{autosummary}
ReturnToDollarEfficiency
ProfitabilityEfficiency
PriceData
PriceSpec
```
