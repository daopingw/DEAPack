# Kalhor--Kazemi Matin environmental general-network radial DEA

```{eval-rst}
.. currentmodule:: deapack
```

`KalhorKazemiMatinNetworkDEA` implements the corrected activity-specific
weak-disposal technology and input-radial programme of Kalhor and Kazemi
Matin (2018). It evaluates a declared general process graph as one coordinated
organization and returns one system score.

Defining source:

- [official DOI record](https://doi.org/10.1051/ro/2017022);
- [open article PDF at Numdam](https://www.numdam.org/item/10.1051/ro/2017022.pdf).

The implemented source boundary is:

| Element | Implemented contract |
|---|---|
| Technology | corrected general-network technology, source equation (3.2) |
| Measure | input-radial programme, source equations (3.3)--(3.4) |
| Native score | system input factor $h$ |
| Weak disposal | activity-specific $\alpha_j^p/\beta_j^p$ linearization |
| Process efficiencies | not defined |
| Secondary slack completion | not run |
| Directional-distance variant | `deferred_to_next_version` |
| Spanish-airport DDF application | `deferred_to_next_version` |

```{important}
This class does not implement a network directional distance function, a
network SBM, process-efficiency decomposition, pollution-treatment
technology, or material balance. In particular, setting a direction is not a
hidden option on this estimator. The paper's 2008 Spanish-airport application
and the observations it delegates to Lozano and coauthors have not completed
an independent data--formula--result closure either.
```

## Public objects

The environmental graph and its observations are constructed with:

- `EnvironmentalNetworkSpec`;
- `EnvironmentalNetworkData`;
- `ProcessSpec`, `LinkSpec`, `NetworkSpec`, or the
  `TwoStageSeriesSpec` convenience declaration; and
- `KalhorKazemiMatinNetworkDEA`.

All are exported from top-level `deapack`.

## Complete executable example

The bundled recovery chain is a neutral teaching case for the defining
technology; it does not reproduce a paper table.

```python
from deapack import (
    EnvironmentalNetworkData,
    EnvironmentalNetworkSpec,
    KalhorKazemiMatinNetworkDEA,
    TwoStageSeriesSpec,
    load_dataset,
)

frame = load_dataset("environmental_recovery_chain")

graph = TwoStageSeriesSpec(
    inputs="resource_input",
    intermediates="sorted_material",
    outputs=("recovered_service", "residual_load"),
    stage_names=("stage_1", "stage_2"),
)

spec = EnvironmentalNetworkSpec(
    network_spec=graph,
    input_accounts="resource_input",
    desirable_output_accounts="recovered_service",
    undesirable_output_accounts="residual_load",
)

data = EnvironmentalNetworkData.from_frame(
    frame,
    dmu="unit",
    spec=spec,
)

result = KalhorKazemiMatinNetworkDEA(
    returns_to_scale="vrs",
).fit(data)

result.summary()[[
    "dmu_id",
    "system_efficiency",
    "is_system_radially_efficient",
    "score_status",
]]
```

Selected intensities and targets can be inspected directly:

```python
c_intensities = (
    result.intensities[result.intensities["dmu_id"] == "residual_control"]
    [[
        "process_id",
        "reference_dmu_id",
        "alpha",
        "beta",
        "total_intensity",
        "retained_operating_rate",
    ]]
    .sort_values(["process_id", "reference_dmu_id"])
)

c_targets = (
    result.targets[result.targets["dmu_id"] == "residual_control"]
    [[
        "role",
        "account_id",
        "observed",
        "target",
        "downstream_requirement",
    ]]
)
```

The package also contains `environmental_circular_chain`, a neutral
four-process, two-handoff teaching ledger. Its CRS fit is useful for checking
the separate intermediate accounts without treating the result as a paper
table reproduction.

## Environmental account specification

`EnvironmentalNetworkSpec` overlays economic roles on an already declared
production graph. Account declarations accept a variable name, a sequence of
variable names, or a mapping from account ID to member variables. A sequence
creates one singleton economic account per variable; only a mapping combines
several columns into one account.

```python
EnvironmentalNetworkSpec(
    network_spec=graph,
    input_accounts={
        "labor": ("nursing_hours", "technician_hours"),
        "energy": "electricity",
    },
    desirable_output_accounts={
        "completed_care": (
            "internal_clinical_service",
            "final_discharges",
        ),
    },
    undesirable_output_accounts={
        "care_burden": (
            "internal_complication_load",
            "final_readmissions",
        ),
    },
    intermediate_accounts={
        "case_handoff": ("diagnosed_cases",),
    },
)
```

The declaration enforces the following partition:

| Role | Graph requirement | Model treatment |
|---|---|---|
| input account | partitions every external graph input | reference use enters through $\alpha+\beta$ |
| desirable output account | classifies a subset of external outputs and may include internal links | gross active generation minus internal active use must cover the final good |
| undesirable output account | disjoint from desirable accounts; together the two output roles partition all external outputs and may include internal links | gross active generation minus internal active use equals the final bad |
| ordinary intermediate account | partitions links not classified as desirable or undesirable | each producer's active supply covers recipient $\alpha+\beta$ requirement |

When `intermediate_accounts` is omitted, every remaining link variable
receives its own account. Explicit mappings are required when several
physical columns constitute one economic product account.

The specification exposes deterministic ownership helpers:

```python
spec.variable_owner("intermediate")
spec.link_for_variable("intermediate")
spec.variables_for_account("input")
spec.variables_for_role("undesirable_output")
```

`EnvironmentalNetworkData.from_frame(...)` validates observations against
the graph and account semantics. `account_matrix(account_id)` returns a
read-only matrix in canonical member order. `semantic_fingerprint` identifies
the graph-plus-account contract; it excludes observed quantities.

## Technology and input-radial programme

For process $p$ and reference observation $j$:

- $\alpha_j^p\geq0$ is retained active reference activity;
- $\beta_j^p\geq0$ is its complementary activity-specific weak-disposal
  component; and
- $\beta_j^p=0$ when process $p$ produces no declared undesirable output.

The total process intensity is $\alpha_j^p+\beta_j^p$. Inputs and ordinary
intermediate requirements use this total. Desirable and undesirable output
generation uses only $\alpha_j^p$.

For external input account $i$, desirable account $r$, undesirable account
$b$, and producer-specific ordinary-intermediate account $(d,p)$, define:

- $X_i(\alpha+\beta)$: total reference input use;
- $G_r(\alpha)$ and $G_b(\alpha)$: gross active output generation;
- $U_r(\alpha)$ and $U_b(\alpha)$: internal active use;
- $S_{dp}(\alpha)$: active supply from producer $p$; and
- $R_{dp}(\alpha+\beta)$: requirements selected by its recipients.

Equations (3.2)--(3.4) then have the account form

$$
\begin{aligned}
\min_{h,\alpha,\beta}\quad &h\\
\text{subject to}\quad
&X_i(\alpha+\beta)\leq h x_{io}
&&\forall i,\\
&G_r(\alpha)-U_r(\alpha)\geq y_{ro}^{\mathrm{out}}
&&\forall r,\\
&G_b(\alpha)-U_b(\alpha)=u_{bo}^{\mathrm{out}}
&&\forall b,\\
&S_{dp}(\alpha)\geq R_{dp}(\alpha+\beta)
&&\forall d,p,\\
&\mathcal R_p(\alpha+\beta)
&&\forall p,\\
&\alpha_j^p,\beta_j^p\geq0,\qquad
  \beta_j^p=0\ \text{for }p\notin\mathcal P_B.
\end{aligned}
$$

$\mathcal R_p$ is the declared process-level returns-to-scale restriction:

| Value | Restriction for each process |
|---|---|
| `"crs"` | no intensity-sum row |
| `"vrs"` | $\sum_j(\alpha_j^p+\beta_j^p)=1$ |
| `"nirs"` | $\sum_j(\alpha_j^p+\beta_j^p)\leq1$ |
| `"ndrs"` | $\sum_j(\alpha_j^p+\beta_j^p)\geq1$ |

The default is `"vrs"`. Scale restrictions apply separately to every
process, not once to the complete system. The article's primary programme and
first numerical example are VRS; its second example supplies the published
CRS score oracle. NIRS and NDRS are source-described substitutions realized
and independently checked by the package, without a claimed published
numerical oracle.

## Meaning of `beta`

`beta` is a linear weak-disposal component. It is not:

- measured pollutant removal;
- a physical disposal or treatment flow;
- an emissions price or damage weight;
- treatment capacity or abatement expenditure; or
- process inefficiency.

For a positive total process-reference intensity, the returned
`retained_operating_rate` is

$$
\frac{\alpha_j^p}{\alpha_j^p+\beta_j^p}.
$$

It describes the selected comparator activity. Both `alpha` and `beta`
remain intensity variables. A study with observed capture, recycling,
treatment inputs, or mass conservation requires an explicit source-qualified
treatment or material-balance model.

## Score semantics

`score`, `efficiency`, `system_score`, and `system_efficiency` all contain the
optimal input factor $h$.

With a self-inclusive reference population, $0\leq h\leq1$ and one denotes
system input-radial efficiency. `is_system_radially_efficient` tests this
condition within `tolerance`.

An external custom reference population can require $h>1$. The descriptive
score is retained. `is_within_reference_technology` reports whether the
evaluated plan lies within the selected reference technology, operationally
$h\leq1+\text{tolerance}$. When this condition fails, the usual radial
efficiency classification is withheld.

`is_efficient` remains missing. The primary programme does not perform a
secondary residual-slack optimization and therefore does not certify
Pareto--Koopmans efficiency. `components` contains only a `system` component;
process efficiencies are not defined by the source measure.

## Result tables

| Table | Important fields |
|---|---|
| `summary()` | `system_efficiency`, radial-system flag, reference size, RTS, score/target status, `process_efficiencies_defined=False`, account residuals, and omitted intensity mass |
| `components` | the single system component |
| `intensities` | process and reference IDs, `alpha`, `beta`, `total_intensity`, retained operating rate, and whether the process produces a bad |
| `targets` | role, account ID and members, observed value, target, constraint bound/residual, gross/internal output fields, or downstream requirement |
| `links` | source and recipient, flow kind, variable-level active supply/use and beta-supported requirement, plus the account-level balance values and certified `balance_scope` |
| `diagnostics` | solver status plus independent primal, bounds, objective, dual, and economic-account certificates |

The target roles are:

- `external_input_account`;
- `final_desirable_output_account`;
- `final_undesirable_output_account`; and
- `ordinary_intermediate_account`.

For an ordinary intermediate, `target` is producer supply and
`downstream_requirement` is recipient demand. For an environmental account,
the final target is gross active generation less internal active use.

### Link balance scope

Rows in `links` contain both variable-level contributions and the scope of the
economic constraint:

| `balance_scope` | Meaning |
|---|---|
| `link` | the producer-product account contains exactly one ordinary link; `source_minus_requirement` is the constrained balance |
| `producer_product_account` | several ordinary link variables share one producer-product account; use `account_source_supply`, `account_downstream_requirement`, and `account_balance_surplus` |
| `system_product_account` | an internal desirable or undesirable flow is settled through the system-wide gross-generation-minus-internal-use output account |

`balance_is_link_specific` is true only in the first case. For a pooled
producer-product account, an individual row's `source_minus_requirement` may
be negative; the technology constrains the aggregated
`account_balance_surplus`, not every constituent link independently.
Environmental output links do not receive an ordinary-intermediate
nonnegative balance.

Targets and links are reconstructed from complete, unthresholded intensity
vectors. `peer_tolerance` controls only which small total intensities appear
in `intensities`; `max_omitted_total_intensity` discloses omitted mass.

The LP has no secondary target-selection objective. `projection_policy` is
`solver_selected_primary_optimum`. Alternate optimal peer portfolios and
targets can therefore accompany the same system score.

## Constructor and solver contract

```python
KalhorKazemiMatinNetworkDEA(
    *,
    returns_to_scale="vrs",
    reference=None,
    solver=None,
    solver_options=None,
    tolerance=1e-7,
    peer_tolerance=None,
)
```

| Parameter | Contract |
|---|---|
| `returns_to_scale` | `"crs"`, `"vrs"`, `"nirs"`, or `"ndrs"` |
| `reference` | `ReferenceSpec`, reference-kind string, or `None` for auto |
| `solver` | custom object implementing the public LP solver protocol |
| `solver_options` | options for the default SciPy/HiGHS backend; mutually exclusive with `solver` |
| `tolerance` | positive finite acceptance threshold for numerical and economic certificates |
| `peer_tolerance` | positive finite display threshold; defaults to `tolerance` |

`fit(data)` accepts only `EnvironmentalNetworkData`.

The default backend is SciPy/HiGHS. The graph-account block is compiled as
sparse matrices once per distinct reference population and reused. Exactly
one primary LP is solved per evaluated observation. Scores and canonical
plans are withheld when the solver or independent certificate fails.

## Reference populations

`reference=None` creates `ReferenceSpec(kind="auto")`. A cross-section then
uses the global sample; a panel uses contemporaneous observations. Global,
contemporaneous, sequential, window, biennial, and custom reference policies
follow the common reference-set contract where their data requirements are
met.

A custom set uses global row positions:

```python
from deapack import ReferenceSpec

external_model = KalhorKazemiMatinNetworkDEA(
    reference=ReferenceSpec(
        kind="custom",
        custom_rows=(0, 1),
    ),
)
```

The same custom set is used for every evaluated observation. Excluded
organizations cannot silently re-enter through process-specific peer
intensities.

## Data domain and validation

The current model requires:

- finite, nonnegative ratio-scale quantities;
- a valid `NetworkSpec` with one declared occurrence for every graph
  variable and explicit links for internal transfers;
- input accounts that partition all external inputs;
- disjoint desirable and undesirable accounts that classify every external
  output;
- intermediate accounts that partition all otherwise unclassified link
  variables;
- positive aggregate external input for every evaluated observation;
- for every producer process represented in every desirable or undesirable
  product account, at least one final external member from that same process;
  and
- positive support across observations for each such process--product final
  part, without pooling support from another producer.

General directed graphs, including cycles, are admitted when their variable
incidence and accounts satisfy these rules.

Negative values are rejected rather than translated. A translation changes a
radial production account.

## Unit invariance

The score is invariant to independent positive rescaling of each complete
economic account. If one account contains process-specific, internal, and
final parts of the same product, every member must be rescaled together.

Account targets, source supply, and recipient requirement co-transform into
the new unit. The dimensionless score and intensities do not. Scaling only
one fragment of a multi-variable account changes the represented technology
and is not a unit conversion.

## Provenance and numerical oracles

The result metadata includes:

```python
result.metadata["method_id"]
# network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018

result.metadata["source_boundary"]
# {
#     "technology": "Kalhor_Kazemi_Matin_2018_equation_3_2",
#     "measure": "input_radial_equations_3_3_to_3_4",
#     "directional_distance_variant": "deferred_to_next_version",
#     "process_efficiencies": "not_defined",
# }
```

The repository verifies both published examples with an independent dense
SciPy `linprog` compiler that does not call the implementation's private LP
construction. It also tests all four RTS restrictions, account-level unit
invariance, custom-reference exclusion, sparse compilation, one solve per
observation, and source-boundary metadata.

The maintained page records the public economic interpretation, formulation,
source boundary, and verification claims needed to use this method without
depending on private editorial material.
