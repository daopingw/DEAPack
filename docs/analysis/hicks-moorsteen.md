# Hicks--Moorsteen productivity index

```{eval-rst}
.. currentmodule:: deapack
```

`HicksMoorsteenProductivityIndex` estimates Bjurek's adjacent-period
Hicks--Moorsteen total-factor-productivity index.
`HicksMoorsteenDEA`, `MoorsteenBjurekProductivityIndex`, and
`MoorsteenBjurekDEA` are exact API aliases for the same implementation.

The index preserves the economic definition of productivity change as an
output quantity change divided by an input quantity change:

$$
HM^{s,t}=\frac{Q^{s,t}}{X^{s,t}}.
$$

```{note}
Bjurek's source identity uses $s$ and $t$ for the two periods being compared.
They are source-local time labels: $s$ here is not DEAPack's
desirable-output dimension. Outside the source identity, $\sigma$ denotes an
evaluated-plan period and $\tau$ a reference-technology period.
```

Consequently, $HM>1$ means that aggregate output quantity grew faster than
aggregate input quantity, $HM=1$ means no measured productivity change, and
$HM<1$ means decline. An input quantity index above one records input growth;
it is not itself an improvement score.

## Exact eight-distance identity

Let $T^s$ and $T^t$ be the two contemporaneous technologies. DEAPack uses the
Shephard distance conventions

$$
D_O^\tau(x,y)=\inf\{\delta>0:(x,y/\delta)\in\mathcal T^\tau\},
\qquad
D_I^\tau(x,y)=\sup\{\delta>0:(x/\delta,y)\in\mathcal T^\tau\}.
$$

The two output quantity comparisons are

$$
Q_s=
\frac{D_O^s(x^s,y^t)}
     {D_O^s(x^s,y^s)},
\qquad
Q_t=
\frac{D_O^t(x^t,y^t)}
     {D_O^t(x^t,y^s)}.
$$

The two input quantity comparisons are

$$
X_s=
\frac{D_I^s(x^t,y^s)}
     {D_I^s(x^s,y^s)},
\qquad
X_t=
\frac{D_I^t(x^t,y^t)}
     {D_I^t(x^s,y^t)}.
$$

The reported indexes are

$$
Q^{s,t}=(Q_sQ_t)^{1/2},
\qquad
X^{s,t}=(X_sX_t)^{1/2},
\qquad
HM^{s,t}=\frac{Q^{s,t}}{X^{s,t}}.
$$

All eight component distances are retained in the summary as
`distance_output_*` and `distance_input_*` fields. Their solver records and
peer intensities are retained in `result.diagnostics` and
`result.intensities`, indexed by `distance_role`.

## Example

```python
from deapack import DEAData, HicksMoorsteenDEA, load_dataset

frame = load_dataset("productivity_panel")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    period="period",
    inputs=["capital", "labor"],
    outputs="output",
)
result = HicksMoorsteenDEA(
    returns_to_scale="vrs",
).fit(data)

result.summary()[[
    "dmu_id",
    "base_period",
    "comparison_period",
    "productivity_change",
    "output_quantity_index",
    "input_quantity_index",
]]

headline = result.plot(
    kind="performance",
    metric="productivity_change",
    period=2021,
    view="points",
)
output_quantity = result.plot(
    kind="performance",
    metric="output_quantity_index",
    period=2021,
    view="points",
)
input_quantity = result.plot(
    kind="performance",
    metric="input_quantity_index",
    period=2021,
    view="points",
)
```

For unit D from 2020 to 2021, the example gives an output quantity index of
approximately 1.1533, an input quantity index of 1.0200, and
$HM\approx1.1307$. Thus measured output quantity grows by about 15.33 percent,
input quantity grows by 2 percent, and their ratio implies productivity growth
of about 13.07 percent.

The headline plot retains the productivity interpretation: values above one
mean output quantity changed more favorably than input quantity. The two
component plots are deliberately descriptive. An output-quantity index above
one means aggregate output quantity increased; an input-quantity index above
one means aggregate input quantity increased. The latter is not automatically
an improvement. All three use one as the no-change reference, and the
component plots do not expose the source-specific $s$ and $t$ calculation
views as separate performance measures.

## Runtime release certificate

Every displayed transition is conditional on eight independently certified
distance programmes. For each task DEAPack recomputes primal feasibility,
variable bounds, the objective, KKT conditions, complementarity, and strong
duality from the returned solver evidence. It then verifies the radial-factor
and Shephard-distance account in the original physical units and reconstructs the four bilateral quantity
comparisons, their two geometric means, and $HM=Q/X$.

Quantity rows are scaled before solution, so independent positive changes of
the units used for any input or output leave the account unchanged even when
columns differ by many orders of magnitude. A strictly positive radial factor
remains inside the mathematical domain even when it is smaller than the
user's numerical tolerance; only a nonpositive factor or a nonfinite
reciprocal invalidates the corresponding Shephard distance.

The summary exposes `score_valid`, `score_status`, the number of certified and
failed distance tasks, and the maximum quantity-account violation. The
distance-level evidence remains in `result.diagnostics`, including the raw
backend status, certificate reasons, primal and dual residuals, and the
economic-account certificate. If any one of the eight programmes is
uncertified, the transition retains those diagnostics but releases no distance,
quantity-index, or headline productivity claim. Thresholded peer weights have
their own original-unit feasibility gate: an invalid peer account is withheld
without erasing a valid productivity score. Material peer weights are cached
sparsely. In each task diagnostic, `peer_valid` is an exact boolean alias of
`published_peer_account_certified`; this peer-disclosure gate remains
independent of the transition score gate.

Runtime metadata distinguishes logical work from executed work:
`requested_distance_tasks` is eight times the number of matched transitions,
`unique_distance_solves` is the number left after cache reuse, `solver_calls`
equals that unique count, and `additional_solver_calls=0` records that
certification reuses the original solver responses rather than optimizing
again.

## Pairing, technology, and failures

Transitions are matched by `dmu_id` across adjacent values in
`DEAData.period_order`; they are never paired by row position. The first period
has no transition row. `unbalanced="drop"` uses the identifier intersection
and records unmatched observations, while `unbalanced="raise"` rejects an
unbalanced adjacent pair.

The implementation supports explicitly declared CRS or VRS convex
contemporaneous technologies. NIRS and NDRS are not silently treated as
Bjurek's construction. Inputs and desirable outputs must be nonnegative, and
each observation must have a positive input aggregate and a positive output
aggregate. Undesirable outputs require a separately specified environmental
productivity method.

Every index requires all eight positive, certified distance results. If any
task fails or its claimed optimum cannot be certified, DEAPack reports a
missing productivity index and preserves the failed role, raw solver status,
and certificate reason rather than substituting a one-sided comparison.

## Interpretation limits

Hicks--Moorsteen is not an alternative spelling of the conventional
input- or output-oriented Malmquist index. It uses both an output quantity
aggregator and an input quantity aggregator and the two indexes generally
differ.

The current implementation reports the complete quantity identity
$HM=Q/X$ but does not report efficiency change, technical change, scale
change, or input/output mix change. Those components require an explicitly
defined and independently validated decomposition. The bilateral geometric
index also does not claim transitivity when several adjacent changes are
chained. Finally, results are deterministic, sample-dependent frontier
estimates; solver tolerances are not statistical uncertainty intervals.

```{autosummary}
HicksMoorsteenProductivityIndex
HicksMoorsteenDEA
MoorsteenBjurekProductivityIndex
MoorsteenBjurekDEA
```
