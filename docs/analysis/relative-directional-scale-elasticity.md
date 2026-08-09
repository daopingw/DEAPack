# Relative-directional scale elasticity

```{eval-rst}
.. currentmodule:: deapack
```

{func}`relative_directional_scale_elasticity` asks a local operating question:
near a selected efficient VRS plan, how strongly can a declared service mix
respond when a declared resource mix changes by one percent on average?

The method is useful when proportional expansion is too restrictive. A
research organization may contemplate similar percentage increases in staff
and expenditure but compare different combinations of funding, publications,
and patents. A hospital may compare a staffing change that protects emergency
activity more strongly than elective activity. These are different
counterfactuals even when the average resource change is identical.

The function implements the relative directional scale elasticity of [Ren et
al. (2021)](https://doi.org/10.1051/ro/2021131). It is not a directional
distance score and it is not a recommendation to expand or contract.

## Direction contract

For a selected Pareto-efficient target $(\widehat x_o,\widehat y_o)$, the declared local rates
are

$$
x_i(t)=(1+\omega_i t)\widehat x_{io},
\qquad
y_r(\beta)=(1+\delta_r\beta)\widehat y_{ro}.
$$

Both vectors must be explicit, nonnegative, and already mean-one normalized:

$$
\sum_i\omega_i=m,\qquad \sum_r\delta_r=s.
$$

DEAPack validates this normalization and never silently rescales a direction.
Use exact variable-name mappings when column order should not carry meaning.

A direction is recorded as a **declared operating counterfactual**. It should
be described as a management preference only when the study documents that
the responsible decision-makers elicited and adopted it. Otherwise report it
as an authorized policy scenario, a literature-prescribed scenario, or an
analyst-defined sensitivity scenario.

## Example from the defining article

```python
from deapack import (
    DEAData,
    dataset_info,
    load_dataset,
    relative_directional_scale_elasticity,
)

frame = load_dataset("ren_cas_directional_scale")
roles = dataset_info("ren_cas_directional_scale").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = relative_directional_scale_elasticity(
    data,
    input_relative_direction={
        "staff": 1.0,
        "research_expenditure": 1.0,
    },
    output_relative_direction={
        "external_funding": 0.75,
        "high_sci_publications": 0.75,
        "granted_patents": 1.50,
    },
)

result.summary().set_index("dmu_id").loc[
    "DMU 2",
    [
        "scale_elasticity_right",
        "scale_elasticity_left",
        "scale_up_response",
        "scale_down_response",
    ],
]
```

For DMU 2, the right and left elasticities are approximately $1.4127$ and
$1.4592$, reproducing the first scenario in Table 4 of the article. Near the
selected plan, a one-percent average increase in the declared resource mix is
associated with more than one-percent attainable growth in the declared
service mix. This technical response does not say that the patent-weighted
scenario is more valuable than another scenario.

The bundled dataset contains all 16 observations in the article's Table 1.
Its zero-patent observation is deliberately retained. A zero target makes that
particular relative-rate component inactive; it does not remove the
organization from the analysis. If an entire input or output directional rate
base is nonpositive, the affected row fails closed.

## Projection and endpoints

The method is defined at an efficient plan. For an inefficient observation,
`projection_orientation` selects an input- or output-radial VRS projection,
and a slack-completion phase moves the result to a Pareto-efficient target.
The directional elasticities belong to that stored target. They are not
claimed to be invariant across alternative efficient projections.

At the selected target, DEAPack solves the Ren et al. normalized support
problems

$$
\epsilon^+
=
\min v^\top(\omega\odot \widehat x_o),
\qquad
\epsilon^-
=
\max v^\top(\omega\odot \widehat x_o),
$$

subject to

$$
v^\top x_j-u^\top y_j+u_0\geq0,\qquad
v^\top \widehat x_o-u^\top \widehat y_o+u_0=0,\qquad
u^\top(\delta\odot \widehat y_o)=1.
$$

The right endpoint $\epsilon^+$ is the local scale-up response. The left
endpoint $\epsilon^-$ is the local scale-down response, with
$\epsilon^+\leq\epsilon^-$ when both are finite.

For either feasible side:

- a value above one is `more_than_proportional`;
- a value equal to one within `rts_tolerance` is `proportional`;
- a value below one is `less_than_proportional`.

An infinite left endpoint is stored separately from feasibility:
`scale_down_perturbation_exists=False` and
`scale_elasticity_left_is_extended=True`. It marks a local boundary, not
infinite organizational productivity.

## Exact radial reduction

When both relative direction vectors contain only ones, the operating
question becomes proportional. With the same VRS reference set, projection
orientation, selected target, slack-completion rule, solver, and tolerances,
the two endpoints reduce exactly to those from {func}`scale_elasticity`.
This is tested in both input- and output-projection modes.

## Result contract

The summary includes:

- `scale_elasticity_right` and `scale_elasticity_left`;
- `scale_up_perturbation_exists` and
  `scale_down_perturbation_exists`;
- `scale_elasticity_right_is_extended` and
  `scale_elasticity_left_is_extended`;
- `scale_up_response` and `scale_down_response`;
- `directional_rts_right` and `directional_rts_left`;
- projection status, projection selection, inactive direction components,
  `projection_score_valid`, `projection_completion_valid`,
  `projection_target_valid`, and separate endpoint solver statuses.

`result.targets` retains the selected efficient plan, each declared relative
direction, its directional rate base, and whether the component is active.
`result.multipliers` retains the right and left normalized supports.
`result.diagnostics` separates projection, slack-completion, and endpoint
solver evidence.

Both endpoint programmes require all three projection-validity fields to be
true. A retained target row is not sufficient when the primary score or its
slack completion failed certification; the row remains diagnostic and the
endpoint solves are skipped.

The generic `score`, `efficiency`, `distance`, and `is_efficient` fields are
missing because this operator measures a local response at an efficient plan;
it does not issue another efficiency score.

## Scope

- The public leaf uses convex VRS technology, ordinary free disposal, and
  inputs plus desirable outputs.
- Directions are relative percentage rates, not physical-unit DDF
  directions.
- The operator is deterministic and local. It does not model prices, demand,
  quasi-fixed adjustment, risk, or causal effects.
- An expansion decision requires those additional economic and institutional
  considerations even when the scale-up response exceeds one.

```{autosummary}
relative_directional_scale_elasticity
```
