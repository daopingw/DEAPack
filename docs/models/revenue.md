# Revenue efficiency

`RevenueEfficiency` asks how much revenue an organization could earn from its
available input capacity if it chose the best attainable output mix at the
prices it faces.

For observation $o$, let $x_o$ be available inputs, $y_o$ observed
desirable outputs, and $p_o>0$ output prices. The model solves

$$
R_o^*=\max_{\lambda\geq0}\;p_o^\top Y\lambda
\quad\text{subject to}\quad
X\lambda\leq x_o,
$$

with $\mathbf 1^\top\lambda=1$ under VRS and no convexity equality under CRS.
Observed revenue and higher-is-better revenue efficiency are

$$
R_o=p_o^\top y_o,
\qquad
RE_o=\frac{R_o}{R_o^*}.
$$

The summary retains `observed_revenue`, `maximum_revenue`, `revenue_gap`,
`revenue_expansion_ratio`, and `revenue_efficiency`. `score` and `efficiency`
both contain $RE_o$; `distance` is missing because this value measure is not
reported as a technical distance. `is_revenue_efficient` tests the revenue
criterion. It is not copied into `is_efficient`, because a
revenue-maximizing activity can still use more input than necessary and the
current model does not run a Pareto--Koopmans completion.

## Example

```python
from deapack import DEAData, PriceData, RevenueEfficiency, load_dataset

frame = load_dataset("revenue_5x2")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["input_1", "input_2"],
    outputs=["output_1", "output_2"],
)
prices = PriceData.common(
    output_prices={"output_1": 3.0, "output_2": 2.0}
)

result = RevenueEfficiency(returns_to_scale="vrs").fit(data, prices)
result.summary()[
    [
        "dmu_id",
        "observed_revenue",
        "maximum_revenue",
        "revenue_efficiency",
    ]
]
```

The bundled example is also an exact regression oracle. Under VRS its maximum
revenues are $45,46,44,46,46$; under CRS they are
$59,46,44,92,121$. The difference is economically material: CRS permits
scaling observed activities, whereas VRS restricts the comparison to their
convex hull.

## Price and data contract

Prices are supplied through `PriceData`, separately from production
quantities. Output-price names must match every desirable-output name exactly.
Common or observation-specific prices are supported; keyed prices align by DMU
and period rather than row order. Prices must be finite and strictly positive.
Panel monetary comparisons additionally require an explicit currency and base
period.

Revenue metadata records only the output-price contract and a stable
cryptographic signature, not the confidential price payload. Supplying
unrelated input prices therefore does not alter the fitted revenue
specification.

The ordinary revenue model accepts nonnegative inputs and desirable outputs,
requires positive observed revenue, and rejects undesirable outputs. An
environmental revenue model needs an explicit environmental technology and is
not inferred from a `bad_outputs` column.

## Targets, peers, and duals

Targets are labeled `revenue_maximizing_activity`. They report both
$X\lambda^*$, the input use of the selected activity, and $Y\lambda^*$,
its output mix. Unused input capacity is legitimate and is not relabeled as a
technical input slack. Because an LP can have several revenue-maximizing
activities, target uniqueness is reported as unknown.

Input-capacity duals are model-derived local marginal revenues. They describe
the value of a small relaxation within the fitted empirical technology, not an
observed market price or a causal estimate.

## Certified release contract

DEAPack does not treat a backend `optimal` label as a complete economic
certificate. It checks primal and dual optimality and then reconstructs the
input-capacity account, target outputs, maximum revenue, revenue gap, expansion
ratio, and reciprocal efficiency. No additional LP is solved for these checks.

`score_valid` is false when the certified maximum-revenue denominator is not
strictly positive. Targets may still be valid in that case, so their status is
reported separately. `target_valid`, `peer_valid`, and `dual_valid` must be
used for the corresponding tables. An uncertified source programme or revenue
account withholds all derived semantic claims for the affected observation but
keeps observed revenue and raw diagnostics. A peer reporting threshold can
withhold only the displayed intensities, and an incomplete dual publisher can
withhold only the dual table.

The published maximum, gap, and ratios are the same raw account that passed
certification. They are not independently rounded or set to zero afterward;
this preserves the public identities even when valid monetary values are very
small.

## External references and undefined ratios

The familiar bounds $0<RE_o\leq1$ require the evaluated activity to belong
to its reference technology. A custom external reference can produce
`revenue_efficiency > 1` and a negative revenue gap; DEAPack retains that
comparison instead of clipping it. `is_revenue_efficient` remains missing for
that external comparison because membership-based efficiency classification
is not licensed.

An external VRS reference can be infeasible when none of its activities fits
within the evaluated input capacity. Under CRS, an admissible reference can
also yield zero maximum revenue. In that case the optimization result is
retained, but the ratio is missing and `score_status` identifies the invalid
denominator. Solver failures and undefined ratios are never converted into a
normal-looking score.
