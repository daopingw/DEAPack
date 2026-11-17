# Built-in datasets

DEAPack includes small datasets for trying models without preparing a file.
Load a dataset as a pandas table, then inspect its columns:

```python
from deapack import load_dataset

frame = load_dataset("environmental_panel")
frame.head()
```

The examples below write out the actual column names so you can see what is
being modeled. They are grouped by teaching purpose:

- foundations and economic accounts: `frontier_1x1`, `slacks_2x2`,
  `economic_efficiency_4`, `cost_mix_choice`, `coordination_hulls`,
  `integer_coordination_hulls`, `clinic_capacity`, and
  `community_hospital_capstone`;
- directional, scale, and metafrontier analysis: `range_directional_signed`,
  `metafrontier_groups`, and `ren_cas_directional_scale`;
- price-informed revenue analysis: `revenue_5x2` and `revenue_8x2`;
- productivity and environmental accounts: `productivity_panel`,
  `environmental_panel`, `zhou_ang_wang_non_chp_3`,
  `environmental_disposability_contrast`,
  `by_production_component_bottleneck`, `environmental_recovery_chain`, and
  `environmental_circular_chain`;
- connected-production accounts: `network_2stage`,
  `two_stage_public_service`, `open_service_chain`,
  `three_process_service_chain`, `crs_free_link_service_chain`, and
  `strategic_peer_service`;
- multi-period systems: `multiperiod_trajectory_contrast`,
  `dynamic_capacity_backlog`, `dynamic_carryover_portfolio`, and
  `dynamic_network_power_demo`; and
- non-radial and leave-one-out diagnostics: `sbm_slack_contrast`,
  `super_sbm_peer_replacement`, and `directional_super_multivariate_stress`.

Most are deterministic project-authored teaching cases. The separately
attributed open numerical datasets retained in the catalogue are
`ren_cas_directional_scale`, `revenue_5x2`, and `revenue_8x2`. Dataset
metadata state roles and intended teaching uses; a dataset name is not a
claim that its variables or results transfer to another empirical setting.

## Comparing cost, revenue, and profit

`economic_efficiency_4` is the common teaching case for price-informed
efficiency. Its one resource, two services, and common prices stay fixed while
the decision question changes:

```python
from deapack import (
    CostEfficiency,
    DEAData,
    PriceData,
    ProfitEfficiency,
    RevenueEfficiency,
    load_dataset,
)

frame = load_dataset("economic_efficiency_4")
data = DEAData.from_frame(
    frame,
    dmu="plan",
    inputs=["resource"],
    outputs=["standard_service", "premium_service"],
)
prices = PriceData.common(
    input_prices={"resource": 2.0},
    output_prices={
        "standard_service": 3.0,
        "premium_service": 5.0,
    },
)

cost = CostEfficiency(returns_to_scale="vrs").fit(data, prices)
revenue = RevenueEfficiency(returns_to_scale="vrs").fit(data, prices)
profit = ProfitEfficiency().fit(data, prices)
```

For plan D, observed and minimum cost are 12 and 7, observed and maximum
revenue are 19 and 37, and observed and maximum profit are 7 and 27. These are
different counterfactuals over the same empirical technology. The fixture is
synthetic and analytically checked; it is not a published-data reproduction.

## Non-CHP energy--carbon decision accounts

`zhou_ang_wang_non_chp_3` contains three strictly positive, comparable
electricity systems without combined heat and power:

```python
from deapack import DEAData, NonCHPEnergyCarbonDEA, load_dataset

frame = load_dataset("zhou_ang_wang_non_chp_3")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["fossil_energy"],
    outputs=["electricity"],
    bad_outputs=["co2"],
)

result = NonCHPEnergyCarbonDEA(
    account="integrated_energy_carbon",
).fit(data)
```

The fixture is derived from the source equations. For system O, it gives
component steps $(\beta_F,\beta_E,\beta_C)=(0,1,1/2)$, raw non-radial
distance $1/2$, integrated performance index $3/8$, and target $(2,2,2)$.
The same observations deliberately produce different answers under the
energy and carbon accounts because those accounts protect and improve
different operating roles.

These are analytical teaching data, not observations from Zhou, Ang, and
Wang's 126-country application. The complete country-level reference data
are not available in the article or an audited source bundle. See
{doc}`../models/zhou-ang-wang-non-chp` for the three-account contract and the
CHP evidence boundary.

## Environmental process-network oracles

`environmental_recovery_chain` and `environmental_circular_chain` are neutral
teaching ledgers for environmental network contracts. The first isolates a
two-process recovery handoff and residual-control trade-off; the second keeps
two material/support handoffs distinct across a four-process circular-service
chain. They support structural checks, not empirical claims or unique targets.
See
{doc}`../models/kalhor-kazemi-matin-environmental-network`.

## Signed data for a range directional measure

`range_directional_signed` contains one signed input and one signed desirable
output:

```python
from deapack import DEAData, RDM, load_dataset

frame = load_dataset("range_directional_signed")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["input"],
    outputs=["output"],
)

result = RDM().fit(data)
result.summary()
```

The three rows are small enough to verify without another package. C has
input and output ranges 4 and 8; the exact common feasible share is
$\beta_C=2/3$, supported by
$\lambda_A=2/3$ and $\lambda_B=1/3$. Its RDM efficiency is $1/3$, and its
declared directional target, peer activity, and residual slacks can be
inspected separately.

The negative input and output entries test a signed numerical domain. They do
not declare the output undesirable. The dataset is synthetic and theory-led;
Portela, Thanassoulis, and Simpson's bank-branch observations are
confidential and are not reproduced. See {doc}`../models/range-directional`.

## Comparing declared technology groups

`metafrontier_groups` contains six organizations in two declared technology
groups:

```python
from deapack import DEAData, MetafrontierDEA, load_dataset

frame = load_dataset("metafrontier_groups")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    group="technology_group",
    inputs=["resource"],
    outputs=["service"],
)

result = MetafrontierDEA().fit(data)
result.summary()
```

Group 1 demonstrates one service per resource unit; group 2 demonstrates
two. DMU C is inefficient within group 1, so the example contains both a
within-group performance shortfall and a gap between the group and pooled
frontiers. All expected values are exact under input/output orientation and
CRS/VRS.

The data are synthetic and theory-led. They verify the
O'Donnell--Rao--Battese radial decomposition but are not a reconstruction of
the paper's 97-country FAO application. See
{doc}`../analysis/metafrontier` for the complete fit, interpretation, and
pooled-convexification contract.

## Deferred clinic-capacity fixture

`clinic_capacity` is retained as a deterministic development fixture, not as a
current public-method example. The associated physical-capacity prototype is
non-public and deferred to the next version, so this guide intentionally gives
no fitting recipe or interpretation of capacity results. Its evidence audit
is tracked in the
[FGK physical-capacity source protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/fare_grosskopf_kokkelenberg_1989_capacity.md).

## Whole operating modules

`integer_coordination_hulls` contains three neutral project plans for
contrasting indivisible peer choice, integer replication, and continuous
relaxation:

```python
from deapack import DEAData, FRH, load_dataset

frame = load_dataset("integer_coordination_hulls")
data = DEAData.from_frame(
    frame,
    dmu="unit_id",
    inputs=["resource"],
    outputs=["service"],
)

result = FRH(orientation="input").fit(data)
```

The example is useful when branches, production lines, or service modules can
be copied only as complete units. It does not establish that every real
organization is indivisible. The analyst must justify that production
assumption from the operating context.

## Distinct organizations available once

`coordination_hulls` contains four project-authored observations used to
distinguish FDH, the Green--Cook FCH, FRH, CCR, and VRS:

```python
from deapack import DEAData, FCH, load_dataset

frame = load_dataset("coordination_hulls")
data = DEAData.from_frame(
    frame,
    dmu="organization",
    inputs=["resource"],
    outputs=["service"],
)

result = FCH(orientation="input").fit(data)
result.summary()
```

For E, the input factor is $0.70$, supported by the binary coalition
A+B. The data are synthetic and isolate the activity-combination assumption;
they do not recommend a merger or assert that the variables of a real
application are additive.

## Relative-rate scale scenarios

`ren_cas_directional_scale` reproduces all 16 observations in Table 1 of Ren
et al. (2021):

```python
from deapack import (
    DEAData,
    load_dataset,
    relative_directional_scale_elasticity,
)

frame = load_dataset("ren_cas_directional_scale")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["staff", "research_expenditure"],
    outputs=["external_funding", "high_sci_publications", "granted_patents"],
)

result = relative_directional_scale_elasticity(
    data,
    input_relative_direction=(1.0, 1.0),
    output_relative_direction=(0.75, 0.75, 1.50),
)
```

The observations support exact reproduction of the article's DMU 2 scale-up
and scale-down results. They are historical published data for verification
and teaching, not evidence that the direction vectors were elicited
institutional preferences.

## SBM slack contrast

`sbm_slack_contrast` contains three neutral plans with two resources and two
service measures.
It supports input-, output-, and non-oriented SBM with one role declaration:

```python
from deapack import (
    DEAData,
    InputSBM,
    OutputSBM,
    SBM,
    load_dataset,
)

frame = load_dataset("sbm_slack_contrast")
data = DEAData.from_frame(
    frame,
    dmu="unit_id",
    inputs=["resource_a", "resource_b"],
    outputs=["core_service", "quality_service"],
)

input_result = InputSBM(returns_to_scale="crs").fit(data)
output_result = OutputSBM(returns_to_scale="crs").fit(data)
joint_result = SBM(returns_to_scale="crs").fit(data)
```

The contrast is designed to make radial and variable-specific slack accounts
visibly different. The two oriented results remain useful for showing why
resource conservation, service expansion, and joint improvement are distinct
managerial questions.

## Environmental disposability contrast

`environmental_disposability_contrast` contains two neutral plans with
separable and jointly adjusted service/residual accounts. It is an analytical
contrast, not a paper-table reproduction:

```python
from deapack import (
    DEAData,
    ToneNonSeparableSBM,
    UndesirableSBM,
    load_dataset,
)

separable_frame = load_dataset("environmental_disposability_contrast")
separable_data = DEAData.from_frame(
    separable_frame,
    dmu="unit_id",
    inputs=["resource_a", "resource_b"],
    outputs=["joint_service", "independent_service"],
    bad_outputs=["joint_residual", "independent_residual"],
)
separable_result = UndesirableSBM(
    returns_to_scale="vrs",
).fit(separable_data)
```

The same frame exposes a jointly changing service/residual pair and an
independently adjustable pair. Declare the jointly changing variables explicitly
in the hybrid estimator. Continue in the same session:

```python
hybrid_frame = load_dataset("environmental_disposability_contrast")
hybrid_data = DEAData.from_frame(
    hybrid_frame,
    dmu="unit_id",
    inputs=["resource_a", "resource_b"],
    outputs=["joint_service", "independent_service"],
    bad_outputs=["joint_residual", "independent_residual"],
)

hybrid_result = ToneNonSeparableSBM(
    nonseparable_outputs=["joint_service"],
    nonseparable_bad_outputs=["joint_residual"],
    alpha_min=0.7,
    returns_to_scale="vrs",
).fit(hybrid_data)

hybrid_result.summary()
```

Here `alpha` is the retained share of the declared joint operating process,
not a generic weak-disposability parameter. A non-separable target is
`alpha * observed`; its peer `reference_activity` may be better than that
declared projection. The difference is returned as an unscored residual.

The hybrid result makes the declared joint-account choice inspectable. It does
not establish an environmental partition for another production process. See
{doc}`../models/undesirable-sbm` for the model contract.

## Super-SBM peer-replacement contrast

`super_sbm_peer_replacement` contains three efficient resource mixes and one
dominated plan for self-exclusion diagnostics.

```python
from deapack import DEAData, ToneSuperSBM, load_dataset

frame = load_dataset("super_sbm_peer_replacement")
data = DEAData.from_frame(
    frame,
    dmu="unit_id",
    inputs=["resource_a", "resource_b"],
    outputs=["service"],
)

result = ToneSuperSBM(
    orientation="non-oriented",
    returns_to_scale="crs",
).fit(data)
result.summary()
```

The score ranks how difficult a strongly SBM-efficient record is for the
remaining peer population to replace under the model's variable-specific
resource and service account. It is not an efficiency percentage. Targets
and intensities are one solver-selected replacement plan and may differ
across alternate optima even when the ranking value is stable.

## Directional super-efficiency stress case

`directional_super_multivariate_stress` contains a documented neutral
multivariate schedule for leave-one-out directional appraisal:

```python
from deapack import (
    DEAData,
    RayDirectionalSuperEfficiency,
    load_dataset,
)

frame = load_dataset("directional_super_multivariate_stress")
data = DEAData.from_frame(
    frame,
    dmu="unit_id",
    inputs=["input_1", "input_2", "input_3", "input_4"],
    outputs=["output_1", "output_2"],
)

result = RayDirectionalSuperEfficiency().fit(data)
result.summary()
```

The case distinguishes a joint peer-replacement concession from an efficiency
percentage. Its stress schedules are synthetic teaching inputs, not evidence
about the causes of performance. See
{doc}`../evaluation/directional-super-efficiency` for the invalid-projection
policy.

## Two-stage public-service network

`two_stage_public_service` contains two system inputs, two intermediate
screening measures, and two final service measures:

```python
from deapack import (
    ChenCookLiZhuAdditiveDEA,
    KaoHwangRelationalDEA,
    NetworkData,
    TwoStageSeriesSpec,
    load_dataset,
)

frame = load_dataset("two_stage_public_service")

spec = TwoStageSeriesSpec(
    inputs=["staff_hours", "platform_cost_units"],
    intermediates=["screened_cases", "verified_value"],
    outputs=["timely_closures", "public_value"],
    stage_names=("screening", "service_delivery"),
)
data = NetworkData.from_frame(
    frame,
    dmu="unit",
    spec=spec,
)
result = KaoHwangRelationalDEA().fit(data)
additive_result = ChenCookLiZhuAdditiveDEA(
    returns_to_scale="vrs",
).fit(data)
```

The project-authored case includes a proportional scale pair, a resource-drag
plan, a conversion-drag plan, and a different service mix. It supports
relational and additive network examples, stage-account interpretation, and
link-feasible target checks without representing an insurance-industry
sample. The Kao--Hwang and Chen--Cook--Li--Zhu method references and equations
remain documented in {doc}`../models/kao-hwang-network` and
{doc}`../models/chen-additive-network`.

## Open service chains

`open_service_chain` represents a sourcing process handing three order flows
to a delivery process. Sourcing resources enter upstream, while service hours
enter only after the handoff. Delivered value and retained margin are final
service outcomes. This makes it an open production network rather than a
closed two-stage chain:

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
handoffs = ["standard_orders", "priority_orders", "bulk_orders"]
sourcing = ProcessSpec(
    "sourcing",
    inputs=["sourcing_hours", "platform_units", "transport_units"],
    outputs=handoffs,
)
delivery = ProcessSpec(
    "delivery",
    inputs=["standard_orders", "priority_orders", "bulk_orders", "service_hours"],
    outputs=["delivered_value", "retained_margin"],
)
spec = NetworkSpec(
    processes=(sourcing, delivery),
    links=(
        LinkSpec(
            "orders",
            source="sourcing",
            target="delivery",
            variables=handoffs,
        ),
    ),
)
data = NetworkData.from_frame(frame, dmu="unit", spec=spec)
result = CookZhuBiYangAdditiveDEA().fit(data)
```

The case includes a proportional scale pair and deliberately different
resource and service mixes. A `minimum_process_share` setting changes the
admissible valuation policy and therefore is not merely a display choice.

`three_process_service_chain` adds outside resources and final services at its
middle and final processes. Both datasets are deterministic project cases for
software verification and teaching; they are not current supply-chain
performance samples. The Cook--Zhu--Bi--Yang model source, equations, and
scope are documented in {doc}`../models/cook-general-additive-network`.

## Network-SBM service-chain contrasts

`three_process_service_chain` exposes a neutral three-process service case for
VRS/input network-SBM fixed/free comparison.
`crs_free_link_service_chain` exposes a compact CRS/free-link contrast:

```python
from deapack import load_dataset

service_chain = load_dataset("three_process_service_chain")

crs_example = load_dataset("crs_free_link_service_chain")
```

The first case supports process and system reconstruction, fixed/free link
comparisons, and target-feasibility checks. The second contains an explicit
proportional scale pair for the CRS/free-link contract. Both are
project-authored observations; solver-selected peer bases and targets are not
treated as unique when alternate optima exist. Tone and Tsutsui's model
source, equations, and orientation boundary remain documented in
{doc}`../models/tone-tsutsui-network-sbm`.

The historical provincial panel from DEAPack 0.1.x is not an installed 2.0
dataset. Its provenance, variable definitions, and redistribution basis are
incomplete. The CSV has been removed from the public tree, its former loader
identity is retired with no data alias, and this paragraph is the only
non-numerical migration note. In release-contract terms, the
tracked CSV has been removed. A later version may add a properly sourced and
licensed panel under a new reviewed identity.

## Capacity and backlog commitments

`dynamic_capacity_backlog` is a compact teaching account for the existing
classic Dynamic SBM family. Prepared and Strained each use one unit of
resource to provide one unit of service in two consecutive periods. Prepared
enters each period with capacity 2 and backlog 1; Strained has capacity 1 and
backlog 2.

```python
from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    PeriodProductionSpec,
    load_dataset,
)

frame = load_dataset("dynamic_capacity_backlog")
spec = DynamicSBMSpec(
    production=PeriodProductionSpec(
        inputs=["resource"],
        outputs=["service"],
    ),
    carryovers=(
        CarryOverSpec("capacity", "good"),
        CarryOverSpec("backlog", "bad"),
    ),
)
data = DynamicData.from_frame(
    frame,
    spec=spec,
    dmu="organization",
    period="period",
)
result = DynamicSBM(
    orientation="non-oriented",
    returns_to_scale="vrs",
).fit(data)
```

Prepared scores one. Strained has no ordinary input or output slack, but its
capacity target is 2 and backlog target is 1. Its exact period accounts are
$A_t=0.75$ and $B_t=1.5$, so both period and horizon efficiency equal $0.5$.
The fixture is synthetic and theory-led, not organizational observations or
a reproduction of published application data.

## Dynamic-SBM carry-over portfolio

`dynamic_carryover_portfolio` contains a neutral four-path, three-period panel
with one input, one output, and declared good, bad, free, and fixed carry-over
fields. This compact example isolates the free carry-over account:

```python
from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    PeriodProductionSpec,
    load_dataset,
)

frame = load_dataset("dynamic_carryover_portfolio")
spec = DynamicSBMSpec(
    production=PeriodProductionSpec(
        inputs=["operating_input"],
        outputs=["service_output"],
    ),
    carryovers=(
        CarryOverSpec("redeployable_stock", "free"),
    ),
)
data = DynamicData.from_frame(
    frame,
    spec=spec,
    dmu="unit_id",
    period="period",
)
result = DynamicSBM(
    orientation="input",
    returns_to_scale="crs",
    score_variant="free_adjusted_post",
).fit(data)
```

The project case supports internal score reconstruction, period balance, and
adjacent-period continuity checks. It is a deterministic teaching example,
not a source-table reproduction or a current organizational panel. Tone and
Tsutsui's method reference and equations remain documented in
{doc}`../models/tone-tsutsui-dynamic-sbm`.

## Synthetic dynamic-network utility panel

`dynamic_network_power_demo` contains eight synthetic utilities observed over
2021--2024. Generation, grid, and customer-service processes are connected by
gross-power and delivered-power handoffs. The panel also contains:

- generation capacity as a good carry-over;
- maintenance backlog as a bad carry-over;
- fuel inventory as a free carry-over; and
- service obligation as a fixed carry-over.

```python
from deapack import load_dataset

frame = load_dataset("dynamic_network_power_demo")

frame.head()
```

The data are deterministic and theory-led. They are suitable for explaining
link ownership, state inheritance, system/process/period accounts,
visualization, and regression tests. They are **not** the 21 anonymous US
utilities used by Tone and Tsutsui (2014): the article does not provide the
raw panel or utility identities needed to bundle that case.

See {doc}`../models/tone-tsutsui-dynamic-network-sbm` for a complete model
specification and executable fit.

## Find datasets and inspect their descriptions

To list the available names:

```python
from deapack import dataset_info, list_datasets

for info in list_datasets():
    print(info.name)
```

To inspect a dataset's variables, provenance, and suggested uses:

```python
dataset_info("environmental_panel")
```

Its `.roles` mapping is also useful when writing reusable analysis scripts.
The examples above spell out the column names to make the first analysis
easier to follow.
