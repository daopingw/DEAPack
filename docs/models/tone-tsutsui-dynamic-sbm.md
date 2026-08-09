# Tone--Tsutsui dynamic SBM

```{eval-rst}
.. currentmodule:: deapack
```

Tone and Tsutsui’s dynamic slacks-based measure evaluates one organization’s
complete multi-period operating trajectory while enforcing continuity of
assets, capabilities, inventories, burdens, and other accounts carried
between adjacent periods. Its canonical method ID is
`dynamic.sbm.tone_tsutsui_2010`.

```{admonition} Public implementation
:class: important

`ToneTsutsuiDynamicSBM` is the source-qualified public class.
`DynamicSBM` is its exact short alias. The built-in
`dynamic_carryover_portfolio` dataset contains four neutral,
four-period numerical example.
```

Defining and boundary sources:

- [Tone and Tsutsui (2010)](https://doi.org/10.1016/j.omega.2009.07.003);
- [Mariz, Almeida, and Aloise (2018)](https://doi.org/10.1111/itor.12468)
  for the dynamic-DEA family review; and
- [Afzalinejad and Abbasi (2019)](https://doi.org/10.3934/jimo.2018043)
  for a distinct improved dynamic-SBM proposal, which is not silently
  substituted for the Tone--Tsutsui equations.

## Complete public example

```python
from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    PeriodProductionSpec,
    load_dataset,
)

frame = load_dataset("dynamic_carryover_portfolio")
spec = DynamicSBMSpec(
    production=PeriodProductionSpec(
        inputs="input",
        outputs="output",
    ),
    carryovers=(
        CarryOverSpec("free_carryover", kind="free"),
    ),
)
data = DynamicData.from_frame(
    frame,
    spec=spec,
    dmu="dmu",
    period="period",
)

result = DynamicSBM(
    orientation="input",
    returns_to_scale="crs",
    score_variant="free_adjusted_post",
).fit(data)
```

`ToneTsutsuiDynamicSBM(...)` returns the same result because `DynamicSBM`
is an alias, not another estimator.

## Data contract

`DynamicData.from_frame` requires:

- one unique row for every `(DMU, period)` key;
- at least two ordered periods;
- the same complete period set for every DMU;
- one fixed assignment of variables to production and carry-over roles;
- finite numeric values; and
- an explicit `period_order` if the observed labels cannot be ordered safely.

The internal array is read-only and period-major with shape
`(n_periods, n_dmus, n_variables)`. One solver observation is a complete
trajectory, not one DataFrame row.

The public Tone--Tsutsui estimator additionally requires every observed
quantity to be strictly positive. The source normalizes slacks by evaluated
quantities; DEAPack does not silently translate zeros or negative values.

The current reference policy is one global cohort of complete trajectories.
The peer roster is identical in every period, while each period has its own
intensity vector. Contemporaneous, sequential, window, biennial, and
period-varying membership policies are rejected rather than reinterpreted as
dynamic reference sets.

## Period production accounts

For assessed trajectory $o$ in period $t$:

$$
x_{ot}=X_t\lambda^t+s_{ot}^{-},
\qquad
y_{ot}=Y_t\lambda^t-s_{ot}^{+}.
$$

Optional non-discretionary inputs and outputs satisfy equality balances and
do not enter the source slack averages.

The four source carry-over roles use:

$$
\begin{aligned}
z_{ot}^{good} &= Z_t^{good}\lambda^t-s_{ot}^{good},\\
z_{ot}^{bad} &= Z_t^{bad}\lambda^t+s_{ot}^{bad},\\
z_{ot}^{free} &= Z_t^{free}\lambda^t+s_{ot}^{free},\\
z_{ot}^{fixed} &= Z_t^{fixed}\lambda^t.
\end{aligned}
$$

Good, bad, input, and output slacks are nonnegative. A free-carry-over slack
is signed. Positive means that observed stock exceeds the selected benchmark
stock; negative means that it falls short.

Targets are consequently:

$$
\hat x=x-s^-,
\quad
\hat y=y+s^+,
\quad
\hat z^{good}=z^{good}+s^{good},
\quad
\hat z^{bad}=z^{bad}-s^{bad},
\quad
\hat z^{free}=z^{free}-s^{free}.
$$

Fixed external accounts and fixed carry-overs reproduce their observations.

## Exact adjacent-period continuity

For every carry-over role $\alpha$ and transition
$t=1,\ldots,T-1$:

$$
Z_t^\alpha\lambda^t
=
Z_t^\alpha\lambda^{t+1}.
$$

The same $Z_t^\alpha$ block appears on both sides. Replacing the right
side with $Z_{t+1}^\alpha\lambda^{t+1}$ defines a different transition
model and fails the published numerical oracle.

The terminal period retains its observed-to-target balance. There is no
outgoing continuity equation to an unobserved $T+1$, and the source preset
does not infer liquidation, zero terminal stock, depreciation, or salvage
value.

With `returns_to_scale="vrs"`, each period separately imposes

$$
\mathbf 1^\top\lambda^t=1.
$$

With `"crs"`, all period convexity rows are omitted. NIRS, NDRS, and mixed
period-level RTS are outside this source preset.

## Orientations and score reconstruction

Let $A_{ot}$ be the source input account after averaging normalized
ordinary-input and bad-carry-over excesses, and let $B_{ot}$ be the source
output expansion account after averaging ordinary-output and good-carry-over
shortfalls. Period weights are normalized to sum to $T$.

| `orientation` | Optimized base account | Reported efficiency |
|---|---|---|
| `"input"` | weighted mean of $A_{ot}$ | same arithmetic mean |
| `"output"` | weighted mean of $B_{ot}$ | reciprocal; equivalently the weighted harmonic mean of period efficiencies |
| `"non-oriented"` | ratio of weighted input and output accounts | $\sum_t w_tA_{ot}/\sum_t w_tB_{ot}$ |

The non-oriented linear-fractional programme is transformed with the
source-compatible Charnes--Cooper formulation. The result reports
`transform_scale` and reconstruction residuals.

An efficiency value of one applies to the accounts scored by the selected
orientation. It is not a radial contraction factor and does not certify that
every unscored slack is zero.

The result therefore keeps two statements separate.
`is_dynamic_sbm_efficient` tests whether the selected dynamic-SBM criterion
attains one. The generic nullable `is_efficient` is reported only for the
non-oriented account, where every reported input and output slack has been
checked; it remains missing for input- and output-oriented fits because their
unscored side has not received a strong-efficiency completion. A missing
generic status means “not certified,” not inefficient.

One-click plots and result briefs therefore use the reader-facing label
**Intertemporal Operating-Plan Performance**. A value of one is described as
no scored burden or shortfall in the selected positively weighted dynamic
accounts, not as an unconditional claim that every unscored operating
dimension is efficient.

## Relative weights

The constructor accepts label-to-weight mappings:

- `period_weights`;
- `input_weights`; and
- `output_weights`.

Every mapping must contain every corresponding label exactly once. Values
must be finite and strictly positive. DEAPack treats supplied values as
relative weights and source-normalizes them:

$$
\sum_t w_t=T,\qquad
\sum_i w_i^-=m,\qquad
\sum_r w_r^+=s.
$$

Good and bad carry-over items retain the source’s implicit unit weights.
`effective_weights` in result metadata records both the aligned values and
whether equal or user-relative weights were used. Period weights are
importance weights, not discount factors.

## A scored capacity-and-backlog account

`dynamic_capacity_backlog` is a theory-led two-organization teaching panel,
constructed for exact reconstruction rather than copied from an empirical
application. Both organizations use one unit of resource to provide one unit
of service in each period. Their inherited operating positions differ:

| Organization | Period | Resource | Service | Good capacity | Bad backlog |
|---|---:|---:|---:|---:|---:|
| Prepared | 1 | 1 | 1 | 2 | 1 |
| Strained | 1 | 1 | 1 | 1 | 2 |
| Prepared | 2 | 1 | 1 | 2 | 1 |
| Strained | 2 | 1 | 1 | 1 | 2 |

```python
from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    PeriodProductionSpec,
    dataset_info,
    load_dataset,
)

frame = load_dataset("dynamic_capacity_backlog")
roles = dataset_info("dynamic_capacity_backlog").roles
spec = DynamicSBMSpec(
    production=PeriodProductionSpec(
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    ),
    carryovers=(
        CarryOverSpec(roles["good_carryovers"][0], "good"),
        CarryOverSpec(roles["bad_carryovers"][0], "bad"),
    ),
)
data = DynamicData.from_frame(
    frame,
    spec=spec,
    dmu=roles["dmu"],
    period=roles["period"],
)
result = DynamicSBM(
    orientation="non-oriented",
    returns_to_scale="vrs",
).fit(data)
```

Prepared scores one. For Strained, ordinary resource and service slacks are
zero in both periods. The selected plan raises capacity from 1 to 2 and lowers
backlog from 2 to 1. The normalized good-capacity shortfall is therefore 1,
and the normalized bad-backlog excess is $1/2$. With one ordinary item and
one carry-over on each side, every period has

$$
A_t=1-\frac{0+1/2}{2}=0.75,
\qquad
B_t=1+\frac{0+1}{2}=1.5,
\qquad
\rho_t=\frac{A_t}{B_t}=0.5.
$$

Equal period weights give the same horizon efficiency, $0.5$, and the
adjacent-period continuity residual is zero. Both carry-over slacks explicitly
enter the reported score. The selected targets describe one feasible
benchmark operating plan; they are not certified as the unique management
prescription.

## Free-carry-over score variants

### `score_variant="base"`

The signed free-carry-over deviation affects feasibility and continuity but
is absent from the objective. `summary()["efficiency"]` and
`optimization_efficiency` report the same source base score.

### `score_variant="free_adjusted_post"`

The base LP is solved first. The selected signed free slack is then split
into excess and shortage and inserted into the source’s adjusted
side-specific accounts. The reported `efficiency` is the adjusted score;
`optimization_efficiency` retains the actual LP objective.

This adjustment is post-optimal. Slacks may be nonunique, so the adjusted
score and period allocation are marked
`solver_selected_not_uniqueness_certified`. The result specialization ID is
`dynamic.sbm.tone_tsutsui_2010.free_adjusted_post`.

The source’s alternative free-carry-over MIP optimizes mutually exclusive
one-sided deviations with binary decisions. It is not exposed by this LP
estimator. Passing an MIP-like variant raises an error rather than applying
a continuous relaxation or an arbitrary hard-coded big-M.

## Published numerical oracle

The bundled sample has one input, one output, one free carry-over, four
periods, eight DMUs, and CRS. The input-oriented
`free_adjusted_post` result reproduces the paper’s Table 2:

| DMU | Overall | T1 | T2 | T3 | T4 |
|---|---:|---:|---:|---:|---:|
| A | .706 | .544 | .833 | .750 | .694 |
| B | .746 | .683 | .917 | .750 | .635 |
| C | 1 | 1 | 1 | 1 | 1 |
| D | .846 | .842 | .875 | .833 | .833 |
| E | .567 | .625 | .642 | .558 | .444 |
| F | .917 | 1 | 1 | .833 | .833 |
| G | .749 | .767 | .782 | .672 | .775 |
| H | .851 | .850 | .778 | 1 | .778 |

Regression tests use absolute tolerance `5.1e-4` and zero relative tolerance
for printed values. Internal reconstruction, balance, fixed-account, and
continuity identities use tighter tolerances.

## Result-table contract

`fit()` returns the common `DEAResult`.

| Table | Dynamic-SBM content |
|---|---|
| `summary()` | reported and optimization efficiencies; independent `score`, `target`, `carryover`, `peer`, and `dual` validity/status pairs; criterion-specific efficiency flags; operating accounts; semantic, backend, and raw solver status; horizon bounds and reconstruction residuals |
| `components` | one horizon row and one row per period, including base/adjusted accounts, normalized period weight, and exact reconstruction contributions |
| `slacks` | period, semantic role, variable, slack, normalized slack, free excess/shortage, and whether it enters the optimized or reported score |
| `targets` | observed and target account, adjustment, role, and balance residual |
| `intensities` | assessed DMU, period, reference DMU, reference period, and positive intensity |
| `links` | carry-over kind, source/target periods, observed value, adjacent targets, continuity residual, and terminal-boundary status |
| `duals` | certified equality-row marginal values with their source constraint roles |
| `diagnostics` | one primary-solve record per trajectory, with semantic/backend/raw status; LP, canonical and original-unit trajectory certificates; claim-gate reasons; peer omitted mass; and reconstruction residuals |

Convenience filters include:

```python
result.components_for("E")
result.targets_for("E", period=3)
result.peers("E", period=3)
result.links_for("E")
```

Default period accounts, peers, slacks, and targets describe the solver’s
selected optimum. Only the overall objective value is asserted to be unique.

## Plot one certified carry-over path

The result-native trajectory view keeps the complete horizon intact:

```python
result.plot(
    kind="trajectory",
    dmu_id="E",
    variable="free_carryover",
)
```

It combines the selected carry-over's observed and outgoing target rows with
the `links` table's inherited target, so a next-period handoff is never guessed
from two adjacent target rows. A separate panel reports complete period
accounts only after their efficiencies and the native horizon result
reconstruct from the published input, output-expansion, and
effective-period-weight accounts. Those bars combine all scored ordinary
inputs, ordinary outputs, good carry-overs, and bad carry-overs; they do not
attribute performance to the carry-over selected for the upper panel. The
renderer validates each discretionary carry-over slack row's
`included_in_reported_score` flag against the source orientation, score variant,
and slack sign; a fixed carry-over is instead identified by the source model's
explicit no-slack feasibility account. It preserves the source terminal
boundary and states that the solver-selected trajectory is neither
uniqueness-certified nor prescriptive. `period=...` is rejected because an
isolated year is not the Dynamic-SBM unit of analysis.

## Metadata and audit fields

The result includes:

- `method_id="dynamic.sbm.tone_tsutsui_2010"`;
- the adjusted specialization ID when selected;
- the exact eleven-axis expanded method specification;
- period order and deterministic dynamic-spec fingerprint;
- fitted numerical and peer-reporting tolerances;
- source DOI and boundary policy;
- normalized weights and their sources;
- `compiled_reference_sets=1`;
- `primary_solves=primary_solver_calls=solver_calls=n_dmus`;
- `secondary_solves=additional_solver_calls=certificate_extra_solver_calls=0`;
- sparse matrix shape and nonzero count;
- unsupported source extensions; and
- the solver-neutral LP and dynamic-account postsolve release policy.

The matrix and variable scales are internal numerical conditioning choices.
Targets and slacks are returned in original user units. The Charnes--Cooper
scale must be finite and strictly positive; a small legitimate scale is not
discarded merely because it is below the general residual tolerance.

## Certification before result release

A dynamic efficiency result is an account of the complete trajectory, not
just a number returned by an optimizer. DEAPack therefore requires two
independent certificates before publishing either the headline score or its
period-by-period operating plan. The backend label `optimal` alone is not a
release decision.

The shared solver-neutral LP certificate recomputes primal rows, variable
bounds, and the reported objective, then checks row and bound marginals,
stationarity, sign conditions, complementarity, and strong duality. Missing,
nonfinite, or malformed row marginals fail the certificate. Bound marginals
are checked whenever supplied and are required when finite, fixed, or upper
bounds--including fixed transformation-scale variables--cannot be certified
through the standard nonnegative-cone fallback.

The dynamic-SBM certificate then recovers the operating accounts from the
solver coordinates. It checks the transformation scale; base and, when
requested, free-carry-over-adjusted accounts; orientation-specific score
identities; horizon and period reconstruction; production balances; adjacent
carry-over continuity; and fixed-account reproduction. This makes the
published period contributions, targets, peers, and carry-over plan one
jointly feasible managerial narrative rather than unrelated postprocessing
tables. Balance, continuity, and fixed-account checks are also reconstructed
in original user units and normalized by the relevant economic quantity
scale, so an internally scaled LP is not the only evidence released.

Primary failure is atomic and fail-closed. If a backend reports `optimal` but
either required primary certificate rejects the trajectory, semantic
`solver_status` is `numerical_error`; `backend_solver_status` and
`raw_solver_status` retain the backend claim. `score_valid=False`,
`score_status` identifies the failure class, and canonical numerical scores are missing.
`components`, `slacks`, `targets`, `intensities`, `duals`, and `links` are all
withheld. The diagnostic row retains the failed gate, reason, and residuals;
`metadata["postsolve_certificate"]` states the same release contract.

Once the primary score is certified, target, carry-over, thresholded-peer,
and dual accounts are released independently. A reporting threshold is
applied only to the public peer rows; DEAPack then reconstructs period targets,
VRS balances, and adjacent carry-over continuity from those shortened rows in
both canonical and original units. If that sparse peer display no longer
supports the operating plan, `peer_valid=False` and `intensities` is withheld,
while the certified score, targets, and carry-over ledger remain available.
Diagnostics report total and maximum-period omitted intensity. `dual_valid`
certifies a complete finite row-marginal account in the transformed solver
coordinates; it deliberately does not claim an original-unit shadow-price
interpretation that has not been derived.

## Failure behavior

Construction or fitting rejects:

- an unknown orientation or unsupported RTS;
- a non-mapping weight argument;
- a weight mapping with missing or extra labels;
- nonpositive or nonfinite weights;
- nonpositive data;
- an incomplete or duplicate trajectory panel;
- fewer than two periods;
- overlapping or duplicate variable roles;
- `free_adjusted_post` without a free carry-over;
- an unsupported boundary policy; and
- simultaneous `solver` and `solver_options`.

Solver failure or either postsolve-certificate failure produces a summary row
with undefined numerical fields and a diagnostic record; it does not
fabricate an efficiency value or expose a partial trajectory plan.

## Sparse implementation and performance

One immutable CSC equality template is compiled for the complete trajectory
cohort. It contains period-specific intensity blocks, period balances,
adjacent-period continuity rows, period VRS rows where selected, and the
non-oriented normalization row where required. For each assessed DMU, only
the mutable evaluated-account coefficients and objective/normalization values
are updated.

The estimator therefore compiles once and runs one primary LP per
trajectory. It does not pivot pandas data or construct a dense
DMU-period Cartesian matrix inside the solve loop.

Run the deterministic benchmark with:

```bash
python benchmarks/benchmark_dynamic_sbm.py --n-dmus 100 --periods 4
python benchmarks/benchmark_dynamic_sbm.py \
    --n-dmus 100 --periods 4 10 --orientation all
python benchmarks/benchmark_dynamic_sbm.py \
    --n-dmus 1000 --periods 4
```

The benchmark asserts the one-primary-solve-per-trajectory and zero-extra-
certificate-solve contract, all five claim gates, canonical and original-unit
reconstruction, matrix shape, nonzeros, density, and elapsed time.

## Declared source boundary

The public preset does not currently implement:

- a pre-sample initial carry-over condition;
- shared-resource output/good-carry-over accounting;
- the free-carry-over MIP;
- decay, loss, depreciation, terminal value, or lags longer than one;
- missing or unbalanced trajectories;
- alternate-optimum ranges for period accounts;
- the Afzalinejad--Abbasi improved DSBM; or
- process structure within periods; use the separate
  {doc}`tone-tsutsui-dynamic-network-sbm` model when within-period links and
  cross-period carry-overs must be feasible together.

These are separate extensions or methods. They will receive distinct
identities after their equations and numerical oracles are audited.
