# Ray directional super-efficiency

```{eval-rst}
.. currentmodule:: deapack
```

`RayDirectionalSuperEfficiency` implements Ray's VRS, observed-direction
leave-one-out programme. `NerloveLuenbergerSuperEfficiency` is its exact
source-name alias. Both names fit the canonical method
`evaluation.super.directional.ray_2008`.

The method measures how much joint operating concession the remaining peers
need before they can replace an evaluated observation. It uses one common
signed proportional change: positive `beta` represents simultaneous input
saving and desirable-output expansion, while negative `beta` allows all
inputs to rise and all desirable outputs to fall by the corresponding
proportion of their observed values. The reported scalar is a peer-replacement
exposure measure, not technical efficiency above 100 percent.

This method is distinct from generic directional-distance DEA, the deferred
Andersen--Petersen radial prototype, and Tone's variable-specific super-SBM.

## Supported source surface

The public class fixes the choices that define Ray's source method:

| Dimension | Public behavior |
|---|---|
| Technology | convex VRS envelopment with ordinary free disposal |
| Evaluation | remove exactly the focal observation from its base reference population |
| Direction | observed inputs and observed desirable outputs; not user-configurable |
| Inputs | every component must be strictly positive |
| Outputs | nonnegative desirable outputs with a positive row aggregate |
| Undesirable outputs | rejected |
| Native distance | unrestricted signed `beta` |
| Native score | `nl_super_efficiency = 1 - beta` |
| Target completion | none; source phase-one boundary and peer activity are retained separately |

CRS, NIRS, NDRS, arbitrary or range directions, input-only or output-only
directions, zero repairs, undesirable-output technologies, and modified
feasibility programmes are not constructor switches. They are different
models and are not inferred by this class.

## Source programme

For evaluated observation $o$, let $X_{-o}$ and $Y_{-o}$ contain the rows in
its base reference population after exact self-exclusion. The fitted problem
is

$$
\begin{aligned}
\max_{\lambda,\beta}\quad &\beta\\
\text{subject to}\quad
&Y_{-o}^{\mathsf T}\lambda-\beta y_o\geq y_o,\\
&X_{-o}^{\mathsf T}\lambda+\beta x_o\leq x_o,\\
&\mathbf 1^{\mathsf T}\lambda=1,\\
&\lambda\geq0,\qquad\beta\text{ unrestricted}.
\end{aligned}
$$

The source directional boundary is

$$
x_o^D=(1-\beta_o)x_o,
\qquad
y_o^D=(1+\beta_o)y_o,
$$

and the reported Nerlove--Luenberger score is

$$
NL_o=1-\beta_o.
$$

`NL > 1` means that the remaining peers need a larger joint concession to
replace the observed record. `NL = 1` means that they can reach the observed
record without that concession. `NL < 1` means that a simultaneous resource
reduction and service increase remains available even after the focal row is
excluded.

## Fit the project-authored stress example

```python
from deapack import (
    DEAData,
    RayDirectionalSuperEfficiency,
    dataset_info,
    load_dataset,
)

frame = load_dataset("directional_super_multivariate_stress")
roles = dataset_info("directional_super_multivariate_stress").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = RayDirectionalSuperEfficiency().fit(data)
result.summary()[
    [
        "dmu_id",
        "beta",
        "nl_super_efficiency",
        "is_super_efficient",
        "score_valid",
        "solver_status",
    ]
]
```

The neutral multivariate fixture includes ordinary certified rows and a
projection-domain stress row. Tests check the signed identity
`nl_super_efficiency == 1 - beta`, exact self-exclusion, VRS convexity,
boundary feasibility, and fail-closed validity flags. No numerical table from
Ray's application is distributed with the package.

The default plot uses the native score and its declared validity contract:

```python
result.plot(
    kind="performance",
    metric="nl_super_efficiency",
    theme="deapack",
)
```

```{figure} ../_static/figures/directional-super-stress-result.svg
:name: docs-fig-ray-directional-super-result
:alt: Project-authored multivariate stress cases ranked by Nerlove--Luenberger peer-replacement exposure
:width: 92%

The vertical reference at one means that peers reach the observed operation
without a joint concession. The result renderer does not relabel the values as
efficiency percentages.
```

## Result contract

The main result tables keep the scalar, operating account, and numerical
evidence separate:

| Result surface | Contents |
|---|---|
| `summary()` | `beta`, `nl_super_efficiency`, validity flags, directional and super-efficiency classifications, reference sizes, solver state, and failure reason |
| `targets` | the source boundary $((1-\beta)x,(1+\beta)y)$ and the selected peer activity |
| `intensities` | one solver-selected VRS peer mixture after exact self-exclusion |
| `slacks` | input and output feasibility surplus between peer activity and the source boundary; not included in the native score |
| `diagnostics` | scaled residuals, primal--dual certificate evidence, and phase status |

`score`, `efficiency`, and `nl_super_efficiency` contain the same source
scalar for compatibility and discovery. Generic `is_efficient` remains
missing because this value is not an ordinary technical-efficiency
percentage. Use `is_directionally_efficient` and `is_super_efficient` for the
source-specific classifications.

Targets use the unthresholded solver intensities. `peer_tolerance` controls
only which small intensities are displayed; changing it does not change the
score, boundary, or feasibility accounting. A selected mixture can be
non-unique, so the result does not claim a unique operating prescription.

## Negative-output boundary and failure policy

When `beta < -1`, equivalently `NL > 2`, the source output boundary
$(1+\beta)y_o$ is negative for every positive desirable output. Ray retains
the scalar but identifies the resulting projection as conceptually
problematic. DEAPack therefore returns the certified raw values with:

```text
source_projection_nonnegative = False
score_valid = False
ranking_value_valid = True
target_valid = False
solver_status = "optimal"
```

The distinction is deliberate: the LP optimum is auditable, but its boundary
cannot be presented as a meaningful service plan. Package-native plots and
reports use `score_valid` and exclude the row from substantive rankings while
retaining it in the diagnostic layer. The value is neither clipped to two nor
converted into a solver failure.

All other solver and certificate failures close the result row. The class
does not add epsilon to a zero input, translate data, change returns to scale,
relax self-exclusion, or switch to a different super-efficiency method.

## Reference specifications

Ray's application is a global cross-section. DEAPack also accepts its standard
`ReferenceSpec` policies as transparent framework extensions. For every focal
row, the declared base reference set must contain that row before exclusion,
and at least one peer must remain afterward. Panel or custom policies change
the comparison population; they do not change the fixed VRS source equation
inside each fit.

The defining-source boundary, project-case verification, and non-equivalence
claims are recorded in the
[Ray source protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/ray_2008_directional_super_efficiency.md).
