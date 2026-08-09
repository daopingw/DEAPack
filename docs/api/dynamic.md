# Dynamic data, specifications, and models

```{eval-rst}
.. currentmodule:: deapack
```

## Complete-trajectory data

```{autoclass} deapack.DynamicData
:members:
```

`DynamicData` is distinct from row-level `DEAData`. One assessed observation
is a complete DMU trajectory over the declared period order.

## Period production accounts

```{autoclass} deapack.PeriodProductionSpec
:members:
```

## Carry-over roles

```{autoclass} deapack.CarryOverKind
:members:
```

```{autoclass} deapack.CarryOverSpec
:members:
```

The exact source naming aliases are:

- `good` and `desirable`;
- `bad` and `undesirable`;
- `free` and `discretionary`; and
- `fixed`, `non-discretionary`, and `nondiscretionary`.

These aliases select the same historical Tone--Tsutsui balance equations.
They do not make economic effect, managerial control, decay, lag, and
terminal policy universally interchangeable.

## Dynamic specification

```{autoclass} deapack.DynamicSBMSpec
:members:
```

`DynamicSpec` is an exact alias for `DynamicSBMSpec`.

## Tone--Tsutsui dynamic SBM

```{autoclass} deapack.ToneTsutsuiDynamicSBM
:members:
```

`DynamicSBM` is an exact alias for `ToneTsutsuiDynamicSBM`.

See {doc}`../models/tone-tsutsui-dynamic-sbm` for the source equations,
score variants, complete executable example, result-table contract, failure
domain, performance behavior, and the published Table 2 reproduction.

## Minimal executable pattern

```python
from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    PeriodProductionSpec,
    load_dataset,
)

frame = load_dataset("dynamic_carryover_portfolio")
spec = DynamicSBMSpec(
    production=PeriodProductionSpec(
        inputs="input",
        outputs="output",
    ),
    carryovers=(
        CarryOverSpec("free_carryover", "free"),
    ),
)
data = DynamicData.from_frame(
    frame,
    spec=spec,
    dmu="dmu",
    period="period",
)
result = DynamicSBM(
    orientation="input",
    returns_to_scale="crs",
    score_variant="free_adjusted_post",
).fit(data)
```

When processes and within-period handoffs matter as well as carry-overs, use
the separate {doc}`dynamic-network` API and
{doc}`../models/tone-tsutsui-dynamic-network-sbm` model contract.
