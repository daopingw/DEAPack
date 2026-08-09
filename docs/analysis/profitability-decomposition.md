# GDF profitability decomposition

```{eval-rst}
.. currentmodule:: deapack
```

`GDFProfitabilityDecomposition` explains return-to-dollar efficiency through
three matched management accounts:

- **operating performance** asks how much of a declared proportional resource
  saving and service growth contract is technically attainable;
- **scale performance** asks how the VRS operating assessment changes when an
  operating recipe may be proportionally replicated under CRS; and
- **allocative performance** asks whether the organization's input and output
  mix is well adapted to the supplied relative prices.

`ProfitabilityDecomposition` is an exact API alias. The operator follows the
Chavas--Cox generalized-distance framework and the return-to-dollar identity
of [Zofío and Prieto (2006)](https://doi.org/10.1007/s10108-006-9004-0).

## Identities

Let $PE_o$ denote return-to-dollar profitability efficiency, and let
$TE^{CRS}_{GDF,o}$ and $TE^{VRS}_{GDF,o}$ be generalized-distance scores
under matched CRS and VRS technologies. DEAPack reports

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

`allocative_efficiency` is the decomposition result's primary `score` and
`efficiency`. The overall `profitability_efficiency`, both technical
components, and `scale_efficiency` remain in the same summary row.
`crs_reconstruction_residual`, `vrs_reconstruction_residual`, and
`crs_vrs_ordering_residual` make the two identities and the expected
CRS--VRS ordering auditable.

This operator does not reinterpret an arbitrary technical score after fitting.
It internally fits the return-to-dollar benchmark and both GDF components
with the same quantities, prices, reference policy, `alpha`, solver, and
numerical tolerances.

## Worked five-organization account

```python
from deapack import (
    DEAData,
    GDFProfitabilityDecomposition,
    PriceData,
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

result = GDFProfitabilityDecomposition(alpha=0.5).fit(data, prices)
result.summary()[[
    "dmu_id",
    "profitability_efficiency",
    "crs_technical_efficiency",
    "vrs_technical_efficiency",
    "scale_efficiency",
    "allocative_efficiency",
    "crs_reconstruction_residual",
    "vrs_reconstruction_residual",
]]
```

For the balanced contract, the components are:

| DMU | $PE$ | $TE^{CRS}_{GDF}$ | $TE^{VRS}_{GDF}$ | $SE_{GDF}$ | $AE_{GDF}$ |
|---|---:|---:|---:|---:|---:|
| 1 | 0.387960 | 0.636364 | 0.681850 | 0.933290 | 0.609651 |
| 2 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| 3 | 0.765217 | 1.000000 | 1.000000 | 1.000000 | 0.765217 |
| 4 | 0.250000 | 0.250000 | 0.250000 | 1.000000 | 1.000000 |
| 5 | 0.158790 | 0.260870 | 0.360000 | 0.724638 | 0.608696 |

The overall profitability vector is exactly

$$
\left(
\frac{116}{299},\,1,\,\frac{88}{115},\,\frac14,\,\frac{84}{529}
\right),
$$

the CRS technical vector is

$$
\left(\frac7{11},\,1,\,1,\,\frac14,\,\frac6{23}\right),
$$

and the VRS technical vector is

$$
\left(
\frac{13-2\sqrt{30}}3,\,1,\,1,\,\frac14,\,\frac9{25}
\right).
$$

These values reproduce the fixed
[public cross-implementation example](https://github.com/javierbarbero/DataEnvelopmentAnalysis.jl/blob/ca17532cd4de4e47d159cee563c05d9a0db6a61c/test/deaprofitability.jl#L4-L45).

The table supports different management questions. Unit 3 has no fitted
technical or scale shortfall under this contract, but its service and
resource mix earns only about 76.5 percent of the best return available at the
supplied prices. Unit 4 has no allocative or scale shortfall in this account;
its entire profitability gap is associated with the common technical
contract. Unit 5 has material operating, scale, and allocative gaps. These are
benchmark-conditioned diagnoses, not causal attributions to managers.

## What changing $\alpha$ changes

`alpha` determines how the proportional technical adjustment is expressed
between resource discipline and service growth:

- `alpha=0` protects services and assigns the adjustment to resource saving;
- `alpha=1` protects the resource budget and assigns it to service growth; and
- interior values use both margins multiplicatively.

Under CRS, the generalized-distance score is the CRS input-radial score for
every `alpha`. Therefore $PE$, $TE^{CRS}_{GDF}$, and
$AE_{GDF}$ do not change with the bearing parameter in the implemented
ordinary CRS technology. Under VRS, the score and comparator mix may change,
so $TE^{VRS}_{GDF}$ and $SE_{GDF}$ may change while their product
continues to reconstruct the same CRS component.

The decomposition is meaningful only when the chosen path reflects the
decision context. A resource-constrained public service and a growth-oriented
business unit may reasonably use different values of `alpha`; their component
scores should not be compared as though the same counterfactual had been
assessed. Unless institutional evidence supports the value, `alpha` remains
an analyst-defined scenario rather than a revealed management preference.

## Three different targets

The long result tables retain three components:

- `profitability_maximizing_activity` is the feasible operating recipe with
  the highest output value per unit of expenditure;
- `crs_gdf` is the technical contract and peer activity under CRS; and
- `vrs_gdf` is the corresponding technical contract and peer activity at
  observed organizational scales.

Within each GDF component, `path_target`,
`phase_one_reference_activity`, and the slack-completed `target` keep their
model-specific meanings. A profitability-maximizing activity may change the
input and service portfolio to respond to prices. A GDF target preserves the
proportional contract chosen by `alpha`. They answer different questions and
are never collapsed into one generic target.

`is_allocatively_efficient` tests only $AE_{GDF}=1$. It does not certify
technical efficiency or Pareto--Koopmans efficiency, so the generic
`is_efficient` field remains missing for the composite result. Inspect the
CRS and VRS component statuses and targets for technical conclusions.

## Failure and numerical policy

The operator requires the joint domain of its components:

- nonnegative inputs and desirable outputs with positive aggregate input and
  output for every observation;
- complete, finite, strictly positive input and output prices;
- strictly positive evaluated and candidate costs and revenues;
- a reference policy supported by both the return-to-dollar and GDF models;
  and
- `alpha` in the closed interval $[0,1]$.

The value component uses the exact extreme-ratio kernel. CRS GDF and the two
endpoints use exact radial reductions; only an interior VRS GDF needs
repeated LP feasibility checks. If any required component is undefined or a
solver fails, `decomposition_defined=False`, the allocative score is missing,
and `score_status` explains the failure. DEAPack does not reconstruct an
identity from mismatched or failed components.

```{autosummary}
GDFProfitabilityDecomposition
ProfitabilityDecomposition
```
