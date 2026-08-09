# Dynamic-network data, specifications, and model

```{eval-rst}
.. currentmodule:: deapack
```

## Complete dynamic-network trajectories

```{autoclass} deapack.DynamicNetworkData
:members:
```

`DynamicNetworkData` stores one balanced `(period, DMU, variable)` array.
One estimator observation is a complete multi-process trajectory.

## Link-account kinds

```{autoclass} deapack.NetworkSBMLinkKind
:members:
```

Canonical kinds and source aliases are:

- `free`, `discretionary`, or `LF`;
- `fixed`, `non-discretionary`, or `LN`;
- `as_input` or `LB`; and
- `as_output` or `LG`.

As-input ownership belongs to the recipient process. As-output ownership
belongs to the supplier process. These are score-attribution rules:
supplier-recipient continuity remains active for every link kind.

## Process carry-overs

```{autoclass} deapack.ProcessCarryOverSpec
:members:
```

Each declaration assigns one good, bad, free, or fixed state account to one
process.

## Dynamic-network specification

```{autoclass} deapack.DynamicNetworkSBMSpec
:members:
```

## Tone--Tsutsui dynamic network SBM

```{autoclass} deapack.ToneTsutsuiDynamicNetworkSBM
:members:
```

`DynamicNetworkSBM` is an exact alias for
`ToneTsutsuiDynamicNetworkSBM`.

See {doc}`../models/tone-tsutsui-dynamic-network-sbm` for the source
equations, complete synthetic example, result tables, sparse performance
contract, failure behavior, and terminal-index disclosure.

## Minimal executable pattern

```python
from deapack import (
    DynamicNetworkData,
    DynamicNetworkSBM,
    DynamicNetworkSBMSpec,
    LinkSpec,
    NetworkSpec,
    ProcessSpec,
    dataset_info,
    load_dataset,
)

frame = load_dataset("dynamic_network_power_demo")
roles = dataset_info("dynamic_network_power_demo").roles
network = NetworkSpec(
    processes=(
        ProcessSpec(
            "generation",
            roles["generation_inputs"],
            (
                *roles["generation_outputs"],
                *roles["generation_to_grid"],
            ),
        ),
        ProcessSpec(
            "grid",
            (
                *roles["generation_to_grid"],
                *roles["grid_inputs"],
            ),
            roles["grid_outputs"],
        ),
    ),
    links=(
        LinkSpec(
            "power_handoff",
            "generation",
            "grid",
            roles["generation_to_grid"],
        ),
    ),
)
spec = DynamicNetworkSBMSpec(
    network=network,
    link_kinds={"power_handoff": "free"},
)
data = DynamicNetworkData.from_frame(
    frame,
    spec=spec,
    dmu=roles["dmu"],
    period=roles["period"],
)
result = DynamicNetworkSBM().fit(data)
```

The compact fit uses a two-process subset of the teaching panel. The complete
model page declares all three processes and all four carry-over roles.
