# Lewis--Sexton sequential network DEA

```{eval-rst}
.. currentmodule:: deapack
```

`LewisSextonSequentialNetworkDEA` implements the linear forward-quantity
slice of the sequential network method developed by
[Lewis and Sexton (2004)](https://doi.org/10.1016/S0305-0548(03)00095-9).
It asks what the organization could accomplish if an improved plan selected
for one process became an operating condition for the processes that depend
on it.

The canonical method ID is
`network.sequential.lewis_sexton_2004.forward_radial`.

## What “sequential” means

Each process is first treated as a hypothetical sub-DMU and receives an
ordinary radial appraisal against the corresponding processes of the
reference organizations. Those initial appraisals are not yet the
organizational result. DEAPack then propagates the selected process
projections through the declared directed acyclic graph:

1. Under **output orientation**, source-process output targets replace the
   evaluated quantities of their outgoing links.
2. A downstream process is re-appraised using those propagated link
   quantities as inputs.
3. Its selected output targets are passed onward, and the procedure continues
   in topological order.

Input orientation follows the same managerial logic in reverse. A sink
process is appraised first; its selected input requirements replace the link
outputs facing its suppliers; and upstream processes are re-appraised in
reverse topological order.

The class therefore reports two process accounts:

- `phase == "initial"` contains the independent radial appraisal of every
  process; and
- `phase == "propagated"` contains the appraisal after relevant downstream
  or upstream operating conditions have been replaced.

A source under output orientation, or a sink under input orientation, has no
affected link and reuses its certified initial solution.

```{important}
Propagation uses a solver-selected primary radial projection. Radial
efficiency can be unique while the peer mixture and target quantities are
not. A different optimal projection may therefore support a different
propagated operating plan. DEAPack records
`targets_may_be_nonunique=True`; it does not add an undocumented secondary
target-selection rule.
```

## The organizational bottleneck account

The sequential process plans produce one target for every external endpoint.
Lewis and Sexton aggregate an external quantity type across component
processes before comparing target with observed performance. The current
graph contract requires one declared owner for each system endpoint type, so
that sum collapses to the target of its owning process.

For output orientation, let

$$
q_{ro}
=
\frac{\sum_s \widehat y_{rso}}
       {\sum_s y_{rso}}
$$

be the propagated target-to-observed ratio for final-output type $r$. The
organizational expansion factor and the reported higher-is-better efficiency
are

$$
\Phi_o=\min_r q_{ro},
\qquad
E_o=\frac{1}{\Phi_o}.
$$

The minimum is the system bottleneck. A proportional organization-wide
expansion cannot exceed the least-expanded final result, even if another
result has a more ambitious selected target.

For input orientation, define

$$
p_{io}
=
\frac{\sum_s \widehat x_{iso}}
       {\sum_s x_{iso}}.
$$

The organizational input factor is

$$
\Theta_o=\max_i p_{io},
\qquad
E_o=\Theta_o.
$$

Here the maximum is the bottleneck: it is the largest retained-resource
share, hence the resource type that limits a common proportional contraction.
Under a valid self-inclusive reference population, both reporting
conventions place efficiency at one and report larger values as better.

## Reproducing the source illustration

The source's two-organization illustration has two upstream processes feeding
one downstream process. Organization A can double the first handoff while
the second handoff is already radially efficient; organization B has the
opposite upstream pattern.

```python
import pandas as pd

from deapack import (
    LewisSextonSequentialNetworkDEA,
    LinkSpec,
    NetworkData,
    NetworkSpec,
    ProcessSpec,
)

frame = pd.DataFrame(
    {
        "dmu": ["A", "B"],
        "x1": [1.0, 1.0],
        "x2": [1.0, 1.0],
        "y1": [5.0, 10.0],
        "y2": [10.0, 5.0],
        "z1": [20.0, 20.0],
    }
)

spec = NetworkSpec(
    processes=(
        ProcessSpec("p1", inputs="x1", outputs="y1"),
        ProcessSpec("p2", inputs="x2", outputs="y2"),
        ProcessSpec("p3", inputs=("y1", "y2"), outputs="z1"),
    ),
    links=(
        LinkSpec("p1_to_p3", source="p1", target="p3", variables="y1"),
        LinkSpec("p2_to_p3", source="p2", target="p3", variables="y2"),
    ),
)

data = NetworkData.from_frame(frame, dmu="dmu", spec=spec)
result = LewisSextonSequentialNetworkDEA(
    orientation="output",
    returns_to_scale="crs",
).fit(data)

result.summary()[[
    "dmu_id",
    "organizational_factor",
    "system_efficiency",
    "is_sequentially_efficient",
    "score_status",
]]
```

The reproduced organizational expansion factor is $4/3$ for both
organizations, so their reported system efficiency is $3/4$ and
`is_sequentially_efficient` is false. `is_measure_efficient` is the
same method-specific boundary classification. The generic `is_efficient`
field is deliberately missing: sequential radial bottleneck efficiency is
not a Pareto--Koopmans certificate for one simultaneously optimized network
technology. Inspect the initial and propagated process accounts separately:

```python
result.components[[
    "dmu_id",
    "phase",
    "process_id",
    "radial_factor",
    "efficiency",
    "solve_reused",
]]

result.links[[
    "dmu_id",
    "link_id",
    "observed",
    "transmitted_quantity",
    "upstream_supply_target",
    "downstream_requirement_target",
    "disposable_surplus",
]]
```

`targets`, `intensities`, `components`, and `links` retain the selected
process plan. `diagnostics` records solver and primal--dual certification for
every initial and propagated programme. If any required programme or link
balance cannot be certified, the organizational result fails closed rather
than being assembled from partial process results.

## Returns to scale and references

`returns_to_scale` accepts one value for every process or a complete mapping:

```python
model = LewisSextonSequentialNetworkDEA(
    orientation="input",
    returns_to_scale={
        "p1": "crs",
        "p2": "vrs",
        "p3": "nirs",
    },
)
```

Every process uses its own reference intensities and its own declared
CRS, VRS, NIRS, or NDRS restriction. A mapping must name every process
exactly once. `reference` uses the standard DEAPack reference-population
contract; changing the reference population changes every local appraisal
that depends on it.

## Not a simultaneous joint network model

Sequential network DEA is not an alias for any jointly optimized network
technology. In particular, it is distinct from:

- Färe--Grosskopf connected network envelopment;
- Kao--Hwang relational decomposition;
- additive process-efficiency decompositions; and
- Tone--Tsutsui network SBM.

Those methods impose their link commitments while solving one simultaneous
system programme or one common multiplier account. The Lewis--Sexton
procedure instead solves process programmes in sequence and makes a selected
local target the next process's evaluated operating condition. The
technologies, objectives, system scores, and target-selection consequences
can therefore differ even when the same graph and data are used.

## Implemented boundary

This method leaf supports:

- nonnegative forward quantities;
- a directed acyclic graph, including series, fork, and join structures;
- one global input or output orientation;
- process-specific CRS, VRS, NIRS, or NDRS assumptions;
- process-specific reference intensities;
- upstream supply at least as large as downstream requirement, with any
  difference reported as disposable link surplus; and
- distinct external input and output types with one declared owning process.

It deliberately excludes reverse quantities, mixtures of forward and reverse
quantities, cycles, site-characteristic adjustments, mixed process
orientations, shared reference intensities, shared resource allocation,
undesirable link technology, and aggregation of the same external endpoint
type across several processes. These are different model identities, not
configuration flags for the implemented linear forward-quantity method.
