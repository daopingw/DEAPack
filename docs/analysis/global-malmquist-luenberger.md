# Global Malmquist--Luenberger productivity index

```{eval-rst}
.. currentmodule:: deapack
```

`GlobalMalmquistLuenbergerProductivityIndex` implements Oh's circular GML
index. `GlobalMalmquistLuenbergerDEA` is its discoverability alias. All sample
periods contribute to one retrospective global environmental benchmark;
contemporaneous technologies remain available for decomposition.

The named class fixes the same CRS common-factor weak-disposal technology,
null-jointness condition, and observation-scaled `(0, y, b)` programme used
by the classic environmental index. Changing the direction, disposability, or
scale specification defines a different global environmental productivity
method; it is not a configurable form of Oh's GML index. The current public
class does not expose those alternatives under Oh's name. In particular,
adding a scale constraint to the bad-output equality does not create a
source-qualified non-CRS weak-disposal technology.

DEAPack operationalizes Oh's global technology as one pooled CRS conical DEA
envelope. Every observation in the fixed sample vintage may support the
benchmark, nonnegative activity combinations are allowed, and CRS permits
proportional replication. This executable envelope should not be read as a
claim that a literal union of period technologies equals its conical hull.

## Index and economic decomposition

For an evaluated plan from period $\sigma$, the observation-scaled direction
is $g^\sigma=(0,y^\sigma,b^\sigma)$. Thus

$$
GML^{t,t+1}
=\frac{1+D^G(z^t;g^t)}
       {1+D^G(z^{t+1};g^{t+1})}
=EC_G^{t,t+1}\times BPC_G^{t,t+1}.
$$

The contemporaneous operating-shortfall component is

$$
EC_G^{t,t+1}
=\frac{1+D^t(z^t;g^t)}
       {1+D^{t+1}(z^{t+1};g^{t+1})}.
$$

Oh writes the source-native best-practice gap as

$$
BPG^r
=\frac{1+D^r(z^r;g^r)}
       {1+D^G(z^r;g^r)}
\in(0,1],
$$

```{note}
Oh uses $r$ as a time-period label in this source expression. It is local to
the expression and is not DEAPack's desirable-output index. In the generic
package notation, source $r$ maps to evaluated period $\sigma$, while the
contemporaneous reference restriction sets $\tau=\sigma$.
```

and

$$
BPC_G^{t,t+1}
=\frac{BPG^{t+1}}{BPG^t}.
$$

With the same data and contemporaneous environmental technologies, $EC_G$ is
the same own-period operating-shortfall component as $EC_{ML}$. A value above
one records a reduction in that measured shortfall. $BPC_G>1$ records that the
comparison-period opportunity is closer to the fixed global benchmark than
the base-period opportunity. It is not the conventional CFG $TC_{ML}$:
$TC_{ML}$ uses two off-diagonal period-to-period evaluations. Neither
component identifies a causal effect of management, innovation, investment,
or policy.

## Distance roles and nonnegative domain

Each reported transition uses:

| Result field | Evaluated plan | Reference |
|---|---|---|
| `distance_base_on_base` | base period | base-period technology |
| `distance_comparison_on_comparison` | comparison period | comparison-period technology |
| `distance_base_on_global` | base period | pooled global technology |
| `distance_comparison_on_global` | comparison period | pooled global technology |

Every evaluated plan belongs to both its own-period technology and the pooled
global technology. Setting the improvement amount to zero is therefore
feasible, so these self-inclusive distances are nonnegative up to numerical
round-off. The Oh GML operator has no `comparison_on_base` or
`base_on_comparison` task and does not attach conventional ML's negative
cross-period-distance semantics to its own/global fields.

The fixed global technology gives circularity and removes the two
off-diagonal period-to-period solves from the overall index. Adding a period
can change the global benchmark and requires historical global distances to
be recomputed.

## Selecting the dates to compare

Oh's fixed-vintage ratio can compare any two dates under the same retrospective
global environmental benchmark. `comparison_pairs="adjacent"` remains the
backward-compatible default and reports consecutive pairs in
`data.period_order`. Two opt-in forms make a direct endpoint or complete
pairwise account explicit:

```python
# Every forward base/comparison pair in the declared period order.
all_pairs = GlobalMalmquistLuenbergerDEA(comparison_pairs="all").fit(data)

# Only the first-to-last environmental productivity comparison.
endpoint_pair = ((data.period_order[0], data.period_order[-1]),)
endpoint = GlobalMalmquistLuenbergerDEA(
    comparison_pairs=endpoint_pair,
).fit(data)
```

Here `data` denotes a validated environmental panel. A custom selection must
be a nonempty ordered sequence of unique `(base_period, comparison_period)`
tuples. Both labels must be present and each pair must be forward in the
declared period order. Self, reverse, unknown, duplicate, and malformed pairs
are rejected; valid custom order is preserved in the output.

`unbalanced="drop"` or `"raise"` is applied independently to each requested
pair. Dropping an unmatched change recipient does not delete its observation
from the global environmental benchmark. An entrant can therefore influence
the retrospective opportunity set even when it lacks an earlier plan needed
for a particular change account.

For $D$ organizations and $P$ balanced periods, `"all"` emits
$DP(P-1)/2=O(DP^2)$ transition rows. Diagnostics and reported peer rows inherit
that pairwise size. The optimization graph remains $O(DP)$: each observation
needs at most one contemporaneous and one global directional-distance solve,
and the cache assembles nonadjacent GML, EC, and BPC ratios without another LP.
The quadratic output cost is why all-pairs reporting is opt-in.

A direct 1990--2003 GML row says how the organization's joint useful-output and
undesirable-output performance changed between those dates relative to one
fixed full-horizon benchmark. It does not identify the contribution of
management, technology adoption, regulation, or any intermediate year. Direct
and chained comparisons agree by circularity only within the same global
sample vintage.

All-pairs results may contain several base dates for one organization and one
comparison date. For a clear chart, fit the one pair the figure is intended to
communicate:

```python
endpoint.plot(
    kind="performance",
    metric="productivity_change",
    period=data.period_order[-1],
    view="points",
)
```

For all-pairs tables, always filter both `base_period` and
`comparison_period`. This prevents a dashboard from silently combining
different management horizons.

## Certified own-period and global accounts

Each own-period and global distance is released only after the same
solver-neutral LP and common-factor environmental-production checks used by the
core environmental DDF. The transition-level certificate then reconstructs
`productivity_change`, `efficiency_change`, both best-practice gaps,
`best_practice_change`, its `technical_change` schema alias, and the complete
multiplicative identity. It also enforces the self-inclusive nonnegative-distance
domain and the source gap domain $(0,1]$.

If any one of the four tasks or the complete Oh account fails, the transition's
distances, components, headline, and peers are withheld atomically; raw task
diagnostics remain available. Thresholded peers have their own all-four-task
gate, so `peer_valid=False` can coexist with a certified index. These checks use
the already returned solver result and add no optimization task. In each task
diagnostic, `peer_valid` is the exact boolean alias of
`published_peer_account_certified`; the peer gate does not enter the score gate.

Runtime metadata reports four logical distance requests per matched transition
as `requested_distance_tasks`. `unique_distance_solves` counts the requests
left after cache reuse, `solver_calls` equals that unique count, and
`additional_solver_calls=0` makes the solver-neutral certification claim
directly auditable. `comparison_pair_mode`, `selected_period_pairs`,
`unmatched_comparison_pairs`, and `comparison_output_size_complexity` expose
the selected reporting horizon and its materialization cost.

## Exact analytical teaching cases

For the synthetic two-period plant
$(x,y,b)=(1,1,2),(1,2,1)$, the independent source LP gives

| Period | Own-period $D^r$ | Global $D^G$ | Source $BPG^r$ |
|---|---:|---:|---:|
| 0 | 0 | $3/5$ | $5/8$ |
| 1 | 0 | 0 | 1 |

Intensity $4/5$ on the period-1 activity supports the period-0 global
evaluation. Therefore

$$
GML=\frac85,\qquad EC_G=1,\qquad BPC_G=\frac85.
$$

For the three-period extension
$(1,1,4),(1,2,2),(1,4,1)$, global distances are
$(15/17,3/5,0)$. The adjacent changes are $20/17$ and $8/5$;
their product and the endpoint ratio both equal $32/17$. These fixtures are
synthetic analytical certificates, not a reproduction of Oh's country study.

```python
from deapack import DEAData, GlobalMalmquistLuenbergerDEA, load_dataset

frame = load_dataset("environmental_panel")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    period="period",
    inputs=["energy", "labor"],
    outputs="electricity",
    bad_outputs="co2",
)
result = GlobalMalmquistLuenbergerDEA().fit(data)
```

For Central from 2020 to 2021, the bundled teaching data produce
`productivity_change=1.004603`, `efficiency_change=1.000014`, and
`best_practice_change=1.004589`. The source-native gap rises from
`base_best_practice_gap=0.987891` to
`comparison_best_practice_gap=0.992424`; comparison/base reconstructs the
best-practice-change factor.

```python
result.summary().query(
    "dmu_id == 'Central' and comparison_period == 2021"
)[[
    "productivity_change",
    "efficiency_change",
    "best_practice_change",
    "base_best_practice_gap",
    "comparison_best_practice_gap",
    "score_valid",
    "peer_valid",
]]

result.intensities.query(
    "dmu_id == 'Central' and distance_role == 'base_on_global'"
)[[
    "evaluated_period",
    "reference_dmu_id",
    "reference_period",
    "lambda",
]]
```

For a larger panel,
`result.plot(kind="performance", metric="productivity_change")` supplies the
standard no-change benchmark at one. Interpret that visual with the two gap
fields, labeled peers, diagnostics, and recorded global vintage rather than
as a causal ranking.

## Evidence boundary

The independent evidence covers the CRS common-factor programme, the four
nonnegative own/global roles, exact decomposition, fixed-vintage circularity,
peer mapping, and coherent unit changes. The country-year inputs needed to
rebuild the complete published reference sets have not been frozen here, so
the package does not claim an empirical replay of Oh's application.
Non-CRS and literal-union estimators, alternative directions or environmental
technologies, inference, welfare, and causal extensions remain deferred.

```{autosummary}
GlobalMalmquistLuenbergerProductivityIndex
GlobalMalmquistLuenbergerDEA
```
