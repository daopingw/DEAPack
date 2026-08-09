# Free-coordination hull

```{eval-rst}
.. currentmodule:: deapack
```

`FreeCoordinationHullDEA` (`FCH`) is useful when several *distinct existing
organizations* may coordinate their operations, but each organization can
enter the benchmark at most once. Examples include a regional authority
pooling existing service centers or a hospital system coordinating currently
operating clinics.

This is an institutional production assumption:

- FDH permits one observed organization;
- FCH permits a nonempty subset of distinct observed organizations;
- FRH permits nonnegative whole-number copies of operating templates; and
- CCR permits arbitrary nonnegative fractional activity.

The selected FCH coalition is a technically admissible benchmark. It is **not
a recommendation to merge organizations**. Legal authority, geography,
integration cost, labor agreements, service quality, and competition policy
remain separate managerial and institutional questions.

## Technology and radial scores

For reference inputs $X$, desirable outputs $Y$, and binary selection vector
$z$, DEAPack maintains the Green--Cook technology

$$
\widehat{\mathcal T}_{FCH}
=
\left\{
(x,y):
Xz\leq x,\quad
Yz\geq y,\quad
z\in\{0,1\}^{n},\quad
\mathbf 1^\top z\geq1
\right\}.
$$

The last inequality excludes an empty coalition. Ordinary free disposal is
retained.

Input orientation minimizes the common resource factor:

$$
\min_{\theta,z}\ \theta
\quad\text{s.t.}\quad
Xz\leq\theta x_o,\quad
Yz\geq y_o,\quad
z\in\{0,1\}^{n},\quad
\mathbf 1^\top z\geq1.
$$

Both `score` and `efficiency` report $\theta$. Output orientation maximizes
the common service factor:

$$
\max_{\phi,z}\ \phi
\quad\text{s.t.}\quad
Xz\leq x_o,\quad
Yz\geq\phi y_o,\quad
z\in\{0,1\}^{n},\quad
\mathbf 1^\top z\geq1.
$$

Here `score` reports native expansion $\phi$, while `efficiency` reports
$1/\phi$ when the denominator is valid.

FCH has no `returns_to_scale` parameter. Its scale meaning is already fixed
by “each distinct observed organization at most once.”

## What is nested—and what is not

With the same additive nonnegative quantities, positive observation-level
input/output aggregates, cross-sectional comparison population, orientation,
self-membership policy, and ordinary free disposal,

$$
\widehat{\mathcal T}_{FDH}
\subseteq
\widehat{\mathcal T}_{FCH}
\subseteq
\widehat{\mathcal T}_{FRH}.
$$

Consequently,

$$
\theta^{FRH}\leq\theta^{FCH}\leq\theta^{FDH},
\qquad
\phi^{FRH}\geq\phi^{FCH}\geq\phi^{FDH}.
$$

These inequalities compare operating assumptions; they do not determine
which assumption is economically credible.

Two cautions matter:

1. FCH and the VRS convex hull are not generally nested.
2. Relaxing $z\in\{0,1\}^n$ gives
   $0\leq z_j\leq1$ while retaining the nonempty-subset constraint. That
   bounded-intensity model is the direct LP relaxation of FCH; CCR is not.

FRH does have a matched CRS continuous relaxation because its nonnegative
integer replication counts become arbitrary nonnegative real intensities.
That FRH fact must not be transferred to FCH.

## Theory-led four-organization example

The built-in deterministic `coordination_hulls` dataset is designed to make
the technology distinctions visible:

| Organization | Resource | Service |
|---|---:|---:|
| A | 3 | 6 |
| B | 4 | 5 |
| C | 12 | 14 |
| E | 10 | 10 |

For organization E, input-oriented FCH selects A+B. The coalition uses
$3+4=7$ resources and supplies $6+5=11$ services, so
$\theta=7/10=0.70$. Output orientation uses the same coalition and obtains
$\phi=11/10=1.10$, hence standardized efficiency $10/11$.

```python
from deapack import DEAData, FCH, dataset_info, load_dataset

frame = load_dataset("coordination_hulls")
roles = dataset_info("coordination_hulls").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

input_result = FCH(orientation="input").fit(data)
output_result = FCH(
    orientation="output",
    compute_slacks=False,
).fit(data)

input_result.summary().set_index("dmu_id").loc[
    "E", ["score", "efficiency", "coalition_size"]
]
input_result.peers("E")[
    ["reference_dmu_id", "selection_indicator"]
]
```

The maintained exact analytical fixture separates the technologies in both
orientations:

| Model | Input $\theta$ | Output $\phi$ | Output efficiency |
|---|---:|---:|---:|
| FDH | 1.00 | 1.00 | 1.00 |
| FCH | 0.70 | 1.10 | $10/11$ |
| FRH | 0.60 | 1.80 | $5/9$ |
| CCR | 0.50 | 2.00 | 0.50 |
| VRS | 0.75 | $11/9$ | $9/11$ |

The VRS reversal across orientations is a concrete reminder that VRS and FCH
have no general ordering.

These values are not presented as a published Green--Cook numerical table or
as a third-party cross-implementation. The article defines the FCH
formulation. An independent exact test enumerates all 15 nonempty binary
coalitions with integer sums and rational arithmetic, without calling the
production mixed-integer compiler or solver. It proves both orientations for
all four organizations, including the fixture-specific coalitions, radial and
reference activities, and free-disposal residuals. The built-in dataset is
therefore a theory-led analytical certificate of the model's economic
distinctions, not a reproduction of the article's empirical application.

## Targets, certification, and failure policy

With `compute_slacks=True`, a second binary program fixes the certified radial
factor and maximizes row-scaled free-disposal residuals. Results distinguish:

- `radial_target`, the proportional resource or service commitment;
- `binary_subset_reference_activity`, the activity generated by the selected
  organizations; and
- `free_disposal_residual`, the difference between them.

`selection_indicator` is zero or one and `coalition_size` counts selected
organizations. Coalition and target uniqueness are not claimed. Mixed-integer
models do not return LP dual or shadow-price information.

Every accepted phase-one solution must have:

- solver-optimal status;
- finite objective and primal values;
- valid binary formulation and componentwise binary values;
- certified variable bounds and constraints;
- a nonempty selected subset; and
- a finite nonnegative MIP gap no larger than the declared tolerance.

An invalid incumbent or uncertified gap fails closed. If phase two fails, the
certified radial score is retained, but targets, slacks, and generic strong
efficiency remain unclaimed.

The current public leaf accepts nonnegative cross-sectional inputs and
desirable outputs when every observation has positive aggregate input and
output. It rejects panels, negative quantities, zero aggregate input/output,
and undesirable outputs. Panel coordination needs an explicit rule preventing
different periods of one organization from masquerading as distinct
coalition members. Environmental coordination needs its own source-qualified
disposal technology.

Zero components retain their production meaning. For an evaluated
organization, a zero input is a hard zero resource budget: a selected
coalition must also use zero of that input. A zero output imposes no
proportional expansion requirement because $\phi\cdot0=0$, but the selected
coalition's production of that output remains visible in
`binary_subset_reference_activity` and output-slack accounting.

## Historical FAH name

Green--Cook FCH is also called the **free aggregation hull**, historically
abbreviated `FAH`; this identity is confirmed by
[Adler, Olesen, and Volta
(2024)](https://doi.org/10.1287/opre.2022.2348).

DEAPack deliberately does not expose `FAH` as a Python alias.
[Ray (1997)](https://doi.org/10.1023/A:1007747407212) uses the same acronym
for the distinct **free affordability hull**, a cost-indirect technology for
normalized input prices when input quantities are unavailable. Use `FCH` for
Green--Cook binary-subset coordination and always retain source provenance
when reading historical `FAH`.

The defining FCH source is
[Green and Cook (2004)](https://doi.org/10.1057/palgrave.jors.2601773).

```{autosummary}
FreeCoordinationHullDEA
FCH
```

See {doc}`fdh` for one-observation benchmarking and {doc}`frh` for
whole-template replication.
