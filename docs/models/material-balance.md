# Materials-balance environmental efficiency

```{eval-rst}
.. currentmodule:: deapack
```

`MaterialBalanceDEA` implements the Coelli--Lauwers--Van Huylenbroeck
environmental-efficiency measure. `CoelliMaterialBalanceDEA` is a
discoverability alias. The method uses known physical material coefficients;
it is not a transformation of observed undesirable outputs.

## Certified source boundary

The current source-native claim follows
[Coelli, Lauwers, and Van Huylenbroeck (2007)](https://doi.org/10.1007/s11123-007-0052-8),
equation-checked against
[CEPA Working Paper 06/2005](https://economics.uq.edu.au/files/5310/WP062005.pdf).
Its equations (23)--(26) define input-radial technical efficiency and minimum
material inflow under CRS; the source explicitly obtains VRS by adding the
convexity constraint to both programmes.

The certified domain is deliberately narrow: a self-inclusive cross-section
of ordinary nonnegative inputs and desirable outputs, one common set of known
nonnegative physical coefficients, positive observed material inflow, and a
fixed desirable-output commitment. It contains no observed `bad_outputs` and
no explicit abatement process. An independent exact synthetic oracle checks
$TE$, $EE$, $EAE$, and $EE=TE\times EAE$ under both CRS and VRS. It does not
claim farm-level reproduction because the source's unit-level 183-farm
observations are not supplied, and it does not assert a unique
material-minimizing target.

## Physical identity

For material $h$, input contents $a_h\ge0$, and desirable-output contents
$c_h\ge0$, material surplus is

$$
z_{ho}=a_h'x_o-c_h'y_o\ge0.
$$

`MaterialBalanceCoefficients` requires named coefficients for every DEA input
and desirable output, including explicit zeroes. This prevents positional
misalignment and makes the physical units auditable. Observed `bad_outputs`
are rejected because the classic model calculates surplus from this identity.

## Measure and decomposition

For fixed output $y_o$, minimum aggregate material inflow is

$$
\min_{x^e,\lambda}\ a'x^e
\quad\text{s.t.}\quad
Y\lambda\ge y_o,\quad x^e\ge X\lambda,
$$

with the selected returns-to-scale constraint. Since coefficients are
nonnegative, the implementation eliminates $x^e$ and solves the equivalent
sparse LP $\min_\lambda a'X\lambda$.

The same reference technology supplies input-oriented radial technical
efficiency $TE$. The reported decomposition is

$$
EE=\frac{a'x^e}{a'x_o},\qquad
EAE=\frac{EE}{TE},\qquad
EE=TE\times EAE.
$$

All three values are higher-is-better. `score` and `efficiency` contain $EE$;
`distance` is $1-EE$. The ratio is based on material inflow rather than
surplus. Because output is fixed, minimizing inflow also minimizes surplus,
and both quantities remain visible in the result.

Here “environmental allocative” refers to the input mix implied by physical
material-content coefficients. It requires no prices, market valuation, or
damage weights and must not be interpreted as ordinary cost allocative
efficiency.

`is_material_efficient` tests whether the observed plan attains the minimum
material-inflow criterion. It is not copied into `is_efficient`: inputs with
zero material content and output expansion opportunities are outside this
criterion, so material optimality alone is not a Pareto--Koopmans
certificate.

## Example

```python
import pandas as pd

from deapack import DEAData, MaterialBalanceCoefficients, MaterialBalanceDEA

frame = pd.DataFrame(
    {
        "dmu": ["A", "B", "C", "D"],
        "piglets": [1.0, 3.0, 2.0, 4.0],
        "feed": [3.0, 1.0, 2.0, 4.0],
        "meat": [1.0, 1.0, 1.0, 1.0],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["piglets", "feed"],
    outputs="meat",
)
coefficients = MaterialBalanceCoefficients(
    inputs={"phosphorus": {"piglets": 1.0, "feed": 3.0}},
    outputs={"phosphorus": {"meat": 1.0}},
)
result = MaterialBalanceDEA(
    coefficients,
    returns_to_scale="vrs",
).fit(data)
```

For D, $TE=0.5$, $EAE=0.75$, and $EE=0.375$. Its observed aggregate inflow is
16, while the minimum is 6. `targets_for("D")` shows both the radial technical
target $(2,2)$ and the material-minimizing input mix $(3,1)$. `peers("D")`
labels the two component peer systems. Those peer systems and the
material-minimizing target are solver-selected optima and need not be unique.

## Multiple materials are a package extension

If two or more materials are declared, `weights` is mandatory:

```python
coefficients = MaterialBalanceCoefficients(
    inputs={
        "phosphorus": {"piglets": 1.0, "feed": 3.0},
        "nitrogen": {"piglets": 3.0, "feed": 1.0},
    },
    outputs={
        "phosphorus": {"meat": 1.0},
        "nitrogen": {"meat": 1.0},
    },
    weights={"phosphorus": 0.75, "nitrogen": 0.25},
)
```

Weights define the score's aggregate material system and are preserved in
metadata. Per-material inflow and surplus targets are still reported
separately. DEAPack never adds unlike pollutants without an explicit weighting
rule. The source discusses this weighted extension in equations (18)--(21),
and the implementation has property tests. Its independent analytical
validation is `deferred_to_next_version`; the current Coelli certificate
covers one material account only.

## Scope and limitations

The classic measure can identify lower-material input mixes and reductions in
ordinary technical inefficiency. It does not by itself model input-consuming
end-of-pipe abatement. Richer weak-$G$-disposability and explicit-control
models are separate production accounts. Coefficients are treated as known
and common across DMUs, not estimated or silently inferred.

NIRS/NDRS, heterogeneous or estimated coefficients,
panel/custom/external-reference source equivalence, reproduction of the
183-farm application, and welfare, causal, damage, or actual-emission claims
are also `deferred_to_next_version`. A calculated surplus is a physical
account under the declared boundary, not automatic evidence about realized
discharge or environmental harm.

```{autosummary}
MaterialBalanceCoefficients
MaterialBalanceDEA
CoelliMaterialBalanceDEA
```
