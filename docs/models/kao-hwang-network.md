# Kao--Hwang two-stage relational network DEA

```{eval-rst}
.. currentmodule:: deapack
```

`KaoHwangRelationalDEA` implements the constant-returns-to-scale relational
model for a basic two-process series system. External resources enter the
first process, every first-process output is observed once as an intermediate
handoff, and the second process converts that handoff into final outcomes.
`KaoHwangDEA` is an exact API alias.

The defining source is
[Kao and Hwang (2008)](https://doi.org/10.1016/j.ejor.2006.11.041).
The target account follows
[Lim and Zhu (2016)](https://doi.org/10.1016/j.ejor.2015.06.050).

## Scope

This page documents a method inside the existing Network DEA family. The
historical name identifies the source-qualified API entry and its relational
account of organizations, internal links, and process responsibility; it is
not an invitation to catalogue paper-specific variants without distinct
technical content.

## Model and score convention

For evaluated observation $o$, let $x_o$, $z_o$, and $y_o$ denote
external inputs, intermediates, and final outputs. With nonnegative
multipliers $v$, $w$, and $u$, the fitted programme is

$$
\begin{aligned}
\max_{u,v,w}\quad &u^\top y_o\\
\text{subject to}\quad
&w^\top z_j-v^\top x_j\leq0,
&&j=1,\ldots,n,\\
&u^\top y_j-w^\top z_j\leq0,
&&j=1,\ldots,n,\\
&v^\top x_o=1,\\
&u,v,w\geq0.
\end{aligned}
$$

The same $w$ values an intermediate as a stage-1 output and a stage-2
input. This is the implemented link-coupling rule. The inequalities use the
closed limiting form $u,v,w\geq0$; the solver does not insert a
unit-dependent numerical epsilon. A future positive-weight floor or
assurance-region restriction will be an explicit valuation policy. The public
score is

$$
E_o=\frac{u^\top y_o}{v^\top x_o}.
$$

When $w^\top z_o>0$, the selected process accounts are

$$
E_o^{(1)}
=\frac{w^\top z_o}{v^\top x_o},
\qquad
E_o^{(2)}
=\frac{u^\top y_o}{w^\top z_o},
\qquad
E_o=E_o^{(1)}E_o^{(2)}.
$$

`score`, `efficiency`, and `system_efficiency` contain $E_o$.
With a self-inclusive reference set they lie in $[0,1]$, one denotes
relational system efficiency, and larger is better. This multiplicative
identity is specific to the basic Kao--Hwang CRS model. It is not promised for
VRS networks, additive network models, network SBM, or general graphs.

## Complete public example

```python
from deapack import (
    KaoHwangRelationalDEA,
    NetworkData,
    TwoStageSeriesSpec,
    dataset_info,
    load_dataset,
)

frame = load_dataset("two_stage_public_service")
roles = dataset_info("two_stage_public_service").roles
spec = TwoStageSeriesSpec(
    inputs=roles["inputs"],
    intermediates=roles["intermediates"],
    outputs=roles["outputs"],
    stage_names=("screening", "service_delivery"),
    link_id="service_handoff",
)
data = NetworkData.from_frame(frame, dmu=roles["dmu"], spec=spec)

result = KaoHwangRelationalDEA(
    decomposition="maximize_stage_1",
    projection="source_midpoint",
).fit(data)

result.summary()[[
    "dmu_id",
    "system_efficiency",
    "score_valid",
    "stage_1_efficiency",
    "stage_2_efficiency",
    "reconstruction_residual",
    "decomposition_valid",
    "decomposition_status",
    "target_valid",
    "target_status",
    "peer_valid",
    "peer_status",
]]
```

The five project-authored observations exercise a proportional scale pair,
resource and conversion drag, and a different service mix. The repository
checks the CRS system account against an independent Färe--Grosskopf radial
implementation; the example does not reproduce a published data table.

## Stage-attribution policy

The system optimum need not identify one unique intermediate virtual value.
`decomposition` controls the secondary account:

| Value | Behavior |
|---|---|
| `"none"` | do not calculate process scores |
| `"maximize_stage_1"` | hold the optimal system score fixed and maximize $E_o^{(1)}$; this is the default |
| `"maximize_stage_2"` | hold the optimal system score fixed and minimize $E_o^{(1)}$, equivalently maximizing $E_o^{(2)}$ |
| `"bounds"` | solve both secondary programmes, report complete process-score intervals, and select the stage-1-maximizing account for the point fields |

Use bounds when process comparisons affect substantive conclusions:

```python
bounded = KaoHwangRelationalDEA(
    decomposition="bounds",
    projection="none",
).fit(data)

bounded.summary()[[
    "dmu_id",
    "stage_1_efficiency_lower",
    "stage_1_efficiency_upper",
    "stage_2_efficiency_lower",
    "stage_2_efficiency_upper",
    "decomposition_unique",
]]
```

The selected process scores are accounting attributions under the declared
policy, not estimates of causal contributions. Inspect
`decomposition_unique` rather than assuming that a unique system score also
identifies unique process scores. If a requested secondary programme or its
postsolve account is not certified, the system score may remain available
while both process scores and their component rows are withheld atomically.

## Link-feasible targets and peers

The Lim--Zhu envelopment dual uses separate upstream and downstream
intensities:

$$
X\lambda\leq E_o x_o,\qquad
Z\lambda\geq Z\mu,\qquad
Y\mu\geq y_o,\qquad
\lambda,\mu\geq0.
$$

`projection="source_midpoint"` returns:

- external-input targets $X\lambda$;
- final-output targets $Y\mu$;
- downstream intermediate requirement $Z\mu$;
- upstream intermediate supply $Z\lambda$; and
- midpoint link target $(Z\lambda+Z\mu)/2$.

Any intermediate vector between the two endpoints is link-feasible under this
dual account. The midpoint is a deterministic source-qualified selection, not
a uniquely preferred management plan.

```python
result.links.query("dmu_id == 'balanced'")[[
    "link_id",
    "variable",
    "downstream_requirement",
    "upstream_supply",
    "target_lower",
    "target_upper",
    "target",
    "disposable_surplus",
]]
```

`intensities` labels the first-process rows as `upstream_lambda` and the
second-process rows as `downstream_mu`. Shared intermediate multipliers do not
imply shared reference activities. Under CRS, intensities are scaling
coefficients and do not have to sum to one.

Targets always use the complete, unthresholded certified intensities.
`peer_tolerance` applies only to displayed peer rows. After thresholding, the
package independently reconstructs the input, upstream-link, downstream-link,
and output accounts. If those displayed peers no longer reproduce the
published operating plan within `tolerance`, `peer_valid=False` and all peer
rows for that observation are withheld; certified targets and link rows remain
available.

`projection="none"` skips target and link recovery. It leaves `targets`,
`links`, and `intensities` empty and reduces solver work when only system and
process scores are required.

## Result tables

The returned `DEAResult` uses the following network-specific fields:

| Table | Important fields |
|---|---|
| `summary()` | `system_efficiency`, process efficiencies and bounds, `stage_product`, `reconstruction_residual`, four independent validity/status pairs, and raw backend status |
| `components` | one certified system row; two process rows only when the requested decomposition account passes |
| `multipliers` | certified original- and scaled-unit multipliers, virtual contributions, and `shared_between` for intermediates |
| `intensities` | process-specific positive peers only when the thresholded peer account passes |
| `targets` | certified process/variable targets, feasible lower/upper values, validity, status, and projection policy |
| `links` | certified downstream requirement, upstream supply, target interval, selected target, surplus, and balance residual |
| `diagnostics` | solver-neutral LP, raw/published economic, target, link, and peer certificates with independently recomputed residuals |

`is_relationally_efficient` tests whether the system score is one.
`is_stage_1_efficient` and `is_stage_2_efficient` apply to the selected stage
account. `is_efficient` remains missing because this leaf does not perform a
joint residual-slack completion that would certify Pareto--Koopmans
efficiency.

## Reference populations

`reference` accepts a `ReferenceSpec` or a reference-kind string. With the
default `"auto"` policy, a cross-section uses all rows and a panel uses
contemporaneous rows. Global, contemporaneous, sequential, window, biennial,
and custom row policies are constructed by the shared reference-set layer.
The economic interpretation of a panel network comparison remains the
analyst's responsibility; fitting this static leaf by period is not a network
productivity index or a dynamic carry-over model.

External custom reference populations can produce `system_efficiency` above
one. Such values are retained rather than clipped, and
`is_within_reference_technology` records whether the fitted comparison
supports an efficiency classification.

## Postsolve trust and atomic publication

An `optimal` message from a backend is necessary but not sufficient for
publication. Every multiplier solve passes two independent layers:

1. the shared solver-neutral LP certificate recomputes primal feasibility,
   bounds, objective consistency, dual feasibility, complementarity, and
   strong duality from the returned solution; and
2. the relational economic certificate converts the scaled variables back to
   multipliers on the original quantities and reconstructs normalization, both
   process inequalities, the active objective, any fixed-system equality, and
   the system/process multiplication account.

Both the raw solution and the values prepared for publication must pass.
Projection recovery separately certifies raw and published input, link, and
output accounts in original units. Display-thresholded peers then face their
own reconstruction gate. These checks reuse already returned solutions and
make no certification solve.

The four release decisions are intentionally separate:

| Economic object | Validity | Status | Failure effect |
|---|---|---|---|
| system score | `score_valid` | `score_status` | withhold all semantic tables for that observation |
| process attribution | `decomposition_valid` | `decomposition_status` | retain a certified system score but withhold both process rows |
| targets and link account | `target_valid` | `target_status` | retain score/decomposition but withhold all target and link rows |
| displayed peers | `peer_valid` | `peer_status` | retain unthresholded targets but withhold every displayed peer row |

Failures are isolated by observation. `solver_status`,
`backend_solver_status`, and `raw_solver_status` preserve what the backend
actually returned; they are not rewritten from `"optimal"` to
`"numerical_error"` when a later certificate rejects publication. Consult the
validity/status fields and diagnostics for the semantic decision. Empty result
tables retain stable schemas even when every observation fails.

## Admissible domain and explicit exclusions

The current leaf requires:

- exactly two processes and one directed link;
- the first process to produce only the declared intermediates;
- the second process to use only those intermediates;
- distinct columns for external inputs, intermediates, and final outputs;
- finite, nonnegative quantities;
- positive reference-set support for every variable; and
- positive aggregate external input and positive aggregate intermediate
  quantity for every reference observation.

A row with zero aggregate external input has
`score_status="undefined_input_normalizer"`. A zero intermediate virtual value
makes the process decomposition undefined. Negative data raise
`DataValidationError`; translating them would change the ratio account.
Unsupported reference columns and incompatible graphs raise
`ModelSpecificationError`.

The constructor does not accept an orientation or returns-to-scale switch.
The implemented orientation is input-system and the implemented scale
assumption is CRS. Exogenous second-stage inputs, first-stage final outputs,
shared inputs, undesirable intermediates, general networks, VRS relational
models, network SBM, and leader--follower games require distinct
source-qualified methods.

## Numerical and performance behavior

The default backend is SciPy/HiGHS. Data columns and constraint rows are
scaled internally; reported multipliers, targets, and quantities are restored
to their original units. One sparse reference matrix is compiled and reused
for every observation sharing the same reference population.

Solver counts per evaluated observation, excluding an uncommon explicit
projection fallback, are:

| `decomposition` | `projection="none"` | With source-midpoint projection |
|---|---:|---:|
| `"none"` | 1 | normally 1, using primary dual marginals |
| `"maximize_stage_1"` | 2 | normally 2 |
| `"maximize_stage_2"` | 2 | normally 2 |
| `"bounds"` | 3 | normally 3 |

If primary dual marginals fail the projection certificate, the implementation
solves the explicit envelopment dual and records
`phase="projection_fallback"` in diagnostics. `tolerance` governs score,
identity, and certificate checks. `peer_tolerance` controls which positive
intensities are retained for display; it does not alter the fitted LP.

The result metadata reconcile the actual work through
`compiled_reference_sets`, `primary_solves`, `secondary_solves`,
`projection_fallback_solves`, and `solver_calls`. The
`postsolve_certificate.additional_solver_calls` field is always zero: an
explicit projection fallback is part of the requested projection algorithm,
is counted separately, and is not a certificate solve.

The repository benchmark enforces these contracts rather than merely timing
the call:

```bash
python benchmarks/benchmark_network_relational.py \
  --n-dmus 100 \
  --decomposition maximize_stage_1 \
  --projection source_midpoint

python benchmarks/benchmark_network_relational.py \
  --n-dmus 1000 \
  --decomposition none \
  --projection none
```

An August 2026 development-environment run produced the following audited
observations. Timings are illustrative and hardware-dependent; the counts and
certificate gates are enforced by the benchmark itself.

| Workload | Elapsed | Certified releases | Independent work count | Largest audited residual |
|---|---:|---|---|---:|
| 100 DMUs, stage-1 selection and source-midpoint targets | 0.466 s | score, decomposition, target, and peer: 100/100 | 1 compilation; 100 primary + 100 secondary + 0 fallback solves | $3.43\times10^{-13}$ |
| 1,000 DMUs, score only | 7.592 s | score: 1,000/1,000; other objects not requested | 1 compilation; 1,000 primary + 0 secondary + 0 fallback solves | $1.93\times10^{-14}$ |

Both runs reported zero additional certificate solves.

```{autosummary}
KaoHwangRelationalDEA
KaoHwangDEA
NetworkData
TwoStageSeriesSpec
```
