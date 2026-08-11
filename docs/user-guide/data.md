# Data schema

`DEAData` separates the user-facing table from immutable numerical arrays used
by the solver. A cross-section has one row per DMU; a panel has one row per
`(DMU, period)` observation. The numerical compiler performs the matrix
orientation once. Every example below defines its own input table and can be
run independently.

```python
from deapack import DEAData, load_dataset

panel_frame = load_dataset("environmental_panel")
print(panel_frame.head())

panel_data = DEAData.from_frame(
    panel_frame,
    dmu="dmu",
    period="period",
    inputs=["energy", "labor"],
    polluting_inputs=["energy"],
    outputs=["electricity"],
    bad_outputs=["co2"],
)
```

`polluting_inputs` is an explicit subset of `inputs`. It is used only by
technologies such as by-production that distinguish ordinary inputs from
inputs that trigger residual generation. Declaring `energy` as polluting does
not remove it from the intended-production input matrix.

Validation includes:

- unique DMU keys for cross sections;
- unique `(dmu, period)` keys for panels;
- distinct columns for each variable role;
- polluting-input names that are also declared as inputs;
- numeric and finite measurement values;
- explicit period ordering when labels cannot be sorted safely.

Negative values are not silently shifted. Each measure validates whether its
theory supports zero or negative observations.

## Signed accounting values need declared economic roles

A negative observation does not by itself identify an undesirable output. A
negative change in deposits or net service balance may still be a desirable
account for which a larger value is preferred. Conversely, emissions remain
a burden to contract even when an accounting adjustment produces a negative
entry.

`RangeDirectionalDEA` accepts finite signed inputs and desirable outputs
because it measures change relative to each focal observation's remaining
room to the best values in the same VRS comparison population. It does not
pre-shift the data. Use:

```python
from deapack import DEAData, RDM, load_dataset

signed_frame = load_dataset("range_directional_signed")

signed_data = DEAData.from_frame(
    signed_frame,
    dmu="dmu",
    inputs="input",
    outputs="output",
)
result = RDM().fit(signed_data)
```

The variable documentation must still say why less input and more output are
economically preferred. Common translation invariance under VRS is not
permission to shift selected observations or to relabel a burden as a
desirable service. See {doc}`../models/range-directional`.

## Dynamic trajectories are not row-level panel observations

`DynamicData` stores a complete balanced trajectory for every DMU and an
explicit production/carry-over specification:

```python
from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBMSpec,
    PeriodProductionSpec,
    load_dataset,
)

dynamic_frame = load_dataset("dynamic_capacity_backlog")

spec = DynamicSBMSpec(
    production=PeriodProductionSpec(
        inputs="resource",
        outputs="service",
    ),
    carryovers=(
        CarryOverSpec("capacity", "good"),
        CarryOverSpec("backlog", "bad"),
    ),
)
dynamic_data = DynamicData.from_frame(
    dynamic_frame,
    spec=spec,
    dmu="organization",
    period="period",
    period_order=(1, 2),
)
```

One observation in a dynamic fit is the organization’s whole trajectory.
Every DMU must appear exactly once in every declared period. Missing periods
are not imputed, and a row-level `ReferenceSpec` is not silently applied to
the trajectory cohort. See {doc}`../models/tone-tsutsui-dynamic-sbm`.

## Prices remain valuation data

Input and output prices do not become columns in `DEAData`'s production
technology. Economic models receive a separate immutable `PriceData`:

```python
from deapack import PriceData

prices = PriceData.common(
    input_prices={
        "capital": 0.08,
        "labor": 25.0,
        "energy": 0.12,
    }
)
```

Observation-specific prices are constructed with `PriceData.from_frame` and
aligned to quantities by exact DMU or `(DMU, period)` keys. Quantity names
must match exactly; positional matching, silent broadcasting across missing
variables, price imputation, and automatic currency conversion are not
performed. Panel monetary comparisons additionally require an explicit
currency and base period in `PriceSpec`.
