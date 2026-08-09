:orphan:

# Tone (2002) super-SBM

```{eval-rst}
.. currentmodule:: deapack
```

`ToneSuperSBM` asks whether a strongly efficient organization remains
difficult to replace when the rest of the eligible comparison population may
face different pressure on each resource and service. Its exact short alias is
`SuperSBM`; the canonical method ID is
`evaluation.super.sbm.tone_2002`.

This is a two-gate evaluation protocol:

1. ordinary **non-oriented SBM under the same returns-to-scale assumption**
   determines whether the focal row is strongly efficient; then
2. only a strongly efficient row is removed from its own reference population
   and evaluated by Tone's source super-SBM programme.

A row that fails the first gate has no super-SBM score. It is
**not applicable**, rather than a failed super-efficiency solve and rather
than an organization with a low super score. This separation prevents one
ranking column from mixing ordinary inefficiency with frontier
distinctiveness.

```{figure} ../../book/_static/figures/super-efficiency-radial-vs-slack.svg
:name: docs-fig-super-efficiency-radial-vs-slack
:alt: A later radial leave-self-out reconstruction applies one common proportional replacement pressure, while Tone super-SBM first admits only strongly SBM-efficient organizations and then records separate resource and service replacement pressures
:width: 100%

The diagram contrasts Tone's source-qualified method with the common radial
reconstruction found in later super-efficiency literature. Andersen--Petersen
is not a public recipe in this release because its defining full text has not
yet passed the source gate. Super-SBM allows different resource and service
ratios and applies only after the strong-SBM screen.
```

## Supported source surface

The public implementation is deliberately narrower than the wider
super-SBM literature.

| Returns to scale | Non-oriented | Input-oriented | Output-oriented |
|---|:---:|:---:|:---:|
| CRS | supported | supported | supported |
| VRS | supported | deferred | deferred |
| NIRS | deferred | deferred | deferred |
| NDRS | deferred | deferred | deferred |

The data contract requires every input and every desirable output to be
strictly positive. Zero quantities, negative quantities, undesirable outputs,
and automatic structural-versus-incidental-zero classification are not
supported. Tone discusses possible zero cases, but that discussion does not
define a universal automatic repair. Those cases require separately named,
source-qualified models.

## The same-RTS strong-efficiency screen

For each organization $o$, DEAPack first fits ordinary non-oriented SBM using
the complete base reference population and the same CRS or VRS assumption
requested for super-SBM. The row is eligible only when:

- the screen solve is certified optimal;
- its ordinary SBM score is one within tolerance; and
- all material input and output slacks are zero within tolerance.

The summary keeps the ordinary result in `sbm_screen_score` and the
eligibility decision in `is_sbm_eligible`. A screen failure closes the
dependent super programme. An ordinary inefficient row retains
`applicability_status` and a missing `super_sbm_score`.

The focal row must belong to its base reference set during this screen. When
eligible, exactly that row is removed, and at least one peer must remain.

## Non-oriented source programme

Let $X_{-o}$ and $Y_{-o}$ contain the eligible peer rows after removing
organization $o$. For $m$ inputs and $s$ desirable outputs, Tone's CRS
non-oriented super-SBM score is

$$
\delta_o
=
\min_{\bar{x},\bar{y},\lambda}
\frac{
\frac{1}{m}\sum_{i=1}^{m}\bar{x}_i/x_{io}
}{
\frac{1}{s}\sum_{r=1}^{s}\bar{y}_r/y_{ro}
}
$$

subject to

$$
\begin{aligned}
\bar{x} &\geq X_{-o}\lambda,\\
\bar{y} &\leq Y_{-o}\lambda,\\
\bar{x} &\geq x_o,\\
0\leq\bar{y} &\leq y_o,\\
\lambda &\geq0.
\end{aligned}
$$

The peer-replacement plan $(\bar{x},\bar{y})$ is allowed to require more of
some resources than the focal organization used and to retain less of some
services than the focal organization delivered. The equal-dimension averages
make these variable-specific ratios comparable within the source score. They
are not prices, expenditure shares, or user-declared priorities.

Under VRS, the source programme adds

$$
\mathbf{1}^{\mathsf T}\lambda=1.
$$

No VRS input- or output-oriented programme is inferred from this equation.

## Linearization and certification

For the non-oriented programme, define

$$
t=
\left(
\frac{1}{s}\sum_r\frac{\bar{y}_r}{y_{ro}}
\right)^{-1},
\qquad
\widetilde{x}=t\bar{x},
\qquad
\widetilde{y}=t\bar{y},
\qquad
\Lambda=t\lambda.
$$

The Charnes--Cooper programme minimizes

$$
\frac{1}{m}\sum_i\frac{\widetilde{x}_i}{x_{io}}
$$

subject to

$$
\begin{aligned}
\widetilde{x} &\geq X_{-o}\Lambda,\\
\widetilde{y} &\leq Y_{-o}\Lambda,\\
\widetilde{x} &\geq t x_o,\\
0\leq\widetilde{y} &\leq t y_o,\\
\frac{1}{s}\sum_r\frac{\widetilde{y}_r}{y_{ro}}&=1,\\
\Lambda&\geq0,\qquad t>0.
\end{aligned}
$$

For VRS it additionally imposes
$\mathbf{1}^{\mathsf T}\Lambda=t$. Targets, intensities, adjustments, and
technology slacks are released only after the transformed solution and the
back-transformation

$$
\bar{x}=\widetilde{x}/t,\qquad
\bar{y}=\widetilde{y}/t,\qquad
\lambda=\Lambda/t
$$

pass their numerical certificates.

## CRS oriented programmes

Input orientation protects the observed desirable services and asks how
resource-intensive a peer replacement must be:

$$
\begin{aligned}
\delta_o^I
=
\min_{\bar{x},\lambda}\quad&
\frac{1}{m}\sum_i\frac{\bar{x}_i}{x_{io}}\\
\text{subject to}\quad&
\bar{x}\geq X_{-o}\lambda,\\
&Y_{-o}\lambda\geq y_o,\\
&\bar{x}\geq x_o,\qquad\lambda\geq0.
\end{aligned}
$$

Output orientation protects the observed resource limits and asks how much
of the service bundle the peer-only technology can retain:

$$
\begin{aligned}
\delta_o^O
=
\min_{\bar{y},\lambda}\quad&
\left(
\frac{1}{s}\sum_r\frac{\bar{y}_r}{y_{ro}}
\right)^{-1}\\
\text{subject to}\quad&
X_{-o}\lambda\leq x_o,\\
&\bar{y}\leq Y_{-o}\lambda,\\
&0\leq\bar{y}\leq y_o,\qquad\lambda\geq0.
\end{aligned}
$$

These two oriented programmes are exposed only with CRS.

## Project-authored peer-replacement example

The neutral `super_sbm_peer_replacement` data exercise the strong-SBM screen,
leave-self-out comparison, and peer-replacement account without reproducing a
table from Tone (2002):

```python
from deapack import DEAData, ToneSuperSBM, dataset_info, load_dataset

frame = load_dataset("super_sbm_peer_replacement")
roles = dataset_info("super_sbm_peer_replacement").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = ToneSuperSBM(
    orientation="non-oriented",
    returns_to_scale="crs",
).fit(data)

result.summary()[
    [
        "dmu_id",
        "sbm_screen_score",
        "is_sbm_eligible",
        "super_sbm_score",
        "is_super_efficient",
        "applicability_status",
        "solver_status",
    ]
]
```

Rows that fail the ordinary strong-efficiency screen retain an explicit
inapplicability state and no super score. Eligible rows expose the native
ranking scalar together with a certified, solver-selected replacement plan.
The project tests verify score feasibility and account reconstruction without
locking an LP basis because alternate optimal peer plans may exist.

A value above one is not an ordinary percentage-efficiency statement. It says
that the remaining comparison population requires greater variable-specific
replacement pressure under the declared equal-dimension account.

`ToneSuperSBM` is the descriptive class name; `SuperSBM` is its exact alias.

The ranking can be displayed without changing its meaning:

```python
result.plot(
    kind="performance",
    metric="super_sbm_score",
    theme="deapack",
)
```

Only eligible rows with certified scores appear. A taller bar means that the
remaining comparison population faces greater peer-replacement pressure; it
does not mean that the organization is “more efficient” in an ordinary
percentage sense.

## Results and failure closure

The principal summary fields are:

| Field | Meaning |
|---|---|
| `score` / `super_sbm_score` | source super-SBM ranking quantity; missing when inapplicable or uncertified |
| `sbm_screen_score` | ordinary non-oriented SBM score under the same RTS |
| `is_sbm_eligible` | whether the row passed the strong-efficiency screen |
| `is_super_efficient` | whether a valid super score is strictly above one |
| `score_valid` | whether applicability, solve, and transformation certificates permit release |
| `applicability_status` | distinguishes a source-ineligible row from a failed super programme |
| `screen_solver_status` | ordinary SBM screen state |
| `super_solver_status` | source super-SBM solve state when applicable |
| `input_replacement_factor` | average source input replacement ratio when defined |
| `output_retention_factor` | average retained-output ratio when defined |

`efficiency` and `distance` are deliberately missing, and generic
`is_efficient` is `NA`. The result is a frontier-appraisal ranking, not an
ordinary efficiency percentage or distance.

`targets` describe a solver-selected peer-replacement plan, not a
prescription for the focal leader. `slacks` separates:

- `replacement_adjustment`, the difference between the focal record and
  $(\bar{x},\bar{y})$; and
- `technology_slack`, the difference between that replacement plan and the
  selected peer activity.

`intensities` retains the back-transformed peer weights. Alternate optimal
peer plans may exist, so none of these explanatory tables is claimed to be
unique.

The implementation withholds the super score and dependent tables after a
screen failure, an invalid reference population, infeasibility,
unboundedness, a solver limit, failed optimality or normalization checks, or
an invalid back-transformation. It never responds by changing RTS,
orientation, data semantics, or super-efficiency formulation.

## Interpretation and non-equivalence

A large super-SBM value can reflect a genuinely hard-to-replace operating
record, a sparse peer population, omitted quality or risk variables, an
unusual operating scale, or a recording error. It does not establish
managerial superiority, causal policy impact, or statistical outlier status.

Tone super-SBM is not an alias for:

- Andersen--Petersen radial super-efficiency;
- ordinary SBM applied to a leave-one-out sample;
- directional, additive, undesirable-output, zero-data, or negative-data
  super-efficiency;
- VRS-oriented, NIRS, or NDRS super-SBM;
- cross-efficiency or influence diagnostics; or
- an automatic repair for an infeasible peer-only programme.

The implementation follows [Tone
(2002)](https://doi.org/10.1016/S0377-2217(01)00324-1).

```{eval-rst}
.. autosummary::
   ToneSuperSBM
   SuperSBM
```
