# Classical radial DEA: CCR, BCC, and complete presets

```{eval-rst}
.. currentmodule:: deapack
```

`RadialDEA` asks one of two operating questions:

- with current service commitments protected, by what common proportion could
  all controllable resources be reduced?
- with current resources held fixed, by what common proportion could all
  desirable services be expanded?

The first question gives the input contraction $\theta$; the second gives the
output expansion $\phi$. Choose the orientation from what management can
adjust, not from which specification gives the preferred score.

## Family, RTS specializations, and complete presets

The public interfaces expose three levels of composition:

| Interface | Fixed choices | Result identity |
|---|---|---|
| `RadialDEA` | configurable orientation, RTS, reference-information, comparison-eligibility, and slack policies | `method_id="static.radial"` |
| `CCR` | CRS only; orientation defaults to input but remains configurable | `specialization_id="static.radial.crs"` |
| `BCC` | VRS only; orientation defaults to input but remains configurable | `specialization_id="static.radial.vrs"` |
| `CCRInput`, `CCROutput`, `BCCInput`, `BCCOutput` | RTS, orientation, native-score convention, and `compute_slacks=True` with the DEAPack row-scaled lexicographic completion policy; reference information and comparison eligibility remain configurable | the corresponding `preset_id` |

The four complete historical recipes are:

| Preset | RTS | Orientation | Native `score` | `preset_id` |
|---|---|---|---|---|
| `CCRInput` | CRS | input | $\theta$ | `static.radial.crs.input` |
| `CCROutput` | CRS | output | $\phi$ | `static.radial.crs.output` |
| `BCCInput` | VRS | input | $\theta$ | `static.radial.vrs.input` |
| `BCCOutput` | VRS | output | $\phi$ | `static.radial.vrs.output` |

All seven constructors use the same radial implementation. The identities
record how much of the complete recipe the caller selected explicitly; they
do not create duplicate solver engines. A numerically equivalent direct
`RadialDEA` call retains only the family `method_id` rather than guessing a
historical preset after fitting.

Identity-defining fields are revalidated immediately before a fit. If code
mutates the fixed RTS of `CCR`/`BCC`, or the fixed RTS, orientation, or slack
policy of a complete preset, the fit fails rather than emitting provenance
that disagrees with the programme actually solved.

## Model and returns to scale

Input orientation:

$$
\min_{\theta,\lambda}\theta
\quad\text{s.t.}\quad
X\lambda\le\theta x_o,\quad Y\lambda\ge y_o.
$$

Output orientation:

$$
\max_{\phi,\lambda}\phi
\quad\text{s.t.}\quad
X\lambda\le x_o,\quad Y\lambda\ge\phi y_o.
$$

The intensity sum selects the maintained scale technology:

| `returns_to_scale` | Intensity rule | Operating interpretation |
|---|---:|---|
| `"crs"` | no sum restriction | observed activities may be proportionally replicated |
| `"vrs"` | $\mathbf 1^\top\lambda=1$ | comparisons use convex combinations at observed scale |
| `"nirs"` | $\mathbf 1^\top\lambda\leq1$ | the maintained technology rules out increasing returns |
| `"ndrs"` | $\mathbf 1^\top\lambda\geq1$ | the maintained technology rules out decreasing returns |

For input orientation, `score` is the native $\theta$ and already follows the
higher-is-better efficiency convention. For output orientation, `score` is the
native $\phi$; `efficiency` is the harmonized value $1/\phi$. Keep the native
score in an audit trail because the reciprocal display must not obscure which
operating question was fitted.

## Declare who may teach whom before fitting

The radial criterion does not decide whether two organizations have comparable
missions, contracts, measurement systems, or operating rights. Keep that
institutional decision separate from the fitted intensities. The optional
`peer_eligibility` argument accepts a source-neutral, observation-specific
`PeerEligibility` declaration and intersects it with the base `ReferenceSpec`.
It can remove an otherwise visible candidate but cannot add one excluded by a
time window or custom base policy.

The summary reports the candidate count before and after that intersection as
`base_reference_size` and `reference_size`, plus `self_in_reference`. No
evaluated row is silently inserted. See {doc}`../user-guide/reference-sets`
for keyed and positional construction, provenance, audit export, failure
semantics, and the explicit boundary against named categorical DEA models.

The same argument is exposed by `RadialDEA`, `CCR`, `BCC`, and all four
fixed-orientation recipes. A fixed recipe still fixes its historical RTS,
orientation, and slack-completion policy; declaring a comparison population
does not alter those identity-defining choices. For example,
`BCCInput(peer_eligibility=eligibility)` asks the complete input-oriented BCC
question using only the comparison rights declared by `eligibility`.

## A result that proportional efficiency alone misses

The following three branches make the distinction between radial and strong
efficiency visible without a large dataset:

```python
import pandas as pd

from deapack import DEAData, RadialDEA

frame = pd.DataFrame(
    {
        "branch": ["A", "B", "C"],
        "resource": [1.0, 2.0, 1.0],
        "service": [1.0, 1.0, 0.5],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="branch",
    inputs="resource",
    outputs="service",
)

input_result = RadialDEA(
    orientation="input",
    returns_to_scale="vrs",
).fit(data)
output_result = RadialDEA(
    orientation="output",
    returns_to_scale="vrs",
).fit(data)

columns = [
    "dmu_id",
    "score",
    "efficiency",
    "is_radially_efficient",
    "is_efficient",
]
print(input_result.summary()[columns].to_string(index=False))
print(output_result.summary()[columns].to_string(index=False))
print(input_result.slacks.query("dmu_id == 'C'").to_string(index=False))
print(input_result.targets_for("C").to_string(index=False))
```

Under the VRS input model, branch C has $\theta=1$: it cannot reduce its one
unit of resource proportionally and still protect its current service. It is
therefore radially efficient. Yet branch A uses the same resource and supplies
one unit of service rather than one half. The second phase records C's service
shortfall as output slack $0.5$, targets service at $1$, and correctly leaves
`is_efficient=False`.

The VRS output model answers the complementary question. C has
$\phi=2$ and harmonized efficiency $1/2$, because its current resource could
support twice its service. These findings do not conflict: one concerns common
resource contraction and the other common service expansion.

`CCR` and `BCC` are convenient constructors for the CRS and VRS cases of this
same family. They fix only RTS. Orientation remains a separate empirical
choice; when omitted, both constructors use their documented input default.
Use one of the four complete presets when the result should identify an
explicit CCR-I, CCR-O, BCC-I, or BCC-O recipe.

## Published Pareto--Koopmans completion protocol

`is_radially_efficient` classifies the phase-one proportional criterion.
`is_efficient` additionally requires the second-phase slack completion. With
the default `compute_slacks=True`, `slacks`, `targets`, and peers make the
remaining component-specific improvement auditable.

The released protocol identity is
`evaluation.target_completion.pareto_koopmans`. It is not a standalone model
or callable API. `RadialDEA` composes it when `compute_slacks=True` and
discloses the composition in result metadata. The native radial score is
preserved: phase two answers whether a separately attainable input saving or
desirable-output gain remains after the common proportional adjustment has
stopped.

```python
input_result.metadata["target_completion_id"]
# "evaluation.target_completion.pareto_koopmans"
```

The four complete presets fix `compute_slacks=True`. Their first phase
estimates $\theta$ or $\phi$; their second phase holds that radial optimum
fixed and maximizes the sum of row-scaled ordinary input and desirable-output
slacks. Row scaling makes the completion invariant to changes of measurement
units. This is DEAPack's declared target-selection rule, not a claim that the
foundational literature prescribes one unique secondary objective. It is not
a price system, a statement of managerial priorities, or a closest-target
criterion.

When phase two succeeds, the completed target is strongly efficient under the
same ordinary convex input/desirable-output technology: no feasible plan uses
no more of every eligible input and produces no less of every desirable output
while improving at least one quantity. Reported targets and peer intensities
belong to the solver-selected completed optimum and need not be unique,
nearest, least-cost, or prescriptive. They are benchmark comparisons, not
causal estimates of management quality.

## Operating-plan visualization

A certified completed radial result can expose the two claims without placing
unlike quantities on one axis:

```python
figure = input_result.plot(
    kind="improvement",
    dmu_id="C",
)
```

For branch C in the example above, the input-oriented phase-one factor is
$\theta=1$. The reconstructed radial plan therefore remains at resource $1$
and service $0.5$: no common resource contraction is represented as feasible.
The separately certified completion retains resource $1$ and adds the output
slack $0.5$, giving the public completed target of service $1$. The display
keeps

```text
observed operation -> phase-one radial target -> completed target
```

explicit. In particular, the public `targets` table contains the completed
target; it should not be relabelled as $\theta x_o,y_o$ or $x_o,\phi y_o$
without removing the phase-two slacks first.

The radial preparation contract accepts the exact `static.radial` family under
the supported input or output orientations and RTS policies only when the
selected observation is inside the reference technology and both fitted phases
certify. It reconstructs the native $\theta$ or $\phi$ account, every original-
unit target and slack identity, the physical maximum-slack account, and the
certified strong-efficiency classification from the fitted result. Its
original-unit ledger does not
republish a per-variable scaled-slack magnitude because the exact scale also
depends on the selected reference set's row maximum. It does not require peer
or dual publication because the figure displays neither claim, and it performs
no optimization.

The completed target is one selected feasible benchmark under the declared
technology and row-scaled completion rule. The columns do not establish an
implementation order, target uniqueness, transition cost, causation, or a
management prescription.

For a large screening exercise, `compute_slacks=False` skips the second LP for
each evaluated organization:

```python
score_only = RadialDEA(
    orientation="input",
    returns_to_scale="vrs",
    compute_slacks=False,
).fit(data)

assert score_only.metadata["target_completion_id"] is None
```

This is a performance choice with a substantive reporting consequence.
`is_radially_efficient` remains available, but targets and slacks are empty and
`is_efficient` is missing because strong Pareto--Koopmans efficiency was not
assessed.

The released protocol is currently certified only for ordinary adjustable
inputs and desirable outputs under a compatible convex free-disposal
technology. Its extension to weak-disposal accounts, fixed or
non-discretionary quantities, and non-convex technologies is deferred to the
next version. A model-specific projection in one of those families does not
inherit this protocol identity by analogy.

With an explicit external reference, an evaluated activity may lie beyond the
maintained reference technology (input $\theta>1$ or output $\phi<1$), or the
comparison can be infeasible. `is_within_reference_technology` records that
boundary; both efficiency classifications remain missing outside it rather
than labeling a superior external activity inefficient.

## Phase-specific result validity

The proportional score and the completed operating plan are two separate
claims. DEAPack checks them separately after the solver returns:

1. phase one must pass a solver-neutral primal, bound, objective, dual, KKT,
   complementarity, and strong-duality certificate, followed by a
   reconstruction of the radial factor, production inequalities, and RTS
   account;
2. when slack completion is requested, phase two must pass the same LP
   certificate and a separate reconstruction of its row-scaled slack
   objective, targets, production balances, and RTS account.

The checks add no optimization task. They verify the returned solution before
turning numerical arrays into economic claims, and they are applied separately
to every evaluated observation.

The summary makes the release boundary explicit:

| Claim | Validity fields | What may be released |
|---|---|---|
| proportional input saving or output expansion | `score_valid`, `score_status`, `primary_semantic_solver_status`; phase-one backend evidence remains in `primary_solver_status`, `primary_backend_solver_status`, and `primary_raw_solver_status` | `score`, harmonized `efficiency`, and `is_radially_efficient` |
| slack-completed plan | `completion_valid`, `completion_status`, `completion_semantic_solver_status`; phase-two backend evidence remains in `completion_solver_status`, `completion_backend_solver_status`, and `completion_raw_solver_status` | a completed target and the basis for `is_efficient` |
| published target, peers, and dual account | `target_valid`, `peer_valid`, `dual_valid` and their status fields | only the corresponding certified tables |

If phase one is not certified, the score and every semantic result table for
that observation are withheld, while the raw backend status and certificate
residuals remain in `diagnostics`. If phase one is certified but phase two is
not, the proportional score remains available; targets, slacks, peer rows,
dual rows, and the strong-efficiency classification are withheld. Failure for
one organization does not abort or contaminate later organizations.

`solver_status` is the semantic status of the final attempted phase. If a
backend reports `optimal` but either the LP certificate or the economic
reconstruction rejects that phase, the semantic status is `numerical_error`.
`backend_solver_status` and `raw_solver_status` preserve the final backend
claim. `primary_semantic_solver_status` and
`completion_semantic_solver_status` provide the same semantic status at each
phase. The older `primary_solver_status` and `completion_solver_status` remain
backend-status compatibility fields; their explicitly named backend/raw
companions make that provenance visible. `diagnostics` retains semantic,
backend, and raw statuses for each attempted phase. Use the primary semantic
status together with `score_valid` when consuming the proportional score, and
use the completion/target validity fields when consuming the completed
operating plan. A certified primary score therefore remains available when a
later completion attempt fails, even though the final semantic status records
that failure. DEAPack's performance reporting uses this phase-specific score
contract. A high `peer_tolerance` may separately withhold a thresholded peer
display without invalidating an otherwise certified target.

## Verification boundary

The core implementation is checked against an exact three-activity
phase-one certificate for both orientations under CRS, VRS, NIRS, and NDRS.
Two exact VRS cases certify input- and output-oriented slack semantics. An
additional exact two-input/two-output CRS fixture certifies the complete
`CCRInput` and `CCROutput` recipes, including their scores, selected peers,
targets, and residual slacks. A separate dense two-phase compiler cross-checks
scores, slacks, targets, and efficiency status with and without slack
completion on a larger fixture. These claims apply to the stated
self-inclusive cross-sectional references; they are analytical software
evidence, not a claim that a numerical table in the foundational articles has
been reproduced.

Runtime fault tests additionally forge objectives, primals, row marginals,
publication cleanup, and peer displays. They cover both orientations and all
four RTS regimes, include very small measurement units, and verify that the
certificates remain unit-stable and do not add solver calls.

```{autosummary}
RadialDEA
CCR
BCC
CCRInput
CCROutput
BCCInput
BCCOutput
```

Radial DEA intentionally rejects a dataset containing declared undesirable
outputs. Users must choose an explicit environmental technology rather than
letting the model guess a disposability assumption.

`RadialDEA`, its RTS specializations, and the four complete presets construct
a convex envelopment technology. For a non-convex benchmark that compares an
organization with one observed operating plan at a time, use {doc}`fdh`.
