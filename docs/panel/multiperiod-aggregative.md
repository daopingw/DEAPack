# Park--Park multi-period aggregative DEA

```{eval-rst}
.. currentmodule:: deapack
```

`ParkParkMultiperiodAggregativeDEA` implements the two-phase multi-period
aggregative efficiency method of
[Park and Park (2009)](https://doi.org/10.1016/j.ejor.2007.11.028).
Its canonical method ID is
`panel.multiperiod_aggregative.park_park_2009`.
`MultiperiodAggregativeDEA` is an exact API alias.

The method returns one rating for each organization's complete balanced
record. Every period retains a separate contemporaneous peer plan, but one
input contraction factor or output expansion factor must be feasible in all
periods. There is no carry-over, state transition, pooled-period technology,
or productivity-change decomposition.

## Source model

For organization $o$ and period $t$, let $X^t$ and $Y^t$ be the
contemporaneous input and desirable-output matrices. The output-oriented VRS
first phase is

$$
\begin{aligned}
\max_{\phi,\{\lambda^t\}}\quad &\phi\\
\text{s.t.}\quad
&X^t\lambda^t\leq x_o^t,\\
&Y^t\lambda^t\geq\phi y_o^t,\\
&\mathbf 1^\top\lambda^t=1,\qquad
\lambda^t\geq0,
\quad t=1,\ldots,T .
\end{aligned}
$$

The input-oriented first phase minimizes one common $\theta$ subject to
$X^t\lambda^t\leq\theta x_o^t$ and
$Y^t\lambda^t\geq y_o^t$. Under CRS, every period-specific convexity
equation is removed.

Phase 2 fixes the certified first-phase factor and maximizes the source's raw
sum of input and output slacks. This is a strict lexicographic solve: the
radial optimum cannot be traded for additional slack.

```{important}
The secondary objective is expressed in the variables' original units.
Radial factors and the full/weak/inefficient classification are invariant to
independent positive unit changes, but a solver-selected phase-2 target can
change when several optima exist. Peers and individual targets are therefore
reported with `target_uniqueness="not_tested"`.
```

## Minimal example

```python
from deapack import (
    DEAData,
    ParkParkMultiperiodAggregativeDEA,
    dataset_info,
    load_dataset,
)

dataset_name = "multiperiod_trajectory_contrast"
frame = load_dataset(dataset_name)
roles = dataset_info(dataset_name).roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    period=roles["period"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = ParkParkMultiperiodAggregativeDEA(
    orientation="output",
    returns_to_scale="vrs",
).fit(data)
result.summary()[[
    "dmu_id",
    "score",
    "efficiency",
    "efficiency_class",
    "is_efficient",
]]
```

The project-authored panel deliberately contains full, weak, and inefficient
trajectories. `score` retains the source-native factor, while `efficiency`
uses the documented higher-is-better convention. The tests reconstruct every
period target and distinguish radial efficiency from strong completion
without embedding a published result vector.

Input orientation places $\theta$ in both `score` and `efficiency`.

## Result contract

`summary()` contains one row per organization, with `period=None`.

| Field | Meaning |
|---|---|
| `score` / `native_factor` | source-native $\theta$ or $\phi$ |
| `efficiency` | higher-is-better $\theta$ or $1/\phi$ |
| `is_radially_efficient` | factor is one within the declared tolerance |
| `is_efficient` | factor is one and no scale-material phase-2 slack remains |
| `is_weakly_efficient` | factor is one but a material slack remains |
| `efficiency_class` | `full`, `weak`, `inefficient`, or a failure-specific state |
| `score_status` | certification state of phase 1 |
| `target_status` | certification state of mandatory phase 2 |
| `raw_total_slack` | source phase-2 slack total in original units |
| `normalized_total_slack` | diagnostic sum after variable-scale normalization |
| `max_normalized_slack` | scale-aware strong-efficiency diagnostic |

The explanatory tables are period-specific:

- `components` reports the slack account and selected-peer count for each
  period;
- `slacks` and `targets` report every input and output account;
- `intensities` reports positive phase-2 $\lambda^t$ values; and
- `diagnostics` records both solves, primal--dual certification, and
  recomputed economic-constraint residuals.

`result.plot(metric="efficiency")` creates the standard higher-is-better
performance display. `result.plot(metric="score")` retains the native
lower-is-better output-$\phi$ convention. Plot discovery is available through
`result.available_plots()` without importing a plotting backend.

If phase 1 cannot be certified, the model fails closed and does not run phase
2. If phase 1 is certified but phase 2 is not, the radial `score` and
`efficiency` remain available. Targets, slacks, intensities, components, and
the generic strong-efficiency classification are withheld.

## Data and parameter domain

The public source preset requires:

- a `DEAData` panel with at least two periods;
- exactly one observation for every organization--period pair;
- the same organization cohort in every period;
- finite nonnegative inputs and desirable outputs;
- positive aggregate input and output for every row;
- no undesirable outputs, polluting-input declaration, or group-specific
  technology;
- `orientation="input"` or `"output"`;
- `returns_to_scale="crs"` or `"vrs"`; and
- `reference="auto"` or `"contemporaneous"`.

NIRS, NDRS, mixed period-specific returns to scale, window/global/custom
references, time-preference weights, assurance regions, bad outputs, and
unbalanced-panel imputation are outside the Park--Park 2009 method identity.

## Computational behavior

The period technologies are compiled once as sparse diagonal blocks. Each
organization requires two LPs when both phases are certified. With $n$
organizations, $T$ periods, $m$ inputs, and $s$ outputs:

- phase 1 has $nT+1$ variables and $T(m+s)$ production rows, plus $T$
  VRS equations when applicable;
- phase 2 has $nT+T(m+s)$ variables and $T(m+s)$ production-account
  equations, plus the optional $T$ VRS equations; and
- memory for the compiled technology is sparse in the period blocks rather
  than a dense all-period matrix.

Use solver time limits through `SolverOptions`. A time-limited phase 2 follows
the partial-result policy above instead of discarding a certified radial
rating.

## Method boundary

Use this estimator when the decision maker needs one joint rating for several
completed operating periods and no interperiod stock equation belongs in the
production technology. Use:

- separate annual DEA for separate annual decisions;
- a productivity index for change in productivity or best practice;
- window DEA for a rolling reference-population question; or
- dynamic DEA when investment, capacity, inventory, backlog, debt, knowledge,
  or another state connects adjacent operating plans.

This source-specific aggregation protocol is distinct from the dynamic
technology family: a common rating over completed periods is not a
state-dependent production technology. It therefore has its own documented
method identity and result contract.
