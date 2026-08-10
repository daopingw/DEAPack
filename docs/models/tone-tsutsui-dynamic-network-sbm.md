# Tone--Tsutsui dynamic network SBM

```{eval-rst}
.. currentmodule:: deapack
```

Tone and Tsutsui's dynamic network slacks-based measure appraises one
multi-process organization's complete operating trajectory. It combines
within-period process performance attribution with adjacent-period carry-over
continuity in one sparse programme. Its canonical method ID is
`dynamic.network_sbm.tone_tsutsui_2014`.

```{admonition} Public technical implementation; Documentation-only route
:class: important

`ToneTsutsuiDynamicNetworkSBM` is the explicit technical class and
`DynamicNetworkSBM` is its exact short alias. Both return the same estimator
and result contract. This process-by-period construction combines the network
and dynamic axes. Its equations and named terminal-policy resolution have been
audited, but an independent full joint
process-by-period numerical oracle has not been located. Public availability
must not be read as a closed literature-reproduction claim.
```

Audited sources:

- [Tone and Tsutsui (2014)](https://doi.org/10.1016/j.omega.2013.04.002);
  and
- the equation-complete
  [GRIPS workshop paper](https://www.grips.ac.jp/cms/wp-content/uploads/2013/03/DEA_Chapter1.pdf),
  used to freeze the current terminal-account convention where the final
  article's carry-over indices are internally inconsistent.

## Complete synthetic example

`dynamic_network_power_demo` is deterministic teaching data. It is not the
anonymous US-utility panel used in the article; the raw published-case panel
and utility identities are unavailable.

```python
from deapack import (
    DynamicNetworkData,
    DynamicNetworkSBM,
    DynamicNetworkSBMSpec,
    LinkSpec,
    NetworkSpec,
    ProcessCarryOverSpec,
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
            inputs=roles["generation_inputs"],
            outputs=(
                *roles["generation_outputs"],
                *roles["generation_to_grid"],
            ),
        ),
        ProcessSpec(
            "grid",
            inputs=(
                *roles["generation_to_grid"],
                *roles["grid_inputs"],
            ),
            outputs=(
                *roles["grid_outputs"],
                *roles["grid_to_service"],
            ),
        ),
        ProcessSpec(
            "customer_service",
            inputs=(
                *roles["grid_to_service"],
                *roles["service_inputs"],
            ),
            outputs=roles["service_outputs"],
        ),
    ),
    links=(
        LinkSpec(
            "generation_handoff",
            "generation",
            "grid",
            roles["generation_to_grid"],
        ),
        LinkSpec(
            "service_handoff",
            "grid",
            "customer_service",
            roles["grid_to_service"],
        ),
    ),
)

spec = DynamicNetworkSBMSpec(
    network=network,
    link_kinds={
        "generation_handoff": "free",
        "service_handoff": "fixed",
    },
    carryovers=(
        ProcessCarryOverSpec(
            "generation",
            roles["good_carryovers"][0],
            "good",
        ),
        ProcessCarryOverSpec(
            "grid",
            roles["bad_carryovers"][0],
            "bad",
        ),
        ProcessCarryOverSpec(
            "generation",
            roles["free_carryovers"][0],
            "free",
        ),
        ProcessCarryOverSpec(
            "customer_service",
            roles["fixed_carryovers"][0],
            "fixed",
        ),
    ),
)

data = DynamicNetworkData.from_frame(
    frame,
    spec=spec,
    dmu=roles["dmu"],
    period=roles["period"],
)

result = DynamicNetworkSBM(
    orientation="non-oriented",
    returns_to_scale="vrs",
    division_weights={
        "generation": 0.4,
        "grid": 0.3,
        "customer_service": 0.3,
    },
).fit(data)
```

## Specification and data contract

`DynamicNetworkSBMSpec` combines:

- one validated `NetworkSpec`;
- exactly one `NetworkSBMLinkKind` for every link ID;
- zero or more `ProcessCarryOverSpec` declarations; and
- `boundary_policy="tone_tsutsui_2014_core"`.

Every carry-over name must be unique, must belong to a known process, and
cannot also be a within-period network variable. Each link variable remains
an output of its declared supplier and an input of its declared recipient in
the structural `NetworkSpec`; `link_kinds` determines its dynamic-network SBM
balance and scoring treatment.

`DynamicNetworkData.from_frame` requires:

- one unique row per `(DMU, period)` key;
- at least one period;
- the same complete ordered period set for every DMU;
- every specification variable exactly once as a finite numeric column; and
- an explicit `period_order` when labels cannot be ordered safely.

The stored array is read-only and period-major with shape
`(n_periods, n_dmus, n_variables)`. One solver observation is an entire DMU
trajectory. The public estimator requires every model quantity to be
strictly positive because assessed quantities normalize the SBM slacks.
Zero-valued and signed-account variants require separate formulations.

The current reference policy is the global cohort of complete trajectories.
Every process and period draws from the same DMU membership, although each
`(period, process)` has its own intensity vector. Missing histories are not
interpolated, and contemporaneous, sequential, window, or biennial membership
rules are not silently substituted.

## External process balances

For assessed trajectory $o$, process $k=1,\ldots,K$, and period $t$:

$$
x_{ot}^k=X_t^k\lambda^{t,k}+s_{ot}^{k-},
\qquad
y_{ot}^k=Y_t^k\lambda^{t,k}-s_{ot}^{k+}.
$$

Every process used by an input or non-oriented model must have a nonempty
scored input account. Every process used by an output or non-oriented model
must have a nonempty scored output account. Scored link and carry-over roles
count toward those dimensions.

## Four within-period link kinds

For link $(k,\ell)$, supplier $k$, recipient $\ell$, observed quantity
$z_{ot}^{(k,\ell)}$, and data block $Z_t^{(k,\ell)}$:

The published text following Equation (7) retains a continuity condition
analogous to its Equation (3) in every link case. Link kind changes control
and score ownership; it never licenses incompatible endpoint plans.

**`free` / `LF`**

$$
Z_t^{(k,\ell)}\lambda^{t,k}
=
Z_t^{(k,\ell)}\lambda^{t,\ell}.
$$

The common endpoint target is jointly discretionary and absent from the base
score.

**`fixed` / `LN`**

$$
Z_t^{(k,\ell)}\lambda^{t,k}
=z_{ot}^{(k,\ell)}
=Z_t^{(k,\ell)}\lambda^{t,\ell}.
$$

Both endpoint benchmark plans reproduce observation. The link is unscored.

**`as_input` / `LB`**

$$
\begin{aligned}
Z_t^{(k,\ell)}\lambda^{t,k}
&=Z_t^{(k,\ell)}\lambda^{t,\ell},\\
z_{ot}^{(k,\ell)}
&=Z_t^{(k,\ell)}\lambda^{t,\ell}+s_{ot}^{(k,\ell),-}.
\end{aligned}
$$

This is one recipient-process input account. Supplier and recipient benchmark
deliveries remain equal; only the recipient owns the scored excess slack.

**`as_output` / `LG`**

$$
\begin{aligned}
Z_t^{(k,\ell)}\lambda^{t,k}
&=Z_t^{(k,\ell)}\lambda^{t,\ell},\\
z_{ot}^{(k,\ell)}
&=Z_t^{(k,\ell)}\lambda^{t,k}-s_{ot}^{(k,\ell),+}.
\end{aligned}
$$

This is one supplier-process output account. Supplier and recipient benchmark
deliveries remain equal; only the supplier owns the scored shortfall slack.

All four link kinds preserve supplier-recipient continuity. The as-input and
as-output distinctions are one-sided **score-attribution** rules, not permission
to choose incompatible endpoint targets.

## Four carry-over kinds

Each carry-over belongs to one process:

$$
\begin{aligned}
c_{ot}^{k,good}
  &=C_t^{k,good}\lambda^{t,k}-s_{ot}^{k,good},\\
c_{ot}^{k,bad}
  &=C_t^{k,bad}\lambda^{t,k}+s_{ot}^{k,bad},\\
c_{ot}^{k,free}
  &=C_t^{k,free}\lambda^{t,k}+s_{ot}^{k,free},\\
c_{ot}^{k,fixed}
  &=C_t^{k,fixed}\lambda^{t,k}.
\end{aligned}
$$

Good and bad carry-overs enter output and input performance accounts,
respectively. The free slack is signed and feasibility-only. A fixed
carry-over has no slack and reproduces observation.

The current core imposes adjacent-period continuity:

$$
C_t^{k,\alpha}\lambda^{t,k}
=
C_t^{k,\alpha}\lambda^{t+1,k},
\qquad t=1,\ldots,T-1.
$$

Both sides use the transition account observed at $t$.

## Boundary-policy disclosure

`tone_tsutsui_2014_core` contains $T$ period balance accounts and
$T-1$ adjacent-period continuity blocks. Its terminal period has an
observed balance but no outgoing equation to an unobserved $T+1$.

This is an explicit workshop-core convention. The published equations have
been audited directly: the final Omega article defines carry-over observations
over $t=1,\ldots,T-1$, while its objective and period equations also refer
to $z^{(T,T+1)}$. Its terminal indexing is therefore internally
inconsistent. DEAPack records the named $T$-account,
$T-1$-continuity resolution and does not claim that the inconsistency has a
unique answer.

Initial-state constraints, terminal targets or values, depreciation, loss,
longer lags, and stock-transition equations are unsupported extensions, not
defaults.

## Orientations and account reconstruction

For each $(t,k)$, let $A_{ot}^k$ be one minus the mean normalized slack
over external inputs, recipient-owned as-input links, and bad carry-overs.
Let $B_{ot}^k$ be one plus the mean normalized slack over external outputs,
supplier-owned as-output links, and good carry-overs.

Period weights $W_t$ and process weights $w_k$ are nonnegative and each
sum to one after normalization:

$$
A_o=\sum_tW_t\sum_{k=1}^{K}w_kA_{ot}^k,
\qquad
B_o=\sum_tW_t\sum_{k=1}^{K}w_kB_{ot}^k.
$$

| `orientation` | Optimized account | Reported efficiency |
|---|---|---|
| `"input"` | $A_o$ | $A_o$ |
| `"output"` | $B_o$ expansion | $1/B_o$ |
| `"non-oriented"` | input/output ratio | $A_o/B_o$ |

Free and fixed links and carry-overs affect feasibility but do not enter the
base objective. The non-oriented linear-fractional problem uses a
Charnes--Cooper transformation and reports `transform_scale` plus an account
reconstruction residual.

Published Section 3.6.2 also permits source-qualified objective extensions
that include free-link or free-carry-over deviations, referring to the 2009
network and 2010 dynamic SBM treatments for details. The current estimator
does not collapse those alternatives into a Boolean option, and the 2014
article does not define every such extension as mixed-integer. An executable
variant will receive its own method identity after its exact objective,
one-sided deviation treatment, solver class, and result reconstruction are
frozen.

## Relative period and process weights

`period_weights` maps every period label to a finite nonnegative relative
weight. `division_weights` maps every canonical process ID to one. Omitted
mappings use equal weights. Supplied mappings must contain every corresponding
label exactly once, at least one value in each mapping must be positive, and
DEAPack normalizes each vector to sum to one.

A zero-weight period or process still constrains the joint feasible plan, but
its component account is not identified by the objective. System efficiency
of one certifies every lower-level scored account only when every relevant
period and process has positive weight.

`is_dynamic_network_sbm_efficient` records that source criterion. The generic
nullable `is_efficient` is stricter: it is populated only for a non-oriented
fit with strictly positive period and process weights and with every scored
slack checked. Input- and output-oriented fits leave it missing because the
other side has not received a Pareto--Koopmans completion. Zero-weight
accounts also leave it missing rather than turning an unidentified component
into a strong-efficiency claim.

One-click plots and result briefs use the label
**Dynamic Network-System Performance**. Their value-one benchmark is limited
to positively weighted period-process accounts. When a period or process has
zero weight, the brief adds an explicit warning that the result does not
establish efficiency for every period and process.

Weights express exogenous importance, not fitted DEA multipliers, internal
prices, or automatic economic discount factors. Normalized values and their
sources are stored in `metadata["effective_weights"]`.

## Returns to scale

`returns_to_scale` accepts:

- one `"crs"` or `"vrs"` value applied to every process; or
- a mapping from every process ID to `"crs"` or `"vrs"`.

For each VRS process, every period imposes

$$
\mathbf1^\top\lambda^{t,k}=1.
$$

CRS processes omit their convexity rows. NIRS and NDRS are rejected.

When all processes share CRS or all share VRS, the result identifies that
system-wide RTS label. Under a mixed process mapping, the source programme is
valid but overall system RTS is not identified. Inspect the per-process values
and `overall_returns_to_scale_identified`; do not relabel a mixed system as
CRS or VRS.

## Decomposition policy

The overall system optimal value is well defined. Period, process,
period-by-process, peer, slack, and target decompositions can be nonunique.
The current public option is:

```python
DynamicNetworkSBM(decomposition_policy="solver_selected")
```

Lower-level rows are marked
`solver_selected_not_uniqueness_certified`. The source's
reverse-chronological period-priority selection requires a sequence of
secondary LPs after fixing the primary optimum. It is not currently
implemented and is not approximated by epsilon weights.

## Result-table contract

`fit()` returns `DEAResult`.

| Table | Dynamic-network content |
|---|---|
| `summary()` | system efficiency, `score_valid`, `score_status`, criterion-specific and nullable strong-efficiency flags, input and output accounts, orientation, RTS identification, horizon and graph sizes, semantic `solver_status`, retained `backend_solver_status` and `raw_solver_status`, balance/continuity/fixed-account residuals, and selection status |
| `components` | one system row plus period, process, and period-by-process accounts with declared and effective reconstruction weights |
| `slacks` | period, process, role, variable, link ID, raw and normalized slack, managerial semantics, objective inclusion, and joint objective weight |
| `targets` | observed and benchmark quantity in user units, adjustment, role, process/link ownership, and balance residual |
| `intensities` | assessed DMU, period, process, reference DMU, intensity, process RTS, and selection status |
| `links` | within-period links and carry-overs, endpoint targets, ownership, balance policy, continuity status, residuals, and terminal-boundary status |
| `duals` | equality-row marginals and transformed/direct coordinate-system label, released only when the backend result and both postsolve gates certify |
| `diagnostics` | one primary-solve record per assessed trajectory, including LP- and economic-certificate fields and the semantic, backend, and raw solver statuses |

Useful filters include:

```python
result.components_for("Central")
result.targets_for("Central", period=2023)
result.peers("Central", period=2023)
result.links_for("Central")
```

Targets, slacks, and links are returned in original user units. Residual
summary columns identify their coordinate system.

## Failure behavior

Construction or fitting rejects:

- an unknown orientation, NIRS/NDRS, or an incomplete process-RTS mapping;
- a non-mapping period or process weight argument;
- missing, extra, negative, nonfinite, or all-zero relative weights;
- a link-kind mapping that does not classify every link exactly once;
- carry-overs with an unknown process, duplicate name, or network-variable
  overlap;
- duplicate `(DMU, period)` rows or an unbalanced trajectory panel;
- nonpositive model quantities;
- a process with no account on a side required by the orientation;
- an unsupported boundary or decomposition policy; and
- simultaneous `solver` and `solver_options`.

Every primary solution passes two independent postsolve gates before any
economic result is released:

1. the shared solver-neutral LP certificate recomputes primal feasibility,
   bounds, the reported objective, KKT conditions, complementarity, and strong
   duality; and
2. the dynamic-network economic certificate reconstructs the transform scale,
   input/output accounts, system score, targets, within-period links,
   carry-over continuity, fixed accounts, and component aggregation.

Release is atomic per assessed trajectory. If either gate fails, the summary
contains an undefined score with `score_valid=False`; that trajectory
contributes no component, slack, target, intensity, link, or dual row. In
particular, a failed backend cannot leak stale marginals as economic duals.

`solver_status` is the semantic outcome. When a backend reports `optimal` but
postsolve certification rejects its result, `solver_status` is
`numerical_error`; `backend_solver_status` and `raw_solver_status` retain the
backend's original `optimal` claim. A non-optimal backend status is retained as
the semantic status. Diagnostics preserve all three fields and the certificate
reason.

The Charnes--Cooper scale is mathematically admissible when it is finite and
strictly positive. It is **not** compared with the model tolerance: a positive
scale smaller than `tolerance` is not invalid merely because the implied
efficiency is small. A nonfinite or nonpositive scale is reported as a
per-DMU semantic failure rather than raising one exception that discards the
other trajectories.

## Sparse implementation and performance

The implementation compiles one immutable CSC equality template for the
complete trajectory cohort. It allocates:

- one intensity block per `(period, process)`;
- external, scored-link, and carry-over balance blocks;
- supplier-recipient continuity for every link, plus fixed-observation or
  scored-side balances according to link kind;
- adjacent-period carry-over continuity;
- process-period VRS rows where selected; and
- a Charnes--Cooper normalization row only for the non-oriented model.

For each assessed DMU, the estimator copies the sparse template and updates
only observation-dependent coefficients, objective coefficients, and the
normalization row. It performs one primary LP per trajectory under
`solver_selected`; no dense DMU-period Cartesian matrix is rebuilt inside the
solve loop.

The two production postsolve certificates reuse the returned primal and marginals and perform only
sparse matrix/vector and account-reconstruction work. They launch no
optimization task. The execution ledger therefore reports
`solver_calls = primary_solves = n_dmus`, `additional_solver_calls = 0`, and
`certificate_extra_solver_calls = 0`. The dedicated
`benchmark_dynamic_network_sbm.py` guard independently counts compilation and
backend calls, requires every score to pass both certificates, checks the
reconstruction residuals, and exercises input, output, and non-oriented fits.
These are implementation and performance checks. They remain distinct from
the independent analytical oracle described below and do not reproduce the
published anonymous-utility application.

The number of intensity variables grows as
$T\times K\times n_{\mathrm{reference}}$. Link and carry-over rows add
linearly in periods and declared variables, while each dense empirical
reference block contributes nonzeros proportional to the reference cohort.
For large panels, matrix nonzeros and solve time should be reported alongside
the number of DMUs, periods, processes, links, and carry-overs.

## Verification and source boundary

The executable consistency checks include:

- exact K=1 reductions to the implemented Tone--Tsutsui dynamic SBM under its
  common-account domain;
- exact T=1 reductions to static Tone--Tsutsui network SBM for free/fixed
  links;
- source-balance and economic-ownership checks for all four link kinds and all
  four carry-over kinds across the three orientations;
- deterministic synthetic results under CRS/VRS, mixed-RTS metadata, immutable
  sparse-template reuse, balance reconstruction, continuity, and
  failure-domain tests; and
- one compiled reference plus one primary LP per trajectory.

In addition, a production-independent dense Charnes--Cooper programme gives a
genuinely joint analytical certificate. Its synthetic fixture has two
trajectories, two periods, two processes, one recipient-accountable input link,
and one good carry-over per process under non-oriented CRS with equal positive
period and process weights. An exact rational primal and dual both attain
$2/3$. The public result reconstructs the same system score from contributions
$1/12+1/4+1/12+1/4$, reports handoff targets 1 and 3 across the two periods,
and reports both carry-over transition targets at 1 with zero continuity
residuals. Independently deleting the link or carry-over continuity equations
changes the optimum to $1/2$ or $16/27$; deleting both gives $8/17$. Thus both
connections are economically active rather than decorative.

The K=1 and T=1 reductions still establish only internal agreement on their
shared domains. The joint analytical certificate closes that former gap for
its named non-oriented CRS fixture without extending the claim to other
orientations, RTS policies, weights, link or carry-over roles, or boundary
rules. Stronger verification does not broaden the method's declared scope.

The published application reports 21 anonymous US electricity utilities over
1991--1995 with three divisions. The article supplies displayed efficiency
results but not the raw panel or utility identities, so it is retained as a
non-reproduced empirical application rather than claimed as an executable
literature-table oracle. The built-in power demo and the analytical fixture are
explicitly synthetic.

The public technical implementation does not implement:

- the source reverse-chronological secondary decomposition;
- initial or terminal boundary conditions beyond the declared core;
- source-qualified free-link or free-carry-over objective extensions, whose
  exact executable variant has not yet been frozen;
- undesirable-output environmental technologies merely by treating pollution
  as an ordinary input;
- dynamic Malmquist or another productivity-change operator; or
- decay, loss, material balance, shared resources, changing graphs, missing
  trajectories, or statistical inference.

Dynamic Malmquist was not part of the published base model. It requires a
separate source-qualified productivity operator, not post-processing of
adjacent efficiency scores.
