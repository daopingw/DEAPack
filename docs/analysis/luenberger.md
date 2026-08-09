# Luenberger productivity indicator

```{eval-rst}
.. currentmodule:: deapack
```

`LuenbergerProductivityIndicator` is the additive directional-distance
counterpart to the multiplicative Malmquist index. `LuenbergerDEA` is its
discoverability alias.

## Definition

For an evaluated plan $z^\sigma=(x^\sigma,y^\sigma)$ and directional
distance $D^\tau(z^\sigma;g)$ under period-$\tau$ technology:

$$
L^{t,t+1}=\frac{1}{2}\left[
D^t(z^t;g)-D^t(z^{t+1};g)
+D^{t+1}(z^t;g)-D^{t+1}(z^{t+1};g)
\right].
$$

Its additive decomposition is

$$
EC_L=D^t(z^t;g)-D^{t+1}(z^{t+1};g),
$$

$$
TC_L=\frac{1}{2}\left[
D^{t+1}(z^t;g)-D^t(z^t;g)
+D^{t+1}(z^{t+1};g)-D^t(z^{t+1};g)
\right],
\qquad L=EC_L+TC_L.
$$

Positive values mean improvement, zero means no change, and negative values
mean decline. `score` contains $L$; `efficiency` remains missing because the
indicator is not a bounded efficiency level.

## Direction and negative cross-period values

The default input and output directions are full-sample column means. This
gives every observation one common cardinal scale and preserves the indicator
when variable units and their directions are rescaled together. `observed`,
`ones`, global vectors/mappings, and observation-specific matrices remain
available, but changing direction changes additive values and is recorded in
metadata.

The directional-distance variable is free for cross-period solves. A newer
observation beyond an older frontier can require a negative distance. Clipping
that value to zero would understate technical progress and break the additive
decomposition.

## Exact programme-unit example

```python
import pandas as pd

from deapack import DEAData, LuenbergerProductivityIndicator

frame = pd.DataFrame(
    {
        "hospital": ["A", "B", "A", "B"],
        "year": [2020, 2020, 2021, 2021],
        "staff_bundles": [1.0, 2.0, 1.0, 2.0],
        "treatment_batches": [1.0, 2.0, 2.0, 4.0],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="hospital",
    period="year",
    inputs="staff_bundles",
    outputs="treatment_batches",
)
result = LuenbergerProductivityIndicator(
    input_direction={"staff_bundles": 0.0},
    output_direction={"treatment_batches": 1.0},
    returns_to_scale="crs",
).fit(data)

figure = result.plot(
    kind="performance",
    metric="productivity_change",
    period=2021,
    view="points",
)
```

The common programme holds staff fixed and defines one unit as one additional
batch of 100 completed treatments. The certified 2020--2021 results are
$L_A=1$ and $L_B=2$, with $EC_L=0$ and $TC_L=L$ for both hospitals. These are
absolute programme units. Hospital B's value of 2 does not mean that B is
twice as productive as A, and neither value is a percentage. B operates at
twice A's scale, so the same absolute output programme records twice as many
additional treatment batches.

The same identifier-based adjacent-period matching and explicit
`unbalanced="drop"`/`"raise"` policy as Malmquist are used. When several
period pairs are present, `period=...` selects the comparison-period rows to
display; it does not refit the technologies.

## Certified release of the additive account

One transition requires four directional-distance appraisals. DEAPack
certifies each LP from the returned primal, objective, constraints, bounds,
and dual evidence, independently of the backend's status label. It then
checks the complete additive account: both fixed-reference changes, the
arithmetic Luenberger indicator, efficiency change, technical change, and the
identity $L=EC_L+TC_L$ must all reconstruct from those same four distances.
No additional optimization is needed for these checks.

A published summary row has `score_valid=True` and
`score_status="defined"`. The same summary release evidence uses
`postsolve_certified=True`, `economic_postsolve_certified=True`, and
`additive_account_certified=True`. If any one of the four LPs or any additive
identity fails, the transition's headline value and semantic result rows are
withheld atomically; the raw backend outcome and failed residual remain in
`diagnostics`. Consequently the performance plot cannot admit a value merely
because a backend reported `optimal`.

## Scope

This class accepts inputs and desirable outputs. Environmental Luenberger and
Malmquist--Luenberger indicators require explicit bad-output directions and
disposability assumptions and are separate analyses. CRS is the classic TFP
default; other returns-to-scale specifications are sensitivity variants until
their scale components are named explicitly.

```{autosummary}
LuenbergerProductivityIndicator
LuenbergerDEA
```
