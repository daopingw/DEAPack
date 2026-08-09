# Directional distance function

```{eval-rst}
.. currentmodule:: deapack
```

`DirectionalDistanceDEA` maximizes $\beta$ such that

$$
(x_o-\beta g^x,\ y_o+\beta g^y)\in\mathcal{T}.
$$

Direction magnitudes must be nonnegative. The model always interprets a
positive input direction as contraction and a positive desirable-output
direction as expansion.

Economically, the direction is an analyst-declared operating counterfactual:
it specifies the package of resource savings and output gains represented by
one unit of $\beta$. The fitted $\beta$ is the attainable amount of that
package under the declared technology. A direction should be described as a
policy target, managerial commitment, or engineering requirement only when
the study has institutional evidence that the relevant decision maker adopted
it as such.

## Basic use

```python
from deapack import DDF, DEAData, load_dataset

frame = load_dataset("slacks_2x2")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["labor", "capital"],
    outputs=["service", "quality"],
)

result = DDF(
    input_direction="observed",
    output_direction="observed",
    returns_to_scale="vrs",
).fit(data)
```

`DDF` is the discoverability alias for `DirectionalDistanceDEA`.

## Direction specifications

Each role accepts:

- `"observed"`: use each evaluated observation;
- `"mean"`: broadcast the full dataset's column means as one common direction;
- `"ones"`: one in every component;
- `"zeros"`: require no directional change in that role during phase one; the
  observed quantity remains a protected input cap or output floor;
- a scalar or one-dimensional vector shared by all observations;
- a variable-name mapping;
- an `(n_observations, n_variables)` matrix of observation-specific values.

At least one input or output component must be positive for every evaluated
observation. Negative direction values are rejected because signs belong to
the model convention, not to user-supplied magnitudes.

The common `"mean"` direction is useful for additive productivity comparisons
that need one stable cardinal scale across observations and periods. An
`"observed"` direction expresses the counterfactual relative to each unit's
own operating scale, whereas `"ones"` assigns one measurement unit to each
component. These choices change the estimand; they are not neutral plotting
options. Custom mappings and arrays should therefore be accompanied by their
economic rationale and provenance.

## Keep the operating programme and comparison rights distinct

`DirectionalDistanceDEA` and `DDF` accept an observation-specific
`PeerEligibility` declaration. `ReferenceSpec` first determines the base
information available to observation $o$; the eligibility rule then limits
that base to organizations with declared comparison rights. The effective
population is the exact intersection. The direction still states the resource
savings and service gains represented by one unit of $\beta$; admitting or
excluding a candidate does not silently rewrite that operating programme.

The summary exposes `base_reference_size`, effective `reference_size`, and
`self_in_reference`, and result metadata retains the compact rule provenance.
No self row is inserted automatically. If the admitted evidence cannot support
the evaluated operation and its declared programme, the observation is
reported outside the reference technology and semantic claims are withheld.
See {doc}`../user-guide/reference-sets` for construction, audit export, and the
boundary between this generic policy and named categorical or specialist DEA
models.

## Three observed-direction contracts

Holding the data, eligible references, and VRS technology fixed does not make
different directions interchangeable. The following calls declare three
different first-stage operating contracts:

```python
programmes = {
    "save_resources": DDF(
        input_direction="observed",
        output_direction="zeros",
        returns_to_scale="vrs",
    ),
    "expand_services": DDF(
        input_direction="zeros",
        output_direction="observed",
        returns_to_scale="vrs",
    ),
    "improve_jointly": DDF(
        input_direction="observed",
        output_direction="observed",
        returns_to_scale="vrs",
    ),
}

results = {name: model.fit(data) for name, model in programmes.items()}
```

The first programme requires proportional resource saving while protecting
the recorded service commitments. The second requires proportional service
addition without declaring a resource saving; its input inequalities still
protect the recorded resource budget. The third requires both sides of the
package to be feasible together. A zero direction means that the first-stage
package requires no change in that role. It does not rule out an additional
resource saving or service gain during optional slack completion.

The three native `beta` values must remain attached to their directions. Even
when every direction uses observed quantities, a larger beta for one contract
is not evidence that the organization is generically less efficient, that the
contract is economically preferable, or that its changes are easier to
implement.

## Result semantics

- `score = distance = beta`: native attainable improvement potential for the
  declared direction and technology;
- `efficiency = 1 / (1 + beta)`: compatibility field containing a convenience
  display transform for nonnegative distances, not a general efficiency
  measure;
- `is_directionally_efficient`: whether $\beta=0$;
- `is_efficient`: whether $\beta=0$ and all second-phase slacks are zero.

An `optimal` backend label is not by itself a release certificate. The primary
programme is row-scaled for numerical stability and independently checks
primal rows, bounds, the reported objective, row and bound marginals, KKT
conditions, complementarity, strong duality, the directional production
account, and the RTS restriction. Only then are `score`, `distance`, and the
compatibility transformation released with `score_valid=True`.

Validity is claim-specific. `completion_valid`, `target_valid`, `peer_valid`,
and `dual_valid` state whether the corresponding secondary programme or
result table can be used; their companion status fields explain a withheld
claim. A requested slack completion that fails certification does not erase a
certified phase-one $\beta$, but its targets, slacks, completion peers, and
associated semantic claims are not published. Peer intensities are checked
again after the reporting threshold is applied, and duals are released only
when the complete input, output, and non-CRS scale account is available.
Diagnostics retain the raw backend status and certificate residuals. These
checks are postsolve reconstructions and add no optimization task.

The target table adds `direction` and `directional_change` columns. With
`compute_slacks=False`, strong efficiency and targets are intentionally
missing. A reported target is a benchmark-feasible operating plan under the
analyst's counterfactual, not automatically a recommendation or an authorized
commitment.

When slack completion is requested, the second stage holds the optimal
$\beta$ fixed and maximizes a row-scaled slack sum. The physical slacks remain
in the original units, while `scaled_slack` and `max_scaled_slack` put each
quantity relative to a positive scale from its evaluated and reference
values. This prevents a change from tonnes to kilograms from changing the
selected target or the strong-efficiency classification. It is a target
selection and reporting policy layered on the directional score, not a new
definition of the phase-one DDF.

Each published slack row also retains that positive denominator as
`slack_scale`, so downstream validation can reconstruct
`scaled_slack = slack / slack_scale` without access to private solver state.

This composition has the released protocol identity
`evaluation.target_completion.pareto_koopmans`. The protocol is not an
independently callable model: `DirectionalDistanceDEA` composes it through
`compute_slacks=True` and records that composition in result metadata.
Economically, phase two asks whether a resource can still be saved on its own
or a desirable service can still be expanded on its own after no further
amount of the declared direction package is attainable.

```python
result.metadata["target_completion_id"]
# "evaluation.target_completion.pareto_koopmans"
```

When completion succeeds, the selected target is strongly efficient under the
same ordinary convex input/desirable-output technology. It is one optimum
under DEAPack's row-scaled secondary objective, not a claim that the source
literature supplies one uniquely required selection rule. The result does not
certify the target as closest, least-cost, or uniquely preferred, and it does
not estimate whether management caused the observed gap.

`allow_negative_distance=True` reserves negative distances for explicit
cross-technology work. When $\beta<0$, standardized efficiency and efficiency
classification are missing; the native signed distance remains the quantity
to interpret. A finite signed value is still published only after the same LP
and production-account checks pass. Result plots then use a zero-centred signed label: positive
means an attainable improvement remains, zero is the selected-reference
frontier, and negative means the assessed plan lies outside that reference
technology. They do not rank a more negative value as better.

## Operating-plan visualization

A certified nonnegative ordinary DDF result with slack completion can expose
the existing variable-level `improvement` view:

```python
figure = result.plot(kind="improvement", dmu_id="E")
```

For every input and desirable output, the figure separates the observed
quantity, the target implied by the declared move `beta * direction`, and the
final target after any variable-specific completion slack. Quantities retain
their original units and do not share a synthetic physical axis. This view
requires the exact `static.directional_distance` identity, both certified
solve phases, the completed target account, and reconstructable public target
and slack rows. It reads only the fitted `DEAResult` and adds no solver call.

The figure does not require peer or dual publication because it displays
neither claim. It also does not turn the selected target into a causal
diagnosis, implementation order, unique optimum, or least-cost plan. Use the
generic `performance` plot when the analytical question is instead the
cross-organization distribution of native beta values.

## Current boundary

This class supports inputs and desirable outputs. Undesirable outputs require
an environmental DDF with an explicit disposability technology; they are not
silently treated as ordinary outputs.

The reusable Pareto--Koopmans completion protocol is narrower than the full
environmental and special-data method atlas. Its current certificate covers
ordinary adjustable inputs and desirable outputs under a compatible convex
free-disposal technology. Extending that protocol identity to weakly disposable
quantities, fixed or non-discretionary variables, or non-convex technologies
is deferred to the next version.

The repository's analytical certificate covers a deliberately narrower
domain: a self-inclusive cross-sectional global reference, nonnegative
distance policy, three observed-direction programmes, all four supported
returns-to-scale assumptions, and separately compiled small dense fixtures.
It does not certify negative distances, custom or panel reference policies,
undesirable outputs, every direction resolver, unique peers, or inference.
See `specs/oracles/directional-distance-analytical.md` for the exact cases.

```{autosummary}
DirectionalDistanceDEA
DDF
```
