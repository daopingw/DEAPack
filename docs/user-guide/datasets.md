# Built-in datasets

Built-in datasets are deterministic. They support teaching,
figures, regression tests, and examples with analytically transparent
frontiers.

```python
from deapack import dataset_info, list_datasets, load_dataset

for info in list_datasets():
    print(info.name, info.teaching_uses)

frame = load_dataset("environmental_panel")
roles = dataset_info("environmental_panel").roles
```

The 33 current datasets are grouped by teaching purpose:

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

## One dataset, four economic questions

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
    dataset_info,
    load_dataset,
)

frame = load_dataset("economic_efficiency_4")
roles = dataset_info("economic_efficiency_4").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
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
from deapack import DEAData, NonCHPEnergyCarbonDEA, dataset_info, load_dataset

frame = load_dataset("zhou_ang_wang_non_chp_3")
roles = dataset_info("zhou_ang_wang_non_chp_3").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
    bad_outputs=roles["bad_outputs"],
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

## Signed range-directional oracle

`range_directional_signed` contains one signed input and one signed desirable
output:

```python
from deapack import DEAData, RDM, dataset_info, load_dataset

frame = load_dataset("range_directional_signed")
roles = dataset_info("range_directional_signed").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = RDM().fit(data)
result.summary()[["dmu_id", "beta", "rdm_efficiency", "solver_status"]]
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

## Declared-group metafrontier oracle

`metafrontier_groups` contains six organizations in two declared technology
groups:

```python
from deapack import DEAData, MetafrontierDEA, dataset_info, load_dataset

frame = load_dataset("metafrontier_groups")
roles = dataset_info("metafrontier_groups").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    group=roles["group"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = MetafrontierDEA().fit(data)
result.summary()[
    [
        "dmu_id",
        "group_efficiency",
        "meta_efficiency",
        "metatechnology_ratio",
    ]
]
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
from deapack import DEAData, FRH, dataset_info, load_dataset

frame = load_dataset("integer_coordination_hulls")
roles = dataset_info("integer_coordination_hulls").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = FRH(orientation="input").fit(data)
```

The example is useful when branches, production lines, or service modules can
be copied only as complete units. It does not establish that every real
organization is indivisible. The analyst must justify that production
assumption from the operating context.

## Distinct organizations available once

`coordination_hulls` contains the four observations used to distinguish FDH,
the Green--Cook FCH, FRH, CCR, and VRS in the companion book:

```python
from deapack import DEAData, FCH, dataset_info, load_dataset

frame = load_dataset("coordination_hulls")
roles = dataset_info("coordination_hulls").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = FCH(orientation="input").fit(data)
result.summary().query("dmu_id == 'E'")[["score", "coalition_size"]]
```

The resulting input factor is $0.70$, supported by the binary coalition
A+B. The data are synthetic and isolate the activity-combination assumption;
they do not recommend a merger or assert that the variables of a real
application are additive.

## Relative-rate scale scenarios

`ren_cas_directional_scale` reproduces all 16 observations in Table 1 of Ren
et al. (2021):

```python
from deapack import (
    DEAData,
    dataset_info,
    load_dataset,
    relative_directional_scale_elasticity,
)

frame = load_dataset("ren_cas_directional_scale")
roles = dataset_info("ren_cas_directional_scale").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
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
    dataset_info,
    load_dataset,
)

frame = load_dataset("sbm_slack_contrast")
roles = dataset_info("sbm_slack_contrast").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
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
    dataset_info,
    load_dataset,
)

separable_frame = load_dataset("environmental_disposability_contrast")
separable_roles = dataset_info("environmental_disposability_contrast").roles
separable_data = DEAData.from_frame(
    separable_frame,
    dmu=separable_roles["dmu"],
    inputs=separable_roles["inputs"],
    outputs=separable_roles["outputs"],
    bad_outputs=separable_roles["bad_outputs"],
)
separable_result = UndesirableSBM(
    returns_to_scale="vrs",
).fit(separable_data)
```

The same frame exposes a jointly changing service/residual pair and an
independently adjustable pair. The role metadata can be passed directly to the
public hybrid estimator:

```python
hybrid_frame = load_dataset("environmental_disposability_contrast")
hybrid_roles = dataset_info("environmental_disposability_contrast").roles
hybrid_data = DEAData.from_frame(
    hybrid_frame,
    dmu=hybrid_roles["dmu"],
    inputs=hybrid_roles["inputs"],
    outputs=hybrid_roles["outputs"],
    bad_outputs=hybrid_roles["bad_outputs"],
)

hybrid_result = ToneNonSeparableSBM(
    nonseparable_outputs=hybrid_roles["nonseparable_good_outputs"],
    nonseparable_bad_outputs=hybrid_roles["nonseparable_bad_outputs"],
    alpha_min=0.7,
    returns_to_scale="vrs",
).fit(hybrid_data)

hybrid_result.summary()[["dmu_id", "efficiency", "alpha"]]
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
from deapack import DEAData, ToneSuperSBM, dataset_info, load_dataset

frame = load_dataset("super_sbm_peer_replacement")
roles = dataset_info("super_sbm_peer_replacement").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = ToneSuperSBM(
    orientation="non-oriented",
    returns_to_scale="crs",
).fit(data)
result.summary()[
    ["dmu_id", "is_sbm_eligible", "super_sbm_score", "applicability_status"]
]
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
    dataset_info,
    load_dataset,
)

frame = load_dataset("directional_super_multivariate_stress")
roles = dataset_info("directional_super_multivariate_stress").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = RayDirectionalSuperEfficiency().fit(data)
result.summary()[["dmu_id", "beta", "nl_super_efficiency", "score_valid"]]
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
    dataset_info,
    load_dataset,
)

frame = load_dataset("two_stage_public_service")
roles = dataset_info("two_stage_public_service").roles

spec = TwoStageSeriesSpec(
    inputs=roles["inputs"],
    intermediates=roles["intermediates"],
    outputs=roles["outputs"],
    stage_names=("screening", "service_delivery"),
)
data = NetworkData.from_frame(
    frame,
    dmu=roles["dmu"],
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
    dataset_info,
    load_dataset,
)

frame = load_dataset("open_service_chain")
roles = dataset_info("open_service_chain").roles
handoffs = roles["links"]
sourcing = ProcessSpec(
    "sourcing",
    inputs=roles["sourcing_inputs"],
    outputs=handoffs,
)
delivery = ProcessSpec(
    "delivery",
    inputs=(*handoffs, *roles["service_inputs"]),
    outputs=roles["outputs"],
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
data = NetworkData.from_frame(frame, dmu=roles["dmu"], spec=spec)
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
from deapack import dataset_info, load_dataset

service_chain = load_dataset("three_process_service_chain")
service_chain_roles = dataset_info("three_process_service_chain").roles

crs_example = load_dataset("crs_free_link_service_chain")
crs_roles = dataset_info("crs_free_link_service_chain").roles
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
    dataset_info,
    load_dataset,
)

frame = load_dataset("dynamic_capacity_backlog")
roles = dataset_info("dynamic_capacity_backlog").roles
spec = DynamicSBMSpec(
    production=PeriodProductionSpec(
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    ),
    carryovers=(
        CarryOverSpec(roles["good_carryovers"][0], "good"),
        CarryOverSpec(roles["bad_carryovers"][0], "bad"),
    ),
)
data = DynamicData.from_frame(
    frame,
    spec=spec,
    dmu=roles["dmu"],
    period=roles["period"],
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
    dataset_info,
    load_dataset,
)

frame = load_dataset("dynamic_carryover_portfolio")
roles = dataset_info("dynamic_carryover_portfolio").roles
spec = DynamicSBMSpec(
    production=PeriodProductionSpec(
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    ),
    carryovers=(
        CarryOverSpec(roles["free_carryovers"][0], "free"),
    ),
)
data = DynamicData.from_frame(
    frame,
    spec=spec,
    dmu=roles["dmu"],
    period=roles["period"],
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
from deapack import dataset_info, load_dataset

frame = load_dataset("dynamic_network_power_demo")
roles = dataset_info("dynamic_network_power_demo").roles

print(frame[[roles["dmu"], roles["period"]]].drop_duplicates())
print(dataset_info("dynamic_network_power_demo").teaching_uses)
```

The data are deterministic and theory-led. They are suitable for explaining
link ownership, state inheritance, system/process/period accounts,
visualization, and regression tests. They are **not** the 21 anonymous US
utilities used by Tone and Tsutsui (2014): the article does not provide the
raw panel or utility identities needed to bundle that case.

See {doc}`../models/tone-tsutsui-dynamic-network-sbm` for a complete model
specification and executable fit.
