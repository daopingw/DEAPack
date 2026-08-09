# Radial group and metafrontier analysis

```{eval-rst}
.. currentmodule:: deapack
```

`RadialMetafrontierDEA` fits one radial frontier for every declared group and one
radial metafrontier to the pooled observations. It implements the
O'Donnell--Rao--Battese deterministic DEA account:

$$
\text{metafrontier efficiency}
=
\text{group efficiency}
\times
\text{metatechnology ratio}.
$$

The metatechnology ratio (MTR) is also historically called the technology gap
ratio (TGR). A larger MTR means that the group frontier is closer to the
pooled metafrontier at the evaluated input-output mix. It is not a second
managerial-efficiency score.

`MetafrontierDEA` is its concise exact alias; both names identify the same
implementation, while `RadialMetafrontierDEA` is the canonical API symbol.

## Fit the built-in analytic example

The `metafrontier_groups` dataset contains six organizations in two declared
technology groups:

```python
from deapack import (
    DEAData,
    RadialMetafrontierDEA,
    dataset_info,
    load_dataset,
)

frame = load_dataset("metafrontier_groups")
roles = dataset_info("metafrontier_groups").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    group=roles["group"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = RadialMetafrontierDEA().fit(data)
result.summary()[
    [
        "dmu_id",
        "group",
        "group_efficiency",
        "meta_efficiency",
        "metatechnology_ratio",
        "decomposition_certified",
    ]
]
```

The default profile is output oriented and VRS, matching the primary
article's main DEA specification.

| DMU | Group efficiency | Meta efficiency | MTR/TGR |
|---|---:|---:|---:|
| A | 1.00 | 0.50 | 0.50 |
| B | 1.00 | 0.50 | 0.50 |
| C | 0.50 | 0.25 | 0.50 |
| D | 1.00 | 1.00 | 1.00 |
| E | 1.00 | 1.00 | 1.00 |
| F | 1.00 | 1.00 | 1.00 |

For DMU C, the certified identity is

$$
0.25=0.50\times0.50.
$$

## Programmes and score conventions

For observation $o$, let $S=G$ denote its declared group reference and
$S=M$ the pooled meta reference. The output-oriented programme is

$$
\begin{aligned}
\phi_o^S=\max_{\phi,\lambda}\quad &\phi\\
\text{subject to}\quad
&X_S\lambda\leq x_o,\\
&Y_S\lambda\geq\phi y_o,\\
&\mathbf 1^\top\lambda=1
  &&\text{under VRS only},\\
&\lambda\geq0.
\end{aligned}
$$

The reported efficiency is $E_o^S=1/\phi_o^S$. The input-oriented
programme is

$$
\begin{aligned}
\theta_o^S=\min_{\theta,\lambda}\quad &\theta\\
\text{subject to}\quad
&X_S\lambda\leq\theta x_o,\\
&Y_S\lambda\geq y_o,\\
&\mathbf 1^\top\lambda=1
  &&\text{under VRS only},\\
&\lambda\geq0,
\end{aligned}
$$

and reports $E_o^S=\theta_o^S$. Use
`orientation="input"` or `"output"` and
`returns_to_scale="crs"` or `"vrs"`. NIRS and NDRS are intentionally outside
this source leaf.

For matched certified solves,

$$
E_o^M\leq E_o^G,\qquad
MTR_o=\frac{E_o^M}{E_o^G}\in(0,1].
$$

The output summary retains `group_phi` and `meta_phi`; the input summary
retains `group_theta` and `meta_theta`.

## Declared groups and data validation

Group membership is part of `DEAData`:

```python
data = DEAData.from_frame(
    frame,
    dmu="organization",
    group="technology_group",
    inputs=["labor", "capital"],
    outputs=["service"],
)
```

The operator requires:

- finite, nonnegative input and desirable-output quantities;
- at least one positive input and output for every observation;
- one non-missing group label per observation;
- at least two nonempty groups; and
- common variable meanings, units, and organizational missions across groups.

Groups are treated as declared ex ante. The fit does not cluster
organizations, select the number of groups, or search for a score-maximizing
partition. It is also not a conditional-frontier estimator: continuous or
discrete operating conditions do not locally reweight the opportunity set.
Undesirable outputs require a separately specified environmental technology
and are rejected here.

The method registry describes declared membership as the internal
`reference.group` component. That label is used by this composed analysis; it
is not a standalone public reference-policy constructor or fitted result.

## Pooled convexification

Under VRS, each group frontier is a convex hull of its own observations. The
metafrontier is a second convex hull formed by pooling all groups. Its peer
plan may therefore combine organizations from different operating
environments.

This is recorded as
`result.metadata["metafrontier_construction"] == "pooled_convex"`. Under CRS
the construction is `pooled_conic`. Neither construction is the nonconvex
union of separately estimated group technologies.

Likewise, `technology.meta.pooled_convex` names the VRS technology component
inside this radial analysis. It is not a generic public meta-technology
constructor, and it does not imply that nonconvex, directional, slack-based,
or environmental metafrontiers are implemented.

Cross-group virtual combinations may be informative but operationally
unavailable. Inspect meta peers before presenting their target as an
implementable plan:

```python
result.peers("C")[
    [
        "frontier_level",
        "reference_dmu_id",
        "reference_group",
        "lambda",
    ]
]
```

`frontier_level` is `"group"` or `"metafrontier"`. Group peers are restricted
to the evaluated observation's declared group; metafrontier peers can come
from any declared group.

## Targets, slacks, and phase policy

The source-faithful default is `compute_slacks=False`. It performs two
phase-one radial solves per observation—one group solve and one pooled meta
solve—and returns empty target and slack tables. Phase-one
`intensities`, `peers()`, and duals remain available without adding solves.
They describe one solver-selected radial optimum and can be nonunique.

Set `compute_slacks=True` to follow each group and meta radial optimum with
DEAPack's lexicographic slack refinement. Targets, slacks, intensities, and
diagnostics retain their `frontier_level`. Slack completion may select
different intensities and duals from the phase-one-only fit.

```python
diagnostic_result = RadialMetafrontierDEA(
    compute_slacks=True,
).fit(data)

diagnostic_result.targets_for("C")[
    ["frontier_level", "role", "variable", "observed", "target"]
]
```

DMU C's output-oriented group target is four services; its metafrontier
target is eight. Peer intensities can be nonunique even when the efficiencies
are unique.

The ordinary fit therefore needs no additional flag for a score-only job:

```python
result = RadialMetafrontierDEA().fit(data)
```

It reports the complete radial decomposition while avoiding the optional
slack-refinement solves.

## Panel reference policy

For panel data, the source profile pools **all study periods** at both
levels. Every group receives one time-invariant frontier using all of its
period observations, and the metafrontier pools every group and period.

The metadata value is
`temporal_information_set="all_study_periods_pooled"`. This is a
retrospective fixed-sample account. It is not a contemporaneous, sequential,
window, or biennial frontier, and it is not a productivity index.

For a cross section, the metadata records
`"cross_section_not_applicable"` because there is no temporal information
choice.

## Result and failure contract

The main summary fields are:

| Field | Meaning |
|---|---|
| `score` | native MTR, released only when the complete decomposition is certified |
| `score_valid` | exact Boolean alias of `decomposition_certified` for the native MTR claim |
| `score_status` | semantic release reason for `score`, independent of a backend's raw status |
| `solver_status` | semantic outer status for the group/meta decomposition |
| `group_efficiency` | radial efficiency against the declared group frontier |
| `metafrontier_efficiency` | radial efficiency against the pooled metafrontier |
| `meta_efficiency` | exact convenience alias of `metafrontier_efficiency` |
| `metatechnology_ratio` | canonical MTR field |
| `technology_gap_ratio` | historical TGR alias with the same values |
| `reconstruction_residual` | absolute identity residual $\lvert E^M-E^G\times MTR\rvert$ |
| `decomposition_certified` | component optimality, nestedness, bounds, and identity all pass |
| `is_metafrontier_efficient` | whether the selected radial metafrontier criterion attains one |
| `is_efficient` | nullable Pareto--Koopmans status inherited from the pooled metafrontier solve's slack completion |
| `group_solver_status` | semantic group phase-one status after LP and economic certification |
| `metafrontier_solver_status` | corresponding semantic pooled phase-one status |
| `group_backend_solver_status` / `group_raw_solver_status` | group phase-one backend termination retained without semantic promotion |
| `metafrontier_backend_solver_status` / `metafrontier_raw_solver_status` | corresponding pooled backend termination; `meta_*` spellings are convenience aliases |
| `group_score_valid` / `group_score_status` | validity and semantic release reason for the group radial score |
| `metafrontier_score_valid` / `metafrontier_score_status` | corresponding pooled radial-score evidence, with exact `meta_*` aliases |
| `group_completion_valid` / `group_completion_status` | validity and status of requested group slack completion; validity is missing when not requested |
| `metafrontier_completion_valid` / `metafrontier_completion_status` | corresponding pooled completion evidence, with exact `meta_*` aliases |
| `group_target_valid` / `group_target_status` | availability and status of the group target account |
| `metafrontier_target_valid` / `metafrontier_target_status` | corresponding pooled target evidence, with exact `meta_*` aliases |
| `group_peer_valid` / `group_peer_status` | validity and release reason for the displayed group peer account after reporting thresholds |
| `metafrontier_peer_valid` / `metafrontier_peer_status` | corresponding pooled peer evidence, with exact `meta_*` aliases |
| `group_dual_valid` / `group_dual_status` | completeness and release reason for the group radial dual account |
| `metafrontier_dual_valid` / `metafrontier_dual_status` | corresponding pooled dual evidence, with exact `meta_*` aliases |

`score` contains the MTR; standardized `efficiency` contains metafrontier
efficiency. Prefer the named component columns in reports.

The outer `solver_status` vocabulary is exactly `optimal`,
`component_failure`, `invalid_component`, `undefined_ratio`, or
`certificate_failure`. Its paired `score_status` is respectively `defined` or
one of `unavailable_component_solver_failure`,
`unavailable_uncertified_component_score`,
`undefined_nonpositive_group_efficiency`, and
`unavailable_failed_decomposition_certificate`. A backend can therefore report
an optimal component solve while the outer MTR remains unavailable.

The group and pooled `*_solver_status` fields use the radial phase-one semantic
vocabulary: `optimal`, `limit_reached`, `infeasible`, `unbounded`,
`numerical_error`, or `failed`. A backend-optimal solution rejected by either
the solver-neutral LP certificate or the economic reconstruction is therefore
`numerical_error`, while the paired `*_backend_solver_status` and
`*_raw_solver_status` still record `optimal`. Score, completion, target, peer,
and dual status fields preserve the underlying radial release reason rather
than inferring availability from raw termination. Controlled successful states are
`defined` for a component score; `certified` for completion;
`certified_slack_completion` for a completed target or peer account;
`certified_primary_program` for a score-only peer or dual account; and
`certified_primary_program_after_completion` for a primary dual retained after
completion. `not_requested`, `not_available_without_certified_primary`, the
relevant solver/certificate failure,
`unavailable_after_peer_reporting_threshold`, and
`unavailable_incomplete_primary_dual_account` remain explicit non-release
states.

Radial efficiency equal to one need not rule out a residual output shortfall
or input excess. With `compute_slacks=True`, the generic `is_efficient` field
therefore uses the pooled metafrontier solve's completed slack assessment
rather than copying `is_metafrontier_efficient`. With
`compute_slacks=False`, the generic field remains missing.

Component failures are fail-closed. An available group result may remain
visible when its meta solve fails, but meta efficiency, MTR, and
`decomposition_certified` are withheld. A nesting or identity violation is
reported rather than repaired by clipping the ratio to one.

Certificate tolerances govern residual, bound, nestedness, and reconstruction
checks; they are not a minimum economically meaningful efficiency or MTR. Any
finite, strictly positive certified group efficiency remains a valid ratio
denominator, and a strictly positive MTR is preserved even when it is smaller
than the numerical tolerance. Only values numerically indistinguishable from
one receive near-one display cleanup. Zero or non-finite denominators fail
closed rather than being replaced or thresholded.

The MTR decomposition depends on the two primary score certificates, not on
optional target completion. Thus a certified group/meta efficiency identity
can remain available when a secondary target search fails; the completion and
target fields then state explicitly that no strong-efficiency or target claim
may be taken from that component. Conversely, a raw `optimal` solver status
does not rescue a component whose radial postsolve certificate failed.

Solver accounting comes from the child radial results' metadata, not from
counting diagnostic rows. `primary_solver_calls` sums all group and pooled
phase-one calls; `secondary_solver_calls` sums the optional group and pooled
slack-completion calls; `solver_calls` is their total. The synonymous
`phase_one_solver_calls` and `phase_two_solver_calls` remain available. For
the six-organization example, score-only fitting reports 12 primary, zero
secondary, and 12 total calls; certified slack completion reports 12, 12, and
24. Postsolve certification reuses those solutions, so
`additional_solver_calls` and `certificate_extra_solver_calls` are always
zero.

## One-command decomposition figure

Install the optional visualization backend with
`python -m pip install 'DEAPack[viz]'`, then use:

```python
figure = result.plot(kind="metafrontier")
figure.savefig(
    "metafrontier-decomposition.png",
    dpi=200,
    bbox_inches="tight",
)
```

The dedicated figure keeps all three certified quantities together. For each
organization, one marker reports efficiency against its declared-group
frontier, a second reports efficiency against the pooled metafrontier, and the
connector identifies them as two benchmark results for the same observation.
The connector's length is not a decomposition component. The row reports the
MTR, so the identity

$$
E_o^M=E_o^G\times MTR_o
$$

remains visible. Organizations are grouped by their declared group rather than
re-ranked by one component. The connector only links the two benchmark results;
the MTR is the opportunity-proximity account, not a causal allocation of
responsibility between management and environment.

The plot is available only for the certified classic radial group/meta result.
It verifies the exact method identity, orientation, CRS/VRS pooled
construction, fitted time-information policy, both component score
certificates, the fitted three-row component ledger, both phase-one diagnostic
certificates, nestedness and ratio bounds, and the reported identity. A row
that does not claim a certified decomposition is omitted and counted. A row
that claims certification without complete component evidence, disagrees with
the ledger, or does not reconstruct the bounded identity causes plotting to
fail closed rather than display a repaired account. If no certified rows
remain, no figure is produced.

For a multi-period panel, select the displayed period explicitly:

```python
panel_figure = panel_result.plot(
    kind="metafrontier",
    period=2025,
)
```

This selection does not refit a contemporaneous frontier: the source profile
still uses the all-study-period pooled reference policy described above. The
dedicated plot rejects `metric`, `dmu_id`, and `variable` and currently supports
only `view="auto"`.

### Keep the performance plot for one indicator

When the reporting question concerns only one registered quantity, the generic
performance plot remains available. For example, an MTR ranking or ECDF uses:

```python
mtr_figure = result.plot(
    kind="performance",
    metric="metatechnology_ratio",
)
```

The benchmark is one, and a larger MTR means closer proximity between the
declared-group frontier and the pooled meta opportunity at that evaluated
mix. This is not a preference ordering over managers or organizations. The
same generic contract can display `group_efficiency` or
`metafrontier_efficiency` as a single metric. It does not reconstruct the
three-part decomposition and does not turn MTR into a management score. See
{doc}`../user-guide/visualization` for both visualization contracts.

## Interpretation and source boundary

The decomposition is an accounting identity, not a causal allocation of
responsibility. Unmeasured service quality, case mix, capital vintage, demand,
data error, and group selection can affect all three values. Report group
definitions, orientation, RTS, pooled construction, time policy, and both
component scores.

The implementation follows [O'Donnell, Rao, and Battese
(2008)](https://doi.org/10.1007/s00181-007-0119-4). Their illustrative
application uses 97 countries over 1986--1990, one agricultural output, and
five inputs. The complete observation-level panel and original DEAP control
files are not available with the paper. DEAPack verifies the published DEA
programmes with the transparent `metafrontier_groups` analytic oracle; it
does not claim to reproduce the FAO application.

```{autosummary}
RadialMetafrontierDEA
MetafrontierDEA
```
