# Maximum-profit gap

```{eval-rst}
.. currentmodule:: deapack
```

`ProfitEfficiency` asks a broader economic question than cost or revenue
efficiency: if both resource use and the output portfolio may change, which
attainable operating plan earns the greatest net value at the prices faced by
the evaluated organization?

For input prices $w_o$, desirable-output prices $p_o$, and a VRS reference
technology, the current implementation solves

$$
\Pi_o^*=
\max_{\lambda\geq0}
\left(p_o^\top Y\lambda-w_o^\top X\lambda\right)
\quad\text{subject to}\quad
\mathbf 1^\top\lambda=1.
$$

The native result is

$$
G_o^\Pi=\Pi_o^*-\left(p_o^\top y_o-w_o^\top x_o\right).
$$

`observed_profit`, `maximum_profit`, and `profit_gap` retain these monetary
values. `score` is the gap and `score_direction` is `lower_is_better`.
`efficiency` and `distance` are missing. DEAPack does not report
`observed_profit / maximum_profit`: that ratio reverses or loses meaning when
either profit is zero or negative.

## Example

```python
import pandas as pd

from deapack import DEAData, PriceData, ProfitEfficiency

frame = pd.DataFrame(
    {
        "unit": ["A", "B", "C", "D"],
        "staff": [4.0, 5.0, 3.0, 6.0],
        "standard": [6.0, 4.0, 5.0, 3.0],
        "specialist": [2.0, 5.0, 1.0, 2.0],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="unit",
    inputs="staff",
    outputs=["standard", "specialist"],
)
prices = PriceData.common(
    input_prices={"staff": 2.0},
    output_prices={"standard": 3.0, "specialist": 5.0},
)

result = ProfitEfficiency().fit(data, prices)
result.summary()[
    ["dmu_id", "observed_profit", "maximum_profit", "profit_gap"]
]
```

The observed profits are $20,27,14,7$, and the maximum is $27$. Unit D
therefore forgoes $20$ monetary units. Its selected
`profit_maximizing_activity` is an economic counterfactual, not a technical
slack target.

## Prices and admissible data

Both price sides are required through one `PriceData` object. Names must match
every declared input and desirable output exactly. Common and keyed
observation-specific prices are supported; panel prices require currency and
base-period metadata. Result provenance stores signatures, never the price
payload.

The current public leaf accepts nonnegative quantities with at least one
strictly positive input and output per observation, finite strictly positive
prices, and desirable outputs only. Negative observed and even negative
maximum profit remain valid. Undesirable outputs require an explicit
environmental-economic technology and are not inferred from a `bad_outputs`
column.

## VRS, shutdown, and CRS

Only VRS is currently public. The convexity equality makes the finite
reference hull explicit, but it does **not** include a zero-activity shutdown
option. If every represented activity loses money, maximum profit can
therefore be negative.

Adding the origin or changing the convexity equality to an inequality changes
the technology and will be a separately registered shutdown preset. Under
unconstrained CRS, any represented positive-profit activity can be replicated
without bound. Shutdown does not impose a capacity limit and cannot cure that
positive-profit ray, so the current constructor rejects CRS, NIRS, and NDRS.

## Status, targets, and caching

With a self-inclusive reference, a `profit_gap` within the declared monetary
tolerance sets `is_profit_efficient=True` without rewriting the reported gap.
Complete strictly positive prices also make this
a Pareto--Koopmans certificate: any activity that strictly dominated the
observation would earn greater profit. A positive profit gap does not prove
technical inefficiency—an organization may be technically efficient but
choose the wrong mix—so generic `is_efficient` is missing rather than false.

For an external reference, raw observed, maximum, and gap values are retained,
but `score_status="undefined_external_reference"` and the public score fails
closed. Targets and intensities are still available for auditing the
comparison.

The optimum depends on the reference rows and joint price vector, not on the
evaluated quantities. DEAPack therefore reuses the complete LP solution for
common prices and a common reference; metadata reports `solver_calls` and
cache counts.

An optimum is released only after two linked certificates. The first checks
the LP and reconstructs the cached target quantities, target cost, target
revenue, and maximum profit. The second reconstructs each evaluated
organization's observed cost, revenue, profit, and profit gap. A failed cached
task is reused only as a failed task; it is never mislabeled as a reused target
account. All checks require zero additional solver calls.

`score_valid` identifies a certified self-appraisal gap. An external comparison
can retain certified target and value accounts while its score remains
undefined. `target_valid`, `peer_valid`, and `dual_valid` govern the three
semantic tables independently. Missing or incomplete dual publication does
not erase a certified profit account, but its dual rows are withheld.

The reported `maximum_profit` and `profit_gap` are exactly the monetary account
that was certified. `monetary_tolerance` may classify a sufficiently small gap
as economically indistinguishable from zero; it does not rewrite the maximum,
gap, or target-value identities after certification.

```{autosummary}
ProfitEfficiency
PriceData
PriceSpec
```
