# Cook--Zhu--Bi--Yang general additive network DEA

```{eval-rst}
.. currentmodule:: deapack
```

`CookZhuBiYangAdditiveDEA` implements the CRS additive efficiency
decomposition of
[Cook, Zhu, Bi, and Yang (2010)](https://doi.org/10.1016/j.ejor.2010.05.006)
for a connected directed acyclic production graph.
Its canonical method ID is `network.additive.cook_zhu_bi_yang_2010`.

```{note}
This is technical Documentation for the general additive
process-attribution route inside the existing Network DEA family. It does not
add a handbook model family or a separate book chapter.
```

The model allows:

- external resources to enter any process;
- external results to leave any process;
- observed internal links between processes;
- distinct branches that later rejoin;
- links that skip an intervening process; and
- endogenous process-input shares, with optional lower bounds.

Every internal link uses one shared nonnegative multiplier in its source
output and target input roles. The first public leaf is CRS only. It does not
provide a projection, target quantities, process peers, VRS, or a claim that
the selected process decomposition is unique.

## Process and system accounts

For process $k$, observation $j$, let

$$
A_{kj}
=
\text{valued external inputs entering }k
+
\text{valued links entering }k
$$

and

$$
B_{kj}
=
\text{valued external outputs leaving }k
+
\text{valued links leaving }k.
$$

The CRS multiplier programme for evaluated observation $o$ is

$$
\begin{aligned}
\max\quad &\sum_{k=1}^{K} B_{ko}\\
\text{subject to}\quad
&\sum_{k=1}^{K} A_{ko}=1,\\
&B_{kj}-A_{kj}\leq0,
&&k=1,\ldots,K,\quad j\in R_o,\\
&\text{all quantity multipliers}\geq0.
\end{aligned}
$$

When $A_{ko}>0$, process efficiency and its aggregation weight are

$$
\theta_{ko}=\frac{B_{ko}}{A_{ko}},
\qquad
\alpha_{ko}=\frac{A_{ko}}{\sum_{\ell=1}^{K} A_{\ell o}}.
$$

The public system score is

$$
\theta_o
=
\sum_{k=1}^{K}\alpha_{ko}\theta_{ko}
=
\frac{\sum_{k=1}^{K} B_{ko}}{\sum_{k=1}^{K} A_{ko}}.
$$

`system_efficiency` contains $\theta_o$, `weighted_process_sum` reconstructs
the weighted identity, and `reconstruction_residual` audits the difference.
The $\alpha$ values are endogenous virtual process-input shares. They are
not observed cost shares or analyst-supplied importance weights.

With a self-inclusive reference population, the system score is bounded by
one and larger is better. A process ratio can be undefined when its selected
virtual input is numerically zero; the result records that boundary rather
than inserting a hidden positive epsilon.

## Declaring the seller--buyer graph

The bundled `open_service_chain` data provide a neutral sourcing--delivery
observations in the source. Products shipped by the seller are internal
links. Buyer labor enters externally at the second process.

```python
from deapack import (
    CookZhuBiYangAdditiveDEA,
    LinkSpec,
    NetworkData,
    NetworkSpec,
    ProcessSpec,
    load_dataset,
)

frame = load_dataset("open_service_chain")
product_links = (
    "product_a",
    "product_b",
    "product_c",
)
spec = NetworkSpec(
    processes=(
        ProcessSpec(
            "seller",
            inputs=(
                "seller_labor",
                "operating_cost",
                "shipping_cost",
            ),
            outputs=product_links,
        ),
        ProcessSpec(
            "buyer",
            inputs=(*product_links, "buyer_labor"),
            outputs=("sales", "profit"),
        ),
    ),
    links=(
        LinkSpec(
            "seller_to_buyer",
            source="seller",
            target="buyer",
            variables=product_links,
        ),
    ),
)
data = NetworkData.from_frame(frame, dmu="dmu", spec=spec)

result = CookZhuBiYangAdditiveDEA().fit(data)
result.summary()[[
    "dmu_id",
    "system_efficiency",
    "weighted_process_sum",
    "reconstruction_residual",
    "score_valid",
    "process_account_valid",
    "link_account_valid",
    "decomposition_status",
]]
```

Process accounts are tidy rows rather than stage-number-specific columns:

```python
result.components[[
    "dmu_id",
    "component_id",
    "efficiency",
    "aggregation_weight",
    "virtual_input",
    "virtual_output",
    "weight_origin",
]]
```

This permits the same result schema to represent two-stage, three-stage, and
branched graphs.

## Minimum process shares

`minimum_process_share` accepts:

- a scalar applied to every process; or
- a mapping from `process_id` to a named floor.

The restriction

$$
\alpha_{ko}\geq\beta_k
$$

is implemented as $A_{ko}\geq\beta_k$ under the unit normalization. The
floors must be finite, nonnegative, and jointly feasible; their sum cannot
exceed one.

Equal seller--buyer shares can be requested explicitly:

```python
balanced = CookZhuBiYangAdditiveDEA(
    minimum_process_share={
        "seller": 0.5,
        "buyer": 0.5,
    },
).fit(data)
```

These floors alter the admissible multiplier account. They are sensitivity
or governance restrictions, not numerical tolerances. In the source example,
the equal-share restriction changes supply chain 1’s system score from
approximately 0.92495 to 0.86323.

## Three-stage open-series example

`three_process_service_chain` has an external input at every process, an external
output leaving process 2, another output leaving process 3, and links
1→2 and 2→3.

```python
frame_3 = load_dataset("three_process_service_chain")
spec_3 = NetworkSpec(
    processes=(
        ProcessSpec(
            "stage_1",
            inputs="stage_1_input",
            outputs="link_1_2",
        ),
        ProcessSpec(
            "stage_2",
            inputs=("link_1_2", "stage_2_input"),
            outputs=("stage_2_output", "link_2_3"),
        ),
        ProcessSpec(
            "stage_3",
            inputs=("link_2_3", "stage_3_input"),
            outputs="stage_3_output",
        ),
    ),
    links=(
        LinkSpec(
            "stage_1_to_stage_2",
            source="stage_1",
            target="stage_2",
            variables="link_1_2",
        ),
        LinkSpec(
            "stage_2_to_stage_3",
            source="stage_2",
            target="stage_3",
            variables="link_2_3",
        ),
    ),
)
data_3 = NetworkData.from_frame(frame_3, dmu="dmu", spec=spec_3)

result_3 = CookZhuBiYangAdditiveDEA(
    minimum_process_share=0.1,
).fit(data_3)
```

The common floor reproduces the source policy
$\alpha_{1o},\alpha_{2o},\alpha_{3o}\geq0.1$.

## Supported graph semantics

The model compiles `NetworkSpec` into a declaration-order-invariant
topological layout. Each observed variable must have one unambiguous role:

- an external input occurs as an input of one process;
- an external output occurs as an output of one process; or
- a link variable occurs exactly as an output of its declared source and an
  input of its declared target.

Distinct link variables may branch, rejoin, or skip processes. The following
are not inferred:

- splitting one observed link column across multiple targets;
- shared external-resource pools;
- joint products used by several processes;
- transformations or losses between link endpoints;
- undesirable links;
- inventories or carry-overs;
- feedback cycles; and
- disconnected process systems.

Such mechanisms require an explicit allocation, flow, environmental, or
dynamic technology.

## Decomposition status and alternate optima

The fitted LP maximizes system efficiency. It does not solve process-priority
programmes or complete bounds for process scores and weights.

`decomposition_status` records that the displayed process rows come from a
primary system optimum. It must not be read as a uniqueness certificate.
Cook et al.’s own seller--buyer tables display different process shares for
efficient unit 6 while preserving system and process scores of one. The
selected process account is therefore one admissible optimum.

Use `components` to report the selected account, and avoid wording such as
“the process’s unique weight” unless a separate identification analysis has
established it.

## Result tables

The first leaf guarantees the following network-specific outputs:

| Table | Important fields |
|---|---|
| `summary()` | system and reconstruction fields; separate score, process, and link validity/status; explicit unavailable target/peer status; unchanged backend/raw solver status |
| `components` | certified system/process rows with efficiency, aggregation weight, original-quantity virtual inputs/outputs, and account status |
| `multipliers` | certified published external-input, link, and external-output multipliers and original-quantity contributions |
| `links` | certified observed endpoints, one shared multiplier, independently matched supplier/recipient virtual contributions, balance residual, and link-account status |
| `diagnostics` | solver-neutral LP and raw/published original-quantity system/process/link/constraint-slack certificates, reasons, and residuals |

There is no source-qualified general projection in this release.
`targets` and `intensities` are empty. `links` is an observed shared-valuation
account, not an operational target plan. `projection` is not a constructor
parameter.

## Certification before result release

A backend label of `optimal` is necessary but is not sufficient to publish an
efficiency account. Before any result is released, DEAPack applies two
independent audit gates.

First, the shared solver-neutral LP certificate recomputes primal constraints,
the unit virtual-input normalization, variable bounds, and the reported
objective. It then checks row marginals, reduced-cost signs, complementarity,
Karush--Kuhn--Tucker stationarity, and strong duality. Missing, nonfinite, or
wrong-length row marginals are rejected. Lower- and upper-bound marginals are
also checked when supplied and are required whenever nonstandard finite,
fixed, or upper bounds cannot be certified through the ordinary nonnegative
cone.

Second, the Cook--Zhu--Bi--Yang certificate rebuilds raw and
publication-cleaned accounts from the originally declared quantities. Total
selected virtual input must equal one, the LP objective must equal total
selected virtual output, every reference-process constraint slack must remain
nonnegative within tolerance, minimum process shares must hold, and system
efficiency must equal the virtual-input-share-weighted process account. Each
internal product is independently valued in its supplying-output and
receiving-input roles and must have zero shared-valuation balance residual.
This gate guards against publishing an algebraically plausible solver vector
that does not represent the source model's system, process, and link accounts.

Failure is atomic and fail-closed. The summary preserves the backend's
unaltered `solver_status`--including `optimal` when that is what the backend
reported--but sets `score_valid=False`, assigns an explicit `score_status`,
and leaves every canonical score as missing. All model-derived semantic
subtables are withheld. `process_account_valid` and `link_account_valid`
therefore become false together with the headline; `target_valid` and
`peer_valid` remain false with
`not_available_in_source_contract`, because this CRS source does not define
either account. `diagnostics` retains the failed gate, reason, and residuals
so that a numerical or custom-backend problem can be investigated without
mistaking it for an economic result. Result schemas remain stable even when
every solve fails. The same contract is summarized in
`metadata["postsolve_certificate"]`.

## Reference populations

`reference` accepts `None`, a `ReferenceSpec`, or a reference-kind string.
The shared reference layer supplies global, contemporaneous, sequential,
window, biennial, and custom row policies. The model remains a static
network appraisal when fitted period by period; it is not a network
productivity index or a dynamic carry-over model.

External custom reference populations can place a system score above one.
Such values should be interpreted as benchmark-relative comparisons, not as
self-inclusive efficiency classifications.

## Admissible data and failure conditions

The current leaf requires:

- a weakly connected directed acyclic `NetworkSpec`;
- finite, nonnegative quantities;
- positive reference support for every declared variable;
- a positive aggregate process input for every process/reference row;
- shared nonnegative multipliers for every internal link; and
- a feasible set of minimum process-share floors.

Negative quantities are not translated automatically because translation
would change the ratio account. A zero process-input account can make a
selected process ratio undefined even when the system score is defined.
Graph ambiguity, cycles, unsupported data columns, or infeasible share floors
fail explicitly.

## Source boundaries and numerical oracle

The checked source supplies:

- the complete CRS multiplier programme;
- ten seller--buyer observations and system/process results;
- component-share sensitivity tables;
- a complete three-stage dataset and results under 0.1 share floors; and
- structural illustrations of branching and non-adjacent links.

The source does not print a universal incidence-matrix formulation for every
graph. The canonical node/edge layout is DEAPack’s implementation abstraction
of the source’s process roles and graph-specific examples, not a theorem
attributed to the paper.

It does not supply an equation-complete general VRS programme, VRS dual,
projection, or numerical VRS table. The public class consequently has no
`returns_to_scale` switch.

Equation (5) of the paper prints $\eta_{2k}$ once in the seller--buyer
objective, while its normalization, process constraints, efficiency
definitions, and the general equation all use $\eta_{1k}$ for the same
seller-to-buyer link. DEAPack follows the structurally coherent
$\eta_{1k}$ account and documents the printed-symbol discrepancy. In this
source-local expression, $k$ indexes linked products; it is not the core
DEAPack process index $k=1,\ldots,K$.

Source values are display-rounded. The three-stage weights, for example, can
sum to 0.99 or 1.01 after two-decimal printing. Numerical identity checks use
the unrounded fitted account.

## Numerical and performance behaviour

The default backend is SciPy/HiGHS. The graph is compiled to a canonical
topological layout, variables are grouped by external-input, link, and
external-output roles, and process constraints use sparse matrices.
Reference columns and process rows are scaled internally.

One compiled reference matrix is reused by all evaluated observations that
share a reference population. The primary leaf solves one linear programme
per evaluated observation. `tolerance` controls score, zero-denominator, and
identity checks; it does not impose a hidden process-share floor.

Execution counts are machine-readable. For $n$ evaluated observations,
`primary_solver_calls=n`, `secondary_solver_calls=0`,
`projection_fallback_solver_calls=0`, and `solver_calls=n`.
`additional_solver_calls` and `certificate_extra_solver_calls` are both zero:
all certificates inspect the completed primary solve without optimizing
again. The release benchmark checks those fields against a counting backend,
requires one compilation per reference set, and rejects missing certificates
or nonfinite residual evidence.

The constructor contract is:

```python
CookZhuBiYangAdditiveDEA(
    minimum_process_share=0.0,
    reference=None,
    solver=None,
    solver_options=None,
    tolerance=1e-7,
)
```
