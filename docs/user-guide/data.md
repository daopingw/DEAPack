(data-schema)=

# Preparing data

Start with a table: one row per decision-making unit (DMU), and one column
for each input or output. `DEAData.from_frame()` tells DEAPack what those
columns mean. It does not estimate a model yet.

## A simple input–output table

This complete example uses the same small dataset as the {doc}`../getting-started/quickstart`:

```python
from deapack import DEAData, load_dataset

frame = load_dataset("slacks_2x2")
print(frame.head())

data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["labor", "capital"],
    outputs=["service", "quality"],
)
```

Here `dmu` identifies the organization, `labor` and `capital` are resources,
and `service` and `quality` are desirable outputs. Use the exact column names
from your own table. A single column can be written as a string, such as
`inputs="labor"`; use a list for several columns.

## Read your own data

For a CSV file, read it with pandas, then use `DEAData.from_frame()` as above:

```python
import pandas as pd

frame = pd.read_csv("my_data.csv")
print(frame.head())
```

This block requires your own file. Replace `my_data.csv` with its path and
replace the DMU, input, and output names in the preceding example with your
actual column names. For an Excel file, use `pd.read_excel("my_data.xlsx")`
instead; pandas may ask you to install an Excel reader such as `openpyxl`.

The sections below are independent examples for more specific data layouts.
You only need the layout that matches your study.

## Panel data and undesirable outputs

For repeated observations, add a period column. For pollution or other outputs
you want to reduce, use `bad_outputs`:

```python
from deapack import DEAData, load_dataset

panel_frame = load_dataset("environmental_panel")
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

Each row is now one organization in one period. `polluting_inputs` identifies
the subset of inputs responsible for residual generation; it is used by models
such as by-production. It does not remove energy from the input list. Most
ordinary DEA studies do not need this extra role. See
{doc}`../reference/environmental-models` for model choices.

## Zero and negative observations

Do not shift negative values or add small constants just to make a model run.
Different measures support different data ranges. A negative value is not, by
itself, an undesirable output: the variable's economic meaning determines
whether more or less is preferred.

For example, the range directional measure accepts finite signed inputs and
desirable outputs:

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
result.summary()
```

See {doc}`../models/range-directional` for the comparison this model makes.
Its ability to use signed values does not justify changing a variable's role.

## Dynamic data with carry-overs

A panel column alone does not create a dynamic model. When resources or
burdens connect consecutive periods, use `DynamicData` and declare those
carry-overs:

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
    production=PeriodProductionSpec(inputs="resource", outputs="service"),
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

One evaluated unit is the organization's entire trajectory. Every DMU must
appear once in every declared period; missing periods are not filled in.
A row-level `ReferenceSpec` is not automatically applied to this trajectory
comparison. Continue with {doc}`../models/tone-tsutsui-dynamic-sbm` to fit it.

## Prices for economic efficiency

Keep quantities and prices separate. For prices shared by all organizations:

```python
from deapack import PriceData

prices = PriceData.common(
    input_prices={"capital": 0.08, "labor": 25.0, "energy": 0.12},
)
```

Price names must match the corresponding quantity names in your study. This
example defines prices only; it is not paired with the earlier two-input table.
Use `PriceData.from_frame()` when prices differ by observation. It matches
prices to quantities by DMU, or by DMU and period, not by row position. No
missing prices or currency conversions are inferred. Panel monetary
comparisons also require the currency and base period in `PriceSpec`.
See {doc}`../models/cost` for a complete economic-efficiency example.

## If data validation fails

Check that:

- DMU identifiers are unique, or DMU–period pairs are unique for a panel;
- measured quantities are numeric and finite;
- column names and variable roles match your table;
- every polluting input also appears in `inputs`; and
- periods have a clear order; provide `period_order` if their labels do not
  sort in the intended order.

DEAPack performs these checks when it prepares the data and fits the chosen
model. You do not need to write a separate validation routine for the examples.
Internally, the package protects the numerical arrays and handles their matrix
orientation; these implementation details do not change how you prepare a table.
