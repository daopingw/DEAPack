# Multiplicative DEA

```{eval-rst}
.. currentmodule:: deapack
```

Multiplicative DEA asks whether an organization's resource and service account
can be improved relative to a best-practice boundary assembled
multiplicatively. It is useful when proportional changes are more meaningful
than additive quantity changes: a target can, for example, describe a 20
percent resource saving and a 10 percent service increase without adding
hours, currency, and cases into one physical-unit objective.

This is a different production account from ordinary CCR or BCC DEA. Taking
logs does not merely transform an ordinary radial score: the 1982 model
maintains a piecewise log-linear boundary, while the 1983 revision supports
piecewise Cobb--Douglas envelopes through its free log intercept. Neither is
an arithmetic combination of quantities in disguise.

## Choosing the constructor

DEAPack keeps the two defining formulations separate while sharing one sparse
log-space compiler:

| Constructor | Fixed variant | Source meaning |
|---|---|---|
| `MultiplicativeDEA()` | `"invariant_1983"` by default | configurable family entry point |
| `InvariantMultiplicativeDEA()` | `"invariant_1983"` | explicit source preset for the unit-invariant 1983 model |
| `C2S2MultiplicativeDEA()` | `"original_1982"` | historical C2S2 model, which is not unit invariant |

The two source presets record distinct `preset_id` values. The historical
`C2S2MultiplicativeDEA` name is deliberately fixed to the 1982 model; it never
silently selects the later modification.

For DMU $o$, write $\widehat x=\log x$ and $\widehat y=\log y$. The 1983
envelopment solves

$$
\min_{\lambda,s^-,s^+}
-\delta\left(\mathbf 1^\top s^-+\mathbf 1^\top s^+\right)
$$

subject to

$$
\widehat X\lambda+s^-=\widehat x_o,
\qquad
\widehat Y\lambda-s^+=\widehat y_o,
\qquad
\mathbf 1^\top\lambda=1,
$$

with $\lambda,s^-,s^+\geq0$ and a common exponent floor $\delta>0$. The
convexity identity makes each target a weighted geometric combination of
observed practices and makes the score invariant to independent positive
changes in the units of every input and output.

The 1982 programme fixes $\delta=1$ and removes
$\mathbf 1^\top\lambda=1$. Its reference activities form a cone in log
coordinates. The resulting score and target can change after an otherwise
innocent change of measurement units.

:::{warning}
`log_convex` and `log_conic` are not synonyms for ordinary physical-space VRS
and CRS. Neither source model exposes a conventional `returns_to_scale` or
input/output `orientation` option. Both models are non-oriented accounts of
simultaneous resource excesses and service shortfalls.
:::

## Minimal executable example

The following two-DMU example satisfies the more restrictive 1982 domain, so
the two variants can be compared directly:

```python
import pandas as pd

from deapack import (
    C2S2MultiplicativeDEA,
    DEAData,
    InvariantMultiplicativeDEA,
)

frame = pd.DataFrame(
    {
        "dmu": ["A", "B"],
        "input": [2.0, 4.0],
        "output": [4.0, 4.0],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs="input",
    outputs="output",
)

invariant = InvariantMultiplicativeDEA().fit(data)
original = C2S2MultiplicativeDEA().fit(data)

comparison = invariant.summary()[["dmu_id", "score"]].rename(
    columns={"score": "invariant_1983"}
)
comparison["original_1982"] = original.summary()["score"].to_numpy()
print(comparison)

print(
    invariant.targets_for("B")[[
        "role", "variable", "observed", "target", "target_factor"
    ]]
)

figure = invariant.plot(kind="performance")
figure.savefig("multiplicative-efficiency.png", dpi=180)
```

The plot call uses the optional Matplotlib backend (`pip install
'DEAPack[viz]'`). It selects `multiplicative_efficiency` automatically and
retains the one-is-best benchmark convention.

The comparison is

| DMU | 1983 invariant score | 1982 original score |
|---|---:|---:|
| A | 1 | 1 |
| B | $1/2$ | $1/4$ |

Under the 1983 model, B is compared with A using $\lambda_A=1$. Its input
target is 2, its output target remains 4, and its input target factor is
$1/2$. Under the 1982 log cone, the selected intensity is
$\lambda_A=2$: B keeps input 4 but receives output target 16. The difference
is a technology difference, not a display transformation of one common score.

## Score and exponent-floor convention

The source multiplier account is

$$
\ell_o
=
\max_{\mu,\nu,\omega}
\left(
\mu^\top\widehat y_o-\nu^\top\widehat x_o+\omega
\right)
$$

subject to

$$
\mu^\top\widehat y_j-\nu^\top\widehat x_j+\omega\leq0
\quad\text{for every reference DMU }j,
$$

and $\mu_r,\nu_i\geq\delta$. The invariant model has a free log intercept
$\omega$; the original model fixes $\omega=0$ and $\delta=1$.

DEAPack reports

$$
E_o=\exp(\ell_o)
=
\exp\left[-\delta\left(\sum_i s_i^-+\sum_r s_r^+\right)\right].
$$

With a feasible self-inclusive reference set, $0<E_o\leq1$ mathematically,
and higher is better. The summary fields are:

- `score`, `efficiency`, and `multiplicative_efficiency`: $E_o$;
- `log_efficiency`: $\ell_o\leq0$;
- `distance` and `log_inefficiency`: $-\ell_o\geq0$; and
- `is_efficient`: whether every fitted log slack is zero within `tolerance`.

For the 1983 model, changing `exponent_floor` applies a transparent score-power
convention:

$$
\ell_o(\delta)=\delta\ell_o(1),
\qquad
E_o(\delta)=E_o(1)^\delta.
$$

It leaves the feasible peer plans, selected target set, and ranking unchanged.
The implementation solves the homogeneous $\delta=1$ LP and rescales the log
score and certified multipliers afterward. The 1982 source fixes the floor at
one, so any other value is rejected rather than described as C2S2.

Scores from studies using different exponent floors should not be compared as
though they had the same cardinal scale. The floor, variant, and score
transform are retained in result metadata.

## Targets, log slacks, and peers

The fitted target satisfies

$$
\widehat x_i^*=\widehat x_{io}-s_i^-,
\qquad
\widehat y_r^*=\widehat y_{ro}+s_r^+.
$$

In original units,

$$
x_i^*=x_{io}e^{-s_i^-},
\qquad
y_r^*=y_{ro}e^{s_r^+}.
$$

For the invariant model,

$$
x_i^*=\prod_j x_{ij}^{\lambda_j},
\qquad
y_r^*=\prod_j y_{rj}^{\lambda_j},
\qquad
\sum_j\lambda_j=1.
$$

Its intensities can therefore be read as weights in a geometric peer mix. For
the original model, the same product expressions hold without the sum-to-one
identity. Its intensities are conic activity coefficients, not percentage
peer shares.

`result.targets` retains both representations:

- `observed` and `target` are quantities in the user's original units;
- `log_observed` and `log_target` are the authoritative log quantities;
- `target_factor` is $x_i^*/x_{io}$ for an input and $y_r^*/y_{ro}$ for an
  output; and
- `original_unit_available`, `factor_available`, and `transform_reason`
  disclose whether exponentiating the log result was representable in
  `float64`.

`result.slacks` uses `log_slack` for $s_i^-$ or $s_r^+$. The compatibility
column `scaled_slack` contains the same log-scale quantity. `slack` and
`absolute_change` contain the corresponding original-unit saving or increase,
while `improvement_factor`, `exponent_weight`, and `weighted_log_slack` retain
the multiplicative account.

Targets are source-optimal frontier projections, but they need not be unique,
closest, least-cost, or preferred by management. Metadata therefore reports
`target_uniqueness="not_guaranteed"` and
`causal_interpretation="not_identified"`.

Only intensities above `peer_tolerance` appear in `result.intensities` and
`result.peers(...)`. Diagnostics retain `reported_intensity_mass` and
`omitted_intensity_mass`, so filtering a small coefficient cannot silently be
mistaken for the complete fitted plan.

## Multipliers

When the solver supplies equality marginals, `result.multipliers` reports the
source multiplier account:

- `role="input_exponent"` contains $\nu_i$;
- `role="output_exponent"` contains $\mu_r$; and
- the invariant model adds `role="log_intercept"`, with
  `variable="omega"`.

The input and output exponent rows record their `lower_bound`. Every emitted
multiplier row is marked `selection="solver_selected_optimum"`; alternate
optimal exponent systems may exist. The exponents are virtual performance
weights. Without additional economic assumptions, they are not market prices,
causal elasticities, or marginal products.

For numerical conditioning, the invariant LP subtracts one reference anchor
from each log coordinate. Before multipliers are released, DEAPack restores
$\omega$ to the original, uncentered log coordinates and verifies the exponent
bounds, every reference inequality, and the focal objective. If this dual
certificate fails, the score and primal target can remain valid but multiplier
rows are withheld; the reason appears in diagnostics.

## Result tables and diagnostics

| Result object | Main multiplicative content |
|---|---|
| `result.summary()` | score, log score/distance, strong status, variant, log-hull type, and solver status |
| `result.targets` | original and log quantities, target factors, and transform availability |
| `result.slacks` | physical changes, log slacks, exponent weights, and improvement factors |
| `result.intensities` | reported reference coefficients and `target_aggregation` |
| `result.multipliers` | certified exponents and, for 1983, the restored free intercept |
| `result.diagnostics` | solver/primal checks, target reconstruction, transform state, multiplier checks, and reported/omitted intensity mass |
| `result.metadata` | method and preset identities, source profile, variant, reference rule, score transform, solver, and tolerances |

Convenience queries include `targets_for(dmu_id)`, `peers(dmu_id)`, and
`multipliers_for(dmu_id)`. On panel data, the tidy tables also carry `period`
and `reference_period`.

## Source profiles and reference extensions

The defining source profile is one self-inclusive cross section evaluated
against the global sample. With that configuration, metadata reports one of:

- `charnes_cooper_seiford_stutz_1983_invariant`; or
- `charnes_cooper_seiford_stutz_1982_original`.

`InvariantMultiplicativeDEA` additionally records
`preset_id="static.multiplicative.invariant.charnes_etal_1983"`, while
`C2S2MultiplicativeDEA` records
`preset_id="static.multiplicative.original.charnes_etal_1982"`.

The shared `ReferenceSpec` machinery also permits global, contemporaneous,
sequential, window, biennial, and custom reference sets where their required
data are available. `reference=None` means all rows in a cross section and a
contemporaneous reference in a panel. See the
{doc}`reference-technology guide <../user-guide/reference-sets>` for the exact
row-selection rules.

Panel and non-global fits are package extensions, not silent claims about the
1982 or 1983 cross-sectional articles. Their metadata changes `source_profile`
to `deapack_invariant_1983_reference_extension` or
`deapack_original_1982_reference_extension`, sets
`source_profile_matches=False`, and records reasons such as
`data_are_not_one_cross_section` and `reference_is_not_the_global_sample`.
This disclosure is informational: a valid extension is still fitted.

An external or custom reference set need not contain the evaluated row. If no
selected geometric/log-conic activity can weakly reduce all inputs and weakly
increase all outputs, that row is infeasible. These source models do not turn
such a run into leave-one-out super-efficiency.

## Admissible data and failures

Both variants require finite, strictly positive ordinary inputs and desirable
outputs because logarithms are part of the technology. They reject zeros,
negative values, arbitrary epsilon replacements, and declared undesirable
outputs. Undesirable outcomes require a separately source-qualified
environmental technology; they must not be relabeled as desirable output
shortfalls here.

The 1983 model admits any value greater than zero, including quantities below
one. The 1982 model requires every input and output to be strictly greater than
one. DEAPack does not rescale a 1982 dataset to manufacture this domain:
because the model is not unit invariant, such preprocessing could change the
answer it is supposed to estimate.

Model-construction and data-domain violations raise an exception before any LP
is solved. Solver infeasibility, unboundedness, numerical errors, or a failed
post-solve primal/economic-account certificate instead produce a fail-closed
summary row: score fields are missing, `solver_status` and `failure_reason`
remain visible, and no target, slack, peer, or multiplier rows are released for
that observation.

The log solution can remain finite when exponentiating a target or target
factor would overflow or underflow `float64`. In that case the score and log
target remain available, the affected original-unit fields are missing, and
the transform flags explain why. Likewise, extreme log inefficiency can make
the floating-point efficiency display underflow to zero even though the
mathematical score is positive; `efficiency_underflowed` identifies that case
and `log_efficiency` remains authoritative.

The exponent floor itself is also range-checked after the normalized solve.
If multiplying a positive normalized log gap by an extreme finite
`exponent_floor` would overflow, or would underflow all the way to zero, the
observation fails closed with an explicit scaling reason. DEAPack does not
publish a spurious zero or one as the source-native score. A separate overflow
during dual-coordinate restoration withholds only the affected multipliers
when the primal score and target remain certified.

## Computational strategy

The base installation uses SciPy/HiGHS and needs no nonlinear or conic solver.
DEAPack:

1. validates and logarithmically transforms the named arrays once;
2. deduplicates reference populations;
3. compiles one immutable sparse CSC matrix per unique reference set;
4. reuses that matrix while changing the focal right-hand side; and
5. solves one LP per evaluated observation.

The 1983 convexity identity permits an exact translation of each log
coordinate by a reference anchor, improving conditioning without changing the
model. The 1982 log cone does not permit that translation and is deliberately
left in its source coordinates. Values only slightly above one can therefore
produce very small input logs and large conic intensities; users should inspect
residual diagnostics rather than changing units to make the solve look easier.

The implementation certifies the backend incumbent, bounds, equality
balances, objective, reconstructed target, convexity identity where
applicable, and source multiplier account before publishing the corresponding
results. `compiled_reference_sets` in metadata reports how many sparse
templates were built.

## Defining sources

The original log-conic model is due to
[Charnes, Cooper, Seiford, and Stutz (1982)](https://doi.org/10.1016/0038-0121(82)90029-5).
The free-intercept, unit-invariant modification and its piecewise
Cobb--Douglas interpretation are due to
[Charnes, Cooper, Seiford, and Stutz (1983)](https://doi.org/10.1016/0167-6377(83)90014-7).

```{autosummary}
MultiplicativeDEA
InvariantMultiplicativeDEA
C2S2MultiplicativeDEA
```
