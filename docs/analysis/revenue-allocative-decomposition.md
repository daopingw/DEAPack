# Revenue technical--allocative decomposition

`RevenueAllocativeDecomposition` distinguishes two managerial sources of a
revenue shortfall:

- output-oriented technical efficiency asks how much the current output bundle
  could be expanded proportionally with the available inputs; and
- revenue allocative efficiency asks whether that technically adjusted bundle
  has the most valuable attainable product or service mix at supplied prices.

The operator fits both components internally with identical quantities,
returns to scale, reference membership, solver policy, and output orientation.
It does not accept unrelated component results.

Let $\phi_o$ be the Farrell output expansion factor and define the
higher-is-better technical score $TE_o^O=1/\phi_o$. With
$RE_o=R_o/R_o^*$, the reported revenue allocative efficiency is

$$
AE_o^R=\frac{RE_o}{TE_o^O}
       =\frac{\phi_o R_o}{R_o^*},
\qquad
RE_o=TE_o^O AE_o^R.
$$

The distinction between $\phi_o y_o$ and $Y\lambda^*$ matters. The first
keeps the observed output proportions fixed; the second may change the output
mix to maximize revenue. Any non-radial output surplus in a technical
projection does not replace the classic Farrell component in this identity.

```python
from deapack import (
    DEAData,
    PriceData,
    RevenueAllocativeDecomposition,
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
    output_prices={"output_1": 3.0, "output_2": 2.0}
)

result = RevenueAllocativeDecomposition(
    returns_to_scale="vrs"
).fit(data, prices)
result.summary()[
    [
        "dmu_id",
        "technical_expansion_factor",
        "technical_efficiency",
        "allocative_efficiency",
        "revenue_efficiency",
        "reconstruction_residual",
    ]
]
```

`allocative_efficiency` is the generic `score` and `efficiency` of the
decomposition result. The summary also retains the native expansion factor,
standardized technical efficiency, overall revenue efficiency, component
solver statuses, denominator-validity fields, and
`reconstruction_residual`.
`is_allocatively_efficient` tests only the price-conditioned output-mix
component. It is not a certificate that every technical improvement has been
exhausted, so `is_efficient` remains missing.

The technical component is accepted only with
`technical_primary_solver_status="optimal"` and
`technical_score_valid=True`. The combined result exposes those component
fields together with `technical_score_status`, then publishes its own
`score_valid`, `score_status`, and `decomposition_defined`. A failed runtime
certificate, non-finite component, or invalid denominator produces a missing
allocative score and a non-optimal combined status even when a backend's raw
status was `optimal`.

For the first unit of the bundled VRS example, observed output is $(7,4)$
and prices are $(3,2)$. Its radial expansion factor is $9/7$, but its
revenue-maximizing activity is $(9,9)$, not merely
$(9,36/7)$. The resulting components are
$TE^O=7/9$, $AE^R=29/35$, and $RE=29/45$.

If either component solver or certificate fails, maximum revenue has an
invalid denominator, or the output expansion factor is nonpositive, the
allocative score is missing. `decomposition_defined` and `score_status` state
why. DEAPack does not divide by zero or manufacture a decomposition outside
its mathematical domain.
