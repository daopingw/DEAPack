# Chavas--Cox generalized distance

```{eval-rst}
.. currentmodule:: deapack
```

`GeneralizedDistanceDEA` evaluates a proportional improvement path that can
express the measured gap through resource discipline, service growth, or
both.
`ChavasCoxGDF` and `GDF` are exact API aliases for the same implemented
method.

For evaluated activity $(x_o,y_o)$, the public score is

$$
D_G(x_o,y_o;\alpha)
=
\min_{\delta>0}
\left\{
\delta:
\left(\delta^{1-\alpha}x_o,\delta^{-\alpha}y_o\right)
\in\mathcal T
\right\},
\qquad 0\leq\alpha\leq1.
$$

The fitted result calls this score `generalized_distance` and stores the same
value in `score` and `efficiency`. With a self-inclusive reference technology,
$0<\delta\leq1$, and higher is better.

## Reading $\alpha$ as an adjustment-path parameter

The bearing parameter does not state which inputs or outputs matter more.
All inputs receive the same resource multiplier
$\delta^{1-\alpha}$, and all desirable outputs receive the same service
multiplier $\delta^{-\alpha}$. Instead, $\alpha$ divides the common
productivity adjustment between the two sides of the operating account:

| `alpha` | Quantity held fixed | Performance question |
|---:|---|---|
| $0$ | current services | How much could every input commitment fall while services are protected? |
| $1/2$ | neither side | What reciprocal proportional resource saving and service growth are jointly attainable? |
| $1$ | current resource budget | How much could every service expand while resources are protected? |

`alpha` is analyst declared. It may represent a legal obligation, budget
condition, or authorized organizational priority when the study documents
that provenance. Otherwise it is a scenario assumption, not a revealed
management preference.

For an interior value, the legacy-named result field `resource_commitment` is
$\delta^{1-\alpha}$ and `service_commitment` is
$\delta^{-\alpha}$. The corresponding summary fields
`resource_saving_pct` and `service_growth_pct` report one minus the first
multiplier and the second multiplier minus one.

The endpoints reproduce familiar bounded radial scores:

$$
\alpha=0:\quad \delta=\theta^I,
\qquad
\alpha=1:\quad \delta=\frac{1}{\phi^O}.
$$

At $\alpha=1/2$, the target follows a balanced reciprocal path. If a future
source-native standard-hyperbolic leaf defines
$h$ by exactly the same reciprocal path, with the same technology, reference,
RTS, disposal, and target policy, then

$$
\boxed{\delta=h^2}.
$$

The current result reports $\delta$ and the two path commitments; it does not
publish a field named as standard hyperbolic efficiency. That separate method
is deferred until its source-native convention and independent oracle pass
their own evidence gate.

:::{admonition} Development migration note
:class: note
Earlier 2.0 development builds exposed
`standard_hyperbolic_efficiency` at `alpha=0.5`. The field has been removed
because its name asserted a source-native method that has not passed the
current evidence gate. At the balanced GDF bearing,
`resource_commitment == sqrt(generalized_distance)` remains the exact
algebraic path factor; it must not be relabeled as a released hyperbolic
efficiency score.
:::

The formulation and its profitability relationships follow
[Chavas and Cox (1999)](https://doi.org/10.1002/j.2325-8012.1999.tb00248.x).
The return-to-dollar decomposition is developed by
[Zofío and Prieto (2006)](https://doi.org/10.1007/s10108-006-9004-0).

## A five-organization example

The bundled `revenue_5x2` dataset is also the fixed public example used to
validate the implementation:

```python
from deapack import DEAData, GDF, load_dataset

frame = load_dataset("revenue_5x2")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["input_1", "input_2"],
    outputs=["output_1", "output_2"],
)

crs = GDF(alpha=0.5, returns_to_scale="crs").fit(data)
vrs = GDF(alpha=0.5, returns_to_scale="vrs").fit(data)

crs.summary()[[
    "dmu_id",
    "generalized_distance",
    "resource_commitment",
    "service_commitment",
    "is_gdf_efficient",
    "is_efficient",
]]
```

At the balanced path, the CRS generalized distances are

$$
\left(\frac7{11},\,1,\,1,\,\frac14,\,\frac6{23}\right),
$$

and the VRS distances are

$$
\left(
\frac{13-2\sqrt{30}}3,\,
1,\,
1,\,
\frac14,\,
\frac9{25}
\right).
$$

These values reproduce the five-unit
[fixed DataEnvelopmentAnalysis.jl oracle](https://github.com/javierbarbero/DataEnvelopmentAnalysis.jl/blob/ca17532cd4de4e47d159cee563c05d9a0db6a61c/test/deaprofitability.jl#L4-L45)
associated with the Zofío--Prieto example.

Unit 4 has $x=(4,8)$, $y=(5,4)$, and $\delta=1/4$. Under the balanced
path, resources are halved and services are doubled:

$$
x^{path}=(2,4),\qquad y^{path}=(10,8).
$$

At the same CRS score, `alpha=0` instead describes a 75 percent resource
saving while services are protected; `alpha=1` describes a fourfold service
level at the current resource budget. These are three operating
counterfactuals for the same CRS productivity gap, not three contradictory
performance assessments or three management commitments.

## Why CRS and VRS behave differently

Under the ordinary CRS cone, the score equals the CRS input-radial efficiency
for every value of $\alpha$. Changing $\alpha$ changes the resource and
service factors and rescales the peer activity, but it does not change the
total productivity gap. `crs_score_equivalence` records this property.

Under VRS, reference intensities must sum to one. The reference activity
cannot be freely rescaled to offset a different path. Consequently,
$\alpha$ may change both the score and the comparator mix. For unit 1 in
the example, the VRS scores at `alpha=0`, `0.5`, and `1` are $0.750$,
approximately $0.68185$, and $7/9$. The corresponding score-stage mixes
of units 2 and 3 are 12.5/87.5 percent, approximately 23.86/76.14 percent,
and 50/50 percent.

This is economically useful. CRS asks about productivity after permitting
proportional replication of an operating recipe. VRS asks what can be
delivered at observed organizational scales. The two assumptions answer
different planning questions.

## GDF is not an additive DDF alias

A directional distance function describes an additive change path,

$$
(x_o-\beta g^x,\;y_o+\beta g^y),
$$

whose direction has the units of the underlying variables. GDF describes a
multiplicative proportional path,

$$
\left(\delta^{1-\alpha}x_o,\;\delta^{-\alpha}y_o\right).
$$

The first is natural when a programme is stated as quantities, such as saving
ten staff-hours while adding five cases. The second is natural when management
or the analyst states a proportional turnaround, such as assessing a
percentage resource reduction together with a percentage service increase.
They can reuse sparse technology matrices, but their scores, paths, and
economic interpretations remain distinct.

## Path point, peer activity, and strong target

Three columns in the long target table must not be treated as synonyms:

- `path_target` is the algebraic point on the declared proportional
  adjustment path;
- `phase_one_reference_activity` is the peer operation that demonstrates
  that the fitted path point is attainable; and
- `target` is the peer operation after the optional row-scaled slack
  completion identifies additional variable-specific opportunities.

Likewise, intensities carry either
`stage="phase_one_reference_activity"` or
`stage="slack_completed_target"`. The completed target is one strongly
efficient comparator under the implemented secondary objective, not a claim
that management has a unique best transition plan.

`is_gdf_efficient` asks whether $\delta$ is numerically one.
`is_efficient` is stricter: it is reported only when the fitted target
completion certifies that no remaining Pareto--Koopmans improvement is
available. With `compute_slacks=False`, the GDF score remains defined but the
generic strong-efficiency status is missing.

With `compute_slacks=True`, GDF composes the released
`evaluation.target_completion.pareto_koopmans` protocol and records the
composition in result metadata. The protocol is not a standalone callable
model. It preserves the fitted path score, then asks whether any ordinary
input could still be reduced separately or any desirable output could still
be increased separately. A successful completion selects a strongly
efficient operation under the same convex technology.

```python
vrs.metadata["target_completion_id"]
# "evaluation.target_completion.pareto_koopmans"
```

The row-scaled slack objective is DEAPack's declared unit-stable
target-selection policy. It is not asserted to be the source literature's
only admissible secondary rule. The selected target need not be unique,
closest, least-cost, or managerially preferred, and it carries no causal
interpretation.

## Numerical strategy and diagnostics

The base installation uses SciPy/HiGHS:

- `alpha=0` is solved exactly as input-radial DEA;
- `alpha=1` is solved exactly as output-radial DEA and reported reciprocally;
- every CRS value of `alpha` uses an exact input-radial reduction; and
- an interior VRS path uses monotone fixed-$\delta$ LP feasibility
  checks with geometric bisection.

For an interior VRS fit, the summary retains `search_lower_bound`,
`search_upper_bound`, `search_absolute_gap`, `search_iterations`,
`feasibility_solves`, and `search_converged`. The returned score is the
certified feasible upper endpoint. If the requested interval is not certified,
the status remains visible instead of silently presenting an uncertain score
as exact.

Technology rows and slack variables are scaled internally for numerical
stability. Reported quantities, slacks, and dual-free targets are converted
back to their original units. `max_scaled_slack` supports comparisons across
variables; `max_slack` remains useful within a named unit system.

## Admissible domain

The public leaf currently supports:

- finite, nonnegative inputs and desirable outputs;
- at least one positive input and one positive output for every observation;
- CRS or VRS convex envelopment;
- global and the implemented custom reference policies; and
- structural zeros when the selected reference activities can honor every
  zero-input commitment and supply every required positive output.

It rejects undesirable outputs because their disposability and joint
production require an explicit environmental technology. It also rejects
NIRS/NDRS until a separate generalized-distance derivation is registered.
With an external reference, scores are retained without clipping and
membership and efficiency flags remain nullable when the fitted comparison
does not justify them.

The reusable Pareto--Koopmans protocol is certified here only for ordinary
adjustable inputs and desirable outputs in the supported convex free-disposal
technology. Weakly disposable quantities, fixed or non-discretionary
variables, and non-convex technologies require a different dominance and
target-selection contract; those protocol extensions are deferred to the
next version.

```{autosummary}
GeneralizedDistanceDEA
ChavasCoxGDF
GDF
```
