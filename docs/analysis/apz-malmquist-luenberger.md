# APZ consistent Malmquist--Luenberger index

```{eval-rst}
.. currentmodule:: deapack
```

`APZMalmquistLuenbergerProductivityIndex` implements the consistency-qualified
environmental productivity account proposed by Aparicio, Pastor, and Zofío
(2013) and operationalized as a general DEA programme by Aparicio et al.
(2017). `APZMalmquistLuenbergerDEA` is its exact alias.

This is a source-qualified preset. It combines the familiar four-distance
Malmquist--Luenberger accounting formula with a distinct capped bad-output
technology; it is not a sign correction or post-processing option for
`MalmquistLuenbergerProductivityIndex`.

## Frozen contract

For an evaluated observation $(x_o^h,y_o^h,b_o^h)$ and a contemporaneous
technology from period $s$, the model maximizes $\beta$ subject to

$$
\begin{aligned}
Y^s\lambda &\ge y_o^h+\beta y_o^h,\\
B^s\lambda &\le b_o^h-\beta b_o^h,\\
X^s\lambda &\le x_o^h,\\
b_o^h-\beta b_o^h &\le \bar b^s,\\
\lambda &\ge 0,
\end{aligned}
$$

where each component of $\bar b^s$ is the largest observed value of that
undesirable output in reference period $s$. There is no convexity row, so the
technology is CRS. The scalar $\beta$ is unrestricted; a cross-period distance
may be negative.

The public preset fixes:

- zero input direction and observation-scaled desirable- and undesirable-output
  directions;
- one full contemporaneous reference set and one componentwise bad-output cap
  per period;
- the four adjacent-period own/cross evaluations;
- strictly positive input and undesirable-output components, and nonnegative
  desirable outputs; and
- `unbalanced="drop"` or `unbalanced="raise"` for unmatched adjacent DMUs.

The positivity requirement is part of the source-qualified compactness
certificate. A future zero-cell extension would be a separately identified
package method, not a silent relaxation of this preset.

## Result and diagnostics contract

The four distance fields and the $ML=EC_{ML}\times TC_{ML}$ formulas are the
same accounting roles documented for the classic
{doc}`Malmquist--Luenberger index <malmquist-luenberger>`. Their production
technology is not the same.

Every task-level diagnostic records `bad_output_cap`, including an infeasible
task. An optimal task additionally populates:

- `directional_bad_target`: $b_o-\beta b_o$;
- `peer_bad_output`: $B^s\lambda$;
- `bad_output_surplus`: the target minus the peer combination;
- `bad_output_cap_slack`: $\bar b^s-(b_o-\beta b_o)$; and
- `bad_output_cap_binding`: undesirable-output accounts whose cap is binding
  within the model tolerance.

The directional target and the peer combination are intentionally distinct:
the APZ bad-output row is an inequality. The result metadata also preserves all
period-specific caps, the source-domain contract, solver counts, and the 2013
`A7` / 2017 `A2` source labels.

All input, desirable-output, undesirable-output, and cap rows are scaled by
their own positive account magnitude before the LP is sent to the backend.
The reported beta is then reconstructed against the original physical
quantities. Consequently, replacing tonnes by kilograms in one column and
millions by units in another cannot change a certified APZ result; only a
genuine change in the production account can do so.

APZ shares only the solver-neutral and four-distance release machinery with the
classic index. Its economic certificate is source-specific: it independently
rebuilds the input and desirable-output balances, the bad-output inequality,
the contemporaneous componentwise cap, nonnegative intensities, and
`objective = -beta`. It therefore accepts a legitimate positive bad-output
surplus instead of incorrectly imposing the CFG equality. All four tasks and the
multiplicative account must certify before a transition is released; thresholded
peers retain a separate gate, and the checks add no optimization task. In each
task diagnostic, `peer_valid` is the exact boolean alias of
`published_peer_account_certified`; this peer-disclosure result does not alter
the score gate. APZ is a source-qualified environmental-productivity preset.

Cached peer weights are stored only at their material sparse positions, while
metadata distinguishes the four logical requests per matched transition from
executed work: `unique_distance_solves` is the count after cache reuse,
`solver_calls` equals it, and `additional_solver_calls=0` makes the
no-extra-solve claim directly auditable.

## Exact source-data oracle

```python
import pandas as pd

from deapack import APZMalmquistLuenbergerDEA, DEAData

frame = pd.DataFrame(
    {
        "dmu": ["A", "B", "A", "B"],
        "period": [0, 0, 1, 1],
        "x": [1.0, 1.0, 1.0, 1.0],
        "y": [7.0, 5.0, 8.0, 5.5],
        "b": [2.0, 5.0, 1.0, 3.0],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    period="period",
    inputs="x",
    outputs="y",
    bad_outputs="b",
)
result = APZMalmquistLuenbergerDEA().fit(data)

result.summary().query("dmu_id == 'B'")[[
    "productivity_change",
    "efficiency_change",
    "technical_change",
]]
```

For unit B, the four APZ distances are
$(2/5,3/11,3/5,5/11)$. Consequently,

$$
ML=\frac{11}{10},\qquad
EC_{ML}=\frac{77}{80},\qquad
TC_{ML}=\frac{8}{7}.
$$

The repository derives these values independently from the published LP and
2013 table. It does not claim to reproduce the 39-country empirical panel in
the 2017 article because the processed unit-level panel is not contained in the
paper.

## What APZ does—and does not—change

| Method | Bad-output account | Temporal reference | Reported opportunity component |
|---|---|---|---|
| Classic CFG ML | common-factor equality | four contemporaneous own/cross tasks | `technical_change` |
| APZ ML | inequality plus a reference-period componentwise cap | the same four roles, all re-solved | `technical_change` |
| Oh GML | common-factor equality | own-period plus one fixed global technology | `best_practice_change` |

APZ can restore some comparisons that are infeasible under the equality
technology, but the 2017 source does not claim that every cross-period task
must become feasible. If any task fails, DEAPack retains all role-level
diagnostics and leaves the multiplicative transition undefined. It also fails
closed when any factor $1+D$ is nonpositive.

```{autosummary}
APZMalmquistLuenbergerProductivityIndex
APZMalmquistLuenbergerDEA
```
