# Input-, output-, and non-oriented slacks-based measures

```{eval-rst}
.. currentmodule:: deapack
```

DEAPack exposes three
[Tone (2001)](https://doi.org/10.1016/S0377-2217(99)00407-5) SBM contracts
over one common convex envelopment technology:

| Managerial purpose | Canonical class | Exact aliases | Canonical method ID |
|---|---|---|---|
| reduce input excess while maintaining outputs | `InputOrientedSlacksBasedDEA` | `InputSBM`, `InputRussell` | `static.sbm.input.tone2001` |
| expand outputs without increasing inputs | `OutputOrientedSlacksBasedDEA` | `OutputSBM`, `OutputRussell` | `static.sbm.output.tone2001` |
| improve inputs and outputs jointly | `SlacksBasedDEA` | `SBM`, `ERG` | `static.sbm.nonoriented.tone2001` |

`ERG` is a discoverability alias for the standard non-oriented SBM on the
strictly positive data domain documented here. The oriented classes are
distinct public methods, not an `orientation` switch on `SlacksBasedDEA`.
Tone (2001, p. 507) establishes the corresponding conditional identities for
the input- and output-oriented Russell measures; `InputRussell` and
`OutputRussell` expose those names without adding two duplicate solvers.
In short, the historical names map into one framework as follows:
Input Russell = input-oriented SBM, Output Russell = output-oriented SBM, and
ERG = non-oriented SBM. The three orientations themselves are not aliases:
they value different operating improvements.

All three models support CRS, VRS, NIRS, and NDRS, use the shared reference
layer, compile each distinct reference set once, and solve one sparse linear
program per evaluated observation. VRS is the default.

## Common production account

For evaluated observation $o$, let $x_o\in\mathbb{R}_{++}^{m}$ contain
controllable inputs and $y_o\in\mathbb{R}_{++}^{s}$ contain desirable
outputs. Every orientation uses

$$
X\lambda+s^-=x_o,\qquad
Y\lambda-s^+=y_o,\qquad
\lambda,s^-,s^+\geq0,
$$

plus the selected returns-to-scale restriction. The fitted target is

$$
\widehat x_o=x_o-s^-,
\qquad
\widehat y_o=y_o+s^+.
$$

Define

$$
L_o^x=\frac{1}{m}\sum_i\frac{s_i^-}{x_{io}},
\qquad
L_o^y=\frac{1}{s}\sum_r\frac{s_r^+}{y_{ro}}.
$$

`input_inefficiency` reports $L_o^x$, and `output_inefficiency` reports
$L_o^y$. For `OutputSBM`, `output_expansion_factor` additionally reports
$1+L_o^y$; it is missing for the input and non-oriented result contracts.
These are equal dimension-weighted proportional accounts. They are not
expenditure shares, prices, or user-supplied importance weights.

## Declare comparison rights before choosing an SBM orientation

All three ordinary SBM classes and their aliases accept `peer_eligibility`.
The declaration states which observations may supply comparison evidence for
each evaluated organization; `ReferenceSpec` separately states which periods
or custom rows are visible. The fitted population is their exact intersection.
The intersection changes neither the evaluated-value denominators in $L_o^x$
and $L_o^y$ nor which side of the account an orientation values.

Every summary reports `base_reference_size`, effective `reference_size`, and
`self_in_reference`. Excluding self is permitted and disclosed rather than
silently repaired. Positive rows in `intensities` are selected only from the
effective population, and the compact result metadata preserves the
eligibility provenance. An external comparison can be infeasible when no
admitted activity maintains the protected resource or service side; the
result then fails closed instead of manufacturing a score. The common
construction and audit workflow is documented in
{doc}`../user-guide/reference-sets`.

This support is limited to the ordinary input-, output-, and non-oriented
black-box SBM family. `UndesirableSlacksBasedDEA`, network SBM, and dynamic SBM
have different production accounts and do not inherit this argument.

## Why the oriented Russell names resolve to these leaves

On the common balance system, define variable-specific input contraction and
output expansion factors

$$
\theta_{io}=\frac{(X\lambda)_i}{x_{io}}
=1-\frac{s_i^-}{x_{io}},
\qquad
\phi_{ro}=\frac{(Y\lambda)_r}{y_{ro}}
=1+\frac{s_r^+}{y_{ro}}.
$$

Minimizing $m^{-1}\sum_i\theta_{io}$ is therefore the input-oriented SBM
programme, while maximizing $s^{-1}\sum_r\phi_{ro}$ is the direct
output-oriented SBM programme. DEAPack reports the latter programme's direct
optimum as `output_expansion_factor` and its reciprocal, higher-is-better
convention as `score` and `efficiency`. Consequently:

- `InputRussell` is exactly `InputOrientedSlacksBasedDEA`;
- `OutputRussell` is exactly `OutputOrientedSlacksBasedDEA` when the Russell
  expansion optimum is reported through this reciprocal score convention.

This identity is conditional on the same strictly positive denominators,
convex technology, returns-to-scale restriction, reference population,
equal dimension weights, and target/alternate-optimum policy. The alias does
not cover the Russell graph measure, closest or strongly efficient Russell
targets, weighted formulations, or zero/signed-data extensions. On the side
that is absent from an oriented objective, DEAPack continues to report a
solver-selected feasible target; it is not a second optimization criterion.

## Input-oriented SBM

`InputOrientedSlacksBasedDEA` minimizes

$$
\rho_o^I
=
1-L_o^x
=
1-\frac{1}{m}\sum_i\frac{s_i^-}{x_{io}}.
$$

`score` and `efficiency` contain the higher-is-better resource-retention
score $\rho_o^I$. `distance` is $1-\rho_o^I=L_o^x$.

The output balances require the selected benchmark to maintain at least the
observed outputs, but $s^+$ does not enter the objective. Returned output
slacks and output targets are therefore solver-selected feasibility
information. They are not output-expansion optima.

```python
from deapack import InputSBM

input_result = InputSBM(
    returns_to_scale="crs",
).fit(data)
```

`InputSBM` and `InputRussell` are exact aliases for
`InputOrientedSlacksBasedDEA` on the equivalence domain above.

## Output-oriented SBM

`OutputOrientedSlacksBasedDEA` solves Tone’s direct linear programme

$$
\max\quad
\tau_o^O
=
1+L_o^y
=
1+\frac{1}{s}\sum_r\frac{s_r^+}{y_{ro}}.
$$

The reported efficiency is its reciprocal:

$$
\rho_o^O
=
\frac{1}{\tau_o^O}.
$$

`score` and `efficiency` contain the higher-is-better reciprocal
$\rho_o^O$. `output_expansion_factor` retains
$1/\rho_o^O=1+L_o^y$, and `distance` is $1-\rho_o^O$. The expansion
factor averages variable-specific proportional gains; it is not a common
radial output factor.

Input balances ensure that the selected benchmark uses no more than the
observed inputs, but $s^-$ does not enter the objective. Returned input
slacks and input targets are solver-selected feasibility information, not
input-saving optima.

```python
from deapack import OutputSBM

output_result = OutputSBM(
    returns_to_scale="crs",
).fit(data)
```

`OutputSBM` and `OutputRussell` are exact aliases for
`OutputOrientedSlacksBasedDEA` on the equivalence domain above.

## Non-oriented SBM

`SlacksBasedDEA` minimizes Tone’s joint fractional account:

$$
\rho_o^{NO}
=
\frac{1-L_o^x}{1+L_o^y}
=
\frac{
1-\frac{1}{m}\sum_i s_i^-/x_{io}
}{
1+\frac{1}{s}\sum_r s_r^+/y_{ro}
}.
$$

Both input and output slacks enter the objective. With a self-inclusive
reference population, $\rho_o^{NO}\in(0,1]$, and $\rho_o^{NO}=1$ exactly when all
normalized input and output slacks are zero. `score` and `efficiency` report
$\rho_o^{NO}$; `distance` reports $1-\rho_o^{NO}$.

```python
from deapack import SBM

joint_result = SBM(
    returns_to_scale="crs",
).fit(data)
```

`SBM` and `ERG` are exact aliases for `SlacksBasedDEA`.

## Tone's five units: published and package evidence

`sbm_slack_contrast` contains a neutral two-resource, two-service contrast.
Tone (2001), Table 1:

```python
import pandas as pd

from deapack import (
    DEAData,
    InputSBM,
    OutputSBM,
    SBM,
    dataset_info,
    load_dataset,
)

frame = load_dataset("sbm_slack_contrast")
roles = dataset_info("sbm_slack_contrast").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

input_result = InputSBM(returns_to_scale="crs").fit(data)
output_result = OutputSBM(returns_to_scale="crs").fit(data)
joint_result = SBM(returns_to_scale="crs").fit(data)

scores = pd.concat(
    {
        "input": input_result.summary().set_index("dmu_id")["score"],
        "output": output_result.summary().set_index("dmu_id")["score"],
        "non_oriented": joint_result.summary().set_index("dmu_id")["score"],
    },
    axis=1,
)
```

The calibrated output is:

| DMU | Input | Output | Non-oriented |
|---|---:|---:|---:|
| A | 0.848485 | 0.818182 | 0.797980 |
| B | 0.719697 | 0.606061 | 0.568182 |
| C | 1.000000 | 1.000000 | 1.000000 |
| D | 1.000000 | 0.666667 | 0.666667 |
| E | 1.000000 | 1.000000 | 1.000000 |

Only the non-oriented column is a published numerical reproduction: it
reproduces Tone's Table 2 CRS scores within solver tolerance. The input- and
output-oriented columns are DEAPack calculations from the checked equations,
not reproductions of published table values. A published numerical oracle for
those two columns has not been located and is deferred to a future version.

The published non-oriented slack reproduction is:

| DMU | `input_1` | `input_2` | `output_1` | `output_2` |
|---|---:|---:|---:|---:|
| A | 0.000000 | 0.357143 | 0.714286 | 0.000000 |
| B | 0.000000 | 0.642857 | 2.285714 | 0.000000 |
| C | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| D | 0.000000 | 0.000000 | 0.000000 | 1.000000 |
| E | 0.000000 | 0.000000 | 0.000000 | 0.000000 |

Use the long-form outputs to audit the account:

```python
joint_result.slacks[[
    "dmu_id",
    "role",
    "variable",
    "slack",
    "normalizer",
    "normalized_slack",
    "average_weight",
]]
joint_result.targets_for("A")
joint_result.peers("A")
```

### Exact VRS orientation oracle

The following small VRS case provides exact values for all three operating
questions:

```python
audit_frame = pd.DataFrame({
    "dmu": ["A", "B", "O"],
    "x1": [2.0, 4.0, 4.0],
    "x2": [4.0, 2.0, 4.0],
    "y1": [1.0, 2.0, 1.0],
    "y2": [2.0, 1.0, 1.0],
})
audit_data = DEAData.from_frame(
    audit_frame,
    dmu="dmu",
    inputs=["x1", "x2"],
    outputs=["y1", "y2"],
)

input_o = (
    InputSBM(returns_to_scale="vrs")
    .fit(audit_data)
    .summary()
    .set_index("dmu_id")
    .loc["O"]
)
output_o = (
    OutputSBM(returns_to_scale="vrs")
    .fit(audit_data)
    .summary()
    .set_index("dmu_id")
    .loc["O"]
)
joint_o = (
    SBM(returns_to_scale="vrs")
    .fit(audit_data)
    .summary()
    .set_index("dmu_id")
    .loc["O"]
)
```

For O,

$$
\rho_O^I=\frac{3}{4},\qquad
\tau_O^O=\frac{3}{2},\qquad
\rho_O^O=\frac{2}{3},\qquad
\rho_O^{NO}=\frac{1}{2}.
$$

`output_o["efficiency"] * output_o["output_expansion_factor"]` reconstructs
one. The three exact values prevent the oriented and joint measures from
being treated as aliases.

## Efficiency flags and normalized diagnostics

`is_sbm_efficient` is orientation-specific:

- input orientation checks that every normalized input slack is within
  tolerance;
- output orientation checks that every normalized output slack is within
  tolerance; and
- non-oriented SBM checks both sides.

`is_efficient` is the nullable Pareto--Koopmans status. It is populated for
the non-oriented model, whose objective includes all input and output slacks.
It is deliberately `NA` for `InputSBM` and `OutputSBM`. A single-oriented
score of 1 does not certify strong efficiency.

The summary retains both raw-unit and normalized maxima:

| Field | Meaning |
|---|---|
| `max_slack` | largest returned slack in original units across both sides |
| `max_normalized_slack` | largest returned proportional slack across both sides |
| `max_objective_slack` | largest original-unit slack on the side valued by the objective |
| `max_objective_normalized_slack` | largest proportional slack on the objective side; used for `is_sbm_efficient` |
| `max_unoptimized_side_slack` | largest original-unit slack on the non-target side of a single orientation |
| `max_unoptimized_side_normalized_slack` | largest proportional slack on that non-target side |

Efficiency classification uses normalized fields because a raw tolerance
cannot compare employees, currency, and service counts consistently. Raw
fields remain useful for operating interpretation.

The following executable case has an input-oriented score of 1 and a positive
output slack:

```python
import pandas as pd

from deapack import DEAData, InputSBM, ReferenceSpec

frame = pd.DataFrame({
    "dmu": ["benchmark", "clinic"],
    "staff": [1.0, 1.0],
    "visits": [2.0, 1.0],
})
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs="staff",
    outputs="visits",
)
reference = ReferenceSpec(kind="custom", custom_rows=[0])
result = InputSBM(reference=reference).fit(data)
result.summary()[[
    "dmu_id",
    "score",
    "is_sbm_efficient",
    "is_efficient",
    "max_unoptimized_side_normalized_slack",
]]
```

For `clinic`, `score == 1` and `is_sbm_efficient` is true, while
`is_efficient` is missing and the unoptimized output-side normalized slack is
1. A mirror-image output-oriented example can retain an unoptimized input
slack.

## Result tables

The three classes use the common `DEAResult` contract.

| Table | SBM-specific content |
|---|---|
| `summary()` | native score, `score_valid`, `score_status`, orientation, inefficiency components, output expansion factor where defined, raw and normalized maxima, efficiency flags, solver and reference status |
| `slacks` | `role`, `variable`, original-unit `slack`, evaluated-value `normalizer`, `normalized_slack`, equal-dimension `average_weight`, and `included_in_objective` |
| `targets` | observed and target quantities with `selection_status` |
| `intensities` | positive reference intensities with solver-selection status |
| `duals` | direct- or transformed-program marginals with explicit constraint roles |
| `diagnostics` | raw solver status plus independent primal, bound, objective, dual, complementarity, strong-duality, and SBM operating-account certificates |

All targets use
`selection_status="solver_selected_primary_optimum"`. The same label applies
to peer intensities. The current model does not solve alternate-optimum
bounds or a secondary closest-target programme.

For a single orientation, the non-objective side is especially weakly
identified: it is present to make the returned reference activity feasible,
not to optimize a second management goal. Even objective-side targets can
vary when multiple optima exist.

## Plot one variable-specific operating plan

The three classic static orientations expose a result-native improvement
view:

```python
figure = joint_result.plot(
    kind="improvement",
    dmu_id="A",
)
```

The left panel places every resource saving and service gain on the evaluated
organization's own proportional ruler. The adjacent ledger retains current
and selected target quantities in their original units and reconstructs the
input-retention and output-expansion accounts. For `InputSBM` and `OutputSBM`,
hatched rows identify the feasibility-only side that is not valued by that
orientation's performance objective.

The plot is deliberately limited to
`static.sbm.input.tone2001`, `static.sbm.output.tone2001`, and
`static.sbm.nonoriented.tone2001`. It does not translate additive, RAM,
environmental, network, dynamic, super-efficiency, or paper-specific variants
into one visual institution. Preparation also requires both postsolve
certificates and independently reconstructs every target, normalized slack,
average account, and headline score. A panel result requires `period=...`
when the same DMU occurs more than once.

## Postsolve certification and fail-closed release

DEAPack does not publish a classic SBM result merely because a backend labels
an incumbent `optimal`. For every evaluated observation it first applies the
shared solver-neutral LP certificate. That certificate independently checks
the primal rows, variable bounds, reported objective, row and bound
marginals, stationarity, complementarity, and strong duality.

The separate SBM account certificate then reverses the Charnes--Cooper
transformation where required and verifies:

- nonnegative intensities, slacks, and targets;
- input, desirable-output, and any applicable bad-output benchmark balances;
- the declared CRS, VRS, NIRS, or NDRS intensity account;
- the direct or fractional normalization identity;
- the backend objective against the reconstructed SBM account; and
- the reported higher-is-better efficiency against its input-retention and
  output-expansion components.

A successful row has `score_valid=True`, `score_status="defined"`, and both
diagnostic certificate fields equal to true. If the solve fails, the LP
certificate fails, or the economic account cannot be reconstructed, the
canonical score, efficiency, and distance are missing. Slacks, targets,
intensities, and duals for that observation are withheld atomically. The raw
backend `solver_status` remains in diagnostics for audit, and one failed
observation does not prevent later observations from being evaluated.

`metadata["postsolve_certificate"]` records this release policy. Certification
does not make the returned peers or target unique, causal, or prescriptive; it
certifies that the published solver-selected plan is numerically optimal and
internally consistent with the fitted SBM institution.

## Direct oriented programmes and Charnes--Cooper

Input-oriented SBM directly minimizes $1-L_o^x$. Output-oriented SBM
directly maximizes

$$
\tau_o^O=1+L_o^y
$$

and then reports $\rho_o^O=1/\tau_o^O$. Both direct programmes record
`linearization="identity_scale"` and `transform_scale=1`.

Only non-oriented SBM uses the Charnes--Cooper variables

$$
\tau
=
\left(
1+\frac{1}{s}\sum_r\frac{s_r^+}{y_{ro}}
\right)^{-1},
\qquad
\Lambda=\tau\lambda,\quad
S^-=\tau s^-,\quad
S^+=\tau s^+.
$$

The transformed balances and normalization are

$$
X\Lambda+S^-=\tau x_o,
\qquad
Y\Lambda-S^+=\tau y_o,
$$

$$
\tau+\frac{1}{s}\sum_r\frac{S_r^+}{y_{ro}}=1.
$$

The non-oriented objective is

$$
\min\quad
\tau-\frac{1}{m}\sum_i\frac{S_i^-}{x_{io}}.
$$

The direct VRS programmes use $\mathbf{1}^\top\lambda=1$; their NIRS and NDRS
variants use the corresponding inequalities. In the transformed
non-oriented programme, those restrictions become
$\mathbf{1}^\top\Lambda=\tau$,
$\mathbf{1}^\top\Lambda\leq\tau$, or
$\mathbf{1}^\top\Lambda\geq\tau$. CRS adds no convexity row. Non-oriented
intensities, slacks, and targets are divided by $\tau$ and returned in
their original scale. Its `transform_scale` is diagnostic, not an economic
score.

## Data, references, and failure conditions

The standard classes require:

- at least one input and one desirable output;
- finite, strictly positive input and output quantities;
- a valid reference population with positive support; and
- a feasible selected returns-to-scale technology.

Strict positivity is structural, but the three objectives use denominators
differently: input-oriented SBM divides only input slacks by $x_{io}$,
output-oriented SBM divides only output slacks by $y_{ro}$, and non-oriented
SBM uses both sets of denominators. DEAPack nevertheless freezes strictly
positive inputs and outputs as the common standard Tone domain for all three
classes. Zero and negative values are rejected instead of being shifted or
replaced by an undocumented epsilon. The standard measure is independently
invariant to positive unit rescaling, but it is not translation invariant.

Tone (2001) writes the CRS programmes explicitly and obtains VRS by adding
$\mathbf{1}^\top\lambda=1$. Result metadata records those two cases with
`returns_to_scale_provenance="tone_2001_explicit"`. NIRS and NDRS are
DEAPack common convex-envelopment variants and are labeled
`"deapack_convex_envelopment_variant"` rather than attributed to the source.

`reference` accepts `None`, a `ReferenceSpec`, or a reference-kind string.
The shared layer supports automatic/global cross-sectional appraisal and the
declared contemporaneous, global, sequential, window, biennial, or custom
panel policies. `peer_eligibility` is not embedded in `ReferenceSpec`; it is a
separate observation-specific comparison-right declaration composed with that
base information policy. An external reference population changes the
evidence and can make an oriented dominance account infeasible when no
eligible activity maintains the required side. Solver status and diagnostics
retain that failure instead of manufacturing a score.

Undesirable outputs require `UndesirableSlacksBasedDEA`. That model has its
own production and disposal contract. Network SBM, dynamic SBM,
super-efficiency SBM, zero/negative-data variants, weighted SBM, and
productivity indexes are not aliases for these three static black-box
classes.

## Constructor contract

All three canonical classes inherit the same constructor parameters:

```python
InputOrientedSlacksBasedDEA(
    returns_to_scale="vrs",
    reference=None,
    peer_eligibility=None,
    solver=None,
    solver_options=None,
    tolerance=1e-7,
    peer_tolerance=None,
)
```

Replace the class name with `OutputOrientedSlacksBasedDEA` or
`SlacksBasedDEA` for the other operating questions. Passing both `solver` and
`solver_options` is invalid.

```{autosummary}
InputOrientedSlacksBasedDEA
InputSBM
InputRussell
OutputOrientedSlacksBasedDEA
OutputSBM
OutputRussell
SlacksBasedDEA
SBM
ERG
```
