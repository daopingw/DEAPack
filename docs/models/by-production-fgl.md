# By-production FGL efficiency

```{eval-rst}
.. currentmodule:: deapack
```

`ByProductionFareGrosskopfLovellDEA` implements the modified output-oriented
Färe--Grosskopf--Lovell index proposed for the by-production technology by
Murty, Russell, and Levkoff (2012). Its
discoverability alias is `ByProductionFGL`.

## Definition

Overall efficiency is the equal-weight mean

$$
E_{FGL}=\frac{1}{2}\left(E_{FGL}^{1}+E_{FGL}^{2}\right).
$$

The productive component is

$$
E_{FGL}^{1}=\min_{\theta,\lambda}
\left\{\frac{1}{s}\sum_r\theta_r:
X\lambda\le x_o,\quad
Y\lambda\ge y_o\oslash\theta,\quad
0<\theta\le\mathbf{1},\quad
\lambda\ge0\right\}.
$$

The environmental component is

$$
E_{FGL}^{2}=\min_{\gamma,\mu}
\left\{\frac{1}{q}\sum_h\gamma_h:
X^p\mu\ge x_o^p,\quad
B\mu\le\gamma\otimes b_o,\quad
0\le\gamma\le\mathbf{1},\quad
\mu\ge0\right\}.
$$

Under the source's positive-output, self-inclusive CRS profile, both
components and the overall score are in $(0,1]$ and higher is better.
Overall efficiency equals one only when both output vectors admit no further
coordinatewise improvement in their respective subtechnologies. Input slack
can remain, so this native criterion is not a Pareto--Koopmans certificate.

## Sparse certified solution

Set $\phi_r=1/\theta_r$. The productive objective becomes the convex function
$s^{-1}\sum_r1/\phi_r$ over linear technology constraints. DEAPack solves it
with sparse tangent-cut LPs:

- each master objective is a global lower bound;
- each feasible expansion vector supplies an upper bound;
- iteration stops only when their gap reaches the effective tolerance;
- diagnostics expose `lower_bound`, `upper_bound`, and `optimality_gap`.

The effective FGL tolerance is the larger of `fgl_tolerance` and the model's
numerical `tolerance`; requesting a gap below the backend feasibility scale
does not create false precision. `max_cut_iterations` controls the hard limit.
The environmental component is one exact sparse LP. Before releasing either
component, DEAPack rechecks the actual returned incumbent and full internal
intensity vector after numerical cleaning: factor bounds, component
inequalities, returns to scale, objective consistency, and backend violation
must satisfy `tolerance`. `peers()` discloses only intensities strictly above
`peer_tolerance`; that display rule does not change the solved target. An iteration
limit or failed post-solve certificate produces missing scores and retained
diagnostics rather than unsupported targets or peers.

## Published numerical check

`by_production_component_bottleneck` supplies a neutral three-plan contrast for
Murty, Russell, and Levkoff's Example 1. Their production account is CRS in
both subtechnologies:

```python
from deapack import (
    ByProductionFGL,
    DEAData,
    dataset_info,
    load_dataset,
)

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
published_check = ByProductionFGL().fit(data)
```

The implementation recovers the two component values explicitly discussed
in the source: DMU 2 has productive efficiency $3/4$, environmental
efficiency $1$, and overall FGL efficiency $7/8$; DMU 3 has values $1/3$,
$1/2$, and $5/12$. The regression suite also fixes the scores implied for all
five observations by the same data and equations. Those additional values are
analytical consequences, not numbers claimed to have been tabulated
individually by the authors.

The source profile is the default: CRS in both subtechnologies, a complete
self-inclusive cross-section, separate component intensities, and equal
weights. The result metadata exposes `source_profile_matches` and exact
`source_profile_mismatches`.

## Configurable panel extension

```python
from deapack import ByProductionFGL, DEAData, load_dataset

frame = load_dataset("environmental_panel")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    period="period",
    inputs=["energy", "labor"],
    polluting_inputs="energy",
    outputs="electricity",
    bad_outputs="co2",
)

result = ByProductionFGL(
    intended_returns_to_scale="vrs",
    residual_returns_to_scale="vrs",
    reference="contemporaneous",
).fit(data)
```

This VRS contemporaneous analysis is a DEAPack extension, not a source
reproduction.

The summary contains `productive_efficiency`, `environmental_efficiency`,
`fgl_cut_iterations`, and `fgl_optimality_gap`. Output target factors are
$1/\theta_r\ge1$; bad-output target factors are $\gamma_h\le1$. Long-form
slacks retain the raw and normalized adjustments and each factor's weight in
the overall score.

`is_fgl_efficient` tests whether both native FGL components equal one. That
criterion exhausts the modeled output-space adjustments but does not complete
possible input slack, so the generic Pareto--Koopmans field `is_efficient`
remains missing. `distance = 1 - efficiency` is a DEAPack display complement,
not a source-defined distance.

## Data and scope

The current implementation requires strictly positive desirable and
undesirable outputs plus strictly positive values in a declared nonempty
subset of pollution-generating inputs. The source technology formally admits
nonnegative inputs, but zero pollution-generating inputs create boundary
cases outside the current executable oracle, so this release fails closed on
them. The model applies the same explicit by-production data roles and two
independent returns-to-scale specifications as BP-DDF. VRS/NIRS/NDRS,
temporal or custom references, and the displayed distance complement are
package extensions. The model does not provide alternative policy weights,
explicit abatement outputs, material-balance coefficients, a
Pareto--Koopmans completion, or statistical endogeneity corrections.

Equation-level provenance, the frozen Example 1 correction, and the
independently compiled five-DMU oracle are recorded in
`specs/source_protocols/by_production_fgl_reference.md` and
`specs/oracles/by-production-fgl-project-case.md`.

```{autosummary}
ByProductionFareGrosskopfLovellDEA
ByProductionFGL
```
