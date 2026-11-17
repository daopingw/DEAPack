# Malmquist productivity index

```{eval-rst}
.. currentmodule:: deapack
```

The Malmquist index measures productivity change between periods and separates
it into efficiency change and technical change. Start with `FGNZMalmquist`
for the classical output-oriented, constant-returns-to-scale specification
of Färe, Grosskopf, Norris, and Zhang.

## Fit the classical model

The example uses a panel with two inputs and one desirable output:

```python
from deapack import DEAData, FGNZMalmquist, load_dataset

frame = load_dataset("productivity_panel")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    period="period",
    inputs=["capital", "labor"],
    outputs="output",
)
result = FGNZMalmquist().fit(data)
result.summary()
```

Read `productivity_change`, `efficiency_change`, and `technical_change` in the
summary. Each uses one as the no-change reference: values above one indicate
improvement, and values below one indicate decline. The two components
multiply to give the productivity index; they are not additive percentages.
Check `score_valid` before interpreting a transition. See
{doc}`../user-guide/results` if a result is missing or invalid.

The preset fixes output orientation and CRS, so these choices do not need to
be repeated in the code. A different reference technology or decomposition
answers a different question.

## Choosing a formulation

| Estimator | Use it for |
|---|---|
| `FGNZMalmquist` | Classical CRS index with $M=EC\times TC$ |
| `FGNZEnhancedMalmquist` | Further separate efficiency change into pure-efficiency and scale components |
| `RayDesliMalmquist` | Use Ray--Desli's distinct CRS/VRS decomposition |
| `MalmquistDEA` | Set orientation and returns to scale explicitly for sensitivity analysis |

All four match adjacent-period observations by identifier. The classical
and configurable estimators use four distances under one declared technology.
Enhanced FGNZ adds two own-period VRS distances; Ray--Desli adds four VRS
distances, including cross-period comparisons. Their formulas and supported
data domains are explained below.

## Four distance roles

Let $z^\sigma=(x^\sigma,y^\sigma)$ denote a plan observed in period
$\sigma$, and let $d^\tau(z^\sigma)$ denote its Farrell efficiency-form
distance from the production opportunities represented by period $\tau$.
The preset uses the output-oriented convention $d=1/\phi$. The implementation
evaluates:

| Result field | Evaluated observation | Reference technology |
|---|---|---|
| `distance_base_on_base` | $z^t$ | $T^t$ |
| `distance_comparison_on_base` | $z^{t+1}$ | $T^t$ |
| `distance_base_on_comparison` | $z^t$ | $T^{t+1}$ |
| `distance_comparison_on_comparison` | $z^{t+1}$ | $T^{t+1}$ |

The diagonal values measure operating performance relative to contemporaneous
best practice. The off-diagonal values reappraise each operating plan using
the other period's represented opportunities. A cross-period value can exceed
one because the evaluated observation need not belong to the other period's
technology.

## Index and two-component account

$$
M^{t,t+1}=\left[
\frac{d^t(z^{t+1})}{d^t(z^t)}
\frac{d^{t+1}(z^{t+1})}{d^{t+1}(z^t)}
\right]^{1/2}.
$$

The FGNZ core defines

$$
EC^{t,t+1}=\frac{d^{t+1}(z^{t+1})}{d^t(z^t)},
$$

$$
TC^{t,t+1}=\left[
\frac{d^t(z^{t+1})}{d^{t+1}(z^{t+1})}
\frac{d^t(z^t)}{d^{t+1}(z^t)}
\right]^{1/2},
\qquad M=EC\times TC.
$$

`efficiency_change` records whether the producer's output shortfall relative
to its own-period CRS benchmark became smaller or larger. `technical_change`
is the conventional field name for the change in output opportunities
represented by the two period technologies. Neither component identifies a
cause: changes in practices, investment, regulation, sample composition, and
measurement can all affect the account.

All three fields use the package convention: values above one indicate
measured improvement, one indicates no change, and values below one indicate
decline. `score` contains $M$. `efficiency` and `is_efficient` are deliberately
missing because productivity change is not a bounded efficiency level.
`decomposition_residual` checks $M-EC\times TC$ before display rounding.

The {doc}`global-malmquist` example uses the current synthetic
`multiperiod_trajectory_contrast` panel to compare period-specific and pooled
references. For `trajectory_02` from period 1 to 2 under output orientation
and CRS, both methods give productivity change $2$, efficiency change $1.6$,
and an opportunity-change component of $1.25$. This equality is specific to
that one-input, one-output example, not an equivalence of the two methods.
Their reference technologies differ and need not give the same account on
other data.

## Core four-distance release contract

For `MalmquistProductivityIndex` and `MalmquistDEA`, an optimal backend
label is necessary but not sufficient for publication. Every one of the four
role-specific radial programmes must pass
the shared solver-neutral primal, bound, objective, KKT, complementarity, and
strong-duality certificate. The implementation then reconstructs each radial
production account from both the raw solver vector and the values eligible for
publication. The transition is released only when the four positive distances
also reproduce the complete raw and published $M$, $EC$, $TC$, reference-change,
and $M=EC\times TC$ account.

The summary exposes the resulting gates directly:

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

`score_valid=False` withholds the four published distances, headline,
components, residual, and peer rows for that transition while retaining the
raw role diagnostics. Failure is transition-scoped, so another organization's
transition may still be valid. `peer_valid` is the narrower disclosure gate:
if `peer_tolerance` removes enough intensity mass to break a role account, the
certified score and components remain available but peer rows are withheld.

`result.diagnostics` preserves `backend_solver_status` and reports separate
`lp_postsolve_certified`, `raw_economic_postsolve_certified`,
`published_output_account_certified`, and
`published_peer_account_certified` fields with their residuals. Metadata
reports the deduplicated `solver_calls`, compiled reference sets, and
`additional_solver_calls=0`; all certificates reuse the original four-task
responses. After those checks finish, the task cache retains only material
peer positions and scalar solver/certificate evidence; reference-length
primal and marginal vectors are discarded.

```{important}
This reliability contract is stated here for the classic four-distance core.
It does not promote an FGNZ preset, Ray--Desli, biennial, or another named
variant to the same release statement, and it does not extend this method's
source claim to those separate task graphs.
```

## Source-qualified enhanced FGNZ method

Use the enhanced method when the study needs to divide CRS efficiency change
between pure-efficiency change and scale-efficiency change:

```python
from deapack import FGNZEnhancedMalmquist

enhanced = FGNZEnhancedMalmquist().fit(data)
enhanced.summary()
```

Let $d_C$ and $d_V$ denote output-oriented CRS and VRS distances. The four
CRS tasks are the same roles used by the FGNZ core. The method adds only the
two diagonal VRS tasks $d_V^t(z^t)$ and
$d_V^{t+1}(z^{t+1})$. It does not solve VRS cross-period tasks.

The own-period VRS distances define

$$
PEFFCH=\frac{d_V^{t+1}(z^{t+1})}{d_V^t(z^t)}.
$$

With
$SE^\tau(z^\sigma)=d_C^\tau(z^\sigma)/d_V^\tau(z^\sigma)$, the FGNZ
scale factor is

$$
SCH=\frac{SE^{t+1}(z^{t+1})}{SE^t(z^t)}.
$$

The method checks both nested identities:

$$
EC=PEFFCH\times SCH,
\qquad
M=TECHCH_C\times PEFFCH\times SCH.
$$

Its main fields are:

| Field | Meaning |
|---|---|
| `score`, `productivity_change` | CRS geometric Malmquist index $M$ |
| `efficiency_change` | CRS own-period operating-performance factor $EC$ |
| `technical_change` | CRS opportunity-change factor $TECHCH_C$ |
| `pure_efficiency_change` | own-period VRS factor $PEFFCH$ |
| `fgnz_scale_change` | own-period scale-efficiency ratio $SCH$ |
| `decomposition_residual` | $M-EC\,TECHCH_C$ |
| `efficiency_decomposition_residual` | $EC-PEFFCH\,SCH$ |
| `fgnz_enhanced_decomposition_residual` | $M-TECHCH_C\,PEFFCH\,SCH$ |
| `crs_distance_<role>` | one of four CRS primitive distances |
| `vrs_distance_base_on_base` | base-period own VRS distance |
| `vrs_distance_comparison_on_comparison` | comparison-period own VRS distance |
| `scale_efficiency_<own_role>` | corresponding own-period $d_C/d_V$ ratio |
| `decomposition_defined`, `decomposition_status` | availability of the complete enhanced account |

The method accepts multiple inputs and multiple desirable outputs. Quantities
must be finite and nonnegative, with a positive input aggregate and output
aggregate in every row. Undesirable outputs require an environmental method.
`unbalanced="drop"` is the default and records unmatched identifiers;
`unbalanced="raise"` rejects them.

Under the ordinary self-including VRS technology, each own-period task has
the evaluated observation as a feasible witness. If a custom solver still
fails one, DEAPack preserves the valid CRS $M$, $EC$, $TECHCH_C$, and core
residual, but leaves the enhanced fields missing and reports
`decomposition_status="vrs_own_<status>"`. This is fail-closed software
behavior, not the source-backed cross-VRS partial account described below for
Ray--Desli.

## Source-qualified Ray--Desli method

Use the Ray--Desli method when the empirical claim is the output-oriented VRS
allocation defined by Ray and Desli (1997), not merely a Malmquist calculation
run with `returns_to_scale="vrs"`:

```python
from deapack import RayDesliMalmquist

ray_desli = RayDesliMalmquist().fit(data)
ray_desli.summary()
```

The method has its own source identity because its CRS--VRS construction,
result fields, and partial-failure behavior differ from the configurable
four-distance calculator.

`RayDesliMalmquist` is the exact alias of
`RayDesliMalmquistProductivityIndex`. The method fixes output orientation and
requires a balanced adjacent-period panel, strictly positive quantities, one
or more input variables, and exactly one desirable output. Multiple outputs,
undesirable outputs, zero or negative quantities, input orientation, and
unmatched adjacent-period identifiers are outside its frozen evidence domain.

### Eight distance tasks and exact component formulas

Let $d_C^\tau(z^\sigma)$ and $d_V^\tau(z^\sigma)$ denote
reciprocal-expansion output distances for a target plan from period $\sigma$
against the period-$\tau$ CRS and VRS technologies. The four role suffixes
are shared across the two systems:

| Role suffix | Target observation | Reference technology |
|---|---|---|
| `base_on_base` | $z^t$ | period $t$ |
| `comparison_on_base` | $z^{t+1}$ | period $t$ |
| `base_on_comparison` | $z^t$ | period $t+1$ |
| `comparison_on_comparison` | $z^{t+1}$ | period $t+1$ |

For every suffix, the summary retains `crs_distance_<role>`,
`vrs_distance_<role>`, and `scale_efficiency_<role>`. The last field is the
corresponding source ratio $d_C/d_V$; the four ratios are not collapsed into
one generic scale-change field.

The CRS distances define the same geometric Malmquist index as the FGNZ
core:

$$
M=\left[
\frac{d_C^t(z^{t+1})}{d_C^t(z^t)}
\frac{d_C^{t+1}(z^{t+1})}{d_C^{t+1}(z^t)}
\right]^{1/2}.
$$

The VRS own-period distances define pure-efficiency change,

$$
PEFFCH=\frac{d_V^{t+1}(z^{t+1})}{d_V^t(z^t)},
$$

while all four VRS distances define Ray--Desli technical change,

$$
TECHCH_V=\left[
\frac{d_V^t(z^t)}{d_V^{t+1}(z^t)}
\frac{d_V^t(z^{t+1})}{d_V^{t+1}(z^{t+1})}
\right]^{1/2}.
$$

With
$SE^\tau(z^\sigma)=d_C^\tau(z^\sigma)/d_V^\tau(z^\sigma)$, the
source-native scale factor is

$$
SCH_V=\left[
\frac{SE^t(z^{t+1})}{SE^t(z^t)}
\frac{SE^{t+1}(z^{t+1})}{SE^{t+1}(z^t)}
\right]^{1/2}.
$$

The required reconstruction is

$$
M=PEFFCH\times TECHCH_V\times SCH_V.
$$

This `SCH_V` is a geometric cross-period account. It is not the enhanced
FGNZ ratio of two own-period scale efficiencies, and neither value should be
stored in a generic `scale_change` field.

### Result contract and example

The principal summary fields are:

| Field | Meaning |
|---|---|
| `score`, `productivity_change` | CRS geometric Malmquist index $M$ |
| `pure_efficiency_change` | own-period VRS factor $PEFFCH$ |
| `vrs_technical_change` | VRS opportunity-change factor $TECHCH_V$ |
| `ray_desli_scale_change` | Ray--Desli cross-period scale factor $SCH_V$ |
| `ray_desli_decomposition_residual` | $M-PEFFCH\,TECHCH_V\,SCH_V$ before display rounding |
| `crs_distance_<role>` | one of the four CRS primitive distances |
| `vrs_distance_<role>` | one of the four VRS primitive distances |
| `scale_efficiency_<role>` | the matched $d_C/d_V$ ratio for that role |
| `decomposition_defined` | boolean availability flag for the complete three-factor account |
| `decomposition_status` | whether the complete three-factor account is defined |

For D from 2020 to 2021:

```python
ray_desli.summary().query(
    "dmu_id == 'D' and comparison_period == 2021"
)[[
    "productivity_change",
    "pure_efficiency_change",
    "vrs_technical_change",
    "ray_desli_scale_change",
    "ray_desli_decomposition_residual",
    "decomposition_defined",
    "decomposition_status",
]]
```

The result is approximately $M=1.130664$, $PEFFCH=1.033588$,
$TECHCH_V=1.113763$, and $SCH_V=0.982185$, with a zero reconstruction
residual to numerical tolerance. The factors multiply; their percentage
departures from one are not additive shares. They describe a
benchmark-conditional allocation and do not identify the effects of
management, innovation, investment, or resizing.

### Diagnostics and partial VRS infeasibility

Diagnostics identify both the distance role and the returns-to-scale system:

```python
ray_desli.diagnostics.query(
    "dmu_id == 'D' and comparison_period == 2021"
)[[
    "distance_role",
    "returns_to_scale",
    "evaluated_period",
    "technology_period",
    "farrell_efficiency",
    "solver_status",
]]
```

A cross-period VRS program may be infeasible even when all four CRS programs
and both own-period VRS programs are valid. In that source-defined partial
case, `productivity_change` and `pure_efficiency_change` remain available.
`vrs_technical_change`, `ray_desli_scale_change`, and
`ray_desli_decomposition_residual` are missing, and `decomposition_status`
is `"vrs_cross_infeasible"` while
`decomposition_defined` is false. DEAPack does not impute a VRS distance,
substitute a CRS component, change the reference technology, or infer the
missing factor as a residual.

In that row, `solver_status` remains `"optimal"` because it records the
availability of the CRS headline index; `decomposition_status` separately
records whether all VRS tasks needed by the three-factor allocation succeeded.

This behavior follows the reporting semantics of Ray and Desli's Table 1,
which retains Ireland's Malmquist and pure-efficiency values while marking
the VRS-dependent technical and scale entries infeasible. DEAPack's tests use
independently compiled synthetic panels; they do not reproduce the paper's
Penn World Table 5.6 application.

## Configurable sensitivity analysis

The generic class exposes the same four-distance operator:

```python
from deapack import MalmquistProductivityIndex

sensitivity = MalmquistProductivityIndex(
    orientation="input",
    returns_to_scale="vrs",
).fit(data)
```

Input orientation uses $d=\theta$. Under CRS, input- and output-oriented
radial indexes coincide theoretically. Non-CRS runs can be informative
sensitivity checks, but their two generic component fields are not a complete
scale decomposition and do not receive the FGNZ preset identity.

The enhanced FGNZ identity
$M=PEFFCH\times SCH\times TECHCH$, the Ray--Desli VRS account, and Balk's
scale-and-mix account are non-equivalent decompositions. Enhanced FGNZ and
Ray--Desli each have their own public method. Neither can be reconstructed by
relabeling a generic VRS result or by treating a residual as a source-defined
component. Balk remains deferred until its own evidence gate closes.

## Pairing, reference membership, and failures

Transitions are matched by `dmu_id`, never by row position. Adjacent means
adjacent in `DEAData.period_order`, so labels need not be consecutive integers.
The first period has no predecessor and has no summary row.

For the generic, FGNZ-core, and enhanced-FGNZ estimators,
`unbalanced="drop"` keeps the identifier intersection for each adjacent pair
and records unmatched identifiers in metadata; `unbalanced="raise"` rejects
the first mismatch. Reference technologies still use every eligible
observation in their respective periods, including a DMU that is unmatched
for a particular transition. The source-qualified Ray--Desli method instead
requires a balanced adjacent panel and rejects a mismatch before forming its
eight-task account.

The implementation never substitutes a one-sided ratio when one of the four
distance programs is infeasible. The transition remains missing, while
`result.diagnostics` retains the failing `distance_role`, evaluated period,
technology period, and solver status.

## Scope and evidence

The FGNZ core and enhanced methods accept nonnegative inputs and desirable
outputs with positive per-observation input and output aggregates.
Undesirable outputs require the environmental Malmquist--Luenberger analysis.
Global and biennial Malmquist indexes use different reference technologies
and are separate estimators.

The core preset is checked against exact synthetic four-distance cases that
separate operating-performance change from represented-opportunity change.
That verification does not claim reproduction of the original FGNZ
cross-country application; the exact historical panel vintage and
preprocessing protocol are not frozen in this release. Ray--Desli is checked
against an independent eight-distance compiler on its strictly positive
one-output domain, including a source-backed partial-infeasibility case. That
certificate does not reproduce the Penn World Table 5.6 application. Enhanced
FGNZ is checked against a separate production-free six-task compiler with a
non-unit pure-efficiency factor and two exact reconstruction identities; it
does not reproduce the original OECD/PWT5 application.

## Implementation identities

The short names used in the examples are exact aliases of the full class
names listed below; they do not select different estimators. For automated
provenance checks, identities remain available in each result's `metadata`:

| Example result | `method_id` | Preset or parent identity |
|---|---|---|
| `result` | `productivity.malmquist.adjacent_geometric` | `preset_id="productivity.malmquist.decomposition.fgnz_core"` |
| `enhanced` | `productivity.malmquist.decomposition.fgnz_pure_scale_extension` | `parent_operator_id="productivity.malmquist.adjacent_geometric"` |
| `ray_desli` | `productivity.malmquist.decomposition.ray_desli` | `parent_operator_id="productivity.malmquist.adjacent_geometric"` |

The enhanced and Ray--Desli methods have independent method identities rather
than a `preset_id`. Ray--Desli metadata records CRS for its headline index and
VRS for its auxiliary decomposition.

```{autosummary}
FGNZMalmquistProductivityIndex
FGNZMalmquist
FGNZEnhancedMalmquistProductivityIndex
FGNZEnhancedMalmquist
RayDesliMalmquistProductivityIndex
RayDesliMalmquist
MalmquistProductivityIndex
MalmquistDEA
```
