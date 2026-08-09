# Local returns to scale

`local_returns_to_scale` asks an economic question at the operating plan used
for appraisal: if the organization were to expand or contract its activity
near that plan, would proportionate scale expansion raise output more than,
in proportion to, or less than resource use?

The answer is local. It is not the CRS/VRS efficiency ratio, a measure of
unused capacity, or a statement about the organization at every feasible
operating plan.

## What the operator evaluates

For each observation, DEAPack:

1. estimates an oriented VRS radial projection;
2. completes the projection with a positive-weight, row-scaled slack
   objective so that the selected target is Pareto efficient; and
3. finds the smallest and largest admissible supporting intercept at that
   fixed target.

The public scope is therefore **selected projection**. If several
Pareto-efficient projections are possible, the solver selects one. The
reported interval covers all normalized supports at that selected target; it
does not claim that the classification is invariant across other efficient
projections.

## Sign convention and decision rule

DEAPack records the convention explicitly:

$$
v^\top x-u^\top y+\delta\geq 0.
$$

For input orientation, supports are normalized by
$v^\top \hat{x}=1$; for output orientation, by
$u^\top \hat{y}=1$. Let
$[\underline{\delta},\overline{\delta}]$ be the admissible interval at the
selected target. Then:

- `increasing` means $\overline{\delta}<0$;
- `decreasing` means $\underline{\delta}>0$; and
- `constant` means that zero is admissible.

The comparison uses `rts_tolerance`. An unbounded endpoint can be a legitimate
economic boundary—for example, every admissible support may still imply
decreasing returns even when the positive endpoint has no finite upper bound.
DEAPack publishes that boundary only when it can independently construct and
verify an improving recession ray. A backend `unbounded` status without such
evidence is retained as raw solver information, but the endpoint, interval,
and RTS classification are withheld.

## Example

```python
from deapack import DEAData, local_returns_to_scale

data = DEAData.from_frame(
    frame,
    dmu="unit",
    inputs=["labour", "capital"],
    outputs="service",
)

result = local_returns_to_scale(data, orientation="input")
result.summary()[
    [
        "dmu_id",
        "rts_classification",
        "support_rts_set",
        "support_intercept_lower",
        "support_intercept_upper",
        "support_interval_valid",
        "economic_classification_certified",
        "projection_is_observed",
    ]
]
```

`support_rts_set` preserves economically meaningful ambiguity among alternate
supports at the same target. For example, `increasing|constant` says that both
increasing-returns and constant-returns supports are admissible, while the
Banker--Thrall classification is `constant` because zero belongs to the
interval.

The selected input and output plan is available from `result.targets`, and
the reference mixture from `result.intensities`. A failed projection or
unresolved endpoint produces `indeterminate` rather than a guessed RTS label.
Targets, slacks, and peers are published only when their respective source
certificates remain valid.

Before solving either support endpoint, the operator explicitly requires the
underlying radial row to have `score_valid=True`, `completion_valid=True`, and
`target_valid=True`. The summary preserves these as
`projection_score_valid`, `projection_completion_valid`, and
`projection_target_valid`. `projection_peer_valid` separately controls the
reference-mixture table. A stale or externally retained target or peer row
cannot override failed projection evidence, and no support LP is run for an
uncertified target.

## Release and certificate contract

The operator checks each finite support endpoint at three distinct levels:

1. primal feasibility, bounds, KKT conditions, dual feasibility, strong
   duality, and complementarity for the LP returned by the backend;
2. reconstruction of the support inequalities, target equality,
   orientation-specific normalization, and objective in the original data
   units; and
3. ordering and economic classification of the complete lower--upper
   interval.

An extended endpoint has no finite optimal primal or dual account. Its finite
LP and dual certificate fields are therefore missing rather than false. The
separate `support_intercept_*_unbounded_ray_certified` field must be true, and
the endpoint economic and interval certificates must still pass.

The main summary fields are:

| Layer | Validity and status fields |
|---|---|
| selected projection | `projection_score_valid`, `projection_completion_valid`, `projection_target_valid`, `projection_peer_valid` |
| published component tables | `completion_valid`, `target_valid`, `peer_valid`, with matching `*_status` fields |
| endpoint | `support_intercept_*_valid`, `support_intercept_*_endpoint_status` |
| finite endpoint evidence | `support_intercept_*_lp_postsolve_certified`, `support_intercept_*_dual_postsolve_certified`, `support_intercept_*_economic_postsolve_certified` |
| extended endpoint evidence | `support_intercept_*_unbounded_ray_certified` and `support_intercept_*_max_unbounded_ray_violation` |
| complete economic result | `support_domain_valid`, `support_interval_valid`, `economic_classification_certified`, `analysis_valid`, `analysis_status` |

`solver_status` is the semantic release status. Raw backend evidence is never
overwritten: the aggregate fields are `backend_solver_status` and
`raw_solver_status`, while each endpoint also retains
`support_intercept_*_backend_status` and
`support_intercept_*_raw_status`. Consequently, a certified extended boundary
can have semantic status `optimal` and backend status `unbounded`; an
uncertified backend result cannot be made economically valid by relabelling
the solver status.

Failure is isolated by observation, and success, endpoint failure, and
all-projection-failure runs retain the same summary and diagnostic columns.
The status vocabulary distinguishes `projection_failure`,
`uncertified_endpoint`, `unverified_unbounded_ray`, and
`mathematically_undefined_support_domain`.

## Solve and compilation accounting

With one resolved observation, the full route performs exactly four required
solves: VRS radial projection, Pareto slack completion, lower support endpoint,
and upper support endpoint. Certificates reconstruct the returned accounts
and add zero optimization solves. For one common reference set, the benchmark
observes one projection-reference compilation, one support-reference
compilation, and one radial phase-one template compilation. Metadata exposes
`projection_solver_calls`, `support_endpoint_solver_calls`, `solver_calls`,
`compiled_reference_sets`, and `additional_solver_calls`; the last field and
the certificate's own additional-solve count are both zero.

When the decision needs a magnitude rather than only an IRS/CRS/DRS category,
{doc}`Scale elasticity <scale-elasticity>` transforms this same selected
target and complete support interval into separate scale-up and scale-down
percentage responses. It does not fit a second projection.

## Interpretation boundaries

- The technology is always VRS; `reference` changes the comparison set, not
  this maintained technology assumption.
- Input and output orientation may select different targets for an inefficient
  observation and can therefore answer different local operating questions.
- NIRS/NDRS technology comparisons are separate categorical procedures and
  are not substituted for the supporting-intercept interval.
- `score`, `efficiency`, `distance`, and `is_efficient` remain missing because
  this result is a post-estimation classification, not another efficiency
  score. Projection diagnostics are retained in dedicated columns.

The implementation follows [Banker and Thrall
(1992)](https://doi.org/10.1016/0377-2217(92)90178-C) and is
regression-tested against the five-observation example recapitulated by
[Banker *et al.*
(2004)](https://www.deafrontier.net/papers/EJORRTSreview.pdf).
