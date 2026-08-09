# Scale elasticity

```{eval-rst}
.. currentmodule:: deapack
```

`scale_elasticity` puts a magnitude on the local scale question. Near the
selected efficient operating plan, it asks how many percent the maximum
proportional service bundle can change when all resources change by one
percent.

The answer can differ by decision side:

- `scale_elasticity_right` is the scale-up response;
- `scale_elasticity_left` is the scale-down response.

These are local technical responses under the estimated technology. They are
not forecasts of demand, costs, prices, staffing constraints, or the net
benefit of expansion.

## One target, one support interval

The function calls {func}`local_returns_to_scale` once. It retains that
operator's oriented VRS radial projection, Pareto completion, comparison set,
and complete interval of normalized supporting intercepts. It then transforms
the two endpoints; it does not estimate another projection or read one
arbitrary solver dual.

For an inefficient observation, the elasticities therefore describe the same
selected efficient target stored in `result.targets`. Input and output
orientation can select different targets and need not give the same answer for
an inefficient observation.

Let the maximum proportional output response at the selected efficient target
$(\widehat x_o,\widehat y_o)$ be

$$
\bar\beta(\alpha)
=
\max\{\beta\mid(\alpha \widehat x_o,\beta \widehat y_o)\in T\},
\qquad
\bar\beta(1)=1.
$$

The two local responses are

$$
\epsilon^+=\bar\beta'_+(1),
\qquad
\epsilon^-=\bar\beta'_-(1),
\qquad
\epsilon^+\leq\epsilon^-.
$$

DEAPack reports $\epsilon^+$ as the right endpoint and
$\epsilon^-$ as the left endpoint. With the package support convention

$$
v^\top x-u^\top y+\delta\geq0,
$$

the endpoint transformations are:

| Normalization | Scale-up response | Scale-down response |
|---|---:|---:|
| output, $u^\top \widehat y_o=1$ | $1-\overline\delta$ | $1-\underline\delta$ |
| input, $v^\top \widehat x_o=1$ | $1/(1+\overline\delta)$ | $1/(1+\underline\delta)$ |

The formulae agree when they are applied to the same efficient target.

## Reading the two responses

For either feasible side:

- elasticity above one means a more-than-proportional output response;
- elasticity equal to one within `rts_tolerance` means a proportional
  response;
- elasticity below one means a less-than-proportional response.

The aggregate Banker--Thrall classification is retained as
`aggregate_rts_classification`:

$$
\begin{aligned}
\mathrm{IRS}&:\quad 1<\epsilon^+\leq\epsilon^-,\\
\mathrm{DRS}&:\quad \epsilon^+\leq\epsilon^-<1,\\
\mathrm{CRS}&:\quad \epsilon^+\leq1\leq\epsilon^-.
\end{aligned}
$$

At a frontier kink, aggregate `constant` can therefore coexist with a
less-than-proportional scale-up response and a more-than-proportional loss
under scale-down. Averaging the endpoints would hide that economically useful
asymmetry, so DEAPack never reports such an average.

## Boundary values are not management instructions

An extended mathematical endpoint and a feasible operating response are
separate result fields.

- `scale_elasticity_left == inf` can mark a smallest feasible proportional
  operating boundary. In that case
  `scale_down_perturbation_exists == False` and the response label is
  `not_locally_feasible`; infinity is not presented as infinite physical
  productivity.
- `scale_elasticity_right == 0` can coexist with
  `scale_up_perturbation_exists == True`: extra resources remain feasible
  under free disposal, but they support no local increase in the maximum
  proportional output bundle.

A failed projection or unresolved support endpoint yields missing
elasticities, nullable feasibility flags, `indeterminate` response labels,
and a non-identified status rather than a guessed value.

The boundary must itself be certified. A raw backend `unbounded` report is
not enough: the inherited local-RTS result must contain a verified recession
ray. If that evidence is unavailable, `unverified_unbounded_ray` is propagated
and neither one-sided elasticity is released.

## Published seven-unit check

```python
import pandas as pd

from deapack import DEAData, scale_elasticity

frame = pd.DataFrame(
    {
        "unit": [str(i) for i in range(1, 8)],
        "input": [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0],
        "output": [1.0, 3.5, 6.0, 7.0, 8.0, 9.0, 10.0],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="unit",
    inputs="input",
    outputs="output",
)

result = scale_elasticity(data, orientation="output")
result.summary()[
    [
        "dmu_id",
        "scale_elasticity_right",
        "scale_elasticity_left",
        "scale_up_response",
        "scale_down_response",
        "aggregate_rts_classification",
    ]
]
```

The expected right endpoints are
$(5,15/7,2/3,5/7,3/8,4/9,0)$; the left endpoints are
$(+\infty,15/7,5/3,5/7,3/4,4/9,1/2)$. Unit 3 is the
important kink: a one-percent scale-up supports about $0.67\%$ more output,
whereas a one-percent scale-down loses about $1.67\%$ of output. Its
aggregate local classification is nevertheless constant.

## Result contract

The summary retains the local-RTS support and projection fields and adds:

- `scale_elasticity_right` and `scale_elasticity_left`;
- `scale_up_perturbation_exists` and
  `scale_down_perturbation_exists`;
- `scale_elasticity_right_is_extended` and
  `scale_elasticity_left_is_extended`;
- `scale_up_response` and `scale_down_response`;
- `scale_elasticity_is_unique` and `scale_elasticity_status`;
- `scale_elasticity_valid`, `scale_elasticity_domain_valid`, and
  `scale_elasticity_economic_postsolve_certified`;
- `scale_elasticity_right_valid`, `scale_elasticity_left_valid`, and their
  matching `*_status` fields;
- `scale_elasticity_max_transform_violation` and
  `scale_elasticity_failure_kind`;
- `aggregate_rts_classification`.

The selected target, slacks, peers, and endpoint diagnostics remain available
through the common result object. Metadata records the orientation-specific
formula, support sign convention, selected-projection scope, and dependency
on `analysis.returns_to_scale.local.banker_thrall_1992`.
The generic `score`, `efficiency`, `distance`, and `is_efficient` fields remain
missing: scale elasticity is a post-estimation response diagnostic, not
another efficiency percentage.

The transform is released only after five checks agree: the inherited support
interval is valid, both endpoints are valid, the orientation-specific formula
is in its mathematical domain, the right endpoint does not exceed the left,
and the resulting pair satisfies the retained IRS/CRS/DRS identity. This
independent check prevents a forged or accidentally exchanged economic label
from passing merely because two endpoint numbers are available.

`scale_elasticity_status` and `scale_elasticity_failure_kind` keep mathematical
and numerical cases separate. Certified finite, extended, and asymptotic
boundaries are identified results. `mathematically_undefined` denotes a
support-to-elasticity transform outside the radial domain while preserving the
underlying backend status. Projection failures, uncertified finite endpoints,
and unverified unbounded rays remain distinct certificate failures.

The inherited `backend_solver_status`, `raw_solver_status`, endpoint statuses,
and local-RTS certificate fields remain in the summary. Thus consumers can
audit the numerical evidence without treating a backend label as an economic
conclusion. Result columns are stable for success and all-failure runs.

## Solve accounting

`scale_elasticity` calls the local-RTS route once and transforms its certified
interval in memory. It therefore uses the same four required solves per
resolved observation—projection, Pareto completion, and two support
endpoints—and adds no fifth solve. Metadata carries
`projection_solver_calls`, `support_endpoint_solver_calls`, `solver_calls`,
`compiled_reference_sets`, and `additional_solver_calls=0`. Its
`postsolve_certificate` and the nested local-RTS certificate both record zero
additional optimization calls.

## Scope boundaries

- The public leaf is radial, convex VRS, and restricted to inputs and
  desirable outputs.
- Directional, partial, environmental, network-stage, and non-convex FDH
  scale responses are separate methods.
- MPSS is a global scale-target question and is not inferred from these local
  endpoints.
- A local IRS result is not by itself a recommendation to expand. A decision
  also needs demand, prices and costs, quasi-fixed resources, service
  obligations, risk, and implementation constraints.

The implementation follows [Førsund and Hjalmarsson
(2004)](https://doi.org/10.1057/palgrave.jors.2601741) and the convex-
technology treatment in [Podinovski
(2017)](https://doi.org/10.1016/j.ejor.2016.09.029).

```{autosummary}
scale_elasticity
```
