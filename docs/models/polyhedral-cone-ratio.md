# Polyhedral cone-ratio DEA

## The management question

Ordinary CCR DEA permits each organization to choose any nonnegative
supporting valuation that presents its own resource use and service delivery
as favourably as the observed production evidence permits. That flexibility
is useful, but it can conflict with information known outside the quantity
table. A regulator may regard some resource trade-offs as implausible, or a
management team may have a documented valuation policy that should constrain
the appraisal.

`PolyhedralConeRatioDEA` asks which organizations remain favourable when the
input and output valuations must belong to two explicitly declared finite
polyhedral cones. The cones are supplied as nonnegative generator matrices
`A` and `B`. They are substantive valuation information, not fitted market
prices, causal marginal products, a common weight vector, or an automatic
selection of admired organizations.

This public leaf is intentionally narrow:

- one finite, self-inclusive cross section;
- nonnegative ordinary inputs and desirable outputs;
- strictly positive transformed accounts `A x_j` and `B y_j`;
- input orientation and constant returns to scale;
- direct nonnegative sum-form generators; and
- one primary LP per organization, with no ordinary slack completion.

## Declaring a restriction

The generator columns must follow the exact variable order in `DEAData`.
Provenance is required because the same numerical matrix has a different
economic meaning when units, stakeholders, population, or validity period
change.

```python
import numpy as np
import pandas as pd

from deapack import (
    ConeRestrictionProvenance,
    DEAData,
    PolyhedralConeRatioDEA,
)

frame = pd.DataFrame(
    {
        "unit": ["A", "B", "C"],
        "staff": [10.0, 8.0, 12.0],
        "capital": [7.0, 9.0, 6.0],
        "services": [8.0, 7.0, 9.0],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="unit",
    inputs=("staff", "capital"),
    outputs="services",
)
provenance = ConeRestrictionProvenance(
    elicitation_source="approved planning memorandum 2026-04",
    stakeholder="regional service board",
    comparison_population="three comparable operating units",
    validity_period="financial year 2026/27",
    input_quantity_units=("full-time equivalents", "GBP million"),
    output_quantity_units=("thousand completed cases",),
)
model = PolyhedralConeRatioDEA(
    input_generators=np.array([[1.0, 0.2], [0.4, 1.0]]),
    output_generators=np.array([[1.0]]),
    restriction_provenance=provenance,
)
result = model.fit(data)
result.summary()
```

The result metadata retains the complete matrices, variable and generator
order, units, provenance fields, stable matrix signatures, and one combined
provenance fingerprint. Positive diagonal unit conversions require the
covariant updates `A_tilde = A C^{-1}` and `B_tilde = B D^{-1}`. Recoding a
quantity while leaving its generator column numerically unchanged changes the
restriction and can change the score.

## Reading the result without inventing targets

The native score is the input radial factor `theta`. Under self inclusion it
normally lies between zero and one. A value of one establishes measure
efficiency for this programme; it does not by itself establish the source's
stronger interior-valuation efficiency condition. Consequently
`source_efficiency_valid` remains false and `source_efficient` remains unknown
unless a future, separately sourced certificate proves existence of an
interior optimum.

The specialized `PolyhedralConeRatioResult` keeps economically different
accounts apart:

- `intensities` contains reported positive peer coefficients from the
  solver-selected optimum;
- `original_composites` compares the radial quantity account with `X lambda`
  and `Y lambda`, but explicitly labels each difference as not an ordinary
  slack;
- `cone_residuals` contains the certified transformed inequalities
  `A(theta x_o - X lambda)` and `B(Y lambda - y_o)`;
- `generator_coefficients` contains the selected `alpha` and `gamma`; and
- `multipliers` contains the reconstructed original-coordinate valuations
  `A.T @ alpha` and `B.T @ gamma`.

The cone inequalities do not generally imply componentwise dominance in the
original quantities. The result therefore exposes neither a `targets` table
nor a `slacks` table, and it never calls ordinary Pareto--Koopmans completion.

## Layered validity and solver evidence

A certified primary primal preserves `theta`, peers, original composites, and
cone residuals. Reconstructing generator coefficients and original-coordinate
multipliers additionally requires valid solver row marginals and direct
multiplier/envelopment objective agreement. If those marginals are absent,
the primal accounts remain available while `multiplier_valid` is false and the
two multiplier tables are withheld. A malformed or infeasible returned primal
withholds all published numerical accounts for that organization.

The implementation compiles one sparse transformed reference structure and
solves exactly one LP per organization. Certification performs no additional
optimization. `diagnostics` separates backend termination, primal account
validity, LP optimality evidence, multiplier validity, normalization,
transformed-cone residuals, and cross-form objective agreement.

## Evidence and exclusions

The source equations and exact boundary are recorded in the
[source protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/charnes_cooper_huang_sun_1990_polyhedral_cone_ratio.md).
The independent oracle reproduces the published 1990 Example 2 values
`85/86` and `42/43` from a direct multiplier transcription that imports no
production compiler. The documented Example 3 conflict remains excluded.

Identity generators reduce the native scores exactly to input-oriented CCR.
That reduction does not turn cone residuals into ordinary slacks, nor does it
authorize AR-I/II, half-space conversion, VRS, output orientation, common
weights, trade-offs, undesirable outputs, or panel reference policies.
