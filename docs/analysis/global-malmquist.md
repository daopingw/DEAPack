# Global Malmquist productivity index

```{eval-rst}
.. currentmodule:: deapack
```

`GlobalMalmquistProductivityIndex` implements the circular Pastor--Lovell
index. `GlobalMalmquistDEA` is its discoverability alias. One pooled frontier
contains observations from every sample period; contemporaneous frontiers are
retained for the decomposition.

## Fit a global productivity model

The synthetic panel below contains five organizations over three periods,
with one resource input and one service output:

```python
from deapack import DEAData, GlobalMalmquistDEA, load_dataset

frame = load_dataset("multiperiod_trajectory_contrast")
data = DEAData.from_frame(
    frame,
    dmu="unit_id",
    period="period",
    inputs="resource_index",
    outputs="service_units",
)
result = GlobalMalmquistDEA(
    orientation="output",
    returns_to_scale="crs",
).fit(data)
result.summary()
```

Read `productivity_change`, `efficiency_change`, and `best_practice_change`.
Values above one indicate improvement; check `score_valid` before interpreting
them. For `trajectory_02`, the example gives:

| Transition | Productivity change | Efficiency change | Best-practice change |
|---|---:|---:|---:|
| 1 to 2 | 2.00 | 1.60 | 1.25 |
| 2 to 3 | 1.50 | 1.25 | 1.20 |

The two components multiply to the headline index. These results describe
the project's fictional trajectories, not a reproduction of the source
article's empirical application.

## Definition and decomposition

Let $d^G(z)$ be the selected input- or output-oriented Farrell
efficiency-form distance under the pooled global technology. Then

$$
GM^{t,t+1}=\frac{d^G(z^{t+1})}{d^G(z^t)}.
$$

The contemporaneous efficiency-change component is

$$
EC_G^{t,t+1}=\frac{d^{t+1}(z^{t+1})}{d^t(z^t)}.
$$

For a plan observed in period $\sigma$, the contemporaneous restriction sets
the reference period to the same date. Define
$BPG^\sigma=d^G(z^\sigma)/d^\sigma(z^\sigma)$. Best-practice change is

$$
BPC_G^{t,t+1}=\frac{BPG^{t+1}}{BPG^t},\qquad
GM=EC_G\times BPC_G.
$$

`best_practice_change` stores $BPC_G$. `technical_change` mirrors it for the
common result schema. Values above one indicate improvement for every
multiplicative component.

## Solves and circularity

Each transition uses `base_on_global`, `comparison_on_global`,
`base_on_base`, and `comparison_on_comparison`. There is no evaluation of an
observation against the other period's technology, so the cross-period radial
infeasibilities associated with the geometric Malmquist index do not arise.

With one fixed global technology,
$GM^{t,t+1}GM^{t+1,t+2}=GM^{t,t+2}$. This is sample-specific circularity:
adding a period can expand the global frontier, so all global distances and
historical indexes must be recomputed.

## Selecting the dates to compare

By default, the model compares consecutive periods
(`comparison_pairs="adjacent"`). Using the same `data`, request every forward
pair or choose a particular pair:

```python
# Compare all forward pairs.
all_pairs = GlobalMalmquistDEA(comparison_pairs="all").fit(data)

# Compare period 1 with period 3.
endpoint = GlobalMalmquistDEA(comparison_pairs=[(1, 3)]).fit(data)
```

An explicit selection must be a nonempty ordered sequence of unique
`(base_period, comparison_period)` tuples. Both labels must occur in the panel,
and every pair must be forward in the declared period order; self, reverse,
unknown, duplicate, and malformed pairs are rejected. The order supplied by
the analyst is retained in the result.

`unbalanced="drop"` and `"raise"` operate separately on each selected pair.
Dropping an unmatched recipient does not remove its valid observation from the
fixed global frontier. This distinction is important when entry or exit helps
define sector best practice even though the organization has no change account
for one pair.

For a balanced panel with $D$ organizations and $P$ periods, adjacent output
has $D(P-1)$ rows. Opt-in all-pairs output has
$DP(P-1)/2=O(DP^2)$ rows, with four diagnostics and potentially several peer
records per row. Distance work does not grow in the same way: the cache needs
at most one own-period and one global solve per observation, or $2DP=O(DP)$
solves, and assembles nonadjacent ratios without another optimization. The
quadratic result materialization is why `"all"` is not the default.

All pairwise rows use the same retrospective information vintage. A direct
2020--2025 row answers how the organization's observed production performance
changed between those two dates under that one common benchmark. It is not
extra evidence about why the change occurred. Do not combine direct or chained
values from different vintages.

For an unambiguous performance chart, fit the one pair that the figure is meant
to communicate:

```python
endpoint.plot(
    kind="performance",
    metric="productivity_change",
    period=3,
    view="points",
)
```

An all-pairs result can contain several base periods for the same organization
and comparison period. Filter both period columns for tables, or refit that
single explicit pair before plotting rather than allowing a chart to hide the
base-date distinction.

## Comparison with adjacent-period Malmquist

```python
from deapack import MalmquistDEA

adjacent = MalmquistDEA(
    orientation="output",
    returns_to_scale="crs",
).fit(data)
adjacent.summary()
```

For this one-input, one-output CRS example, adjacent and global Malmquist
give the same numerical headline and components. That equality is not a
general property: the adjacent index uses the two period-specific
technologies, whereas the global index uses one full-horizon reference.
With a different production geometry, these reference choices can lead to
different productivity accounts.

All available observations form the global frontier, including identifiers
that cannot be paired in every transition. `unbalanced="drop"` and `"raise"`
govern transition matching, not frontier construction.

## Four-task release contract

Each global transition is published only after its two own-period and two
global-reference radial programmes pass the shared solver-neutral LP
certificate and separate raw and published production-account
reconstructions. Those four positive distances must then reproduce the raw and
published $GM$, $EC_G$, both best-practice gaps, $BPC_G$, and
$GM=EC_G\times BPC_G$ account. A backend `"optimal"` label by itself does not
release the transition.

```python
result.summary()[[
    "score_valid",
    "score_status",
    "all_four_distance_programs_certified",
    "all_four_economic_distance_claims_certified",
    "multiplicative_account_certified",
    "peer_valid",
    "peer_status",
]]
```

If one programme or the complete multiplicative account fails, the headline,
four published distances, components, and peer rows are withheld for that
transition while role diagnostics preserve the raw backend status and failure
reason. Other transitions remain independent. Thresholded peer disclosure has
its own all-four-role gate: a failed displayed-peer reconstruction does not
invalidate an otherwise certified global productivity account.

The diagnostic table separates the LP, raw production, published production,
and peer certificates and records their finite residuals. Metadata reports
four logical distance requests per transition in `requested_distance_tasks`.
Because own-period and global evaluations can be reused across selected
transitions, `unique_distance_solves` can be smaller; `solver_calls` equals
that unique count, and `additional_solver_calls=0` records that certification
does not optimize again. Metadata also reports the contemporaneous plus global
compilations. `comparison_pair_mode`, `selected_period_pairs`,
`unmatched_comparison_pairs`, and `comparison_output_size_complexity` make the
enumeration and its output cost auditable.

```{important}
This contract belongs to the classic full-horizon Global Malmquist operator.
It does not confer the same claim on biennial, sequential-window,
environmental, or named decomposition variants.
```

## Scope

CRS is the classic default. Other returns-to-scale specifications are explicit
sensitivity variants. The class accepts inputs and desirable outputs;
environmental Global Malmquist--Luenberger indexes require a directional
technology with explicit undesirable-output assumptions.

## Validation boundary

The independent Pastor--Lovell certificate recompiles the output-oriented CRS
programmes without DEAPack's reference builder or radial solver helpers. Its
exact three-period panel closes all own-period and global distance roles, the
$GM=EC_G\times BPC_G$ account, peer provenance, coherent unit changes, and
fixed-vintage circularity. The public result is checked against those exact
values rather than against output from another DEAPack model. The same
three-period fixture also verifies direct endpoint release under `"all"` and
that all-pairs output reuses the adjacent task graph rather than adding solves.

This certificate supports the classic desirable-output CRS account with one
self-inclusive pooled raw-observation global technology. Input orientation and
non-CRS settings remain explicit package sensitivity specifications; CRS
input/output agreement has property-test support but is not a second source
certificate. Sequential, biennial, window, environmental, external-reference,
and leave-one-out technologies are outside this validation claim. No inference,
causal attribution, profitability or welfare conclusion, or reproduction of
the source article's empirical application is implied.

```{autosummary}
GlobalMalmquistProductivityIndex
GlobalMalmquistDEA
```
