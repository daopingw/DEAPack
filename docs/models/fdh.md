# Free-disposal hull

```{eval-rst}
.. currentmodule:: deapack
```

`FreeDisposalHullDEA` (`FDH`) benchmarks each organization against observed
operating plans without averaging those plans. It is appropriate when
facilities, service models, or production systems are indivisible enough that
a synthetic convex mixture would not be a credible operating opportunity.

For reference observations $j=1,\ldots,n$, the estimated technology is

$$
\widehat{\mathcal T}_{FDH}
=
\left\{(x,y):
\text{some }j\text{ satisfies }x_j\leq x,\;y_j\geq y
\right\}.
$$

This set admits using more inputs or delivering fewer desirable outputs than
an observed plan. It does **not** admit convex combinations or arbitrary
rescaling of observations. FDH consequently has no `returns_to_scale`
parameter and must not be represented as a CCR/BCC switch.

## Native scores

For input orientation, an eligible reference must deliver at least $y_o$.
Its required common input factor is the largest component ratio, and FDH
chooses the smallest such factor:

$$
\theta_o
=
\min_{j:y_j\geq y_o}
\max_{i:x_{io}>0}\frac{x_{ij}}{x_{io}}.
$$

If $x_{io}=0$, eligibility additionally requires $x_{ij}=0$; no epsilon is
inserted into the denominator. `score` and `efficiency` both report
$\theta_o$.

For output orientation, an eligible reference must use no more than $x_o$:

$$
\phi_o
=
\max_{j:x_j\leq x_o}
\min_{r:y_{ro}>0}\frac{y_{rj}}{y_{ro}}.
$$

Zero components of $y_o$ do not constrain the common expansion factor and
remain available as output slack. `score` reports the native expansion
$\phi_o$ and `efficiency` reports $1/\phi_o$ when $\phi_o>0$.

With ordinary self-inclusive references, input efficiency and reciprocal
output efficiency lie in $[0,1]$. An explicit custom reference can exclude
the evaluated observation. DEAPack then retains the native comparison but
sets efficiency classifications to missing when the observation lies outside
that reference technology.

## Peers, targets, and ties

Every FDH benchmark uses one observed activity. When several observations
give the same radial optimum, `result.peers(...)` returns every alternative:

- each row has `lambda=1`;
- `alternative_rank` makes the alternatives explicit;
- `is_primary` identifies the peer used for reported targets and slacks.

These rows are mutually alternative binary activations. Their `lambda`
values must **not** be summed or interpreted as a convex combination.
With `compute_slacks=True`, the primary peer is selected lexicographically by
the largest unweighted residual input and output improvement. With
`compute_slacks=False`, strong efficiency is deliberately left unclassified.
`tie_tolerance` can widen the list of near-equal peers shown for reporting,
but it never widens the set admitted to slack completion; that certification
always uses the model's stricter numerical `tolerance`.

## Direct dominance algorithm

The implementation uses a vectorized, chunked dominance-and-ratio scan. It
does not formulate a mixed-integer program, invoke an LP solver, or add an
external solver dependency. `chunk_size` bounds temporary memory while
leaving results unchanged. If no single observation satisfies the relevant
dominance conditions, the evaluated row is reported as `infeasible` rather
than being rescued by an undocumented interpolation.

## Validation boundary

The repository's analytical certificate exhaustively enumerates all eligible
single-activity comparisons for an exact five-organization, two-input,
two-output fixture. It checks both orientations, native and harmonized scores,
candidate counts, radial and strong status, the selected observed peer,
targets, and residual slacks through the public API. The certificate is
synthetic and is not a reproduction of a published result table. It does not
extend to partial frontiers, undesirable outputs, sampling inference,
external-reference extrapolation, FCH, or FRH. See
`specs/oracles/fdh-analytical.md` for the exact claim.

```python
from deapack import DEAData, FDH, load_dataset

frame = load_dataset("frontier_1x1")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs="input",
    outputs="output",
)

result = FDH(orientation="output").fit(data)
result.summary()[["dmu_id", "score", "efficiency"]]
```

FDH intentionally rejects declared undesirable outputs. Pollution,
failures, or other unwanted consequences require an explicit environmental
production technology.

```{autosummary}
FreeDisposalHullDEA
FDH
```
