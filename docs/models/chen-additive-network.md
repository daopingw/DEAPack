# Chen--Cook--Li--Zhu additive two-stage network DEA

```{eval-rst}
.. currentmodule:: deapack
```

`ChenCookLiZhuAdditiveDEA` implements the weighted-additive efficiency
decomposition for a closed two-process series system. External inputs enter
stage 1, every stage-1 output is observed once as an intermediate used by
stage 2, and final outputs leave stage 2.
`TwoStageAdditiveDecompositionDEA` is an exact API alias.

```{note}
This is technical Documentation for the additive process-attribution method
inside the existing Network DEA family.
```

The defining formulation is
[Chen, Cook, Li, and Zhu (2009)](https://doi.org/10.1016/j.ejor.2008.05.011).
The implemented envelopment projection follows
[Lim and Zhu (2019)](https://doi.org/10.1016/j.omega.2018.06.005).

```{important}
Here *additive* means that system efficiency is a
virtual-resource-share-weighted arithmetic sum of radial stage efficiencies.
It is not the slack-sum objective implemented by `AdditiveDEA`.
```

## Model and score convention

For evaluated observation $o$, let $x_o$, $z_o$, and $y_o$ denote
external inputs, intermediates, and final outputs. Nonnegative multipliers
$v$, $w$, and $u$ value those roles. Under CRS, the two peer tests are

$$
w^\top z_j-v^\top x_j\leq0,
\qquad
u^\top y_j-w^\top z_j\leq0.
$$

The same $w$ values an intermediate as a stage-1 output and a stage-2 input.
With

$$
v^\top x_o+w^\top z_o=1,
$$

the primary programme maximizes

$$
E_o=w^\top z_o+u^\top y_o.
$$

The reported stage accounts and weights are

$$
\begin{aligned}
E_o^{(1)}&=\frac{w^\top z_o}{v^\top x_o},
&
\alpha_{1o}&=\frac{v^\top x_o}
{v^\top x_o+w^\top z_o},\\
E_o^{(2)}&=\frac{u^\top y_o}{w^\top z_o},
&
\alpha_{2o}&=\frac{w^\top z_o}
{v^\top x_o+w^\top z_o}.
\end{aligned}
$$

They satisfy

$$
E_o=\alpha_{1o}E_o^{(1)}+\alpha_{2o}E_o^{(2)},
\qquad
\alpha_{1o}+\alpha_{2o}=1.
$$

`score`, `efficiency`, and `system_efficiency` contain $E_o$.
`stage_1_weight` and `stage_2_weight` contain the $\alpha$ values. The
weights are endogenous virtual-resource shares; they are not observed budget
shares, market prices, or analyst-supplied importance weights.

With a self-inclusive reference population, system scores lie in $[0,1]$,
one denotes additive system efficiency, and larger is better. External custom
reference populations can produce scores above one; those values are retained
and `is_within_reference_technology` records whether the usual classification
is supported.

## Returns to scale

`returns_to_scale` accepts `"crs"` or `"vrs"`. NIRS and NDRS are not
implemented for this source-defined leaf.

VRS adds free process intercepts $\xi_1,\xi_2$:

$$
\begin{aligned}
w^\top z_j-v^\top x_j+\xi_1&\leq0,\\
u^\top y_j-w^\top z_j+\xi_2&\leq0.
\end{aligned}
$$

The stage numerators become $w^\top z_o+\xi_1$ and
$u^\top y_o+\xi_2$. `stage_1_intercept` and `stage_2_intercept` expose the
fitted values. They are scale corrections in the affine process
technologies, not estimates of fixed monetary cost or managerial value.

## Complete public example

```python
from deapack import (
    ChenCookLiZhuAdditiveDEA,
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

result = ChenCookLiZhuAdditiveDEA(
    returns_to_scale="vrs",
    decomposition="both_priorities",
    projection="source",
).fit(data)

result.summary()[[
    "dmu_id",
    "system_efficiency",
    "stage_1_efficiency",
    "stage_2_efficiency",
    "stage_1_weight",
    "stage_2_weight",
    "reconstruction_residual",
    "score_valid",
    "process_account_valid",
    "decomposition_unique",
    "target_valid",
    "target_status",
    "peer_valid",
]]
```

The project-authored case exercises both CRS and VRS system/stage accounts,
including scale, resource-drag, conversion-drag, and service-mix behavior.
Independent source-equation and cross-implementation tests validate the
certified scope without claiming reproduction of a published data table.

## Stage-attribution policy

The primary system optimum need not identify a unique stage account.
`decomposition` controls the secondary selection:

| Value | Behaviour |
|---|---|
| `"none"` | report the system score only; stage point fields are missing |
| `"maximize_stage_1"` | hold the system optimum fixed, then maximize the stage-1 account |
| `"maximize_stage_2"` | hold the system optimum fixed, then maximize the stage-2 account |
| `"both_priorities"` | solve both secondary accounts and apply the documented lexicographic selection; this is the default |

With `"both_priorities"`, the selected point account normally uses the
stage-1-prioritizing solution. If the stage-2-prioritizing solution preserves
the same maximum stage-1 score and yields a better defined stage-2 score, it
is selected as a tie-break. The two complete alternatives remain in:

- `stage_1_efficiency_when_stage_1_prioritized`;
- `stage_2_efficiency_when_stage_1_prioritized`;
- `stage_1_efficiency_when_stage_2_prioritized`; and
- `stage_2_efficiency_when_stage_2_prioritized`.

`decomposition_unique` is true only when both priority solutions define the
same pair of stage scores within `tolerance`. A false value means that the
system result is better identified than its process-level performance
attribution.

The default closed model permits zero multipliers and zero stage shares. It
does not insert a unit-dependent numerical epsilon. `minimum_stage_share`
provides an explicit sensitivity restriction in $[0,0.5]$. A positive
minimum changes the defining multiplier programme, so the source projection
is unavailable; set `projection="none"` when using it.

## Source projection and split link targets

The Lim--Zhu additive envelopment account uses separate process intensities
$\lambda,\mu$:

$$
\begin{aligned}
X\lambda&\leq E_o x_o,\\
Z\lambda-Z\mu&\geq(1-E_o)z_o,\\
Y\mu&\geq y_o.
\end{aligned}
$$

For VRS it additionally imposes
$\mathbf 1^\top\lambda=\mathbf 1^\top\mu=1$.

`projection="source"` returns:

- external-input targets $X\lambda$;
- upstream intermediate targets $Z\lambda$;
- downstream intermediate targets $Z\mu$;
- final-output targets $Y\mu$; and
- process-specific positive reference intensities.

The two intermediate targets are intentionally not collapsed into one
midpoint. In `links`, `source_target`/`upstream_supply` contain
$Z\lambda$, while `target_target`/`downstream_requirement` contain
$Z\mu$. The generic `target` is missing because this source account does
not select one common handoff target.

```python
result.links_for("balanced")[[
    "variable",
    "source_target",
    "target_target",
    "required_disposition",
    "disposed_quantity",
    "balance_residual",
]]
```

`required_disposition` is $(1-E_o)z_o$;
`disposed_quantity` is $Z\lambda-Z\mu$. These are model-specific link
adjustments, not a recommendation to destroy an economically valuable
intermediate. `balance_residual` audits their difference.

`intensities` labels the stage-1 rows `upstream_lambda` and stage-2 rows
`downstream_mu`. Under CRS, these are activity scaling coefficients and need
not sum to one. Under VRS, each process’s positive and zero intensities
together sum to one.

`projection="none"` skips targets, links, and intensities. This is useful when
only the score account is required.

## Result tables

The returned `DEAResult` provides:

| Table | Important fields |
|---|---|
| `summary()` | system/stage efficiencies, endogenous stage weights, priority-specific accounts, VRS intercepts, reconstruction fields, and separate score/process/target/link/peer validity and status fields |
| `components` | the certified system row and, when requested and certified, two process rows with virtual inputs/outputs, aggregation weights, intercepts, selection policy, and account status |
| `multipliers` | certified published scaled- and original-unit multipliers, virtual contributions, process intercepts, and shared intermediate roles |
| `intensities` | process-specific thresholded peers, released only when their displayed account still reconstructs the certified targets |
| `targets` | certified external-input, split intermediate-output/input, and final-output targets |
| `links` | certified upstream/downstream targets, required and fitted link adjustment, balance residual, and link-account status |
| `diagnostics` | unchanged backend status plus LP, raw/published economic-account, target, and thresholded-peer certificates and residuals |

`is_additively_efficient` tests whether the system score is one.
`is_stage_1_efficient` and `is_stage_2_efficient` refer to the selected stage
account. Generic `is_efficient` remains missing because this leaf does not
perform a residual-slack completion proving Pareto--Koopmans efficiency.

## Certification and atomic result release

An `optimal` backend label is not by itself an economic result. Every primary
and requested stage-priority programme first passes the shared solver-neutral
LP certificate. It independently checks bounds, primal rows, the reported
objective, row and bound marginals, stationarity, complementarity, and strong
duality.

The additive certificate then reconstructs the complete account twice from
the originally declared quantities:

- raw solver multipliers and intercepts;
- publication-cleaned multipliers and intercepts;
- both reference-process inequalities and their constraint slacks;
- the appropriate primary or secondary normalization;
- the reported objective and fixed-system identity; and
- the endogenous stage-share restrictions, when requested.

The gates are deliberately separate:

- `score_valid`/`score_status` govern the system headline;
- `process_account_valid`/`process_account_status` govern selected stage rows
  and multipliers;
- `target_valid`/`target_status` and
  `link_account_valid`/`link_account_status` govern the split projection; and
- `peer_valid`/`peer_status` govern only the thresholded intensity table.

Thus a failed secondary programme cannot erase a certified system score. A
failed target account cannot leak targets or links. A display threshold that
removes too much peer mass withholds `intensities` without discarding the
already certified score or targets. Publication is atomic for each gate and
each evaluated DMU; failure for one DMU does not suppress certified accounts
for another.

`solver_status`, `backend_solver_status`, and `raw_solver_status` preserve the
backend report even when a semantic gate fails. Diagnostics identify the
failed layer and expose such fields as
`lp_postsolve_certified`, `raw_economic_postsolve_certified`,
`published_economic_postsolve_certified`,
`published_target_account_certified`,
`published_peer_account_certified`, and their maximum residuals. Result-table
schemas remain stable when every evaluated programme fails.

## Reference populations

`reference` accepts a `ReferenceSpec` or a reference-kind string. With
`"auto"`, a cross-section uses all rows and a panel uses contemporaneous rows.
Global, contemporaneous, sequential, window, biennial, and custom row
policies are supplied by the shared reference-set layer.

The model remains a static two-stage appraisal when applied period by period.
It is not a network productivity index or a dynamic carry-over technology.

## Admissible domain and exclusions

The current leaf requires:

- exactly two processes and one directed link;
- all first-process outputs to be the declared intermediates and all
  second-process inputs to be those intermediates;
- distinct columns for external inputs, intermediates, and final outputs;
- finite, nonnegative quantities;
- positive reference-set support for every variable; and
- positive aggregate external input and intermediate quantity for each
  reference observation.

An evaluated row with zero aggregate external input or intermediate quantity
receives an undefined score status. Negative quantities raise
`DataValidationError`; translating them would change the ratio account.
Unsupported reference columns and incompatible graphs raise
`ModelSpecificationError`.

The constructor does not cover exogenous stage-2 inputs, stage-1 final
outputs, shared inputs, undesirable intermediates, general graphs, dynamic
carry-overs, network SBM, or non-cooperative games. Those require distinct
source-qualified models.

## Validation basis

The defining Chen and Lim--Zhu papers remain cited for the formulation and
primal--dual projection account. Numerical validation uses the neutral
`two_stage_public_service` case, including system/process reconstruction and
the split-link certificate; source observations, named organizations, and
printed result cells are not bundled. The validation basis is available in
`result.metadata["validation_basis"]`.

## Numerical and performance behaviour

The default backend is SciPy/HiGHS. Data columns and process constraints are
scaled internally, while reported scores, multipliers, and targets are
restored to their original units. One sparse reference matrix is compiled and
reused for every observation sharing the same reference population.

Normal solver counts per evaluated observation are:

| `decomposition` | `projection="none"` | `projection="source"` |
|---|---:|---:|
| `"none"` | 1 | normally 1 |
| `"maximize_stage_1"` | 2 | normally 2 |
| `"maximize_stage_2"` | 2 | normally 2 |
| `"both_priorities"` | 3 | normally 3 |

The source projection is normally recovered from primary dual marginals. If
they are unavailable or fail the certificate, the implementation solves the
explicit envelopment programme and records `phase="projection_fallback"` in
`diagnostics`. That fallback is part of the requested source-projection
contract. It is not an extra solve introduced by postsolve certification.

The result metadata reports the executed graph explicitly:

- `primary_solver_calls`;
- `secondary_solver_calls`;
- `projection_fallback_solver_calls`;
- `solver_calls`, their total;
- `additional_solver_calls=0`; and
- `certificate_extra_solver_calls=0`.

The release benchmark requires these counts to agree with a counting backend,
requires one compilation per distinct reference set, and fails closed if a
validity field, certificate, count, or finite residual is absent.

`tolerance` governs score, identity, uniqueness, and projection-certificate
checks. `peer_tolerance` controls which positive intensities are retained for
display; it does not change the fitted linear programme.

```{autosummary}
ChenCookLiZhuAdditiveDEA
TwoStageAdditiveDecompositionDEA
NetworkData
TwoStageSeriesSpec
```
