# Environmental directional distance

```{eval-rst}
.. currentmodule:: deapack
```

Environmental directional distance models evaluate a declared operating
programme:

$$
(x_o-\beta g^x,\ y_o+\beta g^y,\ b_o-\beta g^b).
$$

Positive $g^x$ represents resource saving, positive $g^y$ service expansion,
and positive $g^b$ undesirable-output reduction. The direction states the
counterfactual; the technology states which counterfactuals are attainable.
Those two choices are recorded separately.

## Choose the production account first

DEAPack exposes distinct public paths because weak disposability is an
economic axiom, not one universal linear equation.

| Public class | Maintained production account | Scale identity |
|---|---|---|
| `ChungFareGrosskopfDDF` | Chung--Färe--Grosskopf output DDF with observed good/bad directions | CRS, source preset |
| `ZhouAngWangNonCHPEnergyCarbonDEA` | Zhou--Ang--Wang component-specific fuel, electricity, and carbon accounts for non-CHP systems | CRS, three source presets |
| `CommonFactorWeakDisposalDDF` | common-factor weak disposal with a user-declared DDF direction | CRS, fixed |
| `ActivitySpecificWeakDisposalDDF` | Kuosmanen activity-specific weak disposal with a user-declared DDF direction | VRS, fixed |
| `KuosmanenWeakDisposalDDF` | source-name alias of `ActivitySpecificWeakDisposalDDF` | VRS, fixed |
| `EnvironmentalDirectionalDistanceDEA(disposability="strong")` | strong bad-output disposal | declared RTS |
| `EnvironmentalDirectionalDistanceDEA(disposability="weak")` | legacy bad-output equality only | declared RTS; deprecated spelling |

The last row is retained temporarily so existing projects reproduce their
old numbers. It emits `FutureWarning`, reports
`bad_output_disposability="not_identified"`, and records
`compatibility_alias="weak"`. It must not be cited as either of the two named
weak-disposal technologies.

The Zhou--Ang--Wang method is documented separately because it replaces one
common directional step with account-specific fuel, electricity, and carbon
components and reports named EPI, CPI, or ECPI transformations. See
{doc}`zhou-ang-wang-non-chp`.

## Common-factor weak disposal

The CRS common-factor empirical technology uses

$$
X\lambda\le x,\qquad
Y\lambda\ge y,\qquad
B\lambda=b,\qquad
\lambda\ge0.
$$

Under CRS, scaling $\lambda$ by one common factor scales the represented good
and bad outputs together while preserving input feasibility. This is the
reason the equality identifies the common-factor weak-disposal technology in
this domain. Adding $\mathbf 1^\top\lambda=1$ would invalidate that argument;
`CommonFactorWeakDisposalDDF` therefore has no `returns_to_scale` parameter.

`ChungFareGrosskopfDDF` additionally fixes the source direction
$(g^x,g^y,g^b)=(0,y_o,b_o)`. It asks how far desirable outputs can rise while
undesirable outputs fall in observed proportions, holding inputs fixed.

The fixed-input choice has a documented source-edition boundary. The 1997
journal article defines the output set $P(x)$ and uses the signed direction
$g=(y,-b)$, but its printed equation (3.14) places $(1-\beta)x$ in the input
restriction. Chung and Färe's [1995 working-paper equation
(2.14)](https://econwpa.ub.uni-muenchen.de/econ-wp/mic/papers/9511/9511002.pdf)
instead prints $X\lambda\leq x$, consistent with the output-set definition
and the stated output direction. DEAPack freezes that fixed-resource
programme. This records an edition inconsistency; no evidence of a formal
publisher erratum has been located.

`environmental_panel` is deterministic synthetic teaching data generated for
DEAPack. It is not the confidential application data in the 1997 article,
and results computed from it are not a published numerical reproduction. A
published CFG numerical reproduction is unavailable and deferred to a later
version.

```python
from deapack import ChungFareGrosskopfDDF, DEAData, load_dataset

frame = load_dataset("environmental_panel")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    period="period",
    inputs=["energy", "labor"],
    outputs="electricity",
    bad_outputs="co2",
)

cfg = ChungFareGrosskopfDDF(reference="contemporaneous").fit(data)
```

Null jointness is a separate restriction. The source preset requests it and
validates that an observed activity with positive desirable output does not
have zero total bad output.

### Exact reference-set audit

Consider two operating plans in a DEAPack analytical teaching fixture. These
numbers are not a numerical example published in the source:

| Organization | Resource $x$ | Service $y$ | Residual $b$ |
|---|---:|---:|---:|
| Old | 1 | 1 | 2 |
| New | 1 | 2 | 1 |

With both plans in the pooled CRS technology, their exact CFG distances are
$(3/5,0)$. Pooled evidence shows that Old can jointly increase service and
reduce its residual, while New already exhausts the declared opportunity.
When New is evaluated against Old alone, its distance is $-3/5$. The selected
older evidence can reproduce New only by giving back service and accepting
more residual; the value is not a negative efficiency or a data error.
DEAPack retains the native negative distance and leaves `efficiency` and the
efficiency flags missing.

```{figure} ../../book/_static/figures/cfg-cross-period-reference.svg
:name: fig-docs-cfg-cross-period-reference
:alt: New provides more desirable service with less undesirable residual than Old and lies outside the old fixed-input technology; a dashed reverse CFG comparison reaches the old-reference target of four fifths service and eight fifths residual with beta equal to minus three fifths
:width: 96%

New lies outside the old fixed-input production possibilities. The negative
distance records the reverse movement needed to reach an old-reference
target; it is a signed reference gap, not a better-or-worse efficiency
ranking.
```

Changing `reference` changes an individual distance task; it does not create
a temporal productivity operator. The CFG Malmquist--Luenberger index
combines four source-qualified period and cross-period distance tasks. Oh's
global Malmquist--Luenberger index is a different operator over a fixed
full-sample technology. In particular,
`ChungFareGrosskopfDDF(reference="global")` is not GML.

## Comparable operating populations

An environmental benchmark is credible only when its operating comparison is
credible. `PeerEligibility` can therefore be supplied to the generic
environmental DDF, the common-factor model, and the CFG preset. It declares
which observed operations may serve each evaluated operation; it is combined
with `reference` by intersection. Thus a contemporaneous rule and a
same-regulatory-regime rule mean “operations from the same period that also
satisfy that comparability rule,” not two competing frontiers.

The restriction changes evidence, not the production account. A generic strong
disposal DDF remains strong disposal. A common-factor or CFG fit still requires
good and bad outputs to be represented under one common retained activity
factor, and an external CFG comparison may still produce a certified negative
distance. The result reports `base_reference_size`, `reference_size`,
`self_in_reference`, and compact policy provenance so the reported operating
gap can be read against the population that was actually admitted.

This public comparison-rights contract deliberately stops there. It is not
available on activity-specific weak disposal, by-production, material-balance,
or Zhou--Ang--Wang routes, whose distinct production accounts require their
own evidence and audit. See {doc}`../user-guide/reference-sets` for the
declared-policy schema and reporting checklist.

## Activity-specific weak disposal

Kuosmanen's VRS construction permits reference activities to carry different
weak-disposal factors. In the shared notation its exact linearization uses
nonnegative $\mu$ and $\eta$:

$$
\begin{aligned}
X(\mu+\eta)+\beta g^x&\le x_o,\\
-Y\mu+\beta g^y&\le-y_o,\\
B\mu+\beta g^b&=b_o,\\
\mathbf 1^\top(\mu+\eta)&=1.
\end{aligned}
$$

For a reference activity with positive total intensity,

$$
r_j=\frac{\mu_j}{\mu_j+\eta_j}
$$

is its retained activity proportion. The handbook notation uses $r_j$ to avoid
confusing this activity-specific proportion with the Farrell input score
$\theta$. For backward-compatible table schemas, results still expose
`retention_rate_theta` and `curtailment_share_one_minus_theta`, alongside
`active_mu`, `abatement_tau`, and `total_intensity`. The stable name
`abatement_tau` stores
the quantity denoted by $\eta$ in the mathematical representation; `tau` in
that field name is not a time index. The complement is not an
observed monetary cost, treatment-energy requirement, engineering abatement
process, or causal estimate.

```python
from deapack import ActivitySpecificWeakDisposalDDF

activity_specific = ActivitySpecificWeakDisposalDDF(
    reference="contemporaneous",
    null_jointness=False,
).fit(data)
```

This class is deliberately VRS. Dropping its convexity equation makes
$\tau$ redundant and reduces the technology to the CRS equality
construction; that reduction is not a separate “Kuosmanen CRS” method.

The repository's claim-scoped analytical certificate checks the VRS
activity-specific programme independently of the production compiler. On an
exact three-activity fixture it supplies a primal--dual proof of
$\beta=1/42$, assembles every dense phase-one task directly from the equations,
and verifies all public distances plus the directional target. This is a
synthetic mathematical certificate, not a reproduction of a published
empirical table. It is not inherited by common-factor CRS, strong or generalized
disposal, alternative directions, temporal references, or inference. The shared
common-factor and strong-disposal kernel has its own separately bounded core-policy
certificate described below. See
`specs/oracles/activity-specific-weak-disposal-analytical.md`.

## Strong disposal

The generic environmental kernel uses

$$
B\lambda\le b_o-\beta g^b
$$

when `disposability="strong"`. A second phase may then report additional
bad-output slack. This production account treats residual reduction as
available without an explicit modeled sacrifice. It can be appropriate for a
residual whose independent adjustment is represented by the comparison data,
a historical replication, or a sensitivity analysis. “Costly” and “costless”
here describe restrictions in the modeled opportunity set, not observed money,
engineering effort, or causal regulatory burden.

Strong disposal is incompatible with the package's null-jointness restriction
and the conflicting combination is rejected.

The separate core-policy certificate assembles the generic environmental DDF
programmes without importing DEAPack's production compiler. It checks a non-CFG
direction on the CRS common-factor technology, all four supported strong-disposal
RTS restrictions, and an exact second-phase target with one unit of residual slack.
It is synthetic analytical and cross-implementation evidence, not a source-data
reproduction, and it does not certify the deprecated equality-plus-general-RTS
compatibility path. See
`specs/oracles/environmental-ddf-core-disposal-policies-analytical.md`.

## Results and efficiency flags

A certified primary programme reports the native distance $\beta$, declared
directions, solver diagnostics, and complete technology identity. Targets and
slacks are released only when the optional completion programme was requested
and independently certified. Reference activities are reported only when the
published, thresholded peer account also reconstructs the certified programme.
Consequently, `peer_tolerance` may shorten or empty the displayed peer table,
but it cannot invalidate an otherwise certified score, target, or slack table.
The summary fields `peer_valid` and `peer_status` make that distinction explicit.

`efficiency=1/(1+beta)` is a bounded display transform, not the native DDF
measure. It is released only when $\beta\geq0$ **and** the assessed plan is
certified inside the selected reference technology. Self inclusion supplies
that certificate directly. Under strong disposal, a certified nonnegative
directional plan also implies membership by monotonicity. Under the
equality-based common-factor account with an external reference, a positive
directional target does not necessarily prove membership of the unchanged
assessed plan; DEAPack therefore solves a beta-zero feasibility programme before
publishing the transform or an efficiency classification. The summary records
`self_in_reference`, `is_within_reference_technology`, `membership_status`, and
`efficiency_denominator_valid`.

The same distinction applies to the equality-based VRS activity-specific
technology. For a certified external appraisal with nonnegative $\beta$ and no
structural self inclusion, `ActivitySpecificWeakDisposalDDF` reuses the
row-scaled phase-one balances in a feasibility programme with $\beta=0$. A
certified feasible programme establishes membership; infeasibility establishes
non-membership; and a numerical result that fails its LP and original-quantity
accounts leaves membership unknown. A certified negative $\beta$ establishes
non-membership without that extra call. In every case the native distance and
any independently certified directional target retain their own validity, while
the bounded display transform and efficiency flags remain unavailable unless
membership is certified.

When an external or cross-period reference gives $\beta<0$, the distance means
that the selected technology cannot reproduce the assessed clean-output plan
without reversing part of the declared programme. The display efficiency is
then missing rather than being presented as an efficiency above one.

When `compute_slacks=True`, the second phase maximizes a row-scaled slack
sum. The physical `slack` and `target` columns stay in the original units,
while `scaled_slack` and `max_scaled_slack` provide unit-free audit values.
Changing tonnes to kilograms cannot change the selected secondary target.
Execution metadata reports `phase_one_solver_calls`,
`phase_two_solver_calls`, `membership_solver_calls`, `solver_calls`,
`certificate_extra_solver_calls`, `planned_reference_sets`, and the number
of reference sets actually compiled.
The membership call count is normally zero; an equality-based common-factor or
activity-specific external appraisal can add one beta-zero feasibility task per
otherwise certified row. `certificate_extra_solver_calls` is separately
zero because LP and economic release certification reuses returned solutions;
it must not be read as the total number of membership tasks.

### Open one certified operating plan

The existing `improvement` plot turns a certified nonnegative common-factor
DDF result into an original-unit operating ledger. It separates the common
commitment $\beta g$ from any additional variable-specific slack found by the
completion programme, then reports the selected target without putting energy,
labour, electricity, and emissions on a fictitious common quantity scale.

```python
from deapack import CommonFactorWeakDisposalDDF, DEAData, load_dataset

frame = load_dataset("environmental_panel")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    period="period",
    inputs=["energy", "labor"],
    outputs="electricity",
    bad_outputs="co2",
)
result = CommonFactorWeakDisposalDDF(
    input_direction="zeros",
    output_direction="observed",
    bad_output_direction="observed",
    reference="contemporaneous",
).fit(data)

result.plot(kind="improvement", dmu_id="Central", period=2020)
```

This reporting contract is deliberately narrow. It accepts the family-level
CRS common-factor weak-disposal model and the exact
`ChungFareGrosskopfDDF` source preset because both use the same production
account. It does not reinterpret strong disposal, the deprecated equality
selector, activity-specific weak disposal, by-production DDF, or a method
specialization as the same plan.

Discovery advertises the plot only when at least one observation has a valid
nonnegative $\beta$, certified reference-technology membership, at least one
positive direction component, certified primary and completion programmes, a
certified target, and a fully reconstructable direction/slack/target ledger. An
external common-factor row may therefore carry an additional certified phase-zero
membership diagnostic. A negative
cross-reference distance remains a legitimate signed DDF result, but it is not
presented as an improvement programme. `peer_valid` and `dual_valid` are not
release conditions for this target-only display because neither peers nor
duals appear in it. A vector summary prefilter avoids deep reconstruction of
rows that cannot qualify, and the ordinary observed/zero/one path copies only
the selected plan. Plot preparation reads the fitted public tables and adds no
optimization task; any required membership programme was completed during fit.

The displayed target is conditional on the selected technology, direction,
returns to scale, and reference information. It is one solver-selected
feasible benchmark, not a uniqueness claim, causal estimate, engineering
design, investment recommendation, or cost calculation.

`is_directionally_efficient` means that the selected operating programme
cannot be enlarged. It is not automatically a general
Pareto--Koopmans certificate. Equality-based weak-disposal paths do not add
an independent bad-output slack in phase two, so a zero selected-direction
distance with no input/good-output slack leaves `is_efficient` missing. A
positive distance or remaining permitted slack can still establish
`is_efficient=False`.

Null jointness is optional on the generic and activity-specific classes. When
requested, DEAPack checks the observed activities explicitly; it is never
inferred merely from the word “weak.”

The shared environmental kernel used by
`EnvironmentalDirectionalDistanceDEA`, `CommonFactorWeakDisposalDDF`, and
`ChungFareGrosskopfDDF` certifies each executed LP independently of the backend's
status label and then reconstructs the environmental balances, objective, RTS
account, and row-scaled completion target. Phase-one input, desirable-output, and
undesirable-output rows are scaled independently before solution; RTS rows retain
unit scale, and all reported quantities remain in their original units.
`score_valid=True` requires the LP certificate, the raw production account, and
the cleaned account actually used for publication. If that gate fails, the raw
`solver_status` remains visible but the score, duals, peers, slacks, and targets
are withheld. If the primary programme passes and only the optional
slack-completion phase fails, the native distance remains valid while
`completion_valid=False`; no uncertified projection table is released.

Peer and dual claims have independent release gates. Thresholded intensities must
reconstruct the same environmental programme before `peer_valid=True`. Dual rows
are all-or-nothing: every required input, desirable-output, undesirable-output,
and non-CRS marginal must be finite, and quantity-row marginals are converted back
to original units before `dual_valid=True`. These postsolve checks use no additional
optimization task. They do not turn the deprecated `"weak"` compatibility selector
into a named weak-disposal technology.

## Migration from the old selector

Old code continues to run for one compatibility cycle:

```python
from deapack import EnvironmentalDDF

legacy = EnvironmentalDDF(
    disposability="weak",
    returns_to_scale="vrs",
).fit(data)
```

This call preserves the old equality-plus-VRS feasible set and emits a
warning. Choose the replacement from the production account, not from which
new score happens to be numerically closest:

- use `ChungFareGrosskopfDDF` for the source CRS output DDF;
- use `CommonFactorWeakDisposalDDF` for the CRS technology with another
  declared direction;
- use `ActivitySpecificWeakDisposalDDF` for Kuosmanen's convex VRS
  activity-specific technology; or
- use `EnvironmentalDirectionalDistanceDEA(disposability="strong")` when
  free contraction is the maintained assumption.

By-production, material-balance, explicit-treatment, and undesirable-output
SBM models remain different production accounts.

```{autosummary}
ChungFareGrosskopfDDF
CommonFactorWeakDisposalDDF
ActivitySpecificWeakDisposalDDF
KuosmanenWeakDisposalDDF
EnvironmentalDirectionalDistanceDEA
EnvironmentalDDF
```
