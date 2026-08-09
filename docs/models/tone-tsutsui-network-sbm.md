# Tone--Tsutsui network SBM

```{eval-rst}
.. currentmodule:: deapack
```

Tone and Tsutsui’s network slacks-based measure evaluates one connected
organization while retaining process-specific resources, results, slacks,
and peer intensities. Its canonical method ID is
`network.sbm.tone_tsutsui_2009`.

```{admonition} Public implementation
:class: important

`ToneTsutsuiNetworkSBM` is the public source-faithful class and `NetworkSBM`
is its exact short alias. Both names are exported from `deapack`. The public
datasets `three_process_service_chain` and `crs_free_link_service_chain` provide the
two source-oracle samples described below.
```

Defining sources:

- [Tone and Tsutsui (2009)](https://doi.org/10.1016/j.ejor.2008.05.027);
- the equation-complete
  [GRIPS discussion paper](https://doi.org/10.24545/00000978); and
- [Kao’s network DEA review](https://doi.org/10.1016/j.ejor.2014.02.039)
  for family boundaries.

## Complete public example

This example evaluates the ten source utilities as connected
generation--transmission--distribution systems. The input orientation asks
where external resources could be conserved; VRS permits a different
process-level scale environment; and `free` treats both handoffs as
quantities the divisions may redesign jointly.

```python
from deapack import (
    LinkSpec,
    NetworkData,
    NetworkSBM,
    NetworkSpec,
    ProcessSpec,
    load_dataset,
)

frame = load_dataset("three_process_service_chain")
spec = NetworkSpec(
    processes=(
        ProcessSpec(
            "stage_1",
            inputs="stage_1_input",
            outputs="link_1_2",
        ),
        ProcessSpec(
            "stage_2",
            inputs=("link_1_2", "stage_2_input"),
            outputs=("stage_2_output", "link_2_3"),
        ),
        ProcessSpec(
            "stage_3",
            inputs=("link_2_3", "stage_3_input"),
            outputs="stage_3_output",
        ),
    ),
    links=(
        LinkSpec(
            "handoff_1_2",
            source="stage_1",
            target="stage_2",
            variables="link_1_2",
        ),
        LinkSpec(
            "handoff_2_3",
            source="stage_2",
            target="stage_3",
            variables="link_2_3",
        ),
    ),
)
data = NetworkData.from_frame(frame, dmu="dmu", spec=spec)

result = NetworkSBM(
    orientation="input",
    returns_to_scale="vrs",
    link_control="free",
    division_weights={
        "stage_1": 0.4,
        "stage_2": 0.2,
        "stage_3": 0.4,
    },
).fit(data)
```

`ToneTsutsuiNetworkSBM(...)` produces the same result because `NetworkSBM`
is an alias, not a second estimator.

## Source production technology

For process $k=1,\ldots,K$:

- $X^k$ is the matrix of external inputs;
- $Y^k$ is the matrix of external outputs;
- $\lambda^k$ is a process-specific nonnegative intensity vector;
- $s_o^{k-}$ and $s_o^{k+}$ are external-input and external-output
  slacks for evaluated organization $o$; and
- $Z^{(k,\ell)}$ stores the observed link from supplier process $k$ to
  recipient process $\ell$.

External balances are

$$
x_o^k=X^k\lambda^k+s_o^{k-},
\qquad
y_o^k=Y^k\lambda^k-s_o^{k+}.
$$

The source VRS specification adds

$$
\mathbf1^\top\lambda^k=1
\qquad\text{for every }k.
$$

The source CRS specification omits every process convexity equation. One
system-wide convexity row is not equivalent. Mixed process-level returns to
scale, NIRS, and NDRS are outside this source preset.

Every organization must share one graph and one assignment of variables to
external-input, external-output, or directed-link roles. A link is stored
once and used by both adjacent process accounts.

## Four source link responsibilities

The link policy answers two different management questions:

1. must the benchmark inherit the observed handoff, or may adjacent
   divisions coordinate a different one; and
2. if the handoff itself is scored, which division owns that performance
   responsibility?

All four source roles preserve one supplier--recipient flow. They differ in
whether the observed amount is binding and whether a link slack enters one
process account.

### Fixed and free coordination

`fixed` and `non-discretionary` are source naming aliases. For a fixed link,

$$
Z^{(k,\ell)}\lambda^k
=z_o^{(k,\ell)}
=Z^{(k,\ell)}\lambda^\ell.
$$

Both process benchmark plans reproduce the evaluated organization’s observed
handoff.

`free` and `discretionary` are source naming aliases. For a free link,

$$
Z^{(k,\ell)}\lambda^k
=
Z^{(k,\ell)}\lambda^\ell.
$$

The common target may differ from observation, but source-recipient
continuity remains. Removing the equality does not implement a free link.

For the same sample, orientation, returns to scale, and weights, the
free-link feasible set contains the fixed-link set. The resulting
higher-is-better efficiency therefore cannot exceed its fixed-link
counterpart, subject to solver tolerance.

The fixed/free base objectives do not include proportional link slacks.

### Incoming link as a recipient input

Tone and Tsutsui's equation (26) lets the recipient carry an incoming-link
excess in the input-oriented account:

$$
z_o^{(k,\ell)}
=Z^{(k,\ell)}\lambda^\ell+s_o^{(k,\ell)-},
\qquad
Z^{(k,\ell)}\lambda^k
=Z^{(k,\ell)}\lambda^\ell.
$$

The first equality says how much of the observed handoff the recipient could
avoid. The second still requires the supplier and recipient benchmark plans
to agree. The slack is counted once, in process $\ell$; it is not duplicated
as a supplier shortfall.

### Outgoing link as a supplier output

Equation (27) gives the supplier the mirror output responsibility:

$$
z_o^{(k,\ell)}
=Z^{(k,\ell)}\lambda^k-s_o^{(k,\ell)+},
\qquad
Z^{(k,\ell)}\lambda^k
=Z^{(k,\ell)}\lambda^\ell.
$$

The link shortfall is counted once in supplier $k$'s output-oriented account.
The recipient remains part of the same feasible organizational plan.

These oriented equations do not define a non-oriented accountable-link
score. DEAPack fails closed for `orientation="non-oriented"` with
`as_input` or `as_output`, for `as_output` under input orientation, and for
`as_input` under output orientation.

Use `link_control` for a uniform fixed/free policy. Use `link_kinds` when
links have explicit individual roles:

```python
accountable_result = NetworkSBM(
    orientation="input",
    returns_to_scale="vrs",
    link_kinds={
        "handoff_1_2": "as_input",
        "handoff_2_3": "free",
    },
    division_weights={
        "stage_1": 0.4,
        "stage_2": 0.2,
        "stage_3": 0.4,
    },
).fit(data)
```

The mapping must classify every declared link exactly once. Source aliases
`LB` and `LG` normalize to `as_input` and `as_output`; explicit descriptive
names are preferred in research code.

## Exogenous process weights

The source requires

$$
w_k\geq0,
\qquad
\sum_{k=1}^{K} w_k=1.
$$

These are declared process-importance weights, not fitted DEA multipliers and
not link weights. Cost shares are one possible basis. The source electricity
illustration uses $(0.4,0.2,0.4)$; those values must not become a package
default.

Strictly positive weights are required before system efficiency of one can
be interpreted as certification for every process. A zero-weight process can
constrain feasibility without being identified by the system objective.

## Orientation-specific accounts

For every scored process with positive external normalizers, define

$$
A_o^k
=
1-\frac{1}{m_k}\sum_i
\frac{s_{io}^{k-}}{x_{io}^k},
\qquad
B_o^k
=
1+\frac{1}{r_k}\sum_r
\frac{s_{ro}^{k+}}{y_{ro}^k}.
$$

For fixed and free links these averages contain only external variables. If
$\mathcal I_k$ is the set of incoming links declared `as_input`, equation
(26) replaces the input account by

$$
A_o^k
=
1-\frac{
\displaystyle
\sum_{i=1}^{m_k}\frac{s_{io}^{k-}}{x_{io}^k}
+
\sum_{(h,k)\in\mathcal I_k}\sum_{j=1}^{q_{hk}}
\frac{s_{jo}^{(h,k)-}}{z_{jo}^{(h,k)}}
}{
\displaystyle
m_k+\sum_{(h,k)\in\mathcal I_k}q_{hk}
}.
$$

If $\mathcal O_k$ is the set of outgoing links declared `as_output`,
equation (27) analogously replaces the output account by

$$
B_o^k
=
1+\frac{
\displaystyle
\sum_{r=1}^{r_k}\frac{s_{ro}^{k+}}{y_{ro}^k}
+
\sum_{(k,h)\in\mathcal O_k}\sum_{j=1}^{q_{kh}}
\frac{s_{jo}^{(k,h)+}}{z_{jo}^{(k,h)}}
}{
\displaystyle
r_k+\sum_{(k,h)\in\mathcal O_k}q_{kh}
}.
$$

The dimension changes only for the responsible process. An accountable link
never receives a second endpoint weight.

## Input orientation

Process efficiency is

$$
\theta_o^k=A_o^k,
$$

and system efficiency is the weighted arithmetic identity

$$
\theta_o=\sum_{k=1}^{K} w_k\theta_o^k.
$$

For fixed and free links, only external-input slacks enter the objective. With
an `as_input` link, the recipient-owned incoming excess also enters that
recipient's input account exactly once. External-output slacks and targets
remain feasible but solver-selected unless a separate completion policy is
run; fixed, free, and non-owner link deviations remain unscored.

## Output orientation

Process output efficiency is

$$
\tau_o^k=\frac{1}{B_o^k}.
$$

The direct LP maximizes the system expansion account

$$
q_o
=
\sum_{k=1}^{K} w_k B_o^k
=
\sum_{k=1}^{K}\frac{w_k}{\tau_o^k},
$$

and reports

$$
\tau_o=\frac{1}{q_o}.
$$

The system result is a weighted harmonic aggregation of the process
efficiencies. An arithmetic average of $\tau_o^k$ is not the source model.
For reporting, the denominator-adjusted weights

$$
\omega_o^k
=
\frac{w_kB_o^k}{\sum_{\ell=1}^{K}w_\ell B_o^\ell}
$$

give the exact linear identity
$\tau_o=\sum_{k=1}^{K}\omega_o^k\tau_o^k$. The result stores $w_k$ as
`division_weight` and $\omega_o^k$ as
`effective_reconstruction_weight`.
For fixed and free links, the objective scores only external-output
shortfalls. With an `as_output` link, the supplier-owned outgoing shortfall
also enters that supplier's output account exactly once. External-input
slacks remain feasible but unscored.

## Non-oriented account

At a selected system optimum, process efficiency is

$$
\rho_o^k=\frac{A_o^k}{B_o^k}.
$$

System efficiency is

$$
\rho_o
=
\frac{\sum_{k=1}^{K} w_k A_o^k}
       {\sum_{k=1}^{K} w_k B_o^k}.
$$

It is not $\sum_{k=1}^{K} w_k\rho_o^k$. The exact reconstruction is

$$
\rho_o
=
\sum_{k=1}^{K}\omega_o^k\rho_o^k,
\qquad
\omega_o^k
=
\frac{w_kB_o^k}{\sum_{\ell=1}^{K}w_\ell B_o^\ell}.
$$

The $\omega_o^k$ are endogenous denominator-adjusted reconstruction
weights. They do not replace the exogenous management policy $w_k$.

The non-oriented ratio uses a single source-compatible Charnes--Cooper scale.
The result retains the numerator and denominator accounts, transform scale,
effective reconstruction weights, and reconstruction residual rather than
exposing only the ratio.

## Efficiency and interpretation

All public system and process efficiencies are
higher-is-better, with one denoting the optimum on the positive,
self-inclusive source domain.

Input-oriented score one checks the scored external-input side. It does not
certify zero external-output slack. Output-oriented score one has the mirror
limitation. The result therefore keeps
`is_network_sbm_efficient` separate from the nullable generic
`is_efficient` status.

Division weights may be zero, as in the source formulation. In that case a
system score of one still defines network-SBM efficiency for the declared
management account, but it cannot certify an unweighted division. DEAPack
therefore reports `all_positive_weight_divisions_efficient` while leaving
`all_divisions_efficient` and the generic `is_efficient` status undefined.
With strictly positive weights, system score one identifies every division
on the scored side; only the non-oriented programme certifies both external
sides at once.

Process scores come from the joint system optimum. They are not independent
process DEA scores, causal contributions, or automatically unique
performance-attribution shares.

One-click plots and result briefs label `system_efficiency` as
**Network-System Performance**. Their benchmark note says that value one
means no scored burden or shortfall remains in the positively weighted
process accounts. If any division has zero weight, the brief also displays
an explicit warning that this does not establish efficiency for every
division.

## Targets, peers, and nonuniqueness

For a selected primary optimum,

$$
x_o^{k*}=x_o^k-s_o^{k-*},
\qquad
y_o^{k*}=y_o^k+s_o^{k+*}.
$$

A fixed link target equals $z_o^{(k,\ell)}$. A free link target is

$$
z_o^{(k,\ell)*}
=
Z^{(k,\ell)}\lambda^{k*}
=
Z^{(k,\ell)}\lambda^{\ell*}.
$$

An `as_input` target additionally satisfies

$$
z_o^{(k,\ell)}
=z_o^{(k,\ell)*}+s_o^{(k,\ell)-},
$$

and belongs to the recipient's input target account. An `as_output` target
satisfies

$$
z_o^{(k,\ell)}
=z_o^{(k,\ell)*}-s_o^{(k,\ell)+},
$$

and belongs to the supplier's output target account. In both cases
$z_o^{(k,\ell)*}$ is still the same supplier and recipient reference flow.

The complete target must remain link-feasible. Processes must not be
projected independently after fitting.

The source explicitly permits nonunique process scores. System efficiency
can be fixed while slacks, process attribution, intensities, peers, and free
or accountable link targets vary. DEAPack labels the returned account
`solver_selected_primary_optimum` and the summary
`solver_selected_not_uniqueness_certified`. It does not report attribution
bounds that it has not solved.

Source frontier-existence statements are conditional:

- VRS provides at least one observed efficient exemplar for every process;
- CRS with fixed links has an analogous result; and
- CRS with free links may have a process with no observed efficient
  exemplar.

The last outcome is not by itself a solver error.

## Public result surface

The fitted `DEAResult` separates system performance, divisional performance
attribution, internal coordination, and external operating targets:

| Result area | Public fields used for interpretation |
|---|---|
| `summary()` | `system_efficiency`; independent `score`, `target`, `link`, `peer`, and `dual` validity/status pairs; `is_network_sbm_efficient`; nullable generic efficiency fields; operating accounts; semantic `solver_status` plus backend/raw status; reconstruction and link residuals; `decomposition_status` |
| `components` | `component_kind`, `component_id`, `process_id`, `efficiency`, `division_weight`, `effective_reconstruction_weight`, `input_account`, `output_expansion_account`, `attribution_status` |
| `links` | `link_id`, `link_kind`, `source_process_id`, `recipient_process_id`, `responsibility_owner_process_id`, `responsibility_role`, `observed`, endpoint and accountability targets, `link_slack`, `normalized_link_slack`, objective inclusion, continuity/accountability/fixed residuals, `selection_status` |
| `targets` | external roles plus accountable `link_input` or `link_output` rows, with `process_id`, optional `link_id`, `variable`, `observed`, `target`, `balance_residual`, `selection_status` |
| `diagnostics` | semantic and raw backend status; independent LP, canonical-account, original-unit, target, link, thresholded-peer, and dual-row gates; omitted peer mass; reasons and residuals |
| `metadata` | method/specialization identity, graph and process contract, orientation, RTS, link policy, division weights, score direction, solver tolerances, attribution policy, and zero-extra-solve counters |

Use the one-DMU accessors when preparing a management case:

```python
system_report = result.summary()[[
    "dmu_id",
    "system_efficiency",
    "score_valid",
    "target_valid",
    "link_valid",
    "peer_valid",
    "dual_valid",
    "solver_status",
    "backend_solver_status",
    "reconstruction_residual",
    "max_link_continuity_residual",
    "decomposition_status",
]]

division_report = result.components_for("A")[[
    "component_kind",
    "component_id",
    "efficiency",
    "division_weight",
    "input_account",
    "attribution_status",
]]

handoff_report = result.links_for("A")[[
    "link_id",
    "link_kind",
    "source_process_id",
    "recipient_process_id",
    "responsibility_owner_process_id",
    "responsibility_role",
    "observed",
    "target",
    "link_slack",
    "continuity_residual",
    "accountability_balance_residual",
    "selection_status",
]]

external_targets = result.targets_for("A")[[
    "process_id",
    "role",
    "variable",
    "observed",
    "target",
    "balance_residual",
    "selection_status",
]]

assumptions = {
    key: result.metadata[key]
    for key in (
        "method_id",
        "orientation",
        "returns_to_scale",
        "link_control",
        "link_kinds",
        "division_weights",
        "score_direction",
        "attribution_status",
        "target_selection",
        "base_objective_includes_link_slacks",
        "tolerance",
    )
}
```

For utility A, the example reports system efficiency of approximately
`0.385273`; its selected stage efficiencies are approximately `0.383055`,
`0.382763`, and `0.388747`. The two selected free-link targets are
approximately `0.836000` and `0.354574`. `links` stores those internal
targets, while `targets` stores only external-input and external-output
projections. `intensities` separately records process-specific positive peer
weights.

The selected process accounts, peers, and targets all carry an explicit
selection status. They are valid jointly feasible witnesses of the system
optimum, not certificates that no other optimum exists.

`peer_tolerance` changes only the sparse peer table. After applying that
reporting threshold, DEAPack reconstructs the process targets, link
continuity, and VRS balances again. If the shortened peer list no longer
supports the published operating plan, the score, targets, and links remain
available but `peer_valid=False` and `intensities` is withheld. Diagnostics
report both the omitted intensity mass and the resulting reconstruction
violation.

## Result-native process and handoff figure

For the input-oriented base model with fixed/free links, one organization can
be displayed without turning the network into separate departmental DEA
studies:

```python
figure = result.plot(kind="process", dmu_id="A")
```

The process bars read the selected input accounts, while the system panel
reconstructs `system_efficiency` from `division_weight * efficiency`. The
handoff ledger preserves each variable's original unit and keeps observed and
selected common targets distinct. A zero-weight process is explicitly marked
unscored; it can remain part of the feasible network even though it contributes
nothing to the declared-weight objective.

This visual contract is intentionally narrower than the estimator. It rejects
output and non-oriented accounts because their system aggregation is not the
input arithmetic mean. It also rejects accountable-link specializations and
other Network DEA families because their process quantities arise from
different valuation and responsibility institutions. Before rendering, it
requires both certificates and reconstructs the process weights, system score,
link topology, supplier--recipient continuity, and fixed-link commitments.
Free-link targets remain solver-selected values from one primary optimum, not
unique prescriptions.

## Certification before result release

The system score and its divisional operating plan are published only after
two independent audit gates pass. A backend's `optimal` label by itself does
not establish that either one has passed.

The shared solver-neutral LP certificate independently checks the primal
rows, variable bounds, reported objective, row and bound marginals,
stationarity, sign conditions, complementarity, and strong duality. Missing,
nonfinite, or wrong-length row marginals are rejected. Bound marginals are
validated whenever supplied and are required for finite, fixed, or upper
bounds that cannot be certified by the standard nonnegative-cone fallback.
This is especially important for transformed programmes: a numerically
filled vector is not accepted merely because its backend status is
`optimal`.

The model-specific certificate then reverses any fractional transformation
and reconstructs the organization as one connected operating account. It
checks a valid transformation scale, the orientation-specific score and
objective identity, every process's external-input and external-output
balance, supplier--recipient continuity, fixed handoffs, accountable-link
owner balances, and the weighted system--division reconstruction.
The same quantity accounts are independently returned to their original
units and checked with scale-normalized residuals; the public result does not
rely only on an internally scaled LP.

Primary failure is atomic and fail-closed. When a backend says `optimal` but
either primary certificate rejects the plan, semantic `solver_status` is
`numerical_error`; `backend_solver_status` and `raw_solver_status` preserve
the backend claim. `score_valid=False`, `score_status` identifies the failed
gate, and canonical scores are missing. `components`,
`slacks`, `targets`, `intensities`, `duals`, and `links` are all withheld, so
rows from an uncertified plan cannot leak into a management report.
`diagnostics` retains the exact failed gate, reason, and residuals, and
`metadata["postsolve_certificate"]` records the release policy.

After a certified primary plan exists, public claims are gated separately.
The original-unit target and link accounts, thresholded peer account, and
complete finite dual-row account each have their own validity/status pair.
Failure of the presentation-level peer gate cannot erase a valid efficiency
score or operating target.

## Data domain and explicit failures

The canonical preset requires:

- one connected, graph-compatible cross-section;
- finite, strictly positive external and link quantities;
- a nonempty relevant external block for every scored process;
- one observed account for each directed link;
- source CRS or VRS applied to every process;
- one fixed, free, as-input, or as-output role declared for every link;
- input orientation for every as-input link, output orientation for every
  as-output link, and no accountable-link role in the non-oriented source
  programme;
- nonnegative process weights summing to one; and
- a feasible connected network programme.

Zeros cannot enter a proportional average through an undocumented epsilon.
Negative values cannot be silently translated. Missing process blocks are
not zeros. Lossy or transformed links, shared system resources, undesirable
intermediates, carry-overs, common intensities, intensity-connectivity
restrictions, super-efficiency, and dynamic network SBM require separate
contracts.

## Source reproduction and numerical boundary

```{admonition} Tables 3, 4, and 6 reproduced
:class: important

DEAPack reproduces the printed system efficiencies in Tables 3 and 4
(VRS/input, fixed and free links) and Table 6 (CRS/input/free) with absolute
tolerance `5.1e-4` and zero relative tolerance. The corresponding three
process efficiencies reproduce within absolute tolerance `7.5e-4` and zero
relative tolerance. The slightly wider process tolerance accommodates the
source’s finite-decimal reporting; it is not an economic tolerance.
```

The first oracle contains ten 1994 U.S. vertically integrated electricity
utilities, three series processes, two links, VRS input orientation,
$(0.4,0.2,0.4)$ weights, and both fixed- and free-link results. The second
contains four synthetic DMUs under CRS/input/free and illustrates the absence
of an observed efficient exemplar in one process.

The corresponding public data loaders are:

```python
from deapack import dataset_info, load_dataset

utilities = load_dataset("three_process_service_chain")
utility_roles = dataset_info("three_process_service_chain").roles

crs_example = load_dataset("crs_free_link_service_chain")
crs_roles = dataset_info("crs_free_link_service_chain").roles
```

The source-oracle checks also reconstruct the input-oriented system account
from the declared weights and selected process accounts within
$2\times10^{-9}$, and enforce supplier--recipient link continuity within
$2\times10^{-8}$. These are software accounting checks, distinct from the
rounding tolerance applied to printed source scores.

The accountable-link extensions use a separate analytical certificate rather
than borrowing those utility tables. Under VRS with equal process weights,
the exact equation (26) fixture gives system score $5/8$, recipient link-input
slack 1, and common target 1. The exact equation (27) fixture gives system
score $4/7$, supplier link-output slack 1, and common target 2. Both fixtures
verify zero endpoint-continuity and owner-balance residuals, single-count
dimension weights, unit invariance, invalid orientation failures, one sparse
compile per reference population, and one primary solve per observation.

Table 7 reports one selected CRS/free projection. DEAPack verifies that its
returned external targets and link targets are jointly feasible, but does
not force the solver to return that particular peer basis or target vector.
Alternative process scores, peer intensities, and targets may support the
same primary system efficiency. The public labels
`solver_selected_primary_optimum` and
`solver_selected_not_uniqueness_certified` preserve that boundary.

The source’s numerical application is an input-oriented oracle. Its first
process has no external output, so the article does not provide an
output-oriented or non-oriented numerical table for this dataset. Those
public orientations are validated with exact hand-worked cases and their
native aggregation identities; they must not be described as reproductions
of an absent source table.

The paper’s prose refers to its later empirical tables as Tables 6--8, while
the actual displayed tables are numbered 5--7. Table 4’s printed reference
entry for utility I also has an ambiguous `I(1)` layout. Those provenance
notes must remain attached; alternate-optimal references and targets must not
be promoted to unique source facts.

## Constructor and validation contract

`ToneTsutsuiNetworkSBM` and `NetworkSBM` accept:

| Argument | Public contract |
|---|---|
| `orientation` | `"input"`, `"output"`, or `"non-oriented"`; default `"non-oriented"` |
| `returns_to_scale` | `"crs"` or `"vrs"`; default `"vrs"` |
| `link_control` | `"fixed"`/`"non-discretionary"` or `"free"`/`"discretionary"`; default `"free"` |
| `link_kinds` | optional mapping that classifies every link ID exactly once as `"fixed"`, `"free"`, `"as_input"`, or `"as_output"`; use instead of a non-default `link_control`; accountable roles must match the orientation |
| `division_weights` | mapping from every process ID to a finite nonnegative share summing to one; `None` gives equal shares |
| `reference` | public reference-set specification; default full self-appraisal |
| `solver` / `solver_options` | custom solver or options, but not both |
| `tolerance` | positive finite classification and residual tolerance; default `1e-7` |
| `peer_tolerance` | positive finite reporting threshold; defaults to `tolerance` |

`fit()` requires a validated `NetworkData`. Zero or negative quantities,
missing scored process blocks, incomplete weight mappings, unsupported
returns-to-scale assumptions, and inconsistent graph roles fail explicitly
rather than being silently translated or completed.

## Sparse execution contract

Let $n$ be the reference-population size, $K$ the number of processes,
$M$ and $R$ the numbers of external input and output accounts, and let
$Q_{\mathrm{free}}$, $Q_{\mathrm{fixed}}$, and $Q_a$ count link-variable
accounts classified as free, fixed, and accountable (`as_input` or
`as_output`). The source LP has
$Kn+M+R+Q_a+1$ decision variables. Before its final normalization row, the
CRS programme has
$M+R+Q_{\mathrm{free}}+2Q_{\mathrm{fixed}}+2Q_a$ balance rows; VRS adds
$K$ process-convexity rows.

DEAPack compiles each distinct reference population once, stores the static
blocks in CSC form, and solves one primary LP per evaluated observation. The
complete equality-matrix structure is cached; fitting a new DMU updates only
the observation-dependent scale column and, for the non-oriented model, the
normalization coefficients. Reproduce workload-specific timing with:

```console
python benchmarks/benchmark_network_sbm.py --n-dmus 100
python benchmarks/benchmark_network_sbm.py --n-dmus 1000
python benchmarks/benchmark_network_sbm.py \
    --n-dmus 100 --orientation all --link-policy all
```

The benchmark checks compilation and the exact one-primary-solve-per-DMU
contract, zero certificate solves, all five claim gates, score and
original-unit account reconstruction, link continuity, matrix dimensions,
nonzero count, and density. Runtime remains backend- and hardware-dependent.
