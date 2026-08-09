# Malmquist--Luenberger productivity index

```{eval-rst}
.. currentmodule:: deapack
```

`MalmquistLuenbergerProductivityIndex` implements the adjacent-period
Chung--Färe--Grosskopf environmental productivity index.
`MalmquistLuenbergerDEA` is its discoverability alias. The class is a
source-qualified preset, not a configurable label for arbitrary bad-output
productivity models.

## Frozen model contract

The preset fixes:

- inputs during each distance evaluation;
- expansion of observed desirable outputs;
- contraction of observed undesirable outputs;
- CRS;
- common-factor weak disposal;
- null jointness; and
- adjacent-period technologies for the four comparison roles.

For an observation $z^\sigma=(x^\sigma,y^\sigma,b^\sigma)$ from period
$\sigma$, DEAPack stores the nonnegative direction magnitudes
$g(z^\sigma)=(0,y^\sigma,b^\sigma)$ and evaluates

$$
\left(x^\sigma,\;(1+\beta)y^\sigma,\;(1-\beta)b^\sigma\right).
$$

This is the same programme often written with the signed vector
$(0,y^\sigma,-b^\sigma)$. Do not pass negative bad-output magnitudes to the
API.

Directions are observation-scaled. The base and comparison observations use
their own $y$ and $b$ values, so the four distance tasks do not share one
common physical direction vector.

```{note}
The journal definition, output set $P(x)$, and direction $g=(y,-b)$ hold
inputs fixed, but printed equation (3.14) contains $(1-\beta)x$ in its input
row. The earlier
[Chung--Färe working paper, equation (2.14)](https://econwpa.ub.uni-muenchen.de/econ-wp/mic/papers/9511/9511002.pdf)
prints $X\lambda\leq x$. DEAPack follows the fixed-input definition and
working-paper programme. This records a source-edition inconsistency, not a
claim of a formal publisher erratum.
```

Changing the direction, bad-output technology, or returns to scale defines a
different adjacent-period environmental productivity method. The current
public class does not expose such variants under the Chung--Färe--Grosskopf
name; a separately specified method needs its own economic interpretation and
validation evidence.

## Distance roles and result fields

Let
$D_\sigma^\tau=D^\tau(z^\sigma;g(z^\sigma))$, where $\sigma$ identifies
the evaluated-plan period and $\tau$ the reference-technology period.

| Mathematical role | Result field | Evaluated period | Technology period |
|---|---|---:|---:|
| $D_t^t$ | `distance_base_on_base` | base | base |
| $D_{t+1}^t$ | `distance_comparison_on_base` | comparison | base |
| $D_t^{t+1}$ | `distance_base_on_comparison` | base | comparison |
| $D_{t+1}^{t+1}$ | `distance_comparison_on_comparison` | comparison | comparison |

The index is

$$
ML
=\left[
\frac{1+D_t^t}{1+D_{t+1}^t}
\frac{1+D_t^{t+1}}{1+D_{t+1}^{t+1}}
\right]^{1/2}
=EC_{ML}\times TC_{ML},
$$

with

$$
EC_{ML}
=\frac{1+D_t^t}{1+D_{t+1}^{t+1}}
$$

and

$$
TC_{ML}
=\left[
\frac{1+D_t^{t+1}}{1+D_t^t}
\frac{1+D_{t+1}^{t+1}}{1+D_{t+1}^t}
\right]^{1/2}.
$$

The corresponding summary fields are `productivity_change`,
`efficiency_change`, `technical_change`, and `decomposition_residual`.
Component labels are benchmark-accounting interpretations, not causal
attributions.

## Signed distances, failed solves, and admissibility

Cross-period directional distances are unrestricted. These states are
distinct:

| State | Output policy |
|---|---|
| optimal, $D<0$, and $1+D>0$ | retain the signed distance and calculate the factor |
| infeasible distance task | leave the transition missing and retain all role-level diagnostics |
| optimal distance task but $1+D\leq0$ | leave the multiplicative index undefined |

Negative distances must not be truncated. The diagnostics table preserves
`distance_role`, `evaluated_period`, `technology_period`, raw and released
solver statuses, the raw and released directional distance, the reported
objective, and the LP and production-account residuals for each of the four
tasks.

## Certified transition release

A backend label of `optimal` is not sufficient evidence for an environmental
productivity claim. Each of the four distance programmes must pass independent
primal, bound, objective, dual-feasibility, complementarity, and strong-duality
checks. DEAPack then rebuilds the common-factor production account before and
after numerical cleanup and verifies the complete multiplicative ML account,
including positive factors and
`productivity_change = efficiency_change * technical_change`.

Only a transition that passes all four task gates and the multiplicative account
receives `score_valid=True`. Otherwise the headline, both components, all four
published distances, and that transition's peer rows are withheld, while the raw
role diagnostics remain available. Peer rows have a separate gate after
`peer_tolerance`: thresholding may make `peer_valid=False` without invalidating an
already certified score. In each task diagnostic, `peer_valid` is the exact
boolean alias of `published_peer_account_certified`; neither field participates
in the score-release gate.

Metadata records four requested distance tasks per matched transition.
`unique_distance_solves` counts the tasks left after cache reuse,
`solver_calls` equals that executed count, and `additional_solver_calls=0`
confirms that certification performs no additional optimization. The release
logic also does not clip a valid signed cross-period distance.

## Independent analytical oracle

The source's mill-level panel is not public in the article, so DEAPack does
not claim to reproduce the published Swedish industry averages. That empirical
application is therefore not part of the current reproduction claim.

The repository instead compiles all four CFG distance programmes independently
with dense SciPy LP arrays. Two exact fixtures verify:

| Fixture | $(D_t^t,D_{t+1}^t,D_t^{t+1},D_{t+1}^{t+1})$ | $(ML,EC_{ML},TC_{ML})$ |
|---|---:|---:|
| More favorable represented opportunity | $(0,-3/5,3/5,0)$ | $(2,1,2)$ |
| Smaller contemporaneous operating shortfall | $(3/5,1/3,3/5,1/3)$ | $(6/5,6/5,1)$ |

The second fixture does not assert equality of the complete period
technologies. The same benchmark segment supported by unit F determines all
four directional evaluations, which is the narrower condition needed for the
fixture's $TC_{ML}=1$ result.

The method is analytically validated, not presented as an empirical
reproduction of the source application.

## Example

```python
from deapack import DEAData, MalmquistLuenbergerDEA, load_dataset

frame = load_dataset("environmental_panel")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    period="period",
    inputs=["energy", "labor"],
    outputs="electricity",
    bad_outputs="co2",
)
result = MalmquistLuenbergerDEA().fit(data)

result.summary()[[
    "dmu_id",
    "base_period",
    "comparison_period",
    "productivity_change",
    "efficiency_change",
    "technical_change",
    "score_valid",
    "peer_valid",
]]
```

```{autosummary}
MalmquistLuenbergerProductivityIndex
MalmquistLuenbergerDEA
```
