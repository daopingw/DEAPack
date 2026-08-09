# Conventional directional distance on a by-production technology

```{eval-rst}
.. currentmodule:: deapack
```

`ByProductionDirectionalDistanceDEA` applies a conventional
output-directional distance to the two-subtechnology account of Murty,
Russell, and Levkoff (2012):

$$
\mathcal{T}_{BP}=\mathcal{T}_1\cap\mathcal{T}_2,
$$

$$
\mathcal{T}_1:\ X\lambda\le x,\quad Y\lambda\ge y,
$$

$$
\mathcal{T}_2:\ X^p\mu\ge x^p,\quad B\mu\le b.
$$

Here $\lambda,\mu\ge0$. In the residual relation, $B\mu\le b$ is paired
with $X^p\mu\ge x^p$; this pair represents costly disposal conditional on the
declared residual-generating inputs. It is not an explicit treatment,
abatement-output, or residual-control technology.

`ByProductionDDF` is its discoverability alias.

The source studies BP-DDF to expose two limitations: the minimum aggregation
can report zero while one component retains improvement potential, and the
limiting component can depend strongly on the direction. The authors propose
the distinct by-production FGL index in response. Reproducing BP-DDF
therefore establishes fidelity to their diagnostic analysis; it does not
identify BP-DDF as their preferred measure.

## Data contract

Declare undesirable residuals and the subset of ordinary inputs that triggers
their generation:

```python
from deapack import ByProductionDDF, DEAData, dataset_info, load_dataset

frame = load_dataset("by_production_component_bottleneck")
roles = dataset_info("by_production_component_bottleneck").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    polluting_inputs=roles["polluting_inputs"],
    outputs=roles["outputs"],
    bad_outputs=roles["bad_outputs"],
)

result = ByProductionDDF().fit(data)
```

Every polluting input must also be an ordinary input. It remains in $X$ for
intended production and additionally enters $X^p$ for residual generation.
The model never infers this role from a column name.

## Distances, directions, and efficiency states

The model solves independent sparse LPs for

$$
\beta_o^1=\sup\{\beta:X\lambda\le x_o,\quad
Y\lambda\ge y_o+\beta g^y\}
$$

and

$$
\beta_o^2=\sup\{\beta:X^p\mu\ge x_o^p,\quad
B\mu\le b_o-\beta g^b\}.
$$

The native joint distance is
$\beta_o^{BP}=\min(\beta_o^1,\beta_o^2)$. The result stores it in `score` and
`distance`; larger values mean more unrealized joint improvement.
`efficiency=1/(1+distance)` is a DEAPack display transform, not a
transformation defined in the source.

The source holds one nonnegative direction fixed across all observations and
illustrates `output_direction="ones"` together with
`bad_output_direction="ones"`. Those are the package defaults. `"mean"`,
a scalar/vector, and a variable-name mapping also produce a global fixed
direction. `"observed"` and an observation-by-variable matrix are supported
package extensions; they do not inherit the fixed-direction source
reproduction unless their realized rows are identical.

Every observation must have at least one positive desirable-output direction
component and at least one positive bad-output direction component; an empty
component programme cannot enter the minimum account.

`is_directionally_efficient` tests whether the joint distance is zero. The
summary identifies `limiting_subtechnology` and retains both component
distances. A zero joint distance does not rule out potential in the
non-limiting component or all residual input/output slacks. The generic
Pareto--Koopmans field `is_efficient` therefore remains missing. Target rows
contain both the joint target and the relevant `component_target`.

Reference appraisal is recorded explicitly. `self_in_reference` reports the
structural inclusion of the assessed row. For an external row, certified
nonnegative intended- and residual-component accounts also certify
`is_within_reference_technology=True`: setting beta to zero only relaxes both
component programmes. No extra membership LP is needed. An infeasible
component marks the row outside the intersection; an uncertified failure leaves
membership missing. `membership_status` records which route supplied the
claim, and fitted metadata distinguishes self, mixed, and wholly external
componentwise appraisal.

## Source-compatible defaults and exact oracle

The source-qualified runtime profile is:

```python
model = ByProductionDDF(
    output_direction="ones",
    bad_output_direction="ones",
    intended_returns_to_scale="crs",
    residual_returns_to_scale="crs",
    reference="auto",
)
```

On a cross-section, `reference="auto"` resolves to the complete
self-inclusive sample. Applied to the packaged fixture loaded above, this
profile reproduces equation (5.6):

```python
source_result = model.fit(data)
source_result.summary()[[
    "dmu_id",
    "intended_distance",
    "environmental_distance",
    "distance",
]]
```

The exact intended-production, environmental, and joint vectors are

$$
\left(0,\frac12,\frac43,1,2\right),\qquad
(3,0,1,3,1),\qquad
(0,0,1,1,1).
$$

The source prints the component expressions for DMUs 1--3; the final two
values follow exactly from the same five observations. An independent dense
compiler checks all five without using the production LP builder.

Runtime metadata records `source_profile`, `source_profile_matches`,
`source_profile_mismatches`, `direction_scope`, and
`efficiency_transform_source`. CRS in both relations, a fixed direction, and
one full self-inclusive cross-section are required for the 2012 source
profile. VRS/NIRS/NDRS, observation-varying directions, and
temporal/non-global references remain labelled extensions.

## Two intensity systems

Peer rows and diagnostics carry `subtechnology`, either
`intended_production` or `residual_generation`. The two intensity vectors are
not forced to match. Returns to scale are explicit and independent:

```python
model = ByProductionDDF(
    intended_returns_to_scale="vrs",
    residual_returns_to_scale="crs",
)
```

This is a sensitivity extension, not the source CRS profile.

## Certified publication contract

Each observation requires exactly two primary LPs: one for intended production
and one for residual generation. Quantity rows are independently scaled by
their input, desirable-output, polluting-input, and bad-output accounts before
optimization. Scaling changes numerical conditioning, not the declared
technology or the reported quantity units.

DEAPack does not publish a joint result merely because both backends return
`optimal`. For each already-solved component it independently checks primal
feasibility, bounds, the reported objective, KKT conditions, complementarity,
strong duality, returns to scale, and the original intended- or
residual-generation quantity account. It repeats the economic account after
small-value cleanup. Both component scores must pass before the minimum,
component distances, directional targets, or limiting-account label are
released.

The result then applies two independent reporting gates:

- `peer_valid` requires both component accounts to remain feasible after the
  reporting threshold is applied to their separate intensity vectors;
- `dual_valid` requires complete, finite row marginals for both components.
  Quantity-row marginals are converted back from scaled rows to the original
  quantity units. They remain solver constraint marginals: for the stored
  residual lower-account row $-X^p\mu\le -x^p$, the marginal is with respect
  to that signed right-hand side and is not automatically a market price or
  marginal abatement cost.

```python
result.summary()[[
    "dmu_id",
    "score_valid",
    "target_valid",
    "peer_valid",
    "dual_valid",
    "intended_distance",
    "environmental_distance",
    "distance",
    "limiting_subtechnology",
]]
```

Diagnostics retain the raw backend status and component certificate residuals
even when a semantic result is withheld. Certification adds no optimization
task: metadata reports `solver_calls=2*n_dmus` for a single common reference
plan and `additional_solver_calls=0`.

## Scope

BP-DDF can reach a weakly efficient joint projection when one component is
already limiting. It is not the by-production FGL index or BP-SBM; those use
different aggregations and are separate measures. This implementation does
not model an explicit abatement output or impose material-balance
coefficients.

Component peers and targets are solver-selected and need not be unique.
Neither a joint target nor a component target is an engineering design,
causal estimate, welfare optimum, or claim of implementation feasibility. A
named extension without an obtainable defining source and independent oracle
remains `deferred_to_next_version`.

```{autosummary}
ByProductionDirectionalDistanceDEA
ByProductionDDF
```
