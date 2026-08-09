# Scale efficiency

Scale efficiency is composed from standardized CRS and VRS efficiencies:

$$
SE_o=\frac{TE_o^{CRS}}{TE_o^{VRS}}.
$$

```python
import pandas as pd

from deapack import DEAData, scale_efficiency

frame = pd.DataFrame(
    {
        "unit": ["A", "B", "C"],
        "input": [1.0, 2.0, 1.0],
        "output": [1.0, 1.0, 0.5],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="unit",
    inputs="input",
    outputs="output",
)

result = scale_efficiency(data, orientation="input")
columns = [
    "dmu_id",
    "crs_efficiency",
    "vrs_efficiency",
    "scale_efficiency",
    "score_valid",
    "is_scale_efficient",
]
print(result.summary()[columns].to_string(index=False))
```

This analysis performs two score-only component fits: one under CRS and one
under VRS. The economic technologies and scores remain distinct, while the
two fits reuse one immutable quantity-matrix compilation for each matched
comparison population. With $K$ distinct reference populations and $N$
evaluated observations, the execution contract is therefore $K$ reference
compilations and $2N$ radial LPs, with no slack-completion phase.

Top-level metadata reports the physically shared count in
`compiled_reference_sets` and the actual total in `solver_calls`.
`component_reference_sets` records each component's logical reference-set
count; those two logical counts must not be added when estimating compilation
work. This remains a composition of the shared radial engine, not an
independent model implementation.

The ratio is released only when both radial component scores are certified,
finite, and have a valid VRS denominator. The summary retains
`crs_score_valid`, `crs_score_status`, `crs_primary_solver_status` and their
`vrs_...` counterparts, then publishes its own `score_valid` and
`score_status`. A backend response that says `optimal` but fails the radial
postsolve certificate therefore produces a missing ratio and a non-optimal
composite `solver_status`; it is not silently treated as valid scale
efficiency. These checks reuse the component solutions and add no LP.

`is_scale_efficient` tests whether the CRS/VRS ratio is one only when the
evaluated plan is certified as belonging to both component technologies. It
does not say that the unit has no technical input excess or output shortfall:
both CRS and VRS efficiency can, for example, equal 0.5 while their ratio
equals one. Accordingly, the generic Pareto--Koopmans field `is_efficient`
remains missing.

With a matched external reference, the numerical ratio is still retained when
both components are valid. CRS contains the corresponding VRS technology, so
the ratio remains at most one up to tolerance even though either component
efficiency may exceed one. Such a ratio is an external institutional
comparison, not a conventional self-inclusive efficiency classification;
`is_scale_efficient` and the composite membership flag therefore remain
missing or false as appropriate. The component membership fields make that
boundary auditable.

## Validation boundary

The repository's analytical certificate checks both orientations on an exact
three-organization fixture and independently compiles the matched CRS and VRS
component programmes on a separate two-input/two-output fixture. The
certificate is limited to strictly positive cross-sectional quantities,
score-only components, and a self-inclusive full-sample global reference. It
does not certify custom or panel reference policies,
targets, local returns to scale, MPSS, capacity, scale elasticity, or
inference. See `specs/oracles/scale-efficiency-analytical.md` for the exact
claims. Separate fault-injection tests verify that failed component runtime
certificates make the composed ratio fail closed.
