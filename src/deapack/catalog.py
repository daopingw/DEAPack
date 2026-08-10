"""Read-only discovery metadata for implemented public DEAPack methods.

The catalog is deliberately defined in Python.  It does not parse the
Markdown method registry at runtime and contains no planned methods.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class MethodInfo:
    """Immutable public metadata for one implemented catalog entry."""

    method_id: str
    identifier_role: str
    kind: str
    title: str
    category: str
    api_symbols: tuple[str, ...]
    verification: str
    documentation: tuple[str, ...]
    publication_scope: str | None = None


_METHODS = tuple(
    sorted(
        (
            MethodInfo(
                method_id=("analysis.allocative_decomposition.cost_input_radial"),
                identifier_role="method_id",
                kind="operator",
                title="Cost technical--allocative decomposition",
                category="economic",
                api_symbols=("AllocativeDecomposition",),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=(
                    "analysis.allocative_decomposition.profitability_gdf."
                    "zofio_prieto_2006"
                ),
                identifier_role="method_id",
                kind="operator",
                title="GDF technical--scale--allocative profitability decomposition",
                category="economic",
                api_symbols=(
                    "GDFProfitabilityDecomposition",
                    "ProfitabilityDecomposition",
                ),
                verification="cross_implementation",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=("analysis.allocative_decomposition.revenue_output_radial"),
                identifier_role="method_id",
                kind="operator",
                title="Revenue technical--allocative decomposition",
                category="economic",
                api_symbols=("RevenueAllocativeDecomposition",),
                verification="cross_implementation",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=("analysis.returns_to_scale.local.banker_thrall_1992"),
                identifier_role="method_id",
                kind="operator",
                title=("Banker--Thrall selected-projection local returns to scale"),
                category="scale",
                api_symbols=("local_returns_to_scale",),
                verification="literature_oracle",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="analysis.reference_frequency.selected_plan",
                identifier_role="method_id",
                kind="procedure",
                title="Certified selected-plan reference frequency",
                category="diagnostics",
                api_symbols=("reference_frequency",),
                verification="cross_implementation",
                documentation=("api",),
                publication_scope="handbook_sensitivity",
            ),
            MethodInfo(
                method_id="analysis.scale_efficiency.radial_ratio",
                identifier_role="method_id",
                kind="operator",
                title="Radial scale-efficiency ratio",
                category="scale",
                api_symbols=("scale_efficiency",),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="analysis.scale_elasticity.local.radial_vrs",
                identifier_role="method_id",
                kind="operator",
                title="One-sided radial VRS scale elasticity",
                category="scale",
                api_symbols=("scale_elasticity",),
                verification="literature_oracle",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=(
                    "analysis.scale_elasticity.directional.relative_vrs.ren_etal_2021"
                ),
                identifier_role="method_id",
                kind="operator",
                title="Ren et al. relative-directional VRS scale elasticity",
                category="scale",
                api_symbols=("relative_directional_scale_elasticity",),
                verification="literature_oracle",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="economic.cost",
                identifier_role="method_id",
                kind="family",
                title="Minimum-cost efficiency",
                category="economic",
                api_symbols=("CostEfficiency",),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="economic.nerlovian.ccf1998",
                identifier_role="method_id",
                kind="preset",
                title="Chambers--Chung--Färe Nerlovian profit inefficiency",
                category="economic",
                api_symbols=(
                    "NerlovianProfitInefficiency",
                    "NerlovianEfficiency",
                ),
                verification="cross_implementation",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="economic.profit.maximum",
                identifier_role="method_id",
                kind="operator",
                title="Maximum-profit gap",
                category="economic",
                api_symbols=("ProfitEfficiency",),
                verification="cross_implementation",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="economic.profitability.return_to_dollar",
                identifier_role="method_id",
                kind="operator",
                title="Return-to-dollar profitability efficiency",
                category="economic",
                api_symbols=(
                    "ReturnToDollarEfficiency",
                    "ProfitabilityEfficiency",
                ),
                verification="cross_implementation",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="economic.revenue",
                identifier_role="method_id",
                kind="family",
                title="Maximum-revenue efficiency",
                category="economic",
                api_symbols=("RevenueEfficiency",),
                verification="cross_implementation",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=("evaluation.cross.game_nash.liang_wu_cook_zhu_2008"),
                identifier_role="method_id",
                kind="preset",
                title="Liang--Wu--Cook--Zhu game cross-efficiency",
                category="evaluation",
                api_symbols=(
                    "LiangWuCookZhuGameCrossEfficiency",
                    "GameCrossEfficiency",
                ),
                verification="cross_implementation",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id="evaluation.super.directional.ray_2008",
                identifier_role="method_id",
                kind="preset",
                title="Ray (2008) directional super-efficiency",
                category="evaluation",
                api_symbols=(
                    "RayDirectionalSuperEfficiency",
                    "NerloveLuenbergerSuperEfficiency",
                ),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id="evaluation.super.sbm.tone_2002",
                identifier_role="method_id",
                kind="preset",
                title="Tone (2002) slacks-based super-efficiency",
                category="evaluation",
                api_symbols=("ToneSuperSBM", "SuperSBM"),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id="environmental.by_production.ddf",
                identifier_role="method_id",
                kind="preset",
                title="By-production directional distance",
                category="environmental",
                api_symbols=(
                    "ByProductionDirectionalDistanceDEA",
                    "ByProductionDDF",
                ),
                verification="cross_implementation",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="environmental.by_production.fgl",
                identifier_role="method_id",
                kind="preset",
                title=(
                    "Modified Färe--Grosskopf--Lovell efficiency under by-production"
                ),
                category="environmental",
                api_symbols=(
                    "ByProductionFareGrosskopfLovellDEA",
                    "ByProductionFGL",
                ),
                verification="cross_implementation",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=("environmental.ddf.output.chung_fare_grosskopf_1997"),
                identifier_role="method_id",
                kind="preset",
                title="Chung--Färe--Grosskopf environmental output DDF",
                category="environmental",
                api_symbols=("ChungFareGrosskopfDDF",),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="environmental.ddf.joint_production",
                identifier_role="method_id",
                kind="family",
                title="Environmental directional distance",
                category="environmental",
                api_symbols=(
                    "EnvironmentalDirectionalDistanceDEA",
                    "EnvironmentalDDF",
                ),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=("environmental.ddf.weak_disposal.activity_specific"),
                identifier_role="method_id",
                kind="family",
                title="Activity-specific weak-disposal directional distance",
                category="environmental",
                api_symbols=(
                    "ActivitySpecificWeakDisposalDDF",
                    "KuosmanenWeakDisposalDDF",
                ),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="environmental.ddf.weak_disposal.common_factor",
                identifier_role="method_id",
                kind="family",
                title="CRS common-factor weak-disposal directional distance",
                category="environmental",
                api_symbols=("CommonFactorWeakDisposalDDF",),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=(
                    "environmental.directional_nonradial.energy_carbon."
                    "zhou_ang_wang_2012_non_chp"
                ),
                identifier_role="method_id",
                kind="preset",
                title="Zhou--Ang--Wang non-CHP energy--carbon source preset",
                category="environmental",
                api_symbols=(
                    "ZhouAngWangNonCHPEnergyCarbonDEA",
                    "NonCHPEnergyCarbonDEA",
                ),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="environmental.material_inflow.coelli2007",
                identifier_role="method_id",
                kind="preset",
                title="Coelli material-inflow efficiency",
                category="environmental",
                api_symbols=("MaterialBalanceDEA", "CoelliMaterialBalanceDEA"),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=("environmental.sbm.nonseparable_hybrid.tone_2003"),
                identifier_role="method_id",
                kind="preset",
                title="Tone non-separable undesirable-output SBM",
                category="environmental",
                api_symbols=(
                    "ToneNonSeparableSBM",
                    "NonSeparableUndesirableSBM",
                    "SBMNS",
                ),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="environmental.sbm.separable_strong",
                identifier_role="method_id",
                kind="preset",
                title="Separable undesirable-output SBM",
                category="environmental",
                api_symbols=("UndesirableSlacksBasedDEA", "UndesirableSBM"),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=(
                    "heterogeneity.metafrontier.radial.odonnell_rao_battese_2008"
                ),
                identifier_role="method_id",
                kind="operator",
                title="O'Donnell--Rao--Battese radial DEA metafrontier",
                category="heterogeneity",
                api_symbols=("RadialMetafrontierDEA", "MetafrontierDEA"),
                verification="cross_implementation",
                documentation=("api",),
                publication_scope="handbook_core",
            ),
            MethodInfo(
                method_id="network.additive.chen_etal_2009",
                identifier_role="method_id",
                kind="preset",
                title="Chen--Cook--Li--Zhu additive two-stage DEA",
                category="network",
                api_symbols=(
                    "ChenCookLiZhuAdditiveDEA",
                    "TwoStageAdditiveDecompositionDEA",
                ),
                verification="cross_implementation",
                documentation=("api",),
                publication_scope="handbook_core",
            ),
            MethodInfo(
                method_id="network.additive.cook_zhu_bi_yang_2010",
                identifier_role="method_id",
                kind="preset",
                title="Cook--Zhu--Bi--Yang general additive network DEA",
                category="network",
                api_symbols=(
                    "CookZhuBiYangAdditiveDEA",
                    "GeneralAdditiveNetworkDEA",
                ),
                verification="cross_implementation",
                documentation=("api",),
                publication_scope="handbook_core",
            ),
            MethodInfo(
                method_id=(
                    "network.environmental.weak_activity_specific."
                    "kalhor_kazemi_matin_2018"
                ),
                identifier_role="method_id",
                kind="preset",
                title=("Kalhor--Kazemi Matin environmental general-network radial DEA"),
                category="network",
                api_symbols=("KalhorKazemiMatinNetworkDEA",),
                verification="cross_implementation",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id="network.radial.fare_grosskopf_2000",
                identifier_role="method_id",
                kind="preset",
                title=("Färe--Grosskopf two-stage intermediate-products radial DEA"),
                category="network",
                api_symbols=("FareGrosskopfNetworkRadialDEA",),
                verification="cross_implementation",
                documentation=("api",),
                publication_scope="handbook_core",
            ),
            MethodInfo(
                method_id="network.relational.kao_hwang_2008",
                identifier_role="method_id",
                kind="preset",
                title="Kao--Hwang two-stage relational network DEA",
                category="network",
                api_symbols=("KaoHwangRelationalDEA", "KaoHwangDEA"),
                verification="cross_implementation",
                documentation=("api",),
                publication_scope="handbook_core",
            ),
            MethodInfo(
                method_id="network.sbm.tone_tsutsui_2009",
                identifier_role="method_id",
                kind="preset",
                title="Tone--Tsutsui network SBM",
                category="network",
                api_symbols=("ToneTsutsuiNetworkSBM", "NetworkSBM"),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="handbook_core",
            ),
            MethodInfo(
                method_id=("network.sbm.tone_tsutsui_2009.accountable_input_link"),
                identifier_role="specialization_id",
                kind="specialization",
                title=(
                    "Tone--Tsutsui recipient-accountable incoming-link "
                    "input specialization"
                ),
                category="network",
                api_symbols=("ToneTsutsuiNetworkSBM", "NetworkSBM"),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id=("network.sbm.tone_tsutsui_2009.accountable_output_link"),
                identifier_role="specialization_id",
                kind="specialization",
                title=(
                    "Tone--Tsutsui supplier-accountable outgoing-link "
                    "output specialization"
                ),
                category="network",
                api_symbols=("ToneTsutsuiNetworkSBM", "NetworkSBM"),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id=("network.sequential.lewis_sexton_2004.forward_radial"),
                identifier_role="method_id",
                kind="preset",
                title="Lewis--Sexton sequential forward radial network DEA",
                category="network",
                api_symbols=("LewisSextonSequentialNetworkDEA",),
                verification="literature_oracle",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id="dynamic.sbm.tone_tsutsui_2010",
                identifier_role="method_id",
                kind="preset",
                title="Tone--Tsutsui dynamic SBM",
                category="dynamic",
                api_symbols=("ToneTsutsuiDynamicSBM", "DynamicSBM"),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="handbook_core",
            ),
            MethodInfo(
                method_id="dynamic.network_sbm.tone_tsutsui_2014",
                identifier_role="method_id",
                kind="preset",
                title="Tone--Tsutsui dynamic network SBM",
                category="dynamic",
                api_symbols=(
                    "ToneTsutsuiDynamicNetworkSBM",
                    "DynamicNetworkSBM",
                ),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id=("dynamic.sbm.tone_tsutsui_2010.free_adjusted_post"),
                identifier_role="specialization_id",
                kind="specialization",
                title="Tone--Tsutsui ex-post free-carry-over adjustment",
                category="dynamic",
                api_symbols=("ToneTsutsuiDynamicSBM", "DynamicSBM"),
                verification="literature_oracle",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id="panel.multiperiod_aggregative.park_park_2009",
                identifier_role="method_id",
                kind="preset",
                title="Park--Park multi-period aggregative radial DEA",
                category="panel",
                api_symbols=(
                    "ParkParkMultiperiodAggregativeDEA",
                    "MultiperiodAggregativeDEA",
                ),
                verification="cross_implementation",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id="productivity.biennial_malmquist",
                identifier_role="method_id",
                kind="operator",
                title="Biennial Malmquist productivity index",
                category="productivity",
                api_symbols=(
                    "BiennialMalmquistProductivityIndex",
                    "BiennialMalmquistDEA",
                ),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id="productivity.global_malmquist",
                identifier_role="method_id",
                kind="operator",
                title="Global Malmquist productivity index",
                category="productivity",
                api_symbols=(
                    "GlobalMalmquistProductivityIndex",
                    "GlobalMalmquistDEA",
                ),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="supporting_reference_policy",
            ),
            MethodInfo(
                method_id="productivity.global_malmquist_luenberger.oh_2010",
                identifier_role="method_id",
                kind="operator",
                title="Oh global Malmquist--Luenberger productivity index",
                category="productivity",
                api_symbols=(
                    "GlobalMalmquistLuenbergerProductivityIndex",
                    "GlobalMalmquistLuenbergerDEA",
                ),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="handbook_sensitivity",
            ),
            MethodInfo(
                method_id="productivity.hicks_moorsteen.bjurek_1996",
                identifier_role="method_id",
                kind="preset",
                title="Bjurek Hicks--Moorsteen total-factor-productivity index",
                category="productivity",
                api_symbols=(
                    "HicksMoorsteenProductivityIndex",
                    "HicksMoorsteenDEA",
                    "MoorsteenBjurekProductivityIndex",
                    "MoorsteenBjurekDEA",
                ),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="handbook_core",
            ),
            MethodInfo(
                method_id="productivity.luenberger",
                identifier_role="method_id",
                kind="operator",
                title="Luenberger productivity indicator",
                category="productivity",
                api_symbols=("LuenbergerProductivityIndicator", "LuenbergerDEA"),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="handbook_core",
            ),
            MethodInfo(
                method_id="productivity.malmquist.adjacent_geometric",
                identifier_role="method_id",
                kind="operator",
                title="Adjacent-period Malmquist productivity index",
                category="productivity",
                api_symbols=("MalmquistProductivityIndex", "MalmquistDEA"),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="handbook_core",
            ),
            MethodInfo(
                method_id="productivity.malmquist.decomposition.fgnz_core",
                identifier_role="preset_id",
                kind="preset",
                title="FGNZ output-oriented CRS Malmquist core decomposition",
                category="productivity",
                api_symbols=(
                    "FGNZMalmquistProductivityIndex",
                    "FGNZMalmquist",
                ),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="handbook_core",
            ),
            MethodInfo(
                method_id=(
                    "productivity.malmquist.decomposition.fgnz_pure_scale_extension"
                ),
                identifier_role="method_id",
                kind="operator",
                title=(
                    "FGNZ enhanced pure-efficiency and scale-efficiency "
                    "Malmquist decomposition"
                ),
                category="productivity",
                api_symbols=(
                    "FGNZEnhancedMalmquistProductivityIndex",
                    "FGNZEnhancedMalmquist",
                ),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id="productivity.malmquist.decomposition.ray_desli",
                identifier_role="method_id",
                kind="operator",
                title="Ray--Desli VRS Malmquist decomposition",
                category="productivity",
                api_symbols=(
                    "RayDesliMalmquistProductivityIndex",
                    "RayDesliMalmquist",
                ),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id=(
                    "productivity.malmquist_luenberger.chung_fare_grosskopf_1997"
                ),
                identifier_role="method_id",
                kind="operator",
                title="Chung--Färe--Grosskopf Malmquist--Luenberger index",
                category="productivity",
                api_symbols=(
                    "MalmquistLuenbergerProductivityIndex",
                    "MalmquistLuenbergerDEA",
                ),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="handbook_core",
            ),
            MethodInfo(
                method_id=(
                    "productivity.malmquist_luenberger.aparicio_pastor_zofio_2013"
                ),
                identifier_role="preset_id",
                kind="preset",
                title=(
                    "Aparicio--Pastor--Zofío consistent Malmquist--Luenberger index"
                ),
                category="productivity",
                api_symbols=(
                    "APZMalmquistLuenbergerProductivityIndex",
                    "APZMalmquistLuenbergerDEA",
                ),
                verification="primary_equations",
                documentation=("api",),
                publication_scope="documentation_only",
            ),
            MethodInfo(
                method_id="static.additive",
                identifier_role="method_id",
                kind="family",
                title="Additive DEA with configurable slack weights",
                category="static",
                api_symbols=("AdditiveDEA", "WeightedAdditiveDEA"),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.bam",
                identifier_role="method_id",
                kind="family",
                title="Bounded-adjusted measure",
                category="static",
                api_symbols=("BoundedAdjustedDEA", "BAM"),
                verification="cross_implementation",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.directional_distance",
                identifier_role="method_id",
                kind="family",
                title="Directional distance function",
                category="static",
                api_symbols=("DirectionalDistanceDEA", "DDF"),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.ebm.input.tone_tsutsui_2010.crs.declared",
                identifier_role="method_id",
                kind="preset",
                title="Declared-calibration Tone--Tsutsui input-oriented CRS EBM",
                category="static",
                api_symbols=("InputOrientedEpsilonBasedDEA",),
                verification="cross_implementation",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.generalized_distance.chavas_cox",
                identifier_role="method_id",
                kind="family",
                title="Chavas--Cox generalized distance",
                category="static",
                api_symbols=(
                    "GeneralizedDistanceDEA",
                    "ChavasCoxGDF",
                    "GDF",
                ),
                verification="cross_implementation",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.radial",
                identifier_role="method_id",
                kind="family",
                title="Farrell radial DEA",
                category="static",
                api_symbols=("RadialDEA",),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.multiplicative",
                identifier_role="method_id",
                kind="family",
                title="Multiplicative DEA",
                category="static",
                api_symbols=(
                    "MultiplicativeDEA",
                    "C2S2MultiplicativeDEA",
                    "InvariantMultiplicativeDEA",
                ),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=("static.multiplicative.invariant.charnes_etal_1983"),
                identifier_role="preset_id",
                kind="preset",
                title="Invariant multiplicative DEA",
                category="static",
                api_symbols=("InvariantMultiplicativeDEA",),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=("static.multiplicative.original.charnes_etal_1982"),
                identifier_role="preset_id",
                kind="preset",
                title="Original C2S2 multiplicative DEA",
                category="static",
                api_symbols=("C2S2MultiplicativeDEA",),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.radial.crs.input",
                identifier_role="preset_id",
                kind="preset",
                title="CCR-I input-oriented radial recipe",
                category="static",
                api_symbols=("CCRInput",),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.radial.crs.output",
                identifier_role="preset_id",
                kind="preset",
                title="CCR-O output-oriented radial recipe",
                category="static",
                api_symbols=("CCROutput",),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.radial.fch.green_cook_2004",
                identifier_role="method_id",
                kind="variant",
                title="Green--Cook free coordination hull",
                category="static",
                api_symbols=("FreeCoordinationHullDEA", "FCH"),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.radial.crs",
                identifier_role="specialization_id",
                kind="specialization",
                title="CCR constant-returns radial specialization",
                category="static",
                api_symbols=("CCR",),
                verification="property",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.radial.fdh",
                identifier_role="method_id",
                kind="variant",
                title="Radial free disposal hull",
                category="static",
                api_symbols=("FreeDisposalHullDEA", "FDH"),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.radial.frh",
                identifier_role="method_id",
                kind="variant",
                title="Radial free replicability hull",
                category="static",
                api_symbols=("FreeReplicabilityHullDEA", "FRH"),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.radial.vrs",
                identifier_role="specialization_id",
                kind="specialization",
                title="BCC variable-returns radial specialization",
                category="static",
                api_symbols=("BCC",),
                verification="property",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.radial.vrs.input",
                identifier_role="preset_id",
                kind="preset",
                title="BCC-I input-oriented radial recipe",
                category="static",
                api_symbols=("BCCInput",),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.radial.vrs.output",
                identifier_role="preset_id",
                kind="preset",
                title="BCC-O output-oriented radial recipe",
                category="static",
                api_symbols=("BCCOutput",),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.ram",
                identifier_role="method_id",
                kind="preset",
                title="Range-adjusted measure",
                category="static",
                api_symbols=("RangeAdjustedDEA", "RAM"),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=(
                    "static.range_directional.portela_thanassoulis_simpson_2004"
                ),
                identifier_role="method_id",
                kind="preset",
                title=("Portela--Thanassoulis--Simpson range-directional measure"),
                category="static",
                api_symbols=("RangeDirectionalDEA", "RDM"),
                verification="cross_implementation",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.sbm.input.tone2001",
                identifier_role="method_id",
                kind="preset",
                title="Tone input-oriented SBM",
                category="static",
                api_symbols=(
                    "InputOrientedSlacksBasedDEA",
                    "InputSBM",
                    "InputRussell",
                ),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.sbm.nonoriented.tone2001",
                identifier_role="method_id",
                kind="preset",
                title="Standard non-oriented ERG/SBM",
                category="static",
                api_symbols=("SlacksBasedDEA", "SBM", "ERG"),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id="static.sbm.output.tone2001",
                identifier_role="method_id",
                kind="preset",
                title="Tone output-oriented SBM",
                category="static",
                api_symbols=(
                    "OutputOrientedSlacksBasedDEA",
                    "OutputSBM",
                    "OutputRussell",
                ),
                verification="primary_equations",
                documentation=("api",),
            ),
            MethodInfo(
                method_id=(
                    "valuation.weight_restriction.cone_ratio.polyhedral_crs."
                    "charnes_etal_1990"
                ),
                identifier_role="method_id",
                kind="preset",
                title="Charnes--Cooper--Huang--Sun polyhedral cone-ratio DEA",
                category="valuation",
                api_symbols=("PolyhedralConeRatioDEA",),
                verification="literature_oracle",
                documentation=("api",),
            ),
        ),
        key=lambda item: item.method_id,
    )
)

_METHOD_BY_ID: Mapping[str, MethodInfo] = MappingProxyType(
    {item.method_id: item for item in _METHODS}
)

if len(_METHOD_BY_ID) != len(_METHODS):
    raise RuntimeError("duplicate canonical method ID in the public method catalog")


def list_methods() -> tuple[MethodInfo, ...]:
    """Return implemented public catalog entries in canonical-ID order."""

    return _METHODS


def method_info(method_id: str) -> MethodInfo:
    """Return metadata for an implemented public catalog entry.

    Raises
    ------
    KeyError
        If ``method_id`` is not an exact ID in the implemented public catalog.
    """

    try:
        return _METHOD_BY_ID[method_id]
    except KeyError:
        raise KeyError(f"unknown DEAPack canonical method ID: {method_id!r}") from None


__all__ = ["MethodInfo", "list_methods", "method_info"]
