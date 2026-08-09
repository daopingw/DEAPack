# Cost technical--allocative decomposition

```{eval-rst}
.. currentmodule:: deapack
```

`AllocativeDecomposition` distinguishes two sources of avoidable cost:

- **input-radial technical efficiency** asks whether all inputs could be
  reduced proportionally while preserving the output commitment;
- **cost allocative efficiency** asks whether the technically adjusted input
  combination is well adapted to the supplied relative prices.

The implemented identity is

$$
CE_o = TE_o^I AE_o^C,
\qquad
AE_o^C = \frac{CE_o}{TE_o^I}.
$$

The operator fits both components internally with the same `DEAData`,
returns to scale, reference policy, solver policy, and input orientation.
It does not accept arbitrary precomputed result objects. This fail-closed
composition prevents a cost result under one technology from being divided
by a technical score under another.

```python
from deapack import (
    AllocativeDecomposition,
    DEAData,
    PriceData,
    load_dataset,
)

frame = load_dataset("cost_mix_choice")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["x1", "x2"],
    outputs="output",
)
prices = PriceData.common(input_prices={"x1": 1.0, "x2": 3.0})

result = AllocativeDecomposition(returns_to_scale="crs").fit(data, prices)
result.summary()[
    [
        "dmu_id",
        "technical_efficiency",
        "allocative_efficiency",
        "cost_efficiency",
        "reconstruction_residual",
    ]
]
```

For this analytical operator, `score` and `efficiency` contain
`allocative_efficiency`; higher is better. The overall cost component remains
in `cost_efficiency`. `reconstruction_residual` makes the defining identity
auditable for every observation.
`is_allocatively_efficient` tests whether the price-conditioned allocative
component equals one. A technically inefficient activity can still have that
property, so the generic Pareto--Koopmans field `is_efficient` remains
missing.

The decomposition consumes only a certified input-radial technical score.
`technical_score_valid`, `technical_score_status`, and
`technical_primary_solver_status` preserve that component evidence; the
combined result publishes `score_valid`, `score_status`, and
`decomposition_defined`. If the cost solve fails, the radial component is
uncertified, either component value is non-finite, or the technical denominator
is too small, allocative efficiency is missing and the combined
`solver_status` is not `optimal`. A raw backend claim of optimality cannot
override a failed component certificate.

The implementation is verified against Example 3 in Coelli's DEAP 2.1 guide.
The published example uses CRS. Results obtained by changing the same data to
VRS are valid model results, but they are not the published oracle.

```{autosummary}
AllocativeDecomposition
```
