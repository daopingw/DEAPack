# Range directional measure for signed accounts

```{eval-rst}
.. currentmodule:: deapack
```

`RangeDirectionalDEA` implements the Portela--Thanassoulis--Simpson (2004)
range directional measure (RDM). Its concise alias is `RDM`; the canonical
method ID is
`static.range_directional.portela_thanassoulis_simpson_2004`.

The model accepts finite signed inputs and desirable outputs while preserving
their economic roles:

- less input is preferred; and
- more desirable output is preferred.

A negative desirable-output observation is not an undesirable output.
Pollution or another burden that management seeks to reduce requires an
environmental model.

## Performance question

For focal observation $o$ and its exact comparison population $J$, define

$$
x_i^{\min}=\min_{j\in J}x_{ij},
\qquad
y_r^{\max}=\max_{j\in J}y_{rj},
$$

and the remaining observed improvement ranges

$$
R^x_{io}=x_{io}-x_i^{\min},
\qquad
R^y_{ro}=y_r^{\max}-y_{ro}.
$$

The non-oriented source programme asks what common share $\beta_o$ of these
input-saving and output-growth rooms is jointly feasible:

$$
\begin{aligned}
\max_{\beta_o,\lambda}\quad &\beta_o\\
\text{subject to}\quad
&X\lambda\leq x_o-\beta_oR^x_o,\\
&Y\lambda\geq y_o+\beta_oR^y_o,\\
&\mathbf 1^\mathsf T\lambda=1,\\
&\lambda\geq0,\qquad\beta_o\geq0.
\end{aligned}
$$

`orientation="input"` sets the output range direction to zero.
`orientation="output"` sets the input range direction to zero. The default
is `"non-oriented"`.

The native `score`, `distance`, and `beta` fields all report $\beta_o$:
larger values mean that a larger share of remaining opportunity is feasible.
The higher-is-better fields are

$$
\texttt{rdm\_efficiency}
=\texttt{efficiency}
=1-\beta_o.
$$

Under the implemented self-inclusive VRS contract, with at least one positive
active direction component, both values lie in $[0,1]$.

## Exact signed-data example

```python
from deapack import DEAData, RDM, dataset_info, load_dataset

frame = load_dataset("range_directional_signed")
roles = dataset_info("range_directional_signed").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = RDM(orientation="non-oriented").fit(data)
result.summary()[
    [
        "dmu_id",
        "beta",
        "rdm_efficiency",
        "is_directionally_efficient",
        "is_efficient",
        "solver_status",
    ]
]
```

The exact result is:

| DMU | `beta` | `rdm_efficiency` | RDM status | strong-efficiency status |
|---|---:|---:|---|---|
| A | $0$ | $1$ | directionally efficient | not certified |
| B | $0$ | $1$ | directionally efficient | not certified |
| C | $2/3$ | $1/3$ | not directionally efficient | false |

For C, `RDM` selects one exact VRS witness with
$\lambda_A=2/3$ and $\lambda_B=1/3$:

```python
slacks = result.slacks.query("dmu_id == 'C'")[
    ["role", "variable", "slack"]
]
accounts = result.targets_for("C").merge(
    slacks,
    on=["role", "variable"],
)
accounts[
    [
        "role",
        "variable",
        "observed",
        "ideal",
        "direction",
        "directional_change",
        "target",
        "peer_activity",
        "slack",
    ]
]
result.peers("C")[["reference_dmu_id", "lambda"]]
```

The input and output source directional targets are $-2/3$ and $10/3$.
The peer activity has the same values in this exact case, so both residual
slacks are zero.

## Directional target, peer activity, and slack

The result deliberately keeps three quantities separate.

| Result location | Meaning |
|---|---|
| `targets["target"]` | source directional target $x_o-\beta R^x_o$ or $y_o+\beta R^y_o$ |
| `targets["peer_activity"]` | activity $X\lambda$ or $Y\lambda$ selected by the phase-one LP |
| `slacks["slack"]` | input amount by which peer activity is below the directional target, or output amount by which it is above |

`targets` also records `observed`, the coordinatewise `ideal`, `direction`,
`direction_active`, `directional_change`, and
`target_pareto_certified=False`. `peers()` reports positive reference weights
in the `lambda` column. A lambda is an activity weight, not a causal
contribution, expenditure share, or managerial instruction.

This initial leaf performs only the source phase-one programme. It has no
hidden additive or lexicographic target-completion phase. Alternative optimal
lambdas, peer activities, and residual slacks can therefore occur even when
the optimal beta is fixed.

## A perfect RDM score is not strong efficiency

`is_directionally_efficient` is true when the certified beta is zero. That
means no positive amount of the common active range-directional package is
feasible. It does not rule out improvement concentrated in one account.

Accordingly:

- a positive beta sets `is_efficient=False`;
- beta zero leaves `is_efficient` missing; and
- `target_pareto_certified` is always false in this initial leaf.

The dedicated performance-plot metric has the same conservative semantics:

```python
figure = result.plot(metric="rdm_efficiency")
figure.savefig("rdm-efficiency.png", dpi=200, bbox_inches="tight")
```

Its benchmark at one means **no positive common range-directional
improvement**. It does not draw a generic strong-efficiency classification.
Omitting `metric` may select the native beta; pass `rdm_efficiency`
explicitly for a higher-is-better management display.

## Comparison populations and reference policies

The implementation uses the same resolved reference set to:

1. calculate the input minima and output maxima;
2. construct the VRS technology; and
3. evaluate a focal observation that belongs to that set.

Every focal observation must be self-included. A custom reference policy that
omits any focal row raises `ModelSpecificationError`. Supported panel and
window policies are valid only when the resolved set for every row satisfies
this contract; extrema are recalculated within each exact resolved set.
`ReferenceSpec` does not currently construct automatic group-specific
reference sets. A justified group comparison must fit separately prefiltered
`DEAData` objects, or wait for explicit group-reference support rather than
mixing group extrema with a pooled frontier.

The coordinatewise ideal need not be a jointly feasible operating plan.
Changing the comparison population changes the ideal, the range direction,
and the performance question. Dataset screening and group construction are
therefore part of the estimand, not neutral preprocessing.

## Translation and units

Adding one finite constant to every observation in a declared input or
output leaves beta unchanged. The extremum shifts by the same constant, the
range stays fixed, and the constant cancels because VRS imposes
$\sum_j\lambda_j=1$.

This is a common-account translation property. It is not permission to shift
selected observations, apply different constants to the extrema and the
technology, or change a variable's economic meaning. The source-qualified
leaf fixes VRS; it does not expose a CRS option.

Multiplying any complete input or output column by a positive unit-conversion
factor also leaves beta and RDM efficiency unchanged. Targets, ideals,
directions, and slacks change to the new physical units.

## Zero active directions

A zero range in one account is valid: the focal observation already has the
best observed value in that coordinate. Its directional target remains at
the observed level while positive ranges in other active accounts can bound
beta.

If all direction components active under the requested orientation are zero,
beta appears in no effective constraint. The programme is mathematically
unbounded. DEAPack does not call the solver for that row and reports:

- `solver_status="unbounded_direction"`;
- missing scores and efficiency fields;
- no target, slack, peer, or dual rows; and
- a diagnostic explaining that the all-zero active direction is undefined.

Positive input room cannot rescue an all-zero output orientation, and
positive output room cannot rescue an all-zero input orientation.

## Constructor and result contract

```{autosummary}
RangeDirectionalDEA
RDM
```

`RangeDirectionalDEA` accepts:

- `orientation`: `"non-oriented"` (default), `"input"`, or `"output"`;
- `reference`: a standard `ReferenceSpec` or reference-policy string;
- `solver` and `solver_options`;
- `tolerance`; and
- `peer_tolerance`, which affects peer reporting only.

Returns to scale are fixed to VRS. There is no `compute_slacks` or
second-stage flag in this source leaf.

The summary adds:

- `score`, `distance`, and `beta`;
- `rdm_efficiency` and standardized `efficiency`;
- `is_directionally_efficient` and conservative `is_efficient`;
- `active_direction_components`;
- `score_certified` and `target_pareto_certified`;
- `max_residual_slack` and `max_certificate_violation`;
- orientation, VRS, reference size, and solver status.

Metadata records the source DOI, direction policy, exact extrema/reference
population identity, self-membership requirement, phase-one-only target
status, solver, tolerances, and solve counts. Certified targets use the full
unthresholded lambda vector; `peer_tolerance` only shortens the displayed
peer table.

## Domain and non-equivalence

The leaf rejects undesirable-output columns and non-finite data. It must not
be treated as an alias for:

- a generic DDF with an analyst-supplied direction;
- RAM's additive full-range normalization;
- inverse RDM or the later SORM;
- ordinary radial BCC after an arbitrary translation; or
- an environmental DDF that contracts burdens.

All can share numerical infrastructure without sharing an economic
estimator.

## Validation and provenance

The built-in dataset is an independent rational oracle, not the source bank
sample. Tests establish the exact beta, efficiency, lambda, target, peer
activity, and slack accounts; VRS translation invariance; positive-units
invariance; the input and output orientations; self-inclusion; all-zero
active-direction failure; solver/certificate failure closure; and
non-equivalence with generic observed-direction DDF.

Portela, Thanassoulis, and Simpson's bank-branch observations are
confidential. DEAPack cites and implements the public equations but does not
claim to reproduce that empirical dataset:
[doi:10.1057/palgrave.jors.2601768](https://doi.org/10.1057/palgrave.jors.2601768).
