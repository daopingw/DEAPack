# Additive DEA

```{eval-rst}
.. currentmodule:: deapack
```

`AdditiveDEA` estimates Pareto--Koopmans inefficiency from simultaneous input
and output slacks. Its source-qualified profile is the VRS, unit-weight,
self-inclusive cross-sectional programme in Charnes et al. (1985):

$$
\delta_o=\max
\left(\sum_i s_i^-+\sum_r s_r^+\right)
$$

subject to

$$
X\lambda+s^-=x_o,\qquad Y\lambda-s^+=y_o,
$$

$$
\mathbf 1^\top\lambda=1,
\qquad
\lambda,s^-,s^+\geq0.
$$

The convexity equation is part of the classic source formulation, not merely
the package default.

## Basic use

```python
from deapack import AdditiveDEA, DEAData, load_dataset

frame = load_dataset("slacks_2x2")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["labor", "capital"],
    outputs=["service", "quality"],
)

result = AdditiveDEA().fit(data)
summary = result.summary()
slacks = result.slacks
targets = result.targets
```

The native `score` and `distance` are both $\delta_o$: zero is efficient and
larger values mean more weighted slack. Raw additive distance is neither
bounded nor unit invariant, so `efficiency` is intentionally missing rather
than populated with an arbitrary transformation.

For the default fit, `result.metadata["source_profile"]` is
`"charnes_etal_1985_eq_4_6"`. A nonmatching configuration records
`"deapack_configurable_additive_extension"` together with explicit mismatch
reasons. Explicitly supplied all-one weights are algebraically identical to
the source objective and therefore retain the same profile; metadata records
that their parameter source was user-declared.

## Configurable package extension

DEAPack can replace the unit sum by

$$
\delta_o=\max
\left(\sum_i\omega_i^x s_i^-+\sum_r\omega_r^y s_r^+\right)
$$

and can apply an explicitly selected RTS or reference policy. These settings
reuse the same solver family but do not inherit the narrow 1985 source
certificate. In particular, the article's equation (5.7) uses
observation-specific reciprocal quantities; it is not an authority for one
arbitrary fixed weight vector across all fitted observations.

Weights may be sequences in data-column order or mappings by variable name:

```python
model = AdditiveDEA(
    input_weights={"labor": 1.0, "capital": 0.01},
    output_weights={"service": 1.0, "quality": 10.0},
)
result = model.fit(data)
```

Every weight must be finite and strictly positive. The exact values appear in
`result.metadata` and in the `weight` column of `result.slacks`. If the
weight-by-unit products have a relative magnitude at or below the solver's
effective dual feasibility tolerance, fitting fails closed rather than
allowing the optimizer to treat a strictly positive account as numerically
weightless. A smaller dynamic weight needs a matching `SolverOptions`
dual-feasibility tolerance; lowering only the model's reporting tolerance is
not sufficient.

`WeightedAdditiveDEA` is a discoverability alias for `AdditiveDEA`; it does
not invoke a second numerical implementation or identify a separately
source-certified historical method.

For VRS, the production LP subtracts one common reference-set anchor from
both the reference accounts and the evaluated account before row scaling;
the convexity equation makes this exactly equivalent to the physical balance
and prevents a common translation from hiding a small improvement. The
anchored reference matrix is compiled once per comparison population and
reused. Other RTS paths retain level-scaled balances. Reported slacks and
targets stay in physical units.
`scaled_slack` uses the maximum reference deviation from the evaluated
account for a unit- and VRS-translation-stable strong-status decision;
`solver_scaled_slack` discloses the numerical LP variable separately. A very
small intensity is retained when its quantities materially explain the
reported target, and dual rows are emitted only after an optimal solve.

## Keep comparison rights separate from the slack account

`AdditiveDEA`, `WeightedAdditiveDEA`, `RangeAdjustedDEA`, and `RAM` accept the
same observation-specific `PeerEligibility` declaration as the classical
radial, SBM, and directional families. For evaluated observation $o$, the
model intersects the rows admitted by `ReferenceSpec` with the candidates
declared eligible for that observation. Eligibility can remove evidence; it
cannot restore a row hidden by a temporal or custom reference rule, and the
model never inserts the evaluated row automatically.

This composition changes the evidence available to the additive programme,
not the meaning of its weights. Unit weights remain unit weights, and a
user-supplied weight continues to value one physical unit of its corresponding
slack. Every fitted summary distinguishes `base_reference_size`, effective
`reference_size`, and `self_in_reference`. Compact `peer_eligibility` metadata
records the declared rule and exact intersection, while positive intensities
remain solver-selected results. See {doc}`../user-guide/reference-sets` for
keyed and positional declarations, common failure semantics, and the list of
families that have completed this audit.

## Range-adjusted measure (RAM)

`RangeAdjustedDEA` supplies the canonical RAM weights
$1/((m+s)R)$, where $R$ is the sample range of the corresponding variable.
It uses VRS and reports:

- `score = efficiency = 1 - distance`;
- `distance`: normalized RAM inefficiency in $[0,1]$;
- `RAM`: a historical discoverability alias for `RangeAdjustedDEA`.

```python
from deapack import RAM

result = RAM().fit(data)
```

RAM supports negative data because its VRS formulation is translation
invariant. The exact source-qualified profile is
`cooper_park_pastor_1999_eq_17_18_20_23`: one self-inclusive cross section,
and one matching global VRS technology/range population. Results expose
`source_profile_matches` and `source_profile_mismatches`.

Comparison eligibility does **not** turn RAM into a locally renormalized
measure. Its input and output ranges are computed once from the full
`DEAData` supplied to the global base policy, before the observation-specific
eligibility intersection. Metadata identifies this scope as
`base_global_data_before_peer_eligibility`. Each observation may then have a
different effective comparison population, but all RAM scores retain the same
full-data range units. Recomputing a private range for every eligible set would
change the measure across observations and could break its bounded common
scale.

Consequently, a RAM fit whose eligibility rule removes any base candidate is
recorded as a configurable DEAPack extension rather than the exact full,
self-inclusive Cooper--Park--Pastor source profile. RAM still accepts only the
automatic or global base reference policy; panel data must request
`reference="global"` explicitly. The eligibility rule is a separate
restriction within that global information base, not permission to use a
contemporaneous, window, or custom RAM normalization.

For a zero observed range, Cooper, Park, and Pastor allow the associated
coordinate constraint to be omitted and its slack contribution set to zero.
DEAPack retains the balance with zero objective weight. Under the same
self-inclusive VRS range/reference population, the constant coordinate and
convexity identity force the slack to zero, so this is source-equivalent.
Metadata records
`zero_range_policy_source="cooper_park_pastor_1999_section_8"`. Panel data
must explicitly use `reference="global"`; this confirms that all-period
ranges and a global frontier are intended, but the panel run remains outside
the one-cross-section source profile.

The bounded-adjusted measure is a distinct one-sided normalization, not a RAM
alias. See {doc}`bam` for `BoundedAdjustedDEA` / `BAM`, its explicit slack
bounds, four returns-to-scale choices, and frozen-global reference policy.

## Runtime certificates and claim-specific release

An LP backend's `optimal` label is retained as raw evidence, but it is not by
itself permission to publish an Additive or RAM result. Both estimators use the
shared solver-neutral certificate to reconstruct primal rows, variable bounds,
the reported objective, dual feasibility, stationarity, complementarity, and
strong duality. The model then reverses its numerical row and objective scales
and checks the raw physical production account before applying any reporting
cleanup.

The published account is checked a second time in original quantity units.
This gate reconstructs resource savings, service gains, targets, the weighted
slack sum, and the selected RTS identity. RAM additionally reconstructs its
range-normalized distance and `efficiency = 1 - distance`. A certificate for
the numerical LP therefore cannot be borrowed as a certificate for a rounded
or rescaled result table.

The summary exposes four separate publication claims:

| Claim | Validity field | Successful status |
|---|---|---|
| native Additive distance or RAM score and its original-unit slack ledger | `score_valid` | `score_status="defined"` |
| original-unit targets | `target_valid` | `target_status="certified_published_quantity_account"` |
| peers remaining after the reporting threshold | `peer_valid` | `peer_status="certified_thresholded_peer_account"` |
| complete original-unit constraint marginals | `dual_valid` | `dual_status="certified_original_unit_dual_account"` |

The peer gate is not a check on the unthresholded optimizer vector alone. It
rebuilds the published target from the intensities that remain visible after
`peer_tolerance` is applied. A materially contributing peer cannot disappear
silently. The dual gate checks the complete published row account and its
original-unit objective identity rather than copying whatever marginal array
the backend returned.

These claims follow a dependency chain without being collapsed into one
all-or-nothing status. A certified score may remain available if a later peer
or dual publication gate fails; the affected table is withheld and its own
validity/status fields explain why. A failed target gate prevents a peer claim
because there is then no certified quantity account for the displayed peers to
reconstruct. Never infer table validity from `solver_status` alone.

`solver_status`, `backend_solver_status`, and `raw_solver_status` all preserve
the backend result. The claim-specific `score_status`, `target_status`,
`peer_status`, and `dual_status` record the semantic release outcomes. Thus an
uncertified backend optimum remains auditable as raw `optimal` evidence while
the affected canonical values are missing. Failures are isolated by
observation, and summary, diagnostic, slack, target, intensity, and dual tables
retain stable columns even when every observation fails. This makes downstream
joins fail closed instead of depending on whether a successful row happened to
create a schema.

The diagnostic table records each gate directly:
`lp_postsolve_certified`, `raw_account_certified`,
`published_account_certified`, `published_quantity_account_certified`,
`published_weighted_slack_account_certified`,
`published_peer_account_certified`, and
`published_dual_account_certified`. Residual fields retain the largest LP,
raw-account, published-account, peer-account, and original-unit dual-account
violations for audit.

Certification reuses the one primary solution. For a global comparison of
$n$ observations, Additive DEA and RAM each compile one reference, run exactly
$n$ primary LPs, run no secondary LP, and add no certificate solve. Inspect
`primary_solver_calls`, `secondary_solver_calls`, `solver_calls`,
`additional_solver_calls`, `certificate_extra_solver_calls`, and
`compiled_reference_sets` in `result.metadata`. The deterministic release
check is:

```console
python benchmarks/benchmark_classical_foundations.py \
    --method additive ram --n-dmus 100
```

The benchmark refuses a missing certificate field, a nonfinite or excessive
residual, a validity/status mismatch, a backend/raw-status disagreement, an
incomplete semantic table, or an execution count that differs from the
measured counting backend.

On the 2 August 2026 development checkpoint, the 100-observation Additive run
completed in 0.260 seconds and the RAM run in 0.258 seconds. Each compiled one
reference, executed 100 primary LPs, executed no secondary or certificate LP,
and certified all 100 score, target, peer, and dual claims. Additive's largest
LP, raw-account, published-account, peer-account, and dual-account residuals
were respectively $1.839\times10^{-14}$, $7.327\times10^{-15}$,
$1.335\times10^{-12}$, $7.327\times10^{-15}$, and
$1.364\times10^{-12}$. RAM's corresponding maxima were
$1.279\times10^{-14}$, $6.350\times10^{-15}$,
$6.350\times10^{-15}$, $6.350\times10^{-15}$, and
$1.110\times10^{-15}$. Timings are regression observations for that machine,
not hardware-independent guarantees.

Runtime certification does not broaden the literature claim. The classic
Additive certificate remains limited to the self-inclusive cross-sectional
VRS unit-weight programme. RAM remains the matched global-range/global-VRS
source profile described above. Configurable fixed weights, other RTS paths,
and panel/reference extensions are tested package behavior, not newly
attributed source formulations.

## Interpretation limits

- `AdditiveDEA` requires finite nonnegative inputs and outputs, and every
  observation must have a strictly positive aggregate input and aggregate
  desirable output. RAM is the translation-invariant exception described
  above.
- Undesirable outputs require an explicit environmental technology.
- Different positive weights can select different targets when the frontier
  has multiple Pareto projections.
- Fixed positive weights, CRS/NIRS/NDRS, and panel or non-global reference
  policies are configurable DEAPack extensions, not part of the classic
  VRS/unit-weight analytical certificate.
- A separately named literature leaf whose defining source cannot be
  obtained is deferred to the next version rather than inferred.
- Fractional measures such as SBM have different score properties and are
  documented as distinct specifications.

```{autosummary}
AdditiveDEA
WeightedAdditiveDEA
RangeAdjustedDEA
RAM
```
