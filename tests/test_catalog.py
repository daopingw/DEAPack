from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import deapack
from deapack import MethodInfo, list_methods, method_info

EXPECTED_METHOD_IDS = {
    "analysis.allocative_decomposition.cost_input_radial",
    "analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006",
    "analysis.allocative_decomposition.revenue_output_radial",
    "analysis.reference_frequency.selected_plan",
    "analysis.returns_to_scale.local.banker_thrall_1992",
    "analysis.scale_efficiency.radial_ratio",
    "analysis.scale_elasticity.directional.relative_vrs.ren_etal_2021",
    "analysis.scale_elasticity.local.radial_vrs",
    "economic.cost",
    "economic.nerlovian.ccf1998",
    "economic.profit.maximum",
    "economic.profitability.return_to_dollar",
    "economic.revenue",
    "evaluation.cross.game_nash.liang_wu_cook_zhu_2008",
    "evaluation.super.directional.ray_2008",
    "evaluation.super.sbm.tone_2002",
    "environmental.by_production.ddf",
    "environmental.by_production.fgl",
    "environmental.ddf.joint_production",
    "environmental.ddf.output.chung_fare_grosskopf_1997",
    "environmental.ddf.weak_disposal.activity_specific",
    "environmental.ddf.weak_disposal.common_factor",
    "environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp",
    "environmental.material_inflow.coelli2007",
    "environmental.sbm.nonseparable_hybrid.tone_2003",
    "environmental.sbm.separable_strong",
    "heterogeneity.metafrontier.radial.odonnell_rao_battese_2008",
    "dynamic.network_sbm.tone_tsutsui_2014",
    "dynamic.sbm.tone_tsutsui_2010",
    "dynamic.sbm.tone_tsutsui_2010.free_adjusted_post",
    "network.additive.chen_etal_2009",
    "network.additive.cook_zhu_bi_yang_2010",
    "network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018",
    "network.radial.fare_grosskopf_2000",
    "network.relational.kao_hwang_2008",
    "network.sbm.tone_tsutsui_2009",
    "network.sbm.tone_tsutsui_2009.accountable_input_link",
    "network.sbm.tone_tsutsui_2009.accountable_output_link",
    "network.sequential.lewis_sexton_2004.forward_radial",
    "panel.multiperiod_aggregative.park_park_2009",
    "productivity.biennial_malmquist",
    "productivity.global_malmquist",
    "productivity.global_malmquist_luenberger.oh_2010",
    "productivity.hicks_moorsteen.bjurek_1996",
    "productivity.luenberger",
    "productivity.malmquist.adjacent_geometric",
    "productivity.malmquist.decomposition.fgnz_core",
    "productivity.malmquist.decomposition.fgnz_pure_scale_extension",
    "productivity.malmquist.decomposition.ray_desli",
    "productivity.malmquist_luenberger.aparicio_pastor_zofio_2013",
    "productivity.malmquist_luenberger.chung_fare_grosskopf_1997",
    "static.additive",
    "static.bam",
    "static.directional_distance",
    "static.ebm.input.tone_tsutsui_2010.crs.declared",
    "static.generalized_distance.chavas_cox",
    "static.multiplicative",
    "static.multiplicative.invariant.charnes_etal_1983",
    "static.multiplicative.original.charnes_etal_1982",
    "static.radial",
    "static.radial.crs",
    "static.radial.crs.input",
    "static.radial.crs.output",
    "static.radial.fch.green_cook_2004",
    "static.radial.fdh",
    "static.radial.frh",
    "static.radial.vrs",
    "static.radial.vrs.input",
    "static.radial.vrs.output",
    "static.ram",
    "static.range_directional.portela_thanassoulis_simpson_2004",
    "static.sbm.input.tone2001",
    "static.sbm.nonoriented.tone2001",
    "static.sbm.output.tone2001",
    "valuation.weight_restriction.cone_ratio.polyhedral_crs.charnes_etal_1990",
}


def test_catalog_contains_only_the_declared_implemented_public_methods() -> None:
    methods = list_methods()

    assert isinstance(methods, tuple)
    assert all(isinstance(item, MethodInfo) for item in methods)
    assert {item.method_id for item in methods} == EXPECTED_METHOD_IDS
    assert [item.method_id for item in methods] == sorted(EXPECTED_METHOD_IDS)
    assert len(methods) == 75
    assert sum(item.identifier_role == "method_id" for item in methods) == 62
    assert sum(item.identifier_role == "specialization_id" for item in methods) == 5
    assert sum(item.identifier_role == "preset_id" for item in methods) == 8
    assert {
        item.method_id
        for item in methods
        if item.identifier_role == "specialization_id"
    } == {
        "dynamic.sbm.tone_tsutsui_2010.free_adjusted_post",
        "network.sbm.tone_tsutsui_2009.accountable_input_link",
        "network.sbm.tone_tsutsui_2009.accountable_output_link",
        "static.radial.crs",
        "static.radial.vrs",
    }
    assert {
        item.method_id for item in methods if item.identifier_role == "preset_id"
    } == {
        "static.radial.crs.input",
        "static.radial.crs.output",
        "static.radial.vrs.input",
        "static.radial.vrs.output",
        "productivity.malmquist.decomposition.fgnz_core",
        "productivity.malmquist_luenberger.aparicio_pastor_zofio_2013",
        "static.multiplicative.invariant.charnes_etal_1983",
        "static.multiplicative.original.charnes_etal_1982",
    }

    assert "static.ebm" not in EXPECTED_METHOD_IDS
    assert "economic.profit" not in EXPECTED_METHOD_IDS
    assert "static.radial.restricted_rts" not in EXPECTED_METHOD_IDS
    assert not hasattr(deapack, "EnvironmentalDirectionalProductivityIndex")
    assert not hasattr(deapack, "GlobalEnvironmentalDirectionalProductivityIndex")
    assert not hasattr(deapack, "BBC")


def test_catalog_metadata_and_collection_are_immutable() -> None:
    methods = list_methods()
    radial = method_info("static.radial")

    with pytest.raises(FrozenInstanceError):
        radial.title = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        radial.api_symbols[0] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        radial.documentation[0] = "changed"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        radial.publication_scope = "documentation_only"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        methods.append(radial)  # type: ignore[attr-defined]

    assert list_methods() is methods
    assert method_info("static.radial") is radial
    assert radial.identifier_role == "method_id"
    assert radial.documentation == ("api", "book")
    assert radial.publication_scope is None


def test_governed_publication_scope_matches_the_machine_registry() -> None:
    root = Path(__file__).resolve().parents[1]
    governed_categories = {
        "productivity",
        "network",
        "dynamic",
        "panel",
        "heterogeneity",
        "evaluation",
        "diagnostics",
        "decision",
        "inference",
        "uncertainty",
    }
    registry_root = root / "specs" / "registry"
    manifest = json.loads(
        (registry_root / "registry-manifest.json").read_text(encoding="utf-8")
    )
    registry_records = {
        record["id"]: record
        for relative in manifest["methods"]
        for record in [
            json.loads((registry_root / relative).read_text(encoding="utf-8"))
        ]
        if record["category"] in governed_categories
    }
    public_registry_records = {
        method_id: record
        for method_id, record in registry_records.items()
        if record["status"]["implementation"] == "implemented"
        and record["status"]["api"] == "public"
    }
    catalog = {
        item.method_id: item
        for item in list_methods()
        if item.category in governed_categories
    }
    catalog_only_scopes = {
        "productivity.malmquist.decomposition.fgnz_core": "handbook_core",
        "network.sbm.tone_tsutsui_2009.accountable_input_link": ("documentation_only"),
        "network.sbm.tone_tsutsui_2009.accountable_output_link": ("documentation_only"),
        "dynamic.sbm.tone_tsutsui_2010.free_adjusted_post": ("documentation_only"),
    }

    assert set(catalog) == set(public_registry_records) | set(catalog_only_scopes)
    for method_id, record in public_registry_records.items():
        assert (
            catalog[method_id].publication_scope
            == record["status"]["publication_scope"]
        )

    assert {
        method_id
        for method_id, record in registry_records.items()
        if record["status"]["publication_scope"] == "next_version"
    }.isdisjoint(catalog)

    assert {
        method_id: catalog[method_id].publication_scope
        for method_id in catalog_only_scopes
    } == catalog_only_scopes
    assert (
        catalog["productivity.malmquist.decomposition.fgnz_core"].identifier_role
        == "preset_id"
    )
    assert {
        method_id
        for method_id, item in catalog.items()
        if item.identifier_role == "method_id"
        and item.publication_scope == "handbook_core"
    } == {
        "productivity.hicks_moorsteen.bjurek_1996",
        "productivity.luenberger",
        "productivity.malmquist.adjacent_geometric",
        "productivity.malmquist_luenberger.chung_fare_grosskopf_1997",
        "network.radial.fare_grosskopf_2000",
        "network.relational.kao_hwang_2008",
        "network.additive.chen_etal_2009",
        "network.additive.cook_zhu_bi_yang_2010",
        "network.sbm.tone_tsutsui_2009",
        "dynamic.sbm.tone_tsutsui_2010",
        "heterogeneity.metafrontier.radial.odonnell_rao_battese_2008",
    }
    assert all(
        item.publication_scope is None
        for item in list_methods()
        if item.category not in governed_categories
    )


def test_fdh_catalog_retains_its_core_book_and_exact_evidence() -> None:
    info = method_info("static.radial.fdh")

    assert info.api_symbols == ("FreeDisposalHullDEA", "FDH")
    assert info.verification == "primary_equations"
    assert info.documentation == ("api", "book")


def test_fch_catalog_exposes_its_claim_scoped_analytical_evidence() -> None:
    info = method_info("static.radial.fch.green_cook_2004")

    assert info.api_symbols == ("FreeCoordinationHullDEA", "FCH")
    assert info.verification == "primary_equations"
    assert info.documentation == ("api",)


def test_every_catalog_symbol_is_available_from_the_top_level_api() -> None:
    for item in list_methods():
        assert item.api_symbols
        for symbol in item.api_symbols:
            assert hasattr(deapack, symbol), (item.method_id, symbol)


def test_reader_facing_public_method_table_matches_the_catalog() -> None:
    table_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "user-guide"
        / "method-catalog.md"
    )
    documented_ids: set[str] = set()
    for line in table_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) > 3 and cells[2].startswith("`") and cells[2].endswith("`"):
            documented_ids.add(cells[2].strip("`"))

    assert documented_ids == {item.method_id for item in list_methods()}


def test_reader_facing_productivity_scope_map_matches_the_catalog() -> None:
    root = Path(__file__).resolve().parents[1]
    catalog_text = (root / "docs" / "user-guide" / "method-catalog.md").read_text(
        encoding="utf-8"
    )
    route_text = catalog_text.split(
        "The four routes themselves are deliberately few:", maxsplit=1
    )[1].split("The complete productivity catalog map", maxsplit=1)[0]
    core_route_ids = {
        "productivity.hicks_moorsteen.bjurek_1996",
        "productivity.luenberger",
        "productivity.malmquist.adjacent_geometric",
        "productivity.malmquist_luenberger.chung_fare_grosskopf_1997",
    }

    for item in list_methods():
        if item.category != "productivity":
            continue
        row_prefix = f"| `{item.publication_scope}` | `{item.method_id}` |"
        assert catalog_text.count(row_prefix) == 1

    assert {
        method_id for method_id in core_route_ids if f"`{method_id}`" in route_text
    } == core_route_ids
    assert route_text.count("`productivity.") == 4


def test_reader_facing_network_dynamic_panel_scope_map_matches_catalog() -> None:
    root = Path(__file__).resolve().parents[1]
    catalog_text = (root / "docs" / "user-guide" / "method-catalog.md").read_text(
        encoding="utf-8"
    )
    scope_map = catalog_text.split(
        "## Network, dynamic, and panel publication map", maxsplit=1
    )[1].split("## Implemented public entries", maxsplit=1)[0]
    governed_categories = {"network", "dynamic", "panel"}

    for item in list_methods():
        if item.category not in governed_categories:
            continue
        row_prefix = f"| `{item.publication_scope}` | `{item.method_id}` |"
        assert scope_map.count(row_prefix) == 1

    assert "Part V of the Handbook retains two network routes" in scope_map
    assert "Part VI retains Dynamic SBM" in scope_map


def test_reader_facing_heterogeneity_scope_map_matches_catalog() -> None:
    root = Path(__file__).resolve().parents[1]
    catalog_text = (root / "docs" / "user-guide" / "method-catalog.md").read_text(
        encoding="utf-8"
    )
    scope_map = catalog_text.split("## Heterogeneity publication map", maxsplit=1)[
        1
    ].split("## Implemented public entries", maxsplit=1)[0]
    item = method_info("heterogeneity.metafrontier.radial.odonnell_rao_battese_2008")

    row_prefix = f"| `{item.publication_scope}` | `{item.method_id}` |"
    assert scope_map.count(row_prefix) == 1
    assert "retains one field-level comparison route" in scope_map
    assert "not another managerial-efficiency score" in scope_map


def test_reader_facing_evaluation_scope_map_matches_catalog() -> None:
    root = Path(__file__).resolve().parents[1]
    catalog_text = (root / "docs" / "user-guide" / "method-catalog.md").read_text(
        encoding="utf-8"
    )
    scope_map = catalog_text.split("## Evaluation publication map", maxsplit=1)[
        1
    ].split("## Implemented public entries", maxsplit=1)[0]

    for item in list_methods():
        if item.category != "evaluation":
            continue
        row_prefix = f"| `{item.publication_scope}` | `{item.method_id}` |"
        assert scope_map.count(row_prefix) == 1

    assert "no separate current" in scope_map
    assert "Handbook route" in scope_map
    assert "non-public prototypes" in scope_map


def test_reader_facing_diagnostics_scope_map_matches_catalog() -> None:
    root = Path(__file__).resolve().parents[1]
    catalog_text = (root / "docs" / "user-guide" / "method-catalog.md").read_text(
        encoding="utf-8"
    )
    scope_map = catalog_text.split("## Diagnostics publication map", maxsplit=1)[
        1
    ].split("## Evaluation publication map", maxsplit=1)[0]

    item = method_info("analysis.reference_frequency.selected_plan")
    row_prefix = f"| `{item.publication_scope}` | `{item.method_id}` |"
    assert scope_map.count(row_prefix) == 1
    assert "one certified solver-selected peer plan" in scope_map
    assert "not an influence, outlier, or statistical-inference claim" in scope_map


def test_docs_index_separates_core_productivity_routes_from_technical_leaves() -> None:
    index_text = (Path(__file__).resolve().parents[1] / "docs" / "index.md").read_text(
        encoding="utf-8"
    )

    def _toctree_entries(caption: str, next_caption: str) -> list[str]:
        block = index_text.split(f":caption: {caption}", maxsplit=1)[1].split(
            f":caption: {next_caption}", maxsplit=1
        )[0]
        return [
            line.strip()
            for line in block.splitlines()
            if line.strip().startswith("analysis/")
        ]

    assert _toctree_entries(
        "Productivity — four Handbook routes",
        "Productivity — supporting and sensitivity companions",
    ) == [
        "analysis/malmquist",
        "analysis/luenberger",
        "analysis/malmquist-luenberger",
        "analysis/hicks-moorsteen",
    ]
    assert _toctree_entries(
        "Productivity — supporting and sensitivity companions",
        "Productivity — specialized Documentation leaves",
    ) == [
        "analysis/global-malmquist",
        "analysis/global-malmquist-luenberger",
    ]
    assert _toctree_entries(
        "Productivity — specialized Documentation leaves",
        "API",
    ) == [
        "analysis/biennial-malmquist",
        "analysis/apz-malmquist-luenberger",
    ]
    assert "Enhanced FGNZ and Ray--Desli" in index_text
    assert "it is not a fifth route" in index_text


def test_erg_is_a_discoverability_alias_not_a_second_method() -> None:
    assert deapack.ERG is deapack.SlacksBasedDEA
    assert method_info("static.sbm.nonoriented.tone2001").api_symbols == (
        "SlacksBasedDEA",
        "SBM",
        "ERG",
    )
    with pytest.raises(KeyError):
        method_info("static.erg")


def test_bam_alias_and_cross_implementation_evidence_are_public() -> None:
    assert deapack.BAM is deapack.BoundedAdjustedDEA
    info = method_info("static.bam")
    assert info.api_symbols == ("BoundedAdjustedDEA", "BAM")
    assert info.verification == "cross_implementation"
    assert info.documentation == ("api",)


def test_by_production_fgl_catalog_exposes_source_oracle_status() -> None:
    info = method_info("environmental.by_production.fgl")

    assert info.title == (
        "Modified Färe--Grosskopf--Lovell efficiency under by-production"
    )
    assert info.verification == "literature_oracle"
    assert info.documentation == ("api",)


def test_zhou_ang_wang_non_chp_is_one_class_with_three_source_accounts() -> None:
    assert deapack.NonCHPEnergyCarbonDEA is (deapack.ZhouAngWangNonCHPEnergyCarbonDEA)
    info = method_info(
        "environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp"
    )

    assert info.identifier_role == "method_id"
    assert info.kind == "preset"
    assert info.api_symbols == (
        "ZhouAngWangNonCHPEnergyCarbonDEA",
        "NonCHPEnergyCarbonDEA",
    )
    assert info.verification == "primary_equations"
    assert info.documentation == ("api",)


def test_range_directional_alias_and_source_evidence_are_public() -> None:
    assert deapack.RDM is deapack.RangeDirectionalDEA
    info = method_info("static.range_directional.portela_thanassoulis_simpson_2004")

    assert info.kind == "preset"
    assert info.api_symbols == ("RangeDirectionalDEA", "RDM")
    assert info.verification == "cross_implementation"
    assert info.documentation == ("api",)


def test_oriented_sbm_symbols_are_distinct_public_presets() -> None:
    assert deapack.InputSBM is deapack.InputOrientedSlacksBasedDEA
    assert deapack.InputRussell is deapack.InputOrientedSlacksBasedDEA
    assert deapack.OutputSBM is deapack.OutputOrientedSlacksBasedDEA
    assert deapack.OutputRussell is deapack.OutputOrientedSlacksBasedDEA
    assert method_info("static.sbm.input.tone2001").api_symbols == (
        "InputOrientedSlacksBasedDEA",
        "InputSBM",
        "InputRussell",
    )
    assert method_info("static.sbm.output.tone2001").api_symbols == (
        "OutputOrientedSlacksBasedDEA",
        "OutputSBM",
        "OutputRussell",
    )


def test_named_radial_recipes_are_complete_public_presets() -> None:
    expected = {
        "static.radial.crs.input": ("CCRInput",),
        "static.radial.crs.output": ("CCROutput",),
        "static.radial.vrs.input": ("BCCInput",),
        "static.radial.vrs.output": ("BCCOutput",),
    }

    for preset_id, symbols in expected.items():
        info = method_info(preset_id)
        assert info.identifier_role == "preset_id"
        assert info.kind == "preset"
        assert info.api_symbols == symbols
        assert info.verification == "primary_equations"
        assert info.documentation == ("api", "book")


def test_fgnz_core_is_a_named_source_qualified_preset() -> None:
    assert deapack.FGNZMalmquist is deapack.FGNZMalmquistProductivityIndex
    info = method_info("productivity.malmquist.decomposition.fgnz_core")

    assert info.identifier_role == "preset_id"
    assert info.kind == "preset"
    assert info.api_symbols == (
        "FGNZMalmquistProductivityIndex",
        "FGNZMalmquist",
    )
    assert info.verification == "primary_equations"
    assert info.documentation == ("api", "book")


def test_core_productivity_accounts_retain_book_placement_and_exact_evidence() -> None:
    for method_id in (
        "productivity.global_malmquist",
        "productivity.global_malmquist_luenberger.oh_2010",
        "productivity.hicks_moorsteen.bjurek_1996",
        "productivity.luenberger",
        "productivity.malmquist.adjacent_geometric",
    ):
        info = method_info(method_id)
        assert info.verification == "primary_equations"
        assert info.documentation == ("api", "book")


def test_enhanced_fgnz_is_a_distinct_source_qualified_operator() -> None:
    assert deapack.FGNZEnhancedMalmquist is (
        deapack.FGNZEnhancedMalmquistProductivityIndex
    )
    info = method_info("productivity.malmquist.decomposition.fgnz_pure_scale_extension")

    assert info.identifier_role == "method_id"
    assert info.kind == "operator"
    assert info.api_symbols == (
        "FGNZEnhancedMalmquistProductivityIndex",
        "FGNZEnhancedMalmquist",
    )
    assert info.verification == "primary_equations"
    assert info.documentation == ("api",)


def test_ray_desli_is_a_distinct_source_qualified_operator() -> None:
    assert deapack.RayDesliMalmquist is deapack.RayDesliMalmquistProductivityIndex
    info = method_info("productivity.malmquist.decomposition.ray_desli")

    assert info.identifier_role == "method_id"
    assert info.kind == "operator"
    assert info.api_symbols == (
        "RayDesliMalmquistProductivityIndex",
        "RayDesliMalmquist",
    )
    assert info.verification == "primary_equations"
    assert info.documentation == ("api",)


def test_local_rts_catalog_exposes_its_book_and_api_evidence() -> None:
    info = method_info("analysis.returns_to_scale.local.banker_thrall_1992")

    assert info.verification == "literature_oracle"
    assert info.documentation == ("api", "book")


def test_scale_elasticity_catalog_exposes_its_oracle_and_documentation() -> None:
    info = method_info("analysis.scale_elasticity.local.radial_vrs")

    assert info.api_symbols == ("scale_elasticity",)
    assert info.verification == "literature_oracle"
    assert info.documentation == ("api", "book")


@pytest.mark.parametrize(
    ("method_id", "symbols"),
    (
        (
            "analysis.mpss.banker_1984",
            ("most_productive_scale_size", "mpss"),
        ),
        (
            "analysis.capacity.physical.fare_grosskopf_kokkelenberg_1989",
            ("physical_capacity",),
        ),
    ),
)
def test_source_incomplete_analysis_prototypes_are_not_public(
    method_id: str,
    symbols: tuple[str, ...],
) -> None:
    for symbol in symbols:
        assert not hasattr(deapack, symbol)
    with pytest.raises(KeyError, match="unknown DEAPack canonical method ID"):
        method_info(method_id)


def test_cfg_malmquist_luenberger_exposes_primary_equation_evidence() -> None:
    info = method_info("productivity.malmquist_luenberger.chung_fare_grosskopf_1997")

    assert info.api_symbols == (
        "MalmquistLuenbergerProductivityIndex",
        "MalmquistLuenbergerDEA",
    )
    assert info.verification == "primary_equations"
    assert info.documentation == ("api", "book")


def test_biennial_malmquist_exposes_claim_scoped_analytical_evidence() -> None:
    info = method_info("productivity.biennial_malmquist")

    assert info.api_symbols == (
        "BiennialMalmquistProductivityIndex",
        "BiennialMalmquistDEA",
    )
    assert info.verification == "primary_equations"
    assert info.documentation == ("api",)
    assert info.publication_scope == "documentation_only"


def test_apz_malmquist_luenberger_is_a_distinct_source_qualified_preset() -> None:
    assert deapack.APZMalmquistLuenbergerDEA is (
        deapack.APZMalmquistLuenbergerProductivityIndex
    )
    info = method_info("productivity.malmquist_luenberger.aparicio_pastor_zofio_2013")

    assert info.identifier_role == "preset_id"
    assert info.kind == "preset"
    assert info.api_symbols == (
        "APZMalmquistLuenbergerProductivityIndex",
        "APZMalmquistLuenbergerDEA",
    )
    assert info.verification == "primary_equations"
    assert info.documentation == ("api",)


def test_only_source_qualified_cross_appraisal_is_public() -> None:
    game = method_info("evaluation.cross.game_nash.liang_wu_cook_zhu_2008")

    for symbol in ("CRSCrossEfficiency", "CrossEfficiency"):
        assert not hasattr(deapack, symbol)
    with pytest.raises(KeyError, match="unknown DEAPack canonical method ID"):
        method_info("evaluation.cross.crs")
    assert game.api_symbols == (
        "LiangWuCookZhuGameCrossEfficiency",
        "GameCrossEfficiency",
    )
    assert game.verification == "literature_oracle"
    assert game.documentation == ("api",)


def test_ap_super_efficiency_is_deferred_from_the_public_surface() -> None:
    for symbol in ("AndersenPetersenSuperEfficiency", "APSuperEfficiency"):
        assert not hasattr(deapack, symbol)
    with pytest.raises(KeyError, match="unknown DEAPack canonical method ID"):
        method_info("evaluation.super.ap_radial")


def test_frh_is_a_cross_implemented_public_technology_variant() -> None:
    assert deapack.FRH is deapack.FreeReplicabilityHullDEA
    info = method_info("static.radial.frh")

    assert info.kind == "variant"
    assert info.api_symbols == ("FreeReplicabilityHullDEA", "FRH")
    assert info.verification == "cross_implementation"
    assert info.documentation == ("api",)


def test_network_sbm_alias_is_not_a_second_method() -> None:
    assert deapack.NetworkSBM is deapack.ToneTsutsuiNetworkSBM
    assert method_info("network.sbm.tone_tsutsui_2009").api_symbols == (
        "ToneTsutsuiNetworkSBM",
        "NetworkSBM",
    )
    with pytest.raises(KeyError):
        method_info("network.sbm")


def test_network_sbm_accountable_links_are_discovery_specializations() -> None:
    incoming = method_info("network.sbm.tone_tsutsui_2009.accountable_input_link")
    outgoing = method_info("network.sbm.tone_tsutsui_2009.accountable_output_link")

    for item in (incoming, outgoing):
        assert item.identifier_role == "specialization_id"
        assert item.kind == "specialization"
        assert item.api_symbols == (
            "ToneTsutsuiNetworkSBM",
            "NetworkSBM",
        )
        assert item.verification == "primary_equations"
        assert item.documentation == ("api",)


def test_fare_grosskopf_network_radial_is_a_system_only_public_leaf() -> None:
    info = method_info("network.radial.fare_grosskopf_2000")

    assert info.api_symbols == ("FareGrosskopfNetworkRadialDEA",)
    assert info.kind == "preset"
    assert info.category == "network"
    assert info.verification == "cross_implementation"
    assert info.documentation == ("api", "book")


def test_kalhor_matin_environmental_network_is_a_source_reproduced_leaf() -> None:
    info = method_info(
        "network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018"
    )

    assert info.api_symbols == ("KalhorKazemiMatinNetworkDEA",)
    assert info.kind == "preset"
    assert info.category == "network"
    assert info.verification == "literature_oracle"
    assert info.documentation == ("api",)


def test_separable_environmental_sbm_exposes_its_bounded_literature_oracle() -> None:
    info = method_info("environmental.sbm.separable_strong")

    assert info.api_symbols == ("UndesirableSlacksBasedDEA", "UndesirableSBM")
    assert info.category == "environmental"
    assert info.verification == "literature_oracle"
    assert info.documentation == ("api", "book")


def test_radial_metafrontier_alias_and_cross_implementation_are_public() -> None:
    assert deapack.MetafrontierDEA is deapack.RadialMetafrontierDEA
    info = method_info("heterogeneity.metafrontier.radial.odonnell_rao_battese_2008")

    assert info.kind == "operator"
    assert info.category == "heterogeneity"
    assert info.api_symbols == ("RadialMetafrontierDEA", "MetafrontierDEA")
    assert info.verification == "cross_implementation"
    assert info.documentation == ("api", "book")


def test_dynamic_sbm_alias_and_adjusted_reporting_specialization() -> None:
    assert deapack.DynamicSBM is deapack.ToneTsutsuiDynamicSBM
    assert method_info("dynamic.sbm.tone_tsutsui_2010").api_symbols == (
        "ToneTsutsuiDynamicSBM",
        "DynamicSBM",
    )
    adjusted = method_info("dynamic.sbm.tone_tsutsui_2010.free_adjusted_post")
    assert adjusted.identifier_role == "specialization_id"
    assert adjusted.api_symbols == (
        "ToneTsutsuiDynamicSBM",
        "DynamicSBM",
    )
    assert adjusted.documentation == ("api",)
    with pytest.raises(KeyError):
        method_info("dynamic.sbm")


def test_dynamic_network_sbm_alias_and_joint_analytical_verification() -> None:
    assert deapack.DynamicNetworkSBM is deapack.ToneTsutsuiDynamicNetworkSBM
    info = method_info("dynamic.network_sbm.tone_tsutsui_2014")
    assert info.api_symbols == (
        "ToneTsutsuiDynamicNetworkSBM",
        "DynamicNetworkSBM",
    )
    assert info.verification == "primary_equations"
    assert info.documentation == ("api",)
    with pytest.raises(KeyError):
        method_info("dynamic.network_sbm.2014")


def test_multiperiod_aggregative_alias_is_one_source_method() -> None:
    assert (
        deapack.MultiperiodAggregativeDEA is deapack.ParkParkMultiperiodAggregativeDEA
    )
    info = method_info("panel.multiperiod_aggregative.park_park_2009")
    assert info.api_symbols == (
        "ParkParkMultiperiodAggregativeDEA",
        "MultiperiodAggregativeDEA",
    )
    assert info.category == "panel"
    assert info.verification == "literature_oracle"
    assert info.documentation == ("api",)
    assert not hasattr(deapack, "MDEA")


@pytest.mark.parametrize(
    "method_id",
    (
        "evaluation.super.directional.ray_2008",
        "evaluation.super.sbm.tone_2002",
        "environmental.material_inflow.coelli2007",
        "environmental.sbm.nonseparable_hybrid.tone_2003",
        "dynamic.network_sbm.tone_tsutsui_2014",
        "static.multiplicative.invariant.charnes_etal_1983",
        "static.multiplicative.original.charnes_etal_1982",
    ),
)
def test_specialized_public_leaves_remain_api_documented_only(
    method_id: str,
) -> None:
    assert method_info(method_id).documentation == ("api",)


def test_method_info_rejects_unknown_or_planned_ids() -> None:
    for method_id in (
        "static.ebm",
        "economic.profit",
        "economic.nerlovian",
        "static.radial.restricted_rts",
        "unknown.method",
    ):
        with pytest.raises(KeyError, match="unknown DEAPack canonical method ID"):
            method_info(method_id)
