# Bounded-adjusted measure (BAM)

```{eval-rst}
.. currentmodule:: deapack
```

`BoundedAdjustedDEA` implements the 2011 Cooper et al. bounded-adjusted
measure. It is a non-oriented, non-radial account of an analyst-declared
operating counterfactual: inputs may fall and desirable outputs may rise in
the same benchmark plan.

## Score and programme

For evaluated organization $o$, define its sample-supported input-reduction
and output-expansion rooms as

$$
L_{io}=x_{io}-\underline{x}_i,
\qquad
U_{ro}=\overline{y}_r-y_{ro},
$$

where $\underline{x}_i=\min_jx_{ij}$ and
$\overline{y}_r=\max_jy_{rj}$ are calculated over the same frozen global
population used to construct the frontier. BAM maximizes

$$
\delta_o^{BAM}
=\frac{1}{m+s}
\left(
\sum_i\frac{s_i^-}{L_{io}}
+\sum_r\frac{s_r^+}{U_{ro}}
\right)
$$

subject to

$$
X\lambda+s^-=x_o,\qquad
Y\lambda-s^+=y_o,
$$

the selected returns-to-scale restriction, and the explicit bounds

$$
0\le s_i^-\le L_{io},\qquad
0\le s_r^+\le U_{ro}.
$$

If a one-sided room is zero, its ratio is defined to contribute zero and the
corresponding slack is fixed at zero. The reported values are

$$
\texttt{distance}=\delta_o^{BAM},\qquad
\texttt{score}=\texttt{efficiency}=1-\delta_o^{BAM}.
$$

Both values are bounded by zero and one under this contract. A high
efficiency means that little of the organization's sample-supported
improvement room remains attainable jointly; it is not a cost-saving,
profit, welfare, or causal effect.

## Basic use

```python
import pandas as pd

from deapack import BAM, DEAData

frame = pd.DataFrame(
    {
        "unit": ["A", "B", "C"],
        "staff": [1.0, 3.0, 2.0],
        "service": [0.1, 4.0, 1.0],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="unit",
    inputs="staff",
    outputs="service",
)

result = BAM(returns_to_scale="vrs").fit(data)
result.summary()
result.slacks
result.targets_for("C")
result.peers("C")
```

`BAM` is an exact discoverability alias for `BoundedAdjustedDEA`; there is one
implementation and one canonical method ID, `static.bam`.

## Returns to scale

`returns_to_scale` accepts:

- `"crs"`: no intensity-sum restriction;
- `"vrs"`: $\mathbf 1^\top\lambda=1$, the default;
- `"nirs"`: $\mathbf 1^\top\lambda\le1$; and
- `"ndrs"`: $\mathbf 1^\top\lambda\ge1$.

DEAPack applies both families of one-sided slack bounds under every
returns-to-scale assumption. Some bounds are mathematically redundant under
particular assumptions, but retaining the complete bounded programme keeps
the score contract explicit and prevents an unbounded additive task under
CRS.

## Result contract

The one-row-per-observation summary adds:

- `distance`: BAM normalized inefficiency;
- `score` and `efficiency`: one minus BAM inefficiency;
- `is_efficient`: tolerance-based status using normalized slacks;
- `max_slack`: the largest physical slack;
- `max_normalized_slack`: the largest one-sided-room share;
- `returns_to_scale`, `reference_size`, and `solver_status`.

`result.slacks` records the physical `slack`, DMU-specific `weight`,
`slack_upper_bound`, and `normalized_slack` for every variable.
`result.targets` preserves the observed-to-target quantity balance;
`result.intensities`, `result.duals`, and `result.diagnostics` use the common
DEAPack contracts.

Metadata records the sample input lower bounds, output upper bounds,
zero-room policy, returns to scale, effective solver tolerances, reference
kind, and canonical registry composition. The numerical LP optimizes each
bounded normalized slack directly. VRS balances are reference-anchored before row
scaling; the remaining RTS paths use level-scaled balances. Physical slacks
and targets are recovered only after the normalized solution is certified,
so a small measurement unit is not erased by an absolute cleanup threshold.
A solver failure yields missing scores and no partial target, peer, dual, or
efficiency claim.

## Supported domain and reference policy

The first public leaf deliberately requires:

- finite, nonnegative inputs and desirable outputs;
- at least one positive input and output for each organization;
- no undesirable-output column;
- one global population for both the sample bounds and frontier.

For cross-sectional data, the default `reference="auto"` resolves to that
global population. Panel data must say `reference="global"` explicitly.
Custom, contemporaneous, window, sequential, biennial, and group-specific
bound populations are not silently inferred. Signed-data and environmental
BAM formulations or compositions require separate source-qualified
contracts.

Positive independent changes of measurement units leave BAM scores unchanged.
The regression contract spans reciprocal coordinate scales as far apart as
$10^{40}$, and peer reporting retains a numerically small intensity whenever
its quantities materially reconstruct the target.
General translation invariance is not claimed by this four-RTS,
nonnegative-data leaf.

## Validation and provenance

The VRS and bounded-CRS score vectors for the 12-DMU, two-input, two-output
example in Cooper, Seiford, and Tone (2007, Table 1.5) were solved separately
with archived GPL-2 `additiveDEA` 1.1/lp_solve and a direct SciPy/HiGHS
formulation. DEAPack matches both vectors to numerical tolerance. Tests also
cover NIRS/NDRS behavior, zero rooms, positive-unit invariance, physical
target balances, invalid domains, and injected solver failure.

Cooper et al. (2011) apply BAM to the 108 Japanese water utilities originally
reported by Aida et al. (1998). The complete source table is readable in the
[CMU author archive](https://iiif.library.cmu.edu/file/Cooper_box0010c_fld00001_bdl0001_doc0001/Cooper_box0010c_fld00001_bdl0001_doc0001.pdf),
but the archive labels it
[In Copyright](http://rightsstatements.org/vocab/InC/1.0/) and several
scanned/printed cells need reconciliation. DEAPack therefore does not bundle
or silently transcribe that table.

## What this class is not

This class does not implement the later Enhanced BAM, natural or managerial
bounds, partially bounded variables, undesirable outputs, or alternative
time/group-specific bound populations. RAM is also distinct: it divides every
organization's slack by one common full sample range, whereas BAM uses each
organization's remaining one-sided room.

```{autosummary}
BoundedAdjustedDEA
BAM
```
