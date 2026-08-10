from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from deapack import (
    BCC,
    CCR,
    ActivitySpecificWeakDisposalDDF,
    AdditiveDEA,
    AllocativeDecomposition,
    APZMalmquistLuenbergerProductivityIndex,
    BCCInput,
    BCCOutput,
    BiennialMalmquistProductivityIndex,
    BoundedAdjustedDEA,
    ByProductionDirectionalDistanceDEA,
    ByProductionFareGrosskopfLovellDEA,
    C2S2MultiplicativeDEA,
    CarryOverSpec,
    CCRInput,
    CCROutput,
    ChungFareGrosskopfDDF,
    CommonFactorWeakDisposalDDF,
    CostEfficiency,
    DEAData,
    DEAResult,
    DirectionalDistanceDEA,
    DynamicData,
    DynamicNetworkData,
    DynamicNetworkSBM,
    DynamicNetworkSBMSpec,
    DynamicSBM,
    DynamicSBMSpec,
    EnvironmentalDirectionalDistanceDEA,
    FGNZEnhancedMalmquistProductivityIndex,
    FGNZMalmquistProductivityIndex,
    FreeDisposalHullDEA,
    GDFProfitabilityDecomposition,
    GeneralizedDistanceDEA,
    GlobalMalmquistLuenbergerProductivityIndex,
    GlobalMalmquistProductivityIndex,
    HicksMoorsteenProductivityIndex,
    InputOrientedSlacksBasedDEA,
    InvariantMultiplicativeDEA,
    LewisSextonSequentialNetworkDEA,
    LinkSpec,
    LuenbergerProductivityIndicator,
    MalmquistLuenbergerProductivityIndex,
    MalmquistProductivityIndex,
    MaterialBalanceCoefficients,
    MaterialBalanceDEA,
    MultiplicativeDEA,
    NerlovianProfitInefficiency,
    NetworkData,
    NetworkSBMLinkKind,
    NetworkSpec,
    OutputOrientedSlacksBasedDEA,
    PeriodProductionSpec,
    PriceData,
    ProcessCarryOverSpec,
    ProcessSpec,
    ProfitEfficiency,
    RadialDEA,
    RangeAdjustedDEA,
    RayDesliMalmquistProductivityIndex,
    ReferenceSpec,
    RevenueAllocativeDecomposition,
    RevenueEfficiency,
    SlacksBasedDEA,
    ToneTsutsuiNetworkSBM,
    UndesirableSlacksBasedDEA,
    local_returns_to_scale,
    scale_efficiency,
    scale_elasticity,
)
from deapack._registry import (
    EXPANDED_SPEC_AXES,
    REGISTRY_SCHEMA_VERSION,
    registry_metadata,
)
from deapack.analysis.mpss import most_productive_scale_size
from deapack.evaluation.super_efficiency import APSuperEfficiency


def _cross_section() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )


def _environmental_cross_section(*, by_production: bool = False) -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "energy": [1.0, 2.0],
                "y": [2.0, 1.0],
                "b": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="energy",
        polluting_inputs="energy" if by_production else None,
        outputs="y",
        bad_outputs="b",
    )


def _panel(*, environmental: bool = False) -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 2.0, 4.0],
            "b": [2.0, 4.0, 1.0, 2.0],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
        bad_outputs="b" if environmental else None,
    )


def _network_cross_section() -> NetworkData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "upstream_input": [2.0, 1.0],
            "upstream_output": [1.0, 2.0],
            "handoff": [1.0, 1.0],
            "downstream_input": [2.0, 1.0],
            "downstream_output": [1.0, 2.0],
        }
    )
    spec = NetworkSpec(
        processes=(
            ProcessSpec(
                "upstream",
                inputs="upstream_input",
                outputs=("upstream_output", "handoff"),
            ),
            ProcessSpec(
                "downstream",
                inputs=("handoff", "downstream_input"),
                outputs="downstream_output",
            ),
        ),
        links=(
            LinkSpec(
                "handoff",
                source="upstream",
                target="downstream",
                variables="handoff",
            ),
        ),
    )
    return NetworkData.from_frame(frame, dmu="dmu", spec=spec)


def _dynamic_panel() -> DynamicData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [1, 1, 2, 2],
            "x": [2.0, 1.0, 2.0, 1.0],
            "y": [1.0, 2.0, 1.0, 2.0],
            "inventory": [2.0, 1.0, 2.0, 1.0],
        }
    )
    spec = DynamicSBMSpec(
        production=PeriodProductionSpec(inputs="x", outputs="y"),
        carryovers=(CarryOverSpec("inventory", "free"),),
    )
    return DynamicData.from_frame(
        frame,
        spec=spec,
        dmu="dmu",
        period="period",
    )


def _dynamic_network_panel() -> DynamicNetworkData:
    spec = DynamicNetworkSBMSpec(
        network=NetworkSpec(
            processes=(
                ProcessSpec(
                    "supplier",
                    inputs="x_supplier",
                    outputs=("y_supplier", "handoff"),
                ),
                ProcessSpec(
                    "recipient",
                    inputs=("handoff", "x_recipient"),
                    outputs="y_recipient",
                ),
            ),
            links=(
                LinkSpec(
                    "handoff",
                    source="supplier",
                    target="recipient",
                    variables="handoff",
                ),
            ),
        ),
        link_kinds={"handoff": NetworkSBMLinkKind.FREE},
        carryovers=(ProcessCarryOverSpec("supplier", "capacity", "good"),),
    )
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [1, 1, 2, 2],
            "x_supplier": [1.0, 2.0, 1.1, 2.1],
            "x_recipient": [1.0, 2.0, 1.1, 2.1],
            "handoff": [1.0, 1.5, 1.1, 1.6],
            "y_supplier": [2.0, 1.0, 2.1, 1.1],
            "y_recipient": [2.0, 1.0, 2.1, 1.1],
            "capacity": [2.0, 1.0, 2.1, 1.1],
        }
    )
    return DynamicNetworkData.from_frame(
        frame,
        spec=spec,
        dmu="dmu",
        period="period",
    )


def _assert_registry(result: DEAResult, method_id: str) -> None:
    metadata = result.metadata
    assert metadata["registry_schema_version"] == REGISTRY_SCHEMA_VERSION
    assert metadata["method_id"] == method_id
    assert tuple(metadata["expanded_spec"]) == EXPANDED_SPEC_AXES
    json.dumps(
        {
            "registry_schema_version": metadata["registry_schema_version"],
            "method_id": metadata["method_id"],
            "preset_id": metadata.get("preset_id"),
            "specialization_id": metadata.get("specialization_id"),
            "expanded_spec": metadata["expanded_spec"],
        },
        allow_nan=False,
    )


def test_network_sbm_result_has_canonical_method_metadata() -> None:
    result = ToneTsutsuiNetworkSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
        link_control="free",
        division_weights={"upstream": 0.25, "downstream": 0.75},
    ).fit(_network_cross_section())

    _assert_registry(result, "network.sbm.tone_tsutsui_2009")
    expanded = result.metadata["expanded_spec"]
    assert expanded["graph"]["kind"] == "general_network"
    assert expanded["graph"]["link_topology"] == {
        "handoff": {
            "source": "upstream",
            "recipient": "downstream",
            "variables": ("handoff",),
        }
    }
    assert expanded["technology"]["returns_to_scale"] == "vrs"
    assert expanded["technology"]["link_control"] == "free"
    assert expanded["technology"]["division_specific_intensities"] is True
    assert expanded["performance"]["orientation"] == "non_oriented"
    assert expanded["valuation"]["division_weights"] == {
        "upstream": 0.25,
        "downstream": 0.75,
    }

    sequential = LewisSextonSequentialNetworkDEA().fit(_network_cross_section())
    _assert_registry(
        sequential,
        "network.sequential.lewis_sexton_2004.forward_radial",
    )
    assert sequential.metadata["expanded_spec"]["graph"]["kind"] == ("directed_acyclic")


@pytest.mark.parametrize(
    ("score_variant", "specialization_id", "adjusted_score_policy"),
    [
        ("base", None, "not_primary"),
        (
            "free_adjusted_post",
            "dynamic.sbm.tone_tsutsui_2010.free_adjusted_post",
            "post_optimal_selected_primary_solution",
        ),
    ],
)
def test_dynamic_sbm_variants_have_canonical_source_qualified_metadata(
    score_variant: str,
    specialization_id: str | None,
    adjusted_score_policy: str,
) -> None:
    result = DynamicSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
        score_variant=score_variant,
    ).fit(_dynamic_panel())

    _assert_registry(result, "dynamic.sbm.tone_tsutsui_2010")
    metadata = result.metadata
    expanded = metadata["expanded_spec"]
    if specialization_id is None:
        assert "specialization_id" not in metadata
    else:
        assert metadata["specialization_id"] == specialization_id
    assert "preset_id" not in metadata
    assert tuple(expanded) == EXPANDED_SPEC_AXES

    assert expanded["context"] == {
        "purpose": "intertemporal_operating_plan_performance",
        "managerial_unit": "complete_dmu_trajectory",
    }
    assert expanded["graph"]["kind"] == "time_expanded_carryover_graph"
    assert expanded["graph"]["periods"] == 2
    assert expanded["graph"]["carryovers"] == (
        {
            "variable": "inventory",
            "kind": "free",
            "effect": "neutral_or_not_scored",
            "control": "endogenous",
        },
    )
    assert expanded["technology"]["family"] == (
        "dynamic_carryover_portfolio_envelopment"
    )
    assert expanded["technology"]["returns_to_scale"] == "vrs"
    assert expanded["technology"]["continuity"] == (
        "same_Z_t_exact_adjacent_period_balance"
    )
    assert expanded["technology"]["boundary_policy"] == "tone_tsutsui_2010"
    assert expanded["technology"]["period_specific_intensities"] is True
    assert expanded["reference"] == {
        "kind": "global_complete_trajectory_cohort",
        "cohort_size": 2,
        "same_membership_every_period": True,
        "self_membership": "allowed",
    }
    assert expanded["performance"] == {
        "family": "dynamic_slacks_based_measure",
        "orientation": "non-oriented",
        "score_variant": score_variant,
        "period_decomposition": "solver_selected",
    }
    assert expanded["evaluation_protocol"]["kind"] == ("joint_horizon_self_appraisal")
    assert expanded["evaluation_protocol"]["alternate_optimum_policy"] == (
        "solver_selected"
    )
    assert (
        expanded["evaluation_protocol"]["adjusted_score_policy"]
        == adjusted_score_policy
    )


def test_dynamic_network_sbm_registry_metadata_is_equation_qualified() -> None:
    result = DynamicNetworkSBM(
        orientation="non-oriented",
        returns_to_scale={"recipient": "crs", "supplier": "vrs"},
        period_weights={1: 1.0, 2: 0.0},
        division_weights={"recipient": 0.0, "supplier": 1.0},
    ).fit(_dynamic_network_panel())

    _assert_registry(
        result,
        "dynamic.network_sbm.tone_tsutsui_2014",
    )
    metadata = result.metadata
    expanded = metadata["expanded_spec"]
    technology = expanded["technology"]

    assert technology["returns_to_scale"] == "mixed"
    assert technology["process_returns_to_scale"] == {
        "recipient": "crs",
        "supplier": "vrs",
    }
    assert technology["overall_returns_to_scale_identified"] is False
    assert technology["equation_source_scope"] == (
        "published_article_with_named_terminal_resolution"
    )
    assert technology["published_equations_audited"] is True
    assert technology["published_terminal_indexing_consistent"] is False
    assert technology["terminal_resolution"] == (
        "T_observed_accounts_T_minus_1_continuity"
    )
    assert technology["terminal_observed_account"] is True
    assert technology["continuity_periods"] == "T_minus_1"
    assert technology["all_link_endpoint_continuity"] is True
    assert expanded["valuation"]["weight_domain"] == (
        "nonnegative_each_group_with_at_least_one_positive"
    )
    assert metadata["source_fidelity_claim"] == (
        "published_equations_audited_and_property_validated_without_"
        "published_numerical_oracle_with_named_terminal_resolution"
    )
    assert metadata["effective_weights"]["zero_weight_periods"] == ("2",)
    assert metadata["effective_weights"]["zero_weight_processes"] == ("recipient",)


def test_static_result_paths_have_canonical_method_metadata() -> None:
    data = _cross_section()
    models = (
        (RadialDEA(), "static.radial"),
        (FreeDisposalHullDEA(), "static.radial.fdh"),
        (AdditiveDEA(), "static.additive"),
        (BoundedAdjustedDEA(), "static.bam"),
        (RangeAdjustedDEA(), "static.ram"),
        (MultiplicativeDEA(), "static.multiplicative"),
        (InputOrientedSlacksBasedDEA(), "static.sbm.input.tone2001"),
        (SlacksBasedDEA(), "static.sbm.nonoriented.tone2001"),
        (OutputOrientedSlacksBasedDEA(), "static.sbm.output.tone2001"),
        (DirectionalDistanceDEA(), "static.directional_distance"),
        (
            GeneralizedDistanceDEA(),
            "static.generalized_distance.chavas_cox",
        ),
    )
    for model, method_id in models:
        _assert_registry(model.fit(data), method_id)

    radial_estimator = RadialDEA().fit(data).metadata["expanded_spec"]["estimator"]
    fdh_estimator = (
        FreeDisposalHullDEA().fit(data).metadata["expanded_spec"]["estimator"]
    )
    assert radial_estimator["estimator_id"] == "estimator.full.dea"
    assert fdh_estimator["estimator_id"] == "estimator.full.fdh"

    _assert_registry(
        scale_efficiency(data),
        "analysis.scale_efficiency.radial_ratio",
    )
    _assert_registry(
        local_returns_to_scale(data),
        "analysis.returns_to_scale.local.banker_thrall_1992",
    )
    _assert_registry(
        scale_elasticity(data),
        "analysis.scale_elasticity.local.radial_vrs",
    )
    _assert_registry(
        most_productive_scale_size(data),
        "analysis.mpss.banker_1984",
    )

    _assert_registry(
        APSuperEfficiency().fit(data),
        "evaluation.super.ap_radial",
    )


def test_radial_specializations_are_explicit_without_claiming_full_presets() -> None:
    data = _cross_section()
    assert CCR().fit(data).metadata["specialization_id"] == "static.radial.crs"
    assert BCC().fit(data).metadata["specialization_id"] == "static.radial.vrs"
    assert "preset_id" not in CCR().fit(data).metadata

    generic = RadialDEA(returns_to_scale="crs").fit(data)
    assert generic.metadata["method_id"] == "static.radial"
    assert "specialization_id" not in generic.metadata

    direct_alias_model = SlacksBasedDEA().fit(data)
    assert "specialization_id" not in direct_alias_model.metadata


def test_multiplicative_source_presets_retain_one_family_method_identity() -> None:
    data = _cross_section()
    invariant = InvariantMultiplicativeDEA().fit(data).metadata
    original_data = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A", "B"], "x": [2.0, 4.0], "y": [4.0, 4.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    original = C2S2MultiplicativeDEA().fit(original_data).metadata

    assert invariant["method_id"] == "static.multiplicative"
    assert invariant["preset_id"] == (
        "static.multiplicative.invariant.charnes_etal_1983"
    )
    assert original["method_id"] == "static.multiplicative"
    assert original["preset_id"] == ("static.multiplicative.original.charnes_etal_1982")


@pytest.mark.parametrize(
    (
        "model",
        "preset_id",
        "orientation",
        "returns_to_scale",
        "native_score",
        "efficiency_transform",
    ),
    [
        (
            CCRInput(),
            "static.radial.crs.input",
            "input",
            "crs",
            "theta",
            "identity",
        ),
        (
            CCROutput(),
            "static.radial.crs.output",
            "output",
            "crs",
            "phi",
            "reciprocal",
        ),
        (
            BCCInput(),
            "static.radial.vrs.input",
            "input",
            "vrs",
            "theta",
            "identity",
        ),
        (
            BCCOutput(),
            "static.radial.vrs.output",
            "output",
            "vrs",
            "phi",
            "reciprocal",
        ),
    ],
)
def test_complete_radial_presets_freeze_result_identity_and_target_policy(
    model,
    preset_id: str,
    orientation: str,
    returns_to_scale: str,
    native_score: str,
    efficiency_transform: str,
) -> None:
    metadata = model.fit(_cross_section()).metadata

    assert metadata["method_id"] == "static.radial"
    assert metadata["preset_id"] == preset_id
    assert "specialization_id" not in metadata
    assert metadata["orientation"] == orientation
    assert metadata["returns_to_scale"] == returns_to_scale
    assert metadata["native_score"] == native_score
    assert metadata["efficiency_transform"] == efficiency_transform
    assert metadata["compute_slacks"] is True
    assert metadata["slack_phase"] == "maximize_row_scaled_sum"
    expanded = metadata["expanded_spec"]
    assert expanded["technology"]["returns_to_scale"] == returns_to_scale
    assert expanded["performance"]["orientation"] == orientation
    assert expanded["performance"]["slack_refinement"] is True
    assert (
        expanded["evaluation_protocol"]["secondary_objective"]
        == "maximize_row_scaled_slacks"
    )

    generic = RadialDEA(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
    ).fit(_cross_section())
    assert "preset_id" not in generic.metadata


def test_environmental_result_paths_have_canonical_method_metadata() -> None:
    environmental = _environmental_cross_section()
    by_production = _environmental_cross_section(by_production=True)
    equality_result = EnvironmentalDirectionalDistanceDEA().fit(environmental)
    equality_technology = equality_result.metadata["expanded_spec"]["technology"]
    assert equality_technology["bad_output_treatment"] == (
        "directional_equality_legacy"
    )
    assert equality_technology["technology_id"] == (
        "environmental.joint_production.envelopment"
    )
    assert equality_technology["bad_output_formulation_id"] == (
        "environmental.formulation.bad_output_directional_equality"
    )
    assert equality_technology["bad_output_disposability_id"] == "not_identified"
    assert equality_technology["bad_output_treatment"] == (
        "directional_equality_legacy"
    )
    assert equality_technology["compatibility_alias"] == "weak"
    assert equality_technology["named_weak_disposal_equivalence"] == "not_claimed"
    _assert_registry(equality_result, "environmental.ddf.joint_production")

    models = (
        (
            CommonFactorWeakDisposalDDF(),
            environmental,
            "environmental.ddf.weak_disposal.common_factor",
        ),
        (
            ChungFareGrosskopfDDF(),
            environmental,
            "environmental.ddf.output.chung_fare_grosskopf_1997",
        ),
        (
            ActivitySpecificWeakDisposalDDF(),
            environmental,
            "environmental.ddf.weak_disposal.activity_specific",
        ),
        (
            UndesirableSlacksBasedDEA(),
            environmental,
            "environmental.sbm.separable_strong",
        ),
        (
            ByProductionDirectionalDistanceDEA(),
            by_production,
            "environmental.by_production.ddf",
        ),
        (
            ByProductionFareGrosskopfLovellDEA(),
            by_production,
            "environmental.by_production.fgl",
        ),
    )
    for model, data, method_id in models:
        _assert_registry(model.fit(data), method_id)

    material_data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x1": [1.0, 2.0],
                "x2": [2.0, 1.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    coefficients = MaterialBalanceCoefficients(
        inputs={"material": {"x1": 1.0, "x2": 1.0}},
        outputs={"material": {"y": 1.0}},
    )
    _assert_registry(
        MaterialBalanceDEA(coefficients).fit(material_data),
        "environmental.material_inflow.coelli2007",
    )


def test_economic_result_paths_have_canonical_price_metadata() -> None:
    data = _cross_section()
    prices = PriceData.common(input_prices={"x": 2.0})

    cost = CostEfficiency().fit(data, prices)
    _assert_registry(cost, "economic.cost")
    valuation = cost.metadata["expanded_spec"]["valuation"]
    assert valuation["kind"] == "supplied_input_prices"
    assert valuation["scope"] == "common"
    assert valuation["input_price_signature"]["sha256"]

    decomposition = AllocativeDecomposition().fit(data, prices)
    _assert_registry(
        decomposition,
        "analysis.allocative_decomposition.cost_input_radial",
    )

    output_prices = PriceData.common(output_prices={"y": 3.0})
    revenue = RevenueEfficiency().fit(data, output_prices)
    _assert_registry(revenue, "economic.revenue")
    revenue_valuation = revenue.metadata["expanded_spec"]["valuation"]
    assert revenue_valuation["kind"] == "supplied_output_prices"
    assert revenue_valuation["scope"] == "common"
    assert revenue_valuation["output_price_signature"]["sha256"]

    revenue_decomposition = RevenueAllocativeDecomposition().fit(data, output_prices)
    _assert_registry(
        revenue_decomposition,
        "analysis.allocative_decomposition.revenue_output_radial",
    )

    joint_prices = PriceData.common(
        input_prices={"x": 2.0},
        output_prices={"y": 3.0},
    )
    profit = ProfitEfficiency().fit(data, joint_prices)
    _assert_registry(profit, "economic.profit.maximum")
    assert (
        profit.metadata["expanded_spec"]["valuation"]["kind"]
        == "supplied_input_and_output_prices"
    )

    nerlovian = NerlovianProfitInefficiency().fit(data, joint_prices)
    _assert_registry(nerlovian, "economic.nerlovian.ccf1998")
    assert (
        nerlovian.metadata["expanded_spec"]["analysis"]["kind"]
        == "additive_decomposition"
    )

    profitability_decomposition = GDFProfitabilityDecomposition().fit(
        data,
        joint_prices,
    )
    _assert_registry(
        profitability_decomposition,
        "analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006",
    )


def test_productivity_result_paths_have_canonical_method_metadata() -> None:
    panel = _panel()
    models = (
        (
            MalmquistProductivityIndex(),
            "productivity.malmquist.adjacent_geometric",
        ),
        (LuenbergerProductivityIndicator(), "productivity.luenberger"),
        (
            GlobalMalmquistProductivityIndex(),
            "productivity.global_malmquist",
        ),
        (
            BiennialMalmquistProductivityIndex(),
            "productivity.biennial_malmquist",
        ),
        (
            HicksMoorsteenProductivityIndex(),
            "productivity.hicks_moorsteen.bjurek_1996",
        ),
    )
    for model, method_id in models:
        _assert_registry(model.fit(panel), method_id)

    fgnz = FGNZMalmquistProductivityIndex().fit(panel)
    _assert_registry(fgnz, "productivity.malmquist.adjacent_geometric")
    assert (
        fgnz.metadata["preset_id"] == "productivity.malmquist.decomposition.fgnz_core"
    )
    assert (
        fgnz.metadata["expanded_spec"]["analysis"]["decomposition_id"]
        == "productivity.malmquist.decomposition.fgnz_core"
    )

    enhanced_fgnz = FGNZEnhancedMalmquistProductivityIndex().fit(panel)
    _assert_registry(
        enhanced_fgnz,
        "productivity.malmquist.decomposition.fgnz_pure_scale_extension",
    )
    assert "preset_id" not in enhanced_fgnz.metadata
    assert enhanced_fgnz.metadata["parent_operator_id"] == (
        "productivity.malmquist.adjacent_geometric"
    )
    assert (
        enhanced_fgnz.metadata["expanded_spec"]["analysis"]["decomposition_id"]
        == "productivity.malmquist.decomposition.fgnz_pure_scale_extension"
    )

    ray_desli = RayDesliMalmquistProductivityIndex().fit(panel)
    _assert_registry(
        ray_desli,
        "productivity.malmquist.decomposition.ray_desli",
    )
    assert "preset_id" not in ray_desli.metadata
    assert ray_desli.metadata["parent_operator_id"] == (
        "productivity.malmquist.adjacent_geometric"
    )
    assert ray_desli.metadata["expanded_spec"]["analysis"]["decomposition_id"] == (
        "productivity.malmquist.decomposition.ray_desli"
    )

    environmental_panel = _panel(environmental=True)
    environmental_models = (
        (
            APZMalmquistLuenbergerProductivityIndex(),
            "productivity.malmquist_luenberger.aparicio_pastor_zofio_2013",
        ),
        (
            MalmquistLuenbergerProductivityIndex(),
            "productivity.malmquist_luenberger.chung_fare_grosskopf_1997",
        ),
        (
            GlobalMalmquistLuenbergerProductivityIndex(),
            "productivity.global_malmquist_luenberger.oh_2010",
        ),
    )
    for model, method_id in environmental_models:
        _assert_registry(model.fit(environmental_panel), method_id)


def test_registry_builder_requires_exact_json_safe_axes() -> None:
    expanded = {axis: {"kind": "not_applicable"} for axis in EXPANDED_SPEC_AXES}
    metadata = registry_metadata("static.example", expanded)

    assert metadata["registry_schema_version"] == REGISTRY_SCHEMA_VERSION
    assert tuple(metadata["expanded_spec"]) == EXPANDED_SPEC_AXES
    json.dumps(metadata, allow_nan=False)

    with pytest.raises(ValueError, match="exactly the eleven"):
        registry_metadata("static.example", {"context": {}})
    with pytest.raises(ValueError, match="mutually exclusive"):
        registry_metadata(
            "static.example",
            expanded,
            preset_id="static.example.complete",
            specialization_id="static.example.partial",
        )

    invalid = dict(expanded)
    invalid["technology"] = np.asarray([1.0, 2.0])
    with pytest.raises(TypeError, match="JSON serializable"):
        registry_metadata("static.example", invalid)


def test_registry_distinguishes_custom_directions_and_freezes_the_spec() -> None:
    data = _cross_section()
    first = DirectionalDistanceDEA(
        input_direction=[1.0],
        output_direction=[1.0],
    ).fit(data)
    second = DirectionalDistanceDEA(
        input_direction=[2.0],
        output_direction=[1.0],
    ).fit(data)

    first_direction = first.metadata["expanded_spec"]["performance"]["input_direction"]
    second_direction = second.metadata["expanded_spec"]["performance"][
        "input_direction"
    ]
    assert first_direction["kind"] == "custom_global"
    assert (
        first_direction["parameter"]["sha256"]
        != second_direction["parameter"]["sha256"]
    )

    with pytest.raises(TypeError, match="immutable"):
        first.metadata["expanded_spec"]["technology"]["family"] = "changed"
    json.dumps(first.metadata["expanded_spec"], allow_nan=False)


def test_registry_records_window_bounds_and_variable_role_assignments() -> None:
    panel = _panel()
    current_only = RadialDEA(
        reference=ReferenceSpec(kind="window", window_before=0, window_after=0)
    ).fit(panel)
    current_and_prior = RadialDEA(
        reference=ReferenceSpec(kind="window", window_before=1, window_after=0)
    ).fit(panel)
    first_reference = current_only.metadata["expanded_spec"]["reference"]
    second_reference = current_and_prior.metadata["expanded_spec"]["reference"]
    assert first_reference["window_before"] == 0
    assert second_reference["window_before"] == 1
    assert first_reference != second_reference

    first_custom = FreeDisposalHullDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(_cross_section())
    second_custom = FreeDisposalHullDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=[1])
    ).fit(_cross_section())
    first_custom_rows = first_custom.metadata["expanded_spec"]["reference"][
        "custom_rows"
    ]
    second_custom_rows = second_custom.metadata["expanded_spec"]["reference"][
        "custom_rows"
    ]
    assert first_custom_rows["count"] == 1
    assert first_custom_rows["sha256"] != second_custom_rows["sha256"]
    ordered_set = FreeDisposalHullDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=[0, 1])
    ).fit(_cross_section())
    reversed_set = FreeDisposalHullDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=[1, 0])
    ).fit(_cross_section())
    assert (
        ordered_set.metadata["expanded_spec"]["reference"]["custom_rows"]["sha256"]
        == reversed_set.metadata["expanded_spec"]["reference"]["custom_rows"]["sha256"]
    )

    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "x1": [1.0, 2.0, 4.0],
            "x2": [4.0, 2.0, 1.0],
            "y": [1.0, 2.0, 3.0],
            "b": [1.0, 2.0, 4.0],
        }
    )
    first_data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        polluting_inputs=["x1"],
        outputs="y",
        bad_outputs="b",
    )
    second_data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        polluting_inputs=["x2"],
        outputs="y",
        bad_outputs="b",
    )
    first_roles = (
        ByProductionDirectionalDistanceDEA()
        .fit(first_data)
        .metadata["expanded_spec"]["data_roles"]
    )
    second_roles = (
        ByProductionDirectionalDistanceDEA()
        .fit(second_data)
        .metadata["expanded_spec"]["data_roles"]
    )
    assert first_roles["variables"]["polluting_inputs"] == ("x1",)
    assert second_roles["variables"]["polluting_inputs"] == ("x2",)
    assert first_roles != second_roles


def test_registry_records_material_valuation_parameters() -> None:
    unweighted_scale = AdditiveDEA(
        input_weights=[1.0],
        output_weights=[1.0],
    ).fit(_cross_section())
    changed_scale = AdditiveDEA(
        input_weights=[2.0],
        output_weights=[1.0],
    ).fit(_cross_section())
    first_weight_signature = unweighted_scale.metadata["expanded_spec"]["valuation"][
        "input_weights"
    ]
    second_weight_signature = changed_scale.metadata["expanded_spec"]["valuation"][
        "input_weights"
    ]
    assert first_weight_signature["sha256"] != second_weight_signature["sha256"]

    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x1": [1.0, 2.0],
                "x2": [2.0, 1.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    first = MaterialBalanceDEA(
        MaterialBalanceCoefficients(
            inputs={"material": {"x1": 1.0, "x2": 1.0}},
            outputs={"material": {"y": 1.0}},
        )
    ).fit(data)
    second = MaterialBalanceDEA(
        MaterialBalanceCoefficients(
            inputs={"material": {"x1": 2.0, "x2": 1.0}},
            outputs={"material": {"y": 1.0}},
        )
    ).fit(data)
    first_valuation = first.metadata["expanded_spec"]["valuation"]
    second_valuation = second.metadata["expanded_spec"]["valuation"]
    assert first_valuation["input_coefficients"]["material"]["x1"] == 1.0
    assert second_valuation["input_coefficients"]["material"]["x1"] == 2.0
    assert first_valuation != second_valuation


def test_third_party_dea_result_remains_backward_compatible() -> None:
    summary = pd.DataFrame(
        {
            "dmu_id": ["external"],
            "period": [None],
            "score": [1.0],
            "efficiency": [1.0],
            "distance": [0.0],
            "is_efficient": [True],
            "solver_status": ["optimal"],
            "model_family": ["third_party"],
        }
    )
    result = DEAResult(summary_frame=summary, metadata={"provider": "external"})

    assert result.metadata["provider"] == "external"
    assert "method_id" not in result.metadata
    assert "registry_schema_version" not in result.metadata
