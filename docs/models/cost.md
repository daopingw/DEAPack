# Cost efficiency

```{eval-rst}
.. currentmodule:: deapack
```

`CostEfficiency` asks how much the evaluated organization would need to
spend if it adopted a cost-minimizing feasible activity while preserving its
observed desirable-output commitment. Supplied prices are held separately
from production quantities in `PriceData`.

For observation $o$, input prices $w_o$, and a compiled reference technology
$(X,Y)$, the model solves

$$
C_o^* =
\min_{\lambda\in\Lambda_{\mathrm{RTS}}} w_o^\top X\lambda
\quad\text{subject to}\quad
Y\lambda\geq y_o .
$$

The public score is

$$
CE_o=\frac{C_o^*}{w_o^\top x_o}.
$$

`score`, `efficiency`, and `cost_efficiency` all contain $CE_o`; higher is
better. The summary also contains `observed_cost`, `minimum_cost`, and
`cost_gap`. `distance` is missing because cost efficiency is not reported as
a distance-function value. `is_cost_efficient` tests whether the observed
cost equals minimum attainable cost. It is not copied into `is_efficient`:
a least-cost plan can still leave a desirable-output expansion opportunity,
and the current model does not run a Pareto--Koopmans completion.

## Price contract

Common prices are declared by exact quantity-variable names:

```python
from deapack import CostEfficiency, DEAData, PriceData, load_dataset

frame = load_dataset("cost_mix_choice")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["x1", "x2"],
    outputs="output",
)
prices = PriceData.common(input_prices={"x1": 1.0, "x2": 3.0})

result = CostEfficiency(returns_to_scale="crs").fit(data, prices)
result.summary()[
    ["dmu_id", "observed_cost", "minimum_cost", "cost_efficiency"]
]
```

Observation-specific prices use `PriceData.from_frame`. They align by
`dmu_id`, or by `(dmu_id, period)` for panel data; source row position is
never an alignment rule. Input-price names must match every declared input
name exactly. The current public cost model rejects missing, extra,
nonfinite, zero, and negative prices before optimization.

Panel monetary comparisons require an explicit currency and base period in
`PriceSpec`. DEAPack does not silently deflate, convert, or impute prices.
Numerical price payloads are represented in result provenance only by stable
cryptographic signatures.

## Technology and reference behavior

The current implementation supports convex CRS and VRS technologies. It
uses every reference policy available through `ReferenceSpec`, including
contemporaneous, global, sequential, window, biennial, and custom sets.

With a self-inclusive reference, the observed activity is feasible and
ordinary cost efficiency is at most one. A custom or counterfactual
reference may omit the evaluated observation. The cost problem can then be
infeasible, or its ratio can exceed one because the external technology is
more expensive than the observation. DEAPack retains that result; it neither
clips the ratio nor substitutes another reference set. The ratio remains a
defined external comparison, but `is_cost_efficient` is missing because the
internal self-appraisal classification is not licensed.

The target table reports one solver-selected `cost_minimizing_activity`.
Changes from observed to target inputs are economically valued changes in
the input mix, not technical input slacks. Output in excess of the maintained
commitment is a constraint surplus, not automatically an output shortfall.
Because a linear program may have several cost-minimizing plans, metadata
records `target_uniqueness="unknown"`.

## Certified release contract

An `optimal` backend status is necessary but not sufficient for publication.
DEAPack independently checks the LP rows, variable bounds, objective,
dual feasibility, complementarity, and strong duality. It then reconstructs
the selected activity, observed and minimum costs, output commitment, cost
gap, and efficiency ratio. These checks are postsolve calculations and add no
optimization calls.

`score_valid`, `target_valid`, `peer_valid`, and `dual_valid` apply to different
claims. If either the LP or cost account is uncertified, the score, minimum
cost, gap, targets, peers, and duals for that observation are withheld while
the directly observed cost and raw diagnostics remain available. Removing
small peer intensities is checked separately; a failed peer display does not
invalidate a certified score or target. Dual rows are likewise released only
when the complete expected account is present.

The public monetary values are the values that were certified. DEAPack does
not independently round or zero the minimum cost, gap, or ratio after the
certificate has been computed. Efficiency classification uses the declared
numerical tolerance without rewriting those identities.

## Dual values

The `duals` table labels output-commitment marginals as
`source="model_derived"` and `value_type="shadow_value"`. They describe the
local modeled cost of tightening an output commitment. They are not supplied
market prices and do not replace `PriceData`.

Cost efficiency currently rejects declared undesirable outputs. Combining
prices with pollution production, disposal, and abatement assumptions
requires a separately registered environmental-economic model.

```{autosummary}
CostEfficiency
PriceData
PriceSpec
```
