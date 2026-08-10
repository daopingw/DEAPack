# Method catalog

DEAPack exposes a small, read-only catalog so applications can discover the
methods that are implemented in the installed package:

```python
from deapack import list_methods, method_info

for method in list_methods():
    print(method.method_id, method.api_symbols, method.verification)

radial = method_info("static.radial")
print(radial.title, radial.verification)
```

`list_methods()` returns an immutable tuple of immutable `MethodInfo` records,
ordered by canonical ID. Each record contains:

- `method_id`: the stable canonical identifier of the catalog entry; its
  provenance field is identified by `identifier_role`;
- `identifier_role`: whether the entry is stored as a result `method_id`,
  constructor-specific `specialization_id`, or complete-recipe `preset_id`;
- `kind`: family, variant, specialization, preset, or analytical operator;
- `title` and `category`: short discovery labels;
- `api_symbols`: public top-level Python names that provide the method;
- `verification`: the current evidence level;
- `documentation`: the immutable tuple of current documentation levels.

The catalog is intentionally conservative. It includes implemented public
model paths, five named reporting/constructor specializations, and eight
complete presets. The presets comprise four classical radial recipes, the
source-qualified FGNZ Malmquist core, APZ environmental productivity, and the
two source-exact multiplicative constructors. It does not list planned entries
from the method atlas or evidence-gated prototypes deferred to a later version.
The installed registry, rather than a hard-coded count in this guide, defines
the current discovery total.

`static.radial.crs` and `static.radial.vrs` are emitted as
`specialization_id` values by `CCR` and `BCC`, while their result `method_id`
remains `static.radial`. These constructors fix RTS only. Orientation defaults
to input but remains configurable, and callers may disable slack completion.
The four complete preset constructors instead fix RTS, orientation, native
score convention, and `compute_slacks=True` with DEAPack's row-scaled
lexicographic slack-completion policy:

| Preset constructor | Result `preset_id` |
|---|---|
| `CCRInput` | `static.radial.crs.input` |
| `CCROutput` | `static.radial.crs.output` |
| `BCCInput` | `static.radial.vrs.input` |
| `BCCOutput` | `static.radial.vrs.output` |

All of these results retain `method_id="static.radial"`. A preset result has
its `preset_id` and no `specialization_id`; a numerically equivalent generic
call is not relabeled after fitting.
`dynamic.sbm.tone_tsutsui_2010.free_adjusted_post` identifies the
post-optimal free-carry-over reporting contract while retaining
`dynamic.sbm.tone_tsutsui_2010` as the fitted method ID. The installed
declared-calibration EBM evaluator is distinct from the still-planned automatic
EBM identities. An unknown or planned ID raises `KeyError`:

```python
method_info("static.ebm")  # KeyError: planned, not executable
```

The verification label `property` means that automated synthetic, identity,
invariance, or failure-domain tests support the implementation. The stronger
`primary_equations` label means that the defining primary equations have been
audited and the advertised branch is covered by claim-scoped analytical or
independent executable evidence; it does not imply reproduction of a
published numerical table. The
`literature_oracle` label records reproduction of a published numerical
example; it does not by itself claim an independent cross-implementation
comparison. `cross_implementation` records agreement with a separately
implemented, publicly reproducible numerical oracle.

`static.radial.fch.green_cook_2004` is cataloged as `primary_equations`: its
Green--Cook formulation is primary-checked, and an independent rational
enumerator exhausts all 15 nonempty coalitions of the package-designed
four-organization analytical fixture in both orientations. Separate tests
establish FDH--FCH--FRH nesting and the absence of a general FCH--VRS
ordering. No published numerical-table reproduction or third-party
cross-implementation is claimed. Its historical
free-aggregation-hull acronym `FAH` is not an API symbol because the same
acronym also denotes Ray's distinct free affordability hull.

## Productivity method map

The public catalog distinguishes principal method families from
source-qualified presets, reference-policy comparisons, sensitivity
companions, and specialized research methods. This organizational distinction
does not change API stability or numerical verification.

The four principal families are:

| Method family | Primary catalog ID | Package reference |
|---|---|---|
| Adjacent-period Malmquist | `productivity.malmquist.adjacent_geometric` | [Malmquist](../analysis/malmquist.md) |
| Luenberger | `productivity.luenberger` | [Luenberger](../analysis/luenberger.md) |
| Malmquist--Luenberger with undesirable outputs | `productivity.malmquist_luenberger.chung_fare_grosskopf_1997` | [Malmquist--Luenberger](../analysis/malmquist-luenberger.md) |
| Hicks--Moorsteen | `productivity.hicks_moorsteen.bjurek_1996` | [Hicks--Moorsteen](../analysis/hicks-moorsteen.md) |

The complete productivity catalog map is below. The FGNZ core is the
source-qualified constructor used inside the adjacent-period Malmquist family;
it is not a fifth principal family.

| Method role | Catalog ID | Package placement |
|---|---|---|
| Principal family | `productivity.malmquist.adjacent_geometric` | Adjacent-period Malmquist |
| Source-qualified preset | `productivity.malmquist.decomposition.fgnz_core` | FGNZ decomposition within Malmquist |
| Principal family | `productivity.luenberger` | Luenberger |
| Principal family | `productivity.malmquist_luenberger.chung_fare_grosskopf_1997` | Undesirable-output productivity |
| Principal family | `productivity.hicks_moorsteen.bjurek_1996` | Total-factor productivity |
| Reference-policy comparison | `productivity.global_malmquist` | Common-reference Malmquist comparison |
| Sensitivity companion | `productivity.global_malmquist_luenberger.oh_2010` | Common-reference Malmquist--Luenberger comparison |
| Specialized method | `productivity.biennial_malmquist` | Biennial reference policy |
| Specialized method | `productivity.malmquist.decomposition.fgnz_pure_scale_extension` | Enhanced FGNZ decomposition |
| Specialized method | `productivity.malmquist.decomposition.ray_desli` | Ray--Desli decomposition |
| Specialized preset | `productivity.malmquist_luenberger.aparicio_pastor_zofio_2013` | APZ environmental productivity |

## Network, dynamic, and panel method map

The network family asks whether process-specific benchmark plans form one
attainable organizational plan and how much process responsibility the evidence
supports. Färe--Grosskopf supplies the connected radial account; Kao--Hwang and
the Chen/Cook additive family provide alternative process-attribution
accounts. Chen is the closed two-stage member, while Cook supplies the open-
graph generalization. Network SBM reports variable-specific resource excesses
and service shortfalls under link continuity.

| Method role | Catalog ID | Package placement |
|---|---|---|
| Principal family | `network.radial.fare_grosskopf_2000` | Connected-system radial account |
| Process-attribution method | `network.relational.kao_hwang_2008` | Relational attribution |
| Process-attribution method | `network.additive.chen_etal_2009` | Closed two-stage additive account |
| Process-attribution method | `network.additive.cook_zhu_bi_yang_2010` | General additive account for open graphs |
| Principal family | `network.sbm.tone_tsutsui_2009` | Network SBM |
| Specialized method | `network.sequential.lewis_sexton_2004.forward_radial` | Sequential target propagation |
| Specialized method | `network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018` | Environmental-network composition |
| Specialized preset | `network.sbm.tone_tsutsui_2009.accountable_input_link` | Recipient-accountable link |
| Specialized preset | `network.sbm.tone_tsutsui_2009.accountable_output_link` | Supplier-accountable link |

Dynamic SBM is the principal implemented trajectory account. Dynamic Network
SBM combines the network and dynamic families; the ex-post free-carry-over
report is a selected-solution sensitivity, and the Park--Park estimator answers
a distinct multiperiod aggregation question.

| Method role | Catalog ID | Package placement |
|---|---|---|
| Principal family | `dynamic.sbm.tone_tsutsui_2010` | Dynamic trajectory account |
| Sensitivity companion | `dynamic.sbm.tone_tsutsui_2010.free_adjusted_post` | Ex-post selected-solution report |
| Combined method | `dynamic.network_sbm.tone_tsutsui_2014` | Network × dynamic composition |
| Specialized method | `panel.multiperiod_aggregative.park_park_2009` | Multiperiod aggregation without a state technology |

These organizational roles neither remove an implemented method from the
public API nor weaken its numerical verification contract.

## Heterogeneity method map

The implemented field-level comparison evaluates declared groups against
their own opportunity sets and against one matched pooled metafrontier. The
metatechnology ratio (MTR, historically also TGR) reports how close the
represented group opportunity frontier is to that broader opportunity set. It
is not another managerial-efficiency score, and the decomposition does not
identify why opportunity sets differ.

| Method role | Catalog ID | Package placement |
|---|---|---|
| Principal family | `heterogeneity.metafrontier.radial.odonnell_rao_battese_2008` | Declared-group radial metafrontier |

Input/output orientation and matched CRS/VRS are choices inside this method,
not additional models. A nonconvex union of separate group hulls, non-radial
or environmental metafrontiers, inferred groups, conditional frontiers, and
group/meta productivity accounts require separate source and numerical
contracts and remain outside the current implementation.

## Diagnostics method map

Selected-plan reference frequency is a bounded descriptive sensitivity for
study design, not a new DEA model. It counts how often each observed
organization appears through a reported active peer edge strictly above the
source result's `peer_tolerance` in one certified solver-selected peer plan
from a static convex global cross-section. Self and other use remain separate. The normalized
`reference_rate` uses total selected-plan frequency--self plus other--over all
evaluated organizations.

| Method role | Catalog ID | Package placement |
|---|---|---|
| Sensitivity companion | `analysis.reference_frequency.selected_plan` | Selected-plan benchmark-use diagnostic |

The procedure does not refit the frontier or assess alternate optima. A high
count is not an influence, outlier, or statistical-inference claim, and one
selected plan is not the global reference set.

## Evaluation method map

Specialized ranking and peer-appraisal procedures have public APIs for
source-qualified research workflows, with assumptions and failure domains
documented in the package reference.

| Method role | Catalog ID | Package placement |
|---|---|---|
| Specialized method | `evaluation.cross.game_nash.liang_wu_cook_zhu_2008` | Source-qualified game cross-efficiency protocol |
| Specialized method | `evaluation.super.directional.ray_2008` | Source-qualified directional super-efficiency protocol |
| Specialized method | `evaluation.super.sbm.tone_2002` | Source-qualified super-SBM protocol |

Ordinary CRS cross-efficiency and the Andersen--Petersen radial
reconstruction remain non-public prototypes scoped to `next_version`; they
therefore do not appear in the installed catalog. Their specialized role does
not weaken the numerical evidence of the three public methods or turn them
into general-purpose rankings.

## Implemented public entries

| Category | Canonical ID | Public API symbols |
|---|---|---|
| Static | `static.radial` | `RadialDEA` |
| Static | `static.radial.crs` | `CCR` |
| Static | `static.radial.vrs` | `BCC` |
| Static | `static.radial.crs.input` | `CCRInput` |
| Static | `static.radial.crs.output` | `CCROutput` |
| Static | `static.radial.vrs.input` | `BCCInput` |
| Static | `static.radial.vrs.output` | `BCCOutput` |
| Static | `static.radial.fdh` | `FreeDisposalHullDEA`, `FDH` |
| Static | `static.radial.fch.green_cook_2004` | `FreeCoordinationHullDEA`, `FCH` |
| Static | `static.radial.frh` | `FreeReplicabilityHullDEA`, `FRH` |
| Static | `static.additive` | `AdditiveDEA`, `WeightedAdditiveDEA` |
| Static | `static.ram` | `RangeAdjustedDEA`, `RAM` |
| Static | `static.bam` | `BoundedAdjustedDEA`, `BAM` |
| Static | `static.ebm.input.tone_tsutsui_2010.crs.declared` | `InputOrientedEpsilonBasedDEA` |
| Static | `static.sbm.input.tone2001` | `InputOrientedSlacksBasedDEA`, `InputSBM`, `InputRussell` |
| Static | `static.sbm.nonoriented.tone2001` | `SlacksBasedDEA`, `SBM`, `ERG` |
| Static | `static.sbm.output.tone2001` | `OutputOrientedSlacksBasedDEA`, `OutputSBM`, `OutputRussell` |
| Static | `static.directional_distance` | `DirectionalDistanceDEA`, `DDF` |
| Static | `static.range_directional.portela_thanassoulis_simpson_2004` | `RangeDirectionalDEA`, `RDM` |
| Static | `static.generalized_distance.chavas_cox` | `GeneralizedDistanceDEA`, `ChavasCoxGDF`, `GDF` |
| Static | `static.multiplicative` | `MultiplicativeDEA`, `C2S2MultiplicativeDEA`, `InvariantMultiplicativeDEA` |
| Static | `static.multiplicative.invariant.charnes_etal_1983` | `InvariantMultiplicativeDEA` |
| Static | `static.multiplicative.original.charnes_etal_1982` | `C2S2MultiplicativeDEA` |
| Valuation | `valuation.weight_restriction.cone_ratio.polyhedral_crs.charnes_etal_1990` | `PolyhedralConeRatioDEA` |
| Scale | `analysis.scale_efficiency.radial_ratio` | `scale_efficiency` |
| Scale | `analysis.returns_to_scale.local.banker_thrall_1992` | `local_returns_to_scale` |
| Scale | `analysis.scale_elasticity.local.radial_vrs` | `scale_elasticity` |
| Scale | `analysis.scale_elasticity.directional.relative_vrs.ren_etal_2021` | `relative_directional_scale_elasticity` |
| Diagnostics | `analysis.reference_frequency.selected_plan` | `reference_frequency` |
| Economic | `economic.cost` | `CostEfficiency` |
| Economic | `analysis.allocative_decomposition.cost_input_radial` | `AllocativeDecomposition` |
| Economic | `economic.revenue` | `RevenueEfficiency` |
| Economic | `analysis.allocative_decomposition.revenue_output_radial` | `RevenueAllocativeDecomposition` |
| Economic | `economic.profit.maximum` | `ProfitEfficiency` |
| Economic | `economic.nerlovian.ccf1998` | `NerlovianProfitInefficiency`, `NerlovianEfficiency` |
| Economic | `economic.profitability.return_to_dollar` | `ReturnToDollarEfficiency`, `ProfitabilityEfficiency` |
| Economic | `analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006` | `GDFProfitabilityDecomposition`, `ProfitabilityDecomposition` |
| Evaluation | `evaluation.cross.game_nash.liang_wu_cook_zhu_2008` | `LiangWuCookZhuGameCrossEfficiency`, `GameCrossEfficiency` |
| Evaluation | `evaluation.super.directional.ray_2008` | `RayDirectionalSuperEfficiency`, `NerloveLuenbergerSuperEfficiency` |
| Evaluation | `evaluation.super.sbm.tone_2002` | `ToneSuperSBM`, `SuperSBM` |
| Environmental | `environmental.ddf.joint_production` | `EnvironmentalDirectionalDistanceDEA`, `EnvironmentalDDF` |
| Environmental | `environmental.ddf.weak_disposal.common_factor` | `CommonFactorWeakDisposalDDF` |
| Environmental | `environmental.ddf.output.chung_fare_grosskopf_1997` | `ChungFareGrosskopfDDF` |
| Environmental | `environmental.ddf.weak_disposal.activity_specific` | `ActivitySpecificWeakDisposalDDF`, `KuosmanenWeakDisposalDDF` |
| Environmental | `environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp` | `ZhouAngWangNonCHPEnergyCarbonDEA`, `NonCHPEnergyCarbonDEA` |
| Environmental | `environmental.sbm.separable_strong` | `UndesirableSlacksBasedDEA`, `UndesirableSBM` |
| Environmental | `environmental.sbm.nonseparable_hybrid.tone_2003` | `ToneNonSeparableSBM`, `NonSeparableUndesirableSBM`, `SBMNS` |
| Environmental | `environmental.by_production.ddf` | `ByProductionDirectionalDistanceDEA`, `ByProductionDDF` |
| Environmental | `environmental.by_production.fgl` | `ByProductionFareGrosskopfLovellDEA`, `ByProductionFGL` |
| Environmental | `environmental.material_inflow.coelli2007` | `MaterialBalanceDEA`, `CoelliMaterialBalanceDEA` |
| Heterogeneity | `heterogeneity.metafrontier.radial.odonnell_rao_battese_2008` | `RadialMetafrontierDEA`, `MetafrontierDEA` |
| Network | `network.radial.fare_grosskopf_2000` | `FareGrosskopfNetworkRadialDEA` |
| Network | `network.relational.kao_hwang_2008` | `KaoHwangRelationalDEA`, `KaoHwangDEA` |
| Network | `network.additive.chen_etal_2009` | `ChenCookLiZhuAdditiveDEA`, `TwoStageAdditiveDecompositionDEA` |
| Network | `network.additive.cook_zhu_bi_yang_2010` | `CookZhuBiYangAdditiveDEA`, `GeneralAdditiveNetworkDEA` |
| Network | `network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018` | `KalhorKazemiMatinNetworkDEA` |
| Network | `network.sbm.tone_tsutsui_2009` | `ToneTsutsuiNetworkSBM`, `NetworkSBM` |
| Network | `network.sbm.tone_tsutsui_2009.accountable_input_link` | `ToneTsutsuiNetworkSBM`, `NetworkSBM` |
| Network | `network.sbm.tone_tsutsui_2009.accountable_output_link` | `ToneTsutsuiNetworkSBM`, `NetworkSBM` |
| Network | `network.sequential.lewis_sexton_2004.forward_radial` | `LewisSextonSequentialNetworkDEA` |
| Panel | `panel.multiperiod_aggregative.park_park_2009` | `ParkParkMultiperiodAggregativeDEA`, `MultiperiodAggregativeDEA` |
| Dynamic | `dynamic.sbm.tone_tsutsui_2010` | `ToneTsutsuiDynamicSBM`, `DynamicSBM` |
| Dynamic | `dynamic.sbm.tone_tsutsui_2010.free_adjusted_post` | `ToneTsutsuiDynamicSBM`, `DynamicSBM` |
| Dynamic network | `dynamic.network_sbm.tone_tsutsui_2014` | `ToneTsutsuiDynamicNetworkSBM`, `DynamicNetworkSBM` |
| Productivity | `productivity.malmquist.adjacent_geometric` | `MalmquistProductivityIndex`, `MalmquistDEA` |
| Productivity | `productivity.malmquist.decomposition.fgnz_core` | `FGNZMalmquistProductivityIndex`, `FGNZMalmquist` |
| Productivity | `productivity.malmquist.decomposition.fgnz_pure_scale_extension` | `FGNZEnhancedMalmquistProductivityIndex`, `FGNZEnhancedMalmquist` |
| Productivity | `productivity.malmquist.decomposition.ray_desli` | `RayDesliMalmquistProductivityIndex`, `RayDesliMalmquist` |
| Productivity | `productivity.luenberger` | `LuenbergerProductivityIndicator`, `LuenbergerDEA` |
| Productivity | `productivity.global_malmquist` | `GlobalMalmquistProductivityIndex`, `GlobalMalmquistDEA` |
| Productivity | `productivity.biennial_malmquist` | `BiennialMalmquistProductivityIndex`, `BiennialMalmquistDEA` |
| Productivity | `productivity.malmquist_luenberger.chung_fare_grosskopf_1997` | `MalmquistLuenbergerProductivityIndex`, `MalmquistLuenbergerDEA` |
| Productivity | `productivity.malmquist_luenberger.aparicio_pastor_zofio_2013` | `APZMalmquistLuenbergerProductivityIndex`, `APZMalmquistLuenbergerDEA` |
| Productivity | `productivity.global_malmquist_luenberger.oh_2010` | `GlobalMalmquistLuenbergerProductivityIndex`, `GlobalMalmquistLuenbergerDEA` |
| Productivity | `productivity.hicks_moorsteen.bjurek_1996` | `HicksMoorsteenProductivityIndex`, `MoorsteenBjurekProductivityIndex`, `HicksMoorsteenDEA`, `MoorsteenBjurekDEA` |

MPSS and Färe--Grosskopf--Kokkelenberg physical capacity do not appear in this
public catalog. They are non-public prototypes deferred to the next version
pending the [Banker MPSS source protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/banker_1984_mpss.md)
and the
[FGK physical-capacity source protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/fare_grosskopf_kokkelenberg_1989_capacity.md).

This discovery layer is maintained in Python and held in exact two-way parity
with the validated machine-readable shadow registry for all 62 public
`method_id` entries and the public APZ `preset_id`. Five `specialization_id`
entries and the other seven `preset_id` entries remain catalog recipes rather
than duplicate machine records. Runtime imports never parse project
documentation or registry JSON.

Each implemented/public method record also names a benchmark that directly
executes its complete API. These scripts test execution structure and
scalability; they do not replace the defining literature or an independent
numerical oracle.

NIRS and NDRS are implemented parameter choices of `RadialDEA` and are
recorded in the result's expanded specification. They do not currently have a
dedicated `method_id`, `specialization_id`, or top-level constructor, so
`static.radial.restricted_rts` is deliberately not a catalog entry.
