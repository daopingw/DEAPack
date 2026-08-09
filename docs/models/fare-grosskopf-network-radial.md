# Färe--Grosskopf two-stage intermediate-products radial DEA

```{eval-rst}
.. currentmodule:: deapack
```

`FareGrosskopfNetworkRadialDEA` measures one coordinated radial performance
account for a two-process organization. Input orientation asks how much of the
external-resource commitment could be released while preserving final
services. Output orientation asks how much final service could be expanded
within the current external-resource commitment. The upstream process may
learn from one peer combination and the downstream process from another, but
the downstream plan cannot require more of an intermediate product than the
upstream plan can supply.

The CRS technology belongs to the network-production framework of
[Färe and Grosskopf (2000)](https://doi.org/10.1016/S0038-0121(99)00012-9).
[Färe and Grosskopf (1996), equation (12)](https://doi.org/10.1016/0165-1765(95)00729-6)
computes an output distance on a CRS intermediate-products network by
maximizing a common final-output expansion. The output programme below is the
closed two-stage series restriction of that source account: external inputs
enter the upstream process, final outputs leave the downstream process, and
the intermediate handoff remains endogenous. These sources also contain
broader allocations and network constructions; this class does not claim
coverage of those additional accounts.
The separately convex VRS statement used by this implementation is documented
by
[Podinovski and Bouzdine-Chameeva (2021)](https://doi.org/10.1007/s11123-021-00610-3).
The VRS option is therefore a later source-qualified extension; it is not
attributed to either Färe--Grosskopf article.

```{important}
This leaf defines one **system** radial score. It does not define stage
efficiencies or a system-to-stage decomposition. Use the distinct
{doc}`kao-hwang-network` leaf when the research question requires the
Kao--Hwang relational stage account.
```

## Complete example

The insurance data used by Kao and Hwang supply a familiar two-process
organization. Expenses support premium acquisition; the two premium measures
are internal products; and underwriting and investment profits are final
outcomes.

```python
from deapack import (
    FareGrosskopfNetworkRadialDEA,
    NetworkData,
    TwoStageSeriesSpec,
    load_dataset,
)

frame = load_dataset("two_stage_public_service")
spec = TwoStageSeriesSpec(
    inputs=("operation_expenses", "insurance_expenses"),
    intermediates=(
        "direct_written_premiums",
        "reinsurance_premiums",
    ),
    outputs=("underwriting_profit", "investment_profit"),
    stage_names=("premium_acquisition", "profit_generation"),
    link_id="premium_handoff",
)
data = NetworkData.from_frame(frame, dmu="company", spec=spec)

result = FareGrosskopfNetworkRadialDEA(
    orientation="output",
    returns_to_scale="crs",
).fit(data)

result.summary()[[
    "dmu_id",
    "system_score",
    "system_efficiency",
    "is_system_radially_efficient",
    "has_link_disposal",
    "score_valid",
    "target_valid",
    "peer_valid",
    "score_status",
]]
```

The default is `orientation="input"`; the example makes the output choice
explicit. The repository verifies the matched CRS system account against an
independently compiled Kao--Hwang primary programme on all 24 insurers and
checks the output programme against a production-independent dense compiler.
That is conditional equation, duality, and cross-implementation evidence. It
is **not** a claim that Färe and Grosskopf published this insurance table or
that an original Färe--Grosskopf numerical table has been reproduced.

## Technology and score

Let $X$, $Z$, and $Y$ contain the external inputs, intermediate products, and
final outputs of the reference organizations. For evaluated organization
$o$, the input-oriented programme is

$$
\begin{aligned}
\min_{\theta,\lambda,\mu}\quad &\theta\\
\text{subject to}\quad
&X\lambda\leq\theta x_o,\\
&Z\mu\leq Z\lambda,\\
&Y\mu\geq y_o,\\
&\lambda,\mu\geq0.
\end{aligned}
$$

It protects the final-service commitment $y_o$ and minimizes the common
external-resource retention factor $\theta_o$. The output-oriented programme
uses the same connected technology but protects the current external-resource
commitment:

$$
\begin{aligned}
\max_{\phi,\lambda,\mu}\quad &\phi\\
\text{subject to}\quad
&X\lambda\leq x_o,\\
&Z\mu\leq Z\lambda,\\
&Y\mu\geq\phi y_o,\\
&\lambda,\mu\geq0.
\end{aligned}
$$

Here $\phi_o$ is the largest common expansion of the represented final
services that the current external-resource commitment can support. This is
the closed-series output-distance account obtained from the CRS source
equation cited above; it is not a separately named model or method ID.

$\lambda$ describes the upstream reference plan and $\mu$ the downstream
reference plan. The middle inequality is the internal operating commitment:
upstream supply $Z\lambda$ must cover downstream requirement $Z\mu$. Their
difference may be disposed of under this technology.

```{important}
The evaluated organization's observed intermediate vector $z_o$ is **not
held fixed** in either programme. The score asks what internally coordinated
handoff the system could support while either preserving $y_o$ with a smaller
external-resource commitment or expanding $y_o$ within the current resource
commitment. Observed intermediates help construct the reference technology
when their organization belongs to the comparison population, and they are
retained in the link table for comparison with the benchmark, but they are not
a conditioning constraint. A model that instead
requires $Z\lambda\geq z_o$ and $Z\mu\leq z_o$ answers a different,
conditional-on-the-observed-handoff question.
```

For VRS, the implementation adds two separate convexity conditions,

$$
\mathbf 1^\top\lambda=1,
\qquad
\mathbf 1^\top\mu=1.
$$

Separate conditions matter. They let each process benchmark itself against a
convex portfolio while preserving the internal-flow commitment; one
system-wide convexity row or a common intensity vector would define a
different empirical technology. The output-oriented VRS option therefore
composes the source-qualified output-distance measure with this later
separately convex technology; equation (12) itself remains a CRS source.

The result separates the native optimization factor from the common
higher-is-better efficiency convention:

| Orientation | `score` and `system_score` | `efficiency` and `system_efficiency` |
|---|---|---|
| input | $\theta_o$ | $\theta_o$ |
| output | $\phi_o$ | $1/\phi_o$ |

With a self-inclusive reference population, ordinarily
$0\leq\theta_o\leq1$ and $\phi_o\geq1$; the corresponding system efficiency
lies in $[0,1]$ and one denotes radial system efficiency. An external custom
reference population can reverse those usual native-factor bounds. The value
is retained, and `is_within_reference_technology` records whether the usual
classification is supported. For output orientation,
`efficiency_denominator_valid` also records whether the certified native
factor can be inverted safely.

`is_system_radially_efficient` tests whether the certified harmonized system
efficiency is one. Generic `is_efficient` remains missing because the model
does not perform a residual-slack completion that would certify
Pareto--Koopmans efficiency.

## Exact CRS score relation to Kao--Hwang

On a matched closed two-stage CRS domain, conic scaling makes the input and
output native factors reciprocal: $\theta_o=1/\phi_o$. The input programme is
also the envelopment dual of the **primary system-score** programme used by
`KaoHwangRelationalDEA`. Consequently, `system_efficiency` from either radial
orientation equals the Kao--Hwang primary system score when all of the
following match. The output-native `system_score` remains $\phi_o$ and is not
itself equal to that higher-is-better value.

- external inputs enter only the first process;
- the same intermediate quantity columns construct the reference technology;
- neither implementation fixes the evaluated organization's observed
  intermediate vector as a conditioning value;
- final outputs leave only the second process;
- both processes have separate nonnegative reference intensities;
- the link permits upstream supply to exceed downstream requirement;
- the comparison population is identical; and
- returns to scale are CRS.

This is an identity of the harmonized primary system efficiency, not an API
alias or equality of complete results. The Färe--Grosskopf leaf returns no
intermediate multipliers, stage ratios, product decomposition, stage-score
ranges, or Lim--Zhu midpoint selection. The Kao--Hwang leaf adds precisely
those valuation, attribution, and reporting decisions. Input and output
efficiencies need not coincide under VRS. The identity is not extended to VRS,
open networks, shared resources, environmental links, or other performance
measures.

## Reading targets and internal flows

The selected primary optimum supplies three linked accounts:

- `targets` contains the upstream external-input plan $X\lambda$ and
  downstream final-output plan $Y\mu$;
- `intensities` keeps positive `upstream_lambda` and `downstream_mu`
  reference activities separately; and
- `links` contains upstream supply, downstream requirement, and disposable
  surplus for every intermediate. Its `observed` field is the organization's
  reported handoff for comparison, and
  `observed_is_conditioning_value=False` prevents it from being mistaken for
  a fitted constraint.

The target table preserves the orientation-specific operating commitment.
For input orientation, the external-input constraint bound is
$\theta_o x_o$ and the final-output bound is $y_o$. For output orientation,
those bounds are $x_o$ and $\phi_o y_o$. The reported targets are the selected
plans $X\lambda$ and $Y\mu$, so a target may improve beyond its radial bound
when the primary LP has residual slack. No residual-slack completion is used,
and neither orientation turns these targets into process-efficiency scores.

```python
result.links_for("Fubon")[[
    "variable",
    "observed",
    "upstream_supply",
    "downstream_requirement",
    "disposable_surplus",
]]
```

There is no single fitted intermediate target in this result. The upstream
and downstream endpoints describe the internal feasibility interval, and
`common_link_target_defined` is false. Selecting a midpoint, a minimum-change
handoff, or another internal operating target would be an additional policy,
not a fact supplied by this primary programme.

The primary LP can have alternate optima. Consequently, target quantities,
peer portfolios, and disposable surplus are labelled
`projection_policy="primary_system_optimum"` and may be solver selected even
when the system score is unique. Substantive reporting should distinguish the
stable system score from the selected illustrative plan.

The `intensities` table retains coefficients strictly above
`peer_tolerance`. Target and link accounts are always reconstructed from the
complete, unthresholded solution. The summary fields
`upstream_omitted_intensity_sum` and
`downstream_omitted_intensity_sum` disclose any coefficient mass omitted from
the display table; under VRS this also reveals whether the displayed
coefficients still sum to one. `peer_valid` is a separate publication gate:
if thresholding prevents the displayed peers from reconstructing the
certified operating plan within `tolerance`, peer rows are withheld while the
certified system score, targets, and links remain available. This display
failure does not trigger another optimization.

## Result tables

| Table | Important fields |
|---|---|
| `summary()` | orientation-qualified native `system_score`, harmonized `system_efficiency`, `score_valid`, `target_valid`, `peer_valid`, their statuses, `efficiency_denominator_valid`, radial-efficiency status, reference size, observed-intermediate conditioning flag, omitted intensity sums, and link-disposal/residual diagnostics |
| `components` | the single system component with native `score` and harmonized `efficiency`; no stage components |
| `intensities` | process ID, reference organization, and separate upstream/downstream intensity roles |
| `targets` | external-input and final-output observed values, targets, constraint bounds, and residuals |
| `links` | observed intermediate, its non-conditioning flag, upstream supply, downstream requirement, disposable surplus, and balance residual |
| `diagnostics` | raw backend status plus the shared solver-neutral LP certificate and separate raw-solution, published-target, and thresholded-peer economic-account certificates |

The native score, component, targets, and link plan are released atomically
only after both the shared LP certificate and the raw and published economic
accounts pass. If any of these primary gates fails, those values are missing
and no semantic table is emitted for that organization. The raw backend
`solver_status` is preserved in both summary and diagnostics, including when
an alleged optimum fails independent certification, and another organization
may still succeed. An unbounded output-expansion programme therefore fails
closed rather than fabricating a reciprocal efficiency. Peer disclosure has
the narrower independent gate described above: a thresholded peer account can
be withheld without retracting a certified score or target plan.

## Reference populations and admissible domain

`reference` accepts a `ReferenceSpec` or a reference-kind string. Under
`"auto"`, a cross-section uses all observations and a panel uses
contemporaneous observations. One sparse quantity block is compiled for each
distinct reference population and reused across its evaluated organizations.
The model solves one primary LP per observation.

The current leaf requires:

- exactly two processes and one directed intermediate link;
- every first-process output to be a declared intermediate and every
  second-process input to be that intermediate;
- process-specific upstream and downstream intensities;
- the upstream-supply-at-least-downstream-requirement link policy;
- distinct columns for external inputs, intermediates, and final outputs;
- finite nonnegative quantities;
- positive aggregate external input and final output for every evaluated
  organization; and
- positive reference support for every declared quantity column.

CRS and VRS are supported. NIRS and NDRS, exogenous second-process inputs,
first-process final outputs, exact handoffs, common process intensities,
shared-resource pools, undesirable intermediates, cycles, and general graphs
require other source-qualified leaves. Negative data are rejected rather than
translated because translation changes the radial production account.

## Numerical behavior

The default backend is SciPy/HiGHS. Quantity columns are scaled internally and
all reported plans are returned in original units. The implementation checks
primal feasibility, bounds, the reported objective, dual marginals, KKT
stationarity, complementarity, and strong duality through the shared
solver-neutral LP certificate. It then reconstructs the complete network
account twice: first from the raw solver vector and then from the numerical
values eligible for publication. A third account checks whether thresholded
peer rows still reproduce that published plan. `tolerance` controls these
certificates. `peer_tolerance` only controls which small positive intensities
are retained for display. Certification performs no additional solve.

The repeatable `benchmarks/benchmark_network_radial.py` fixture accepts both
orientations and reports the selected orientation, elapsed time,
optimal/score/target/peer certificate counts, independently counted primary
solves and compilations, sparse matrix shape and density, all three economic
account residuals, and link-disposal incidence. It asserts that metadata agrees
with the observed execution: the input and output programmes both reuse one
sparse quantity block per reference set, solve exactly one primary LP per
observation, and add no certification solve. Benchmark timings are
machine-specific regression observations, not runtime guarantees.

```{autosummary}
FareGrosskopfNetworkRadialDEA
NetworkData
TwoStageSeriesSpec
```
