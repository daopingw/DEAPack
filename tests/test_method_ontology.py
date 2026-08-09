from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from deapack import list_methods

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ROOT = REPOSITORY_ROOT / "specs" / "registry"
TESTS_ROOT = (REPOSITORY_ROOT / "tests").resolve()
ORACLES_ROOT = (REPOSITORY_ROOT / "specs" / "oracles").resolve()
MANIFEST_PATH = REGISTRY_ROOT / "registry-manifest.json"
HUMAN_REGISTRY_PATH = REPOSITORY_ROOT / "specs" / "METHODS.md"
BOOK_INDEX_PATH = REPOSITORY_ROOT / "book" / "index.md"
SCHEMA_VERSION = "1.0.0"
JSON_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"
REGISTRY_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")

AXES = (
    "context",
    "graph",
    "data_roles",
    "technology",
    "estimator",
    "reference",
    "performance",
    "valuation",
    "evaluation_protocol",
    "analysis",
    "uncertainty",
)

LEVEL_A_OBLIGATIONS = {
    "feasible_set",
    "objective_or_exact_value_transform",
    "target_and_peer_correspondence",
    "parameter_domain",
    "regression_test",
}

DEPENDENCY_RELATIONS = {
    "composes",
    "requires",
    "shares_compiler",
    "exact_reduction",
}

PACKAGE_DEFINED_PUBLIC_DIAGNOSTICS = {
    "analysis.reference_frequency.selected_plan",
}

DEFERRED_METHOD_PROTOCOLS = {
    "analysis.congestion.cooper_deng_huang_li_2002": (
        "cooper_deng_huang_li_2002_congestion.md"
    ),
    "analysis.congestion.fgl_1985": "fare_grosskopf_lovell_congestion.md",
    "evaluation.target_completion.pareto_koopmans.environmental": (
        "charnes_etal_1985_pareto_koopmans_completion.md"
    ),
    "evaluation.target_completion.pareto_koopmans.fch": (
        "charnes_etal_1985_pareto_koopmans_completion.md"
    ),
    "evaluation.target_completion.pareto_koopmans.fdh": (
        "charnes_etal_1985_pareto_koopmans_completion.md"
    ),
    "evaluation.target_completion.pareto_koopmans.frh": (
        "charnes_etal_1985_pareto_koopmans_completion.md"
    ),
    "evaluation.target_completion.pareto_koopmans.nondiscretionary": (
        "charnes_etal_1985_pareto_koopmans_completion.md"
    ),
    "productivity.fare_primont.odonnell_2012": ("odonnell_2012_fare_primont.md"),
    "productivity.environmental_directional.adjacent_geometric": (
        "generic_environmental_directional_productivity.md"
    ),
    "productivity.environmental_directional.global_ratio": (
        "generic_environmental_directional_productivity.md"
    ),
    "productivity.malmquist.decomposition.balk": (
        "fgnz_ray_desli_balk_decompositions.md"
    ),
    "network.input_output.prieto_zofio_2007": "prieto_zofio_2007.md",
    "static.ebm": "tone_tsutsui_2010_ebm.md",
    "static.hyperbolic.standard_reciprocal": "standard_hyperbolic.md",
    "static.radial.nondiscretionary.banker_morey_1986": (
        "banker_morey_1986_nondiscretionary.md"
    ),
    "static.sorm.emrouznejad_anouze_thanassoulis_2010": (
        "emrouznejad_anouze_thanassoulis_2010_sorm.md"
    ),
    "static.subvector_distance": "subvector_distance.md",
    "valuation.weight_restriction.ar1": "assurance_region.md",
    "valuation.weight_restriction.ar2_cross_side": "assurance_region.md",
}

DEFERRED_MACHINE_PROTOCOLS = {
    "analysis.capacity.physical.fare_grosskopf_kokkelenberg_1989": (
        "fare_grosskopf_kokkelenberg_1989_capacity.md"
    ),
    "analysis.mpss.banker_1984": "banker_1984_mpss.md",
    "evaluation.cross.crs": "ordinary_crs_cross_efficiency.md",
    "evaluation.super.ap_radial": "andersen_petersen_1993_super_efficiency.md",
}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    assert isinstance(value, dict), path
    return value


def _manifest() -> dict[str, Any]:
    return _load_json(MANIFEST_PATH)


def _records(kind: str) -> list[tuple[Path, dict[str, Any]]]:
    manifest = _manifest()
    return [
        (REGISTRY_ROOT / relative, _load_json(REGISTRY_ROOT / relative))
        for relative in manifest[kind]
    ]


def _alias_ids(methods: list[tuple[Path, dict[str, Any]]]) -> set[str]:
    aliases: set[str] = set()
    for _, record in methods:
        for historical in record["names"]["historical"]:
            alias_id = historical.get("alias_id")
            if alias_id is not None:
                assert alias_id not in aliases
                aliases.add(alias_id)
    return aliases


def _assert_locator_exists(locator: str) -> None:
    relative = locator.split("::", maxsplit=1)[0]
    assert (REPOSITORY_ROOT / relative).is_file(), locator


def _assert_oracle_derivation_exists(locator: str) -> None:
    """Keep analytical derivations inside the repository oracle directory."""
    path = (REPOSITORY_ROOT / locator).resolve()
    assert path.is_relative_to(ORACLES_ROOT), locator
    assert path.is_file() and path.suffix == ".md", locator


def _assert_pytest_node_exists(locator: str) -> None:
    """Resolve a registry pytest locator without invoking pytest recursively."""
    parts = locator.split("::")
    assert len(parts) in {2, 3}, locator
    path = (REPOSITORY_ROOT / parts[0]).resolve()
    assert path.is_relative_to(TESTS_ROOT), locator
    assert path.is_file() and path.suffix == ".py", locator
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    if len(parts) == 2:
        assert parts[1].startswith("test_"), locator
        assert any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == parts[1]
            for node in tree.body
        ), locator
        return

    matching_classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name.startswith("Test")
        and node.name == parts[1]
    ]
    assert len(matching_classes) == 1, locator
    assert parts[2].startswith("test_"), locator
    assert any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == parts[2]
        for node in matching_classes[0].body
    ), locator


def _assert_pytest_nodes_are_collected(locators: list[str]) -> None:
    """Require every analytical locator to identify a pytest-collected node."""
    relative_paths = sorted(
        {locator.split("::", maxsplit=1)[0] for locator in locators}
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            *relative_paths,
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    collected = {
        line.strip().split("[", maxsplit=1)[0]
        for line in completed.stdout.splitlines()
        if line.strip().startswith("tests/") and "::" in line
    }
    assert set(locators).issubset(collected), {
        "missing": sorted(set(locators) - collected),
        "collected": sorted(collected),
    }


def test_deferred_source_gate_ids_do_not_leak_into_public_registries() -> None:
    """Keep every explicitly deferred source leaf non-executable."""
    source_protocol_root = REPOSITORY_ROOT / "specs" / "source_protocols"
    for protocol in set(DEFERRED_METHOD_PROTOCOLS.values()):
        protocol_path = source_protocol_root / protocol
        assert protocol_path.is_file(), protocol
        assert "deferred_to_next_version" in protocol_path.read_text(encoding="utf-8")

    deferred_ids = set(DEFERRED_METHOD_PROTOCOLS)
    public_ids = {method.method_id for method in list_methods()}
    machine_record_ids = {record["id"] for _, record in _records("methods")}

    assert deferred_ids.isdisjoint(public_ids)
    assert deferred_ids.isdisjoint(machine_record_ids)


def test_deferred_machine_prototypes_do_not_leak_into_the_public_api() -> None:
    """Retain review work without presenting an unclosed source identity."""
    source_protocol_root = REPOSITORY_ROOT / "specs" / "source_protocols"
    machine_records = {record["id"]: record for _, record in _records("methods")}
    public_ids = {method.method_id for method in list_methods()}

    for method_id, protocol in DEFERRED_MACHINE_PROTOCOLS.items():
        protocol_path = source_protocol_root / protocol
        assert protocol_path.is_file(), protocol
        protocol_text = protocol_path.read_text(encoding="utf-8")
        assert "deferred_to_next_version" in protocol_text
        assert method_id in machine_records
        assert machine_records[method_id]["status"]["implementation"] == "prototype"
        assert machine_records[method_id]["status"]["api"] == "none"
        assert method_id not in public_ids


def test_pareto_koopmans_completion_is_one_embedded_protocol() -> None:
    """Freeze one phase-two identity without inventing a duplicate method."""
    protocol_id = "evaluation.target_completion.pareto_koopmans"
    expected_compositions = {
        "static.radial": "evaluated_observation",
        "static.directional_distance": "evaluated_observation",
        "static.generalized_distance.chavas_cox": "fixed_path_target",
    }
    catalog_ids = {method.method_id for method in list_methods()}
    machine_records = {record["id"]: record for _, record in _records("methods")}

    assert protocol_id not in catalog_ids
    assert protocol_id not in machine_records

    actual_compositions = {
        method_id
        for method_id, record in machine_records.items()
        if protocol_id
        in record["composition"]["evaluation_protocol"].get("components", [])
    }
    assert actual_compositions == set(expected_compositions)

    source_id = "doi:10.1016/0304-4076(85)90133-2"
    common_conditions = {
        "condition.pareto_koopmans.ordinary_all_discretionary_domain",
        "condition.pareto_koopmans.positive_row_scale_weights",
    }
    for method_id, scale_anchor in expected_compositions.items():
        record = machine_records[method_id]
        protocol = record["composition"]["evaluation_protocol"]
        assert protocol["fixed"]["target_completion_scale_anchor"] == scale_anchor
        assert common_conditions <= set(protocol["constraints"])
        assert protocol_id in record["implementation"]["registry_dependencies"]
        assert source_id in {source["id"] for source in record["validation"]["sources"]}
        assert (
            "tests/test_target_completion_protocol.py"
            in record["validation"]["tests"]["locators"]
        )

    for method_id in ("static.radial", "static.directional_distance"):
        conditions = set(
            machine_records[method_id]["composition"]["evaluation_protocol"][
                "constraints"
            ]
        )
        assert (
            "condition.pareto_koopmans.evaluated_observation_scale_anchor" in conditions
        )

    gdf_conditions = set(
        machine_records["static.generalized_distance.chavas_cox"]["composition"][
            "evaluation_protocol"
        ]["constraints"]
    )
    assert {
        "condition.pareto_koopmans.fixed_primary_path_target",
        "condition.pareto_koopmans.gdf_finite_nonnegative_fixed_path_target",
        "condition.pareto_koopmans.gdf_fixed_path_target_scale_anchor",
    } <= gdf_conditions

    protocol_path = (
        REPOSITORY_ROOT
        / "specs"
        / "source_protocols"
        / "charnes_etal_1985_pareto_koopmans_completion.md"
    )
    protocol_text = protocol_path.read_text(encoding="utf-8")
    assert "\\(" not in protocol_text
    assert "\\)" not in protocol_text
    assert "Pareto--Koopmans completion principle" in protocol_text
    assert "evaluated-observation weighting policy" in protocol_text
    assert "fixed finite nonnegative path target" in protocol_text
    assert "phase-two composition" in protocol_text
    assert "does not provide independent evidence for the GDF" in protocol_text
    for deferred_id in {
        method_id
        for method_id in DEFERRED_METHOD_PROTOCOLS
        if method_id.startswith(f"{protocol_id}.")
    }:
        assert deferred_id in protocol_text
    assert "deferred_to_next_version" in protocol_text


def test_apz_preset_composes_a_distinct_technology_with_shared_ml_accounting() -> None:
    """Freeze APZ as a composition, not a CFG or Oh naming alias."""
    method_id = "productivity.malmquist_luenberger.aparicio_pastor_zofio_2013"
    cfg_id = "productivity.malmquist_luenberger.chung_fare_grosskopf_1997"
    oh_id = "productivity.global_malmquist_luenberger.oh_2010"
    methods = {record["id"]: record for _, record in _records("methods")}
    relations = {path.name: record for path, record in _records("relations")}

    record = methods[method_id]
    assert record["identifier_role"] == "preset_id"
    assert record["kind"] == "preset"
    assert record["status"] == {
        "priority": "P0",
        "release_tier": 1,
        "implementation": "implemented",
        "api": "public",
        "publication_scope": "documentation_only",
    }

    technology = record["composition"]["technology"]["fixed"]
    assert technology["returns_to_scale"] == "crs"
    assert technology["bad_output_envelopment"] == (
        "B_lambda_le_directional_bad_target_le_reference_period_componentwise_maximum"
    )
    assert technology["bad_output_cap"] == (
        "componentwise_contemporaneous_reference_period_observed_maximum"
    )
    assert technology["cfg_bad_output_equality"] == "not_used"

    reference = record["composition"]["reference"]["fixed"]
    assert reference["distance_tasks_per_pair"] == [
        "base_on_base",
        "comparison_on_base",
        "base_on_comparison",
        "comparison_on_comparison",
    ]
    analysis = record["composition"]["analysis"]["fixed"]
    assert analysis["composition_identity"] == (
        "apz_2017_capped_bad_inequality_technology_plus_standard_four_distance_"
        "malmquist_luenberger_accounting"
    )
    assert analysis["all_distances_recompiled"] is True
    assert analysis["cfg_postprocessing_or_alias"] is False
    assert analysis["oh_global_malmquist_luenberger_alias"] is False

    oracle = record["validation"]["oracle"]
    assert oracle["status"] == "analytically_derived"
    certificate = oracle["analytical_certificate"]
    assert certificate["published_reproduction"] is False
    assert certificate["production_compiler_reused"] is False
    assert certificate["public_api_test_locator"] == (
        "tests/test_apz_malmquist_luenberger.py::"
        "test_apz_table_one_matches_exact_four_distance_certificate_and_diagnostics"
    )
    claims = {claim["claim_id"]: claim for claim in certificate["claims"]}
    assert set(claims) == {
        "productivity.apz.malmquist_luenberger.table_one.exact_account",
        "productivity.apz.malmquist_luenberger.cfg_non_equivalence",
    }
    exact = claims["productivity.apz.malmquist_luenberger.table_one.exact_account"][
        "evaluation_scope"
    ]["cases"][0]["expected"]
    assert exact == {
        "distance_base_on_base": "2/5",
        "distance_comparison_on_base": "3/11",
        "distance_base_on_comparison": "3/5",
        "distance_comparison_on_comparison": "5/11",
        "efficiency_change": "77/80",
        "technical_change": "8/7",
        "productivity_change": "11/10",
        "decomposition_residual": 0.0,
    }

    cfg_relation = relations["productivity-apz-cfg-shared-accounting.json"]
    assert cfg_relation["source"] == method_id
    assert cfg_relation["target"] == cfg_id
    assert cfg_relation["type"] == "shares_compiler"
    assert cfg_relation["equivalence_level"] is None
    assert set(cfg_relation["difference_axes"]) == {
        "context",
        "data_roles",
        "technology",
    }
    assert cfg_relation["conditions"][0]["arguments"]["alias_claim"] == ("forbidden")

    oh_relation = relations["productivity-apz-oh-gml-distinct.json"]
    assert oh_relation["source"] == method_id
    assert oh_relation["target"] == oh_id
    assert oh_relation["type"] == "contrasts_with"
    assert oh_relation["equivalence_level"] == "D"
    assert set(oh_relation["difference_axes"]) == {
        "data_roles",
        "technology",
        "reference",
        "analysis",
    }


def test_fgnz_core_is_a_catalog_preset_over_one_shared_machine_method() -> None:
    """Do not duplicate the Malmquist solver to name its source configuration."""
    preset_id = "productivity.malmquist.decomposition.fgnz_core"
    shared_method_id = "productivity.malmquist.adjacent_geometric"
    catalog = {method.method_id: method for method in list_methods()}
    machine_records = {record["id"]: record for _, record in _records("methods")}

    assert catalog[preset_id].identifier_role == "preset_id"
    assert catalog[preset_id].api_symbols == (
        "FGNZMalmquistProductivityIndex",
        "FGNZMalmquist",
    )
    assert preset_id not in machine_records
    assert shared_method_id in machine_records
    assert (
        machine_records[shared_method_id]["composition"]["analysis"]["fixed"][
            "source_qualified_preset_id"
        ]
        == preset_id
    )


def test_enhanced_fgnz_is_a_distinct_six_task_method_over_the_shared_crs_core() -> None:
    """Freeze the source-qualified FGNZ allocation without aliasing Ray--Desli."""
    method_id = "productivity.malmquist.decomposition.fgnz_pure_scale_extension"
    shared_method_id = "productivity.malmquist.adjacent_geometric"
    ray_desli_id = "productivity.malmquist.decomposition.ray_desli"
    catalog = {method.method_id: method for method in list_methods()}
    machine_records = {record["id"]: record for _, record in _records("methods")}
    relations = {path.name: record for path, record in _records("relations")}

    assert catalog[method_id].identifier_role == "method_id"
    assert catalog[method_id].api_symbols == (
        "FGNZEnhancedMalmquistProductivityIndex",
        "FGNZEnhancedMalmquist",
    )
    record = machine_records[method_id]
    assert record["status"] == {
        "priority": "P0",
        "release_tier": 1,
        "implementation": "implemented",
        "api": "public",
        "publication_scope": "documentation_only",
    }
    assert record["composition"]["performance"]["fixed"]["orientation"] == "output"
    assert (
        record["composition"]["technology"]["fixed"]["headline_returns_to_scale"]
        == "crs"
    )
    assert (
        record["composition"]["technology"]["fixed"]["auxiliary_returns_to_scale"]
        == "vrs"
    )
    assert record["composition"]["analysis"]["fixed"]["parent_operator_id"] == (
        shared_method_id
    )
    assert record["composition"]["reference"]["fixed"]["distance_tasks_per_pair"] == [
        "crs_base_on_base",
        "crs_comparison_on_base",
        "crs_base_on_comparison",
        "crs_comparison_on_comparison",
        "vrs_base_on_base",
        "vrs_comparison_on_comparison",
    ]
    assert all(
        "cross" not in task
        for task in record["composition"]["reference"]["fixed"][
            "distance_tasks_per_pair"
        ][4:]
    )
    assert {
        "pure_efficiency_change",
        "fgnz_scale_change",
        "decomposition_residual",
        "efficiency_decomposition_residual",
        "fgnz_enhanced_decomposition_residual",
        "decomposition_defined",
        "decomposition_status",
    } <= set(record["result_contract"]["components"])

    shared_relation = relations["productivity-fgnz-enhanced-adjacent-malmquist.json"]
    assert shared_relation["source"] == method_id
    assert shared_relation["target"] == shared_method_id
    assert shared_relation["type"] == "shares_compiler"
    assert shared_relation["equivalence_level"] is None
    assert set(shared_relation["difference_axes"]) == {
        "technology",
        "evaluation_protocol",
        "analysis",
    }

    ray_relation = relations["productivity-fgnz-enhanced-ray-desli-distinct.json"]
    assert ray_relation["source"] == method_id
    assert ray_relation["target"] == ray_desli_id
    assert ray_relation["type"] == "contrasts_with"
    assert ray_relation["equivalence_level"] == "D"
    assert set(ray_relation["difference_axes"]) == {
        "data_roles",
        "technology",
        "reference",
        "evaluation_protocol",
        "analysis",
    }
    allocation = ray_relation["conditions"][0]["arguments"]
    assert allocation["fgnz_additional_tasks"] == "two_own_period_vrs_distances"
    assert allocation["ray_desli_additional_tasks"] == (
        "four_own_and_cross_period_vrs_distances"
    )
    assert allocation["component_alias_claim"] == "forbidden"


def test_ray_desli_is_a_distinct_eight_task_method_that_shares_the_crs_headline() -> (
    None
):
    method_id = "productivity.malmquist.decomposition.ray_desli"
    shared_method_id = "productivity.malmquist.adjacent_geometric"
    catalog = {method.method_id: method for method in list_methods()}
    machine_records = {record["id"]: record for _, record in _records("methods")}
    relations = {path.name: record for path, record in _records("relations")}

    assert catalog[method_id].identifier_role == "method_id"
    assert catalog[method_id].api_symbols == (
        "RayDesliMalmquistProductivityIndex",
        "RayDesliMalmquist",
    )
    record = machine_records[method_id]
    assert record["status"] == {
        "priority": "P0",
        "release_tier": 1,
        "implementation": "implemented",
        "api": "public",
        "publication_scope": "documentation_only",
    }
    assert record["composition"]["performance"]["fixed"]["orientation"] == "output"
    assert (
        record["composition"]["technology"]["fixed"]["headline_returns_to_scale"]
        == "crs"
    )
    assert (
        record["composition"]["technology"]["fixed"]["auxiliary_returns_to_scale"]
        == "vrs"
    )
    assert record["composition"]["analysis"]["fixed"]["parent_operator_id"] == (
        shared_method_id
    )
    assert {
        "pure_efficiency_change",
        "vrs_technical_change",
        "ray_desli_scale_change",
        "ray_desli_decomposition_residual",
        "decomposition_defined",
        "decomposition_status",
    } <= set(record["result_contract"]["components"])

    relation = relations["productivity-ray-desli-adjacent-malmquist.json"]
    assert relation["source"] == method_id
    assert relation["target"] == shared_method_id
    assert relation["type"] == "shares_compiler"
    assert relation["equivalence_level"] is None
    assert set(relation["difference_axes"]) == {
        "technology",
        "evaluation_protocol",
        "analysis",
    }


def test_analytically_derived_oracles_have_a_fail_closed_certificate() -> None:
    """Require auditable evidence rather than a free-form oracle label."""
    analytical_records = [
        record
        for _, record in _records("methods")
        if record["validation"]["oracle"]["status"] == "analytically_derived"
    ]
    assert {record["id"] for record in analytical_records} == {
        "analysis.scale_efficiency.radial_ratio",
        "dynamic.network_sbm.tone_tsutsui_2014",
        "environmental.ddf.joint_production",
        "environmental.ddf.output.chung_fare_grosskopf_1997",
        "environmental.ddf.weak_disposal.common_factor",
        "environmental.ddf.weak_disposal.activity_specific",
        "environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp",
        "environmental.material_inflow.coelli2007",
        "environmental.sbm.nonseparable_hybrid.tone_2003",
        "environmental.sbm.separable_strong",
        "productivity.biennial_malmquist",
        "productivity.global_malmquist",
        "productivity.global_malmquist_luenberger.oh_2010",
        "productivity.hicks_moorsteen.bjurek_1996",
        "productivity.luenberger",
        "productivity.malmquist.adjacent_geometric",
        "productivity.malmquist.decomposition.fgnz_pure_scale_extension",
        "productivity.malmquist.decomposition.ray_desli",
        "productivity.malmquist_luenberger.aparicio_pastor_zofio_2013",
        "productivity.malmquist_luenberger.chung_fare_grosskopf_1997",
        "static.additive",
        "static.directional_distance",
        "static.multiplicative",
        "static.radial",
        "static.radial.fdh",
        "static.radial.fch.green_cook_2004",
        "static.radial.frh",
        "static.ram",
        "static.sbm.input.tone2001",
        "static.sbm.output.tone2001",
    }

    for record in analytical_records:
        validation = record["validation"]
        oracle = validation["oracle"]
        certificate = oracle["analytical_certificate"]

        assert validation["evidence_status"] == "primary_checked"
        assert validation["tests"]["status"] == "present"
        assert any(source["role"] == "defining" for source in validation["sources"])
        assert certificate["published_reproduction"] is False
        assert certificate["production_compiler_reused"] is False
        claims = certificate["claims"]
        assert any(
            claim["evidence_kind"] in {"exact_primal_dual", "exact_primal_upper_bound"}
            for claim in claims
        )
        claim_test_locators = [
            locator for claim in claims for locator in claim["test_locators"]
        ]
        claim_ids = [claim["claim_id"] for claim in claims]
        assert len(claim_ids) == len(set(claim_ids))
        assert len(claim_test_locators) == len(set(claim_test_locators))
        assert certificate["public_api_test_locator"] in claim_test_locators

        required_locators = {
            certificate["derivation_locator"],
            certificate["public_api_test_locator"],
            *claim_test_locators,
        }
        assert required_locators.issubset(oracle["locators"])
        _assert_oracle_derivation_exists(certificate["derivation_locator"])
        for locator in claim_test_locators:
            _assert_pytest_node_exists(locator)
        _assert_pytest_nodes_are_collected(claim_test_locators)

        derivation = (REPOSITORY_ROOT / certificate["derivation_locator"]).read_text(
            encoding="utf-8"
        )
        assert record["id"] in derivation
        assert "**Published reproduction:** no" in derivation

    analytical_by_id = {record["id"]: record for record in analytical_records}
    malmquist_record = analytical_by_id["productivity.malmquist.adjacent_geometric"]
    malmquist_analysis = malmquist_record["composition"]["analysis"]["fixed"]
    assert malmquist_analysis["source_qualified_preset_id"] == (
        "productivity.malmquist.decomposition.fgnz_core"
    )
    assert malmquist_analysis["source_qualified_preset_scope"] == (
        "output_orientation_crs_core_efficiency_change_times_technical_change"
    )
    assert malmquist_analysis["source_qualified_decomposition_method_ids"] == [
        "productivity.malmquist.decomposition.fgnz_pure_scale_extension"
    ]
    assert malmquist_analysis["deferred_source_extensions"] == [
        "productivity.malmquist.decomposition.balk"
    ]

    malmquist_certificate = malmquist_record["validation"]["oracle"][
        "analytical_certificate"
    ]
    malmquist_claims = {
        claim["claim_id"]: claim for claim in malmquist_certificate["claims"]
    }
    assert set(malmquist_claims) == {
        "productivity.fgnz.core.exact_four_distance_account",
        "productivity.fgnz.core.exact_task_peer_semantics",
        "productivity.fgnz.core.undefined_distance_failure",
        "productivity.fgnz.core.unit_invariance",
    }
    for claim in malmquist_claims.values():
        assert claim["parameter_scope"] == {
            "orientation": ["output"],
            "returns_to_scale": ["crs"],
            "evaluation_protocol": ["matched_adjacent_period_identifiers"],
            "disposability": ["ordinary_free"],
            "time_aggregation": ["four_distance_geometric_mean"],
        }
        assert claim["reference_scope"] == {
            "requested_kind": "contemporaneous",
            "resolved_kind": "contemporaneous",
            "comparison_population": "full_eligible_sample",
            "self_membership": "allowed",
        }

    exact_malmquist = malmquist_claims[
        "productivity.fgnz.core.exact_four_distance_account"
    ]
    assert exact_malmquist["evidence_kind"] == "exact_primal_upper_bound"
    assert exact_malmquist["evaluation_scope"] == {
        "kind": "named_cases",
        "cases": [
            {
                "case_id": "productivity.fgnz.core.fixture_a",
                "orientation": "output",
                "evaluated_dmu_id": "A",
                "expected": {
                    "distance_base_on_base": "1/2",
                    "distance_comparison_on_base": "9/8",
                    "distance_base_on_comparison": "1/3",
                    "distance_comparison_on_comparison": "3/4",
                    "productivity_change": "9/4",
                    "efficiency_change": "3/2",
                    "technical_change": "3/2",
                    "decomposition_residual": "0",
                },
            },
            {
                "case_id": "productivity.fgnz.core.fixture_b",
                "orientation": "output",
                "evaluated_dmu_id": "B",
                "expected": {
                    "distance_base_on_base": "1",
                    "distance_comparison_on_base": "3/2",
                    "distance_base_on_comparison": "2/3",
                    "distance_comparison_on_comparison": "1",
                    "productivity_change": "3/2",
                    "efficiency_change": "1",
                    "technical_change": "3/2",
                    "decomposition_residual": "0",
                },
            },
        ],
    }
    assert set(exact_malmquist["result_components"]) == {
        "four_farrell_distances",
        "productivity_change",
        "efficiency_change",
        "technical_change",
        "decomposition_residual",
    }
    assert exact_malmquist["data_scope"] == {
        "roles": ["input", "desirable_output"],
        "sign_domain": "strictly_positive",
        "time_structure": "panel",
        "fixture_shape": {
            "observations": 4,
            "inputs": 2,
            "desirable_outputs": 2,
            "undesirable_outputs": 0,
        },
    }

    radial = analytical_by_id["static.radial"]["validation"]["oracle"][
        "analytical_certificate"
    ]
    claims = {claim["claim_id"]: claim for claim in radial["claims"]}
    assert set(claims) == {
        "radial.phase_one.exact_scores",
        "radial.phase_two.crs_exact_slack_semantics",
        "radial.phase_two.exact_slack_semantics",
        "radial.two_phase.independent_dense_compilation",
    }

    phase_one = claims["radial.phase_one.exact_scores"]
    assert phase_one["evidence_kind"] == "exact_primal_upper_bound"
    assert phase_one["test_locators"] == [
        "tests/test_radial_independent_oracle.py::test_exact_radial_rts_oracle",
        "tests/test_radial_independent_oracle.py::"
        "test_named_radial_presets_match_exact_phase_one_oracle",
    ]
    assert set(phase_one["parameter_scope"]["orientation"]) == {"input", "output"}
    assert set(phase_one["parameter_scope"]["returns_to_scale"]) == {
        "crs",
        "vrs",
        "nirs",
        "ndrs",
    }
    assert set(phase_one["parameter_scope"]["evaluation_protocol"]) == {
        "score_only",
        "lexicographic_slack_completion",
    }
    assert phase_one["evaluation_scope"] == {"kind": "all_fixture_observations"}
    assert set(phase_one["result_components"]) == {
        "native_score",
        "harmonized_efficiency",
    }

    phase_two = claims["radial.phase_two.exact_slack_semantics"]
    assert phase_two["evidence_kind"] == "exact_primal_upper_bound"
    assert set(phase_two["parameter_scope"]["orientation"]) == {"input", "output"}
    assert phase_two["parameter_scope"]["returns_to_scale"] == ["vrs"]
    assert phase_two["parameter_scope"]["evaluation_protocol"] == [
        "lexicographic_slack_completion"
    ]
    assert phase_two["evaluation_scope"] == {
        "kind": "named_cases",
        "cases": [
            {
                "case_id": "vrs_input_c",
                "orientation": "input",
                "evaluated_dmu_id": "C",
                "expected": {
                    "native_score": 1.0,
                    "radial_efficiency_status": True,
                    "strong_efficiency_status": False,
                    "output_slack": 0.5,
                    "output_target": 1.0,
                },
            },
            {
                "case_id": "vrs_output_b",
                "orientation": "output",
                "evaluated_dmu_id": "B",
                "expected": {
                    "native_score": 1.0,
                    "radial_efficiency_status": True,
                    "strong_efficiency_status": False,
                    "input_slack": 1.0,
                    "input_target": 1.0,
                },
            },
        ],
    }
    assert set(phase_two["result_components"]) == {
        "native_score",
        "radial_efficiency_status",
        "strong_efficiency_status",
        "slacks",
        "targets",
    }

    crs_phase_two = claims["radial.phase_two.crs_exact_slack_semantics"]
    assert crs_phase_two["evidence_kind"] == "exact_primal_upper_bound"
    assert crs_phase_two["test_locators"] == [
        "tests/test_radial_independent_oracle.py::"
        "test_named_crs_presets_recover_exact_slack_completed_targets"
    ]
    assert set(crs_phase_two["parameter_scope"]["orientation"]) == {
        "input",
        "output",
    }
    assert crs_phase_two["parameter_scope"]["returns_to_scale"] == ["crs"]
    assert crs_phase_two["parameter_scope"]["evaluation_protocol"] == [
        "lexicographic_slack_completion"
    ]
    assert crs_phase_two["evaluation_scope"] == {
        "kind": "named_cases",
        "cases": [
            {
                "case_id": "crs_input_b",
                "orientation": "input",
                "evaluated_dmu_id": "B",
                "expected": {
                    "native_score": 0.5,
                    "peer_a_lambda": 1.0,
                    "input_x1_target": 1.0,
                    "input_x2_target": 1.0,
                    "output_y1_target": 1.0,
                    "output_y2_target": 1.0,
                    "input_x1_slack": 0.0,
                    "input_x2_slack": 0.5,
                    "output_y1_slack": 0.0,
                    "output_y2_slack": 0.5,
                },
            },
            {
                "case_id": "crs_output_b",
                "orientation": "output",
                "evaluated_dmu_id": "B",
                "expected": {
                    "native_score": 2.0,
                    "peer_a_lambda": 2.0,
                    "input_x1_target": 2.0,
                    "input_x2_target": 2.0,
                    "output_y1_target": 2.0,
                    "output_y2_target": 2.0,
                    "input_x1_slack": 0.0,
                    "input_x2_slack": 1.0,
                    "output_y1_slack": 0.0,
                    "output_y2_slack": 1.0,
                },
            },
        ],
    }
    assert set(crs_phase_two["result_components"]) == {
        "native_score",
        "peers",
        "slacks",
        "targets",
    }

    dense = claims["radial.two_phase.independent_dense_compilation"]
    assert dense["evidence_kind"] == "independent_problem_compilation"
    assert set(dense["parameter_scope"]["orientation"]) == {"input", "output"}
    assert set(dense["parameter_scope"]["returns_to_scale"]) == {
        "crs",
        "vrs",
        "nirs",
        "ndrs",
    }
    assert set(dense["parameter_scope"]["evaluation_protocol"]) == {
        "score_only",
        "lexicographic_slack_completion",
    }
    assert dense["evaluation_scope"] == {"kind": "all_fixture_observations"}
    assert set(dense["result_components"]) == {
        "native_score",
        "harmonized_efficiency",
        "radial_efficiency_status",
        "strong_efficiency_status",
        "slacks",
        "targets",
    }

    expected_reference_scope = {
        "requested_kind": "auto",
        "resolved_kind": "global",
        "comparison_population": "full_eligible_sample",
        "self_membership": "allowed",
    }
    expected_data_boundary = {
        "roles": ["input", "desirable_output"],
        "sign_domain": "nonnegative_positive_aggregates",
        "time_structure": "cross_sectional",
    }
    for claim in claims.values():
        assert claim["reference_scope"] == expected_reference_scope
        assert {
            key: value
            for key, value in claim["data_scope"].items()
            if key != "fixture_shape"
        } == expected_data_boundary
        assert claim["data_scope"]["fixture_shape"]["undesirable_outputs"] == 0

    assert phase_one["data_scope"]["fixture_shape"] == {
        "observations": 3,
        "inputs": 1,
        "desirable_outputs": 1,
        "undesirable_outputs": 0,
    }
    assert (
        phase_two["data_scope"]["fixture_shape"]
        == phase_one["data_scope"]["fixture_shape"]
    )
    assert crs_phase_two["data_scope"]["fixture_shape"] == {
        "observations": 2,
        "inputs": 2,
        "desirable_outputs": 2,
        "undesirable_outputs": 0,
    }
    assert dense["data_scope"]["fixture_shape"] == {
        "observations": 6,
        "inputs": 2,
        "desirable_outputs": 2,
        "undesirable_outputs": 0,
    }

    independent_test = (
        REPOSITORY_ROOT / radial["public_api_test_locator"].split("::", maxsplit=1)[0]
    ).read_text(encoding="utf-8")
    forbidden_production_helpers = {
        "radial_phase_one_problem",
        "radial_row_scales",
        "rts_matrices",
        "compile_reference",
        "CompiledReference",
        "._phase_one_problem",
        "._phase_two_problem",
    }
    for helper in forbidden_production_helpers:
        assert helper not in independent_test

    directional = analytical_by_id["static.directional_distance"]["validation"][
        "oracle"
    ]["analytical_certificate"]
    directional_claims = {claim["claim_id"]: claim for claim in directional["claims"]}
    assert set(directional_claims) == {
        "directional.phase_one.exact_scores",
        "directional.phase_two.exact_slack_semantics",
        "directional.two_phase.independent_dense_compilation",
    }

    directional_phase_one = directional_claims["directional.phase_one.exact_scores"]
    assert directional_phase_one["evidence_kind"] == "exact_primal_upper_bound"
    assert set(directional_phase_one["parameter_scope"]["returns_to_scale"]) == {
        "crs",
        "vrs",
        "nirs",
        "ndrs",
    }
    assert directional_phase_one["parameter_scope"]["evaluation_protocol"] == [
        "score_only"
    ]
    assert set(directional_phase_one["parameter_scope"]["direction_policy"]) == {
        "observed_joint",
        "observed_input_only",
        "observed_output_only",
    }
    assert directional_phase_one["parameter_scope"]["negative_distance_policy"] == [
        False
    ]
    assert directional_phase_one["evaluation_scope"] == {
        "kind": "all_fixture_observations"
    }
    assert set(directional_phase_one["result_components"]) == {
        "native_score",
        "directional_distance",
        "compatibility_efficiency",
        "directional_efficiency_status",
    }

    directional_phase_two = directional_claims[
        "directional.phase_two.exact_slack_semantics"
    ]
    assert directional_phase_two["evidence_kind"] == "exact_primal_upper_bound"
    assert set(directional_phase_two["parameter_scope"]["returns_to_scale"]) == {
        "crs",
        "vrs",
        "nirs",
        "ndrs",
    }
    assert directional_phase_two["parameter_scope"]["evaluation_protocol"] == [
        "lexicographic_slack_completion"
    ]
    assert directional_phase_two["parameter_scope"]["direction_policy"] == [
        "observed_joint"
    ]
    assert directional_phase_two["parameter_scope"]["negative_distance_policy"] == [
        False
    ]
    assert directional_phase_two["evaluation_scope"] == {
        "kind": "all_fixture_observations"
    }
    assert set(directional_phase_two["result_components"]) == {
        "strong_efficiency_status",
        "slacks",
        "targets",
    }

    directional_dense = directional_claims[
        "directional.two_phase.independent_dense_compilation"
    ]
    assert directional_dense["evidence_kind"] == "independent_problem_compilation"
    assert set(directional_dense["parameter_scope"]["returns_to_scale"]) == {
        "crs",
        "vrs",
        "nirs",
        "ndrs",
    }
    assert set(directional_dense["parameter_scope"]["evaluation_protocol"]) == {
        "score_only",
        "lexicographic_slack_completion",
    }
    assert set(directional_dense["parameter_scope"]["direction_policy"]) == {
        "observed_joint",
        "observed_input_only",
        "observed_output_only",
        "fixed_two_input_two_output_vector",
    }
    assert directional_dense["parameter_scope"]["negative_distance_policy"] == [False]
    assert directional_dense["evaluation_scope"] == {"kind": "all_fixture_observations"}
    assert set(directional_dense["result_components"]) == {
        "native_score",
        "directional_distance",
        "compatibility_efficiency",
        "directional_efficiency_status",
        "strong_efficiency_status",
        "optimal_row_scaled_slack_sum",
        "max_scaled_slack",
        "targets",
        "intensity_target_reconstruction",
        "returns_to_scale_intensity_restriction",
    }

    expected_directional_reference_scope = {
        "requested_kind": "auto",
        "resolved_kind": "global",
        "comparison_population": "full_eligible_sample",
        "self_membership": "allowed",
    }
    expected_directional_data_boundary = {
        "roles": ["input", "desirable_output"],
        "sign_domain": "strictly_positive",
        "time_structure": "cross_sectional",
    }
    for claim in directional_claims.values():
        assert claim["reference_scope"] == expected_directional_reference_scope
        assert {
            key: value
            for key, value in claim["data_scope"].items()
            if key != "fixture_shape"
        } == expected_directional_data_boundary
        assert claim["data_scope"]["fixture_shape"]["undesirable_outputs"] == 0
        assert "disposability" not in claim["parameter_scope"]
        assert "time_aggregation" not in claim["parameter_scope"]

    assert directional_phase_one["data_scope"]["fixture_shape"] == {
        "observations": 3,
        "inputs": 1,
        "desirable_outputs": 1,
        "undesirable_outputs": 0,
    }
    assert (
        directional_phase_two["data_scope"]["fixture_shape"]
        == directional_phase_one["data_scope"]["fixture_shape"]
    )
    assert directional_dense["data_scope"]["fixture_shape"] == {
        "observations": 6,
        "inputs": 2,
        "desirable_outputs": 2,
        "undesirable_outputs": 0,
    }

    directional_independent_test = (
        REPOSITORY_ROOT
        / directional["public_api_test_locator"].split("::", maxsplit=1)[0]
    ).read_text(encoding="utf-8")
    forbidden_directional_production_helpers = {
        "_resolve_direction",
        "rts_matrices",
        "compile_reference",
        "CompiledReference",
        "._phase_one_problem",
        "._phase_two_problem",
    }
    for helper in forbidden_directional_production_helpers:
        assert helper not in directional_independent_test

    scale = analytical_by_id["analysis.scale_efficiency.radial_ratio"]["validation"][
        "oracle"
    ]["analytical_certificate"]
    scale_claims = {claim["claim_id"]: claim for claim in scale["claims"]}
    assert set(scale_claims) == {
        "scale_efficiency.exact_matched_ratio",
        "scale_efficiency.independent_dense_components",
    }

    scale_exact = scale_claims["scale_efficiency.exact_matched_ratio"]
    assert scale_exact["evidence_kind"] == "exact_primal_upper_bound"
    assert set(scale_exact["parameter_scope"]["orientation"]) == {
        "input",
        "output",
    }
    assert scale_exact["parameter_scope"]["evaluation_protocol"] == [
        "matched_score_only_component_ratio"
    ]
    assert scale_exact["evaluation_scope"] == {"kind": "all_fixture_observations"}
    assert set(scale_exact["result_components"]) == {
        "crs_efficiency",
        "vrs_efficiency",
        "scale_efficiency",
        "ratio_identity",
        "scale_efficiency_status",
        "generic_efficiency_status_missing",
    }

    scale_dense = scale_claims["scale_efficiency.independent_dense_components"]
    assert scale_dense["evidence_kind"] == "independent_problem_compilation"
    assert set(scale_dense["parameter_scope"]["orientation"]) == {
        "input",
        "output",
    }
    assert scale_dense["parameter_scope"]["evaluation_protocol"] == [
        "matched_score_only_component_ratio"
    ]
    assert scale_dense["evaluation_scope"] == {"kind": "all_fixture_observations"}
    assert set(scale_dense["result_components"]) == {
        "crs_efficiency",
        "vrs_efficiency",
        "scale_efficiency",
        "ratio_identity",
        "scale_efficiency_status",
        "generic_efficiency_status_missing",
        "component_diagnostics",
        "execution_accounting",
    }

    expected_scale_reference_scope = {
        "requested_kind": "auto",
        "resolved_kind": "global",
        "comparison_population": "full_eligible_sample",
        "self_membership": "allowed",
    }
    expected_scale_data_boundary = {
        "roles": ["input", "desirable_output"],
        "sign_domain": "strictly_positive",
        "time_structure": "cross_sectional",
    }
    for claim in scale_claims.values():
        assert claim["reference_scope"] == expected_scale_reference_scope
        assert {
            key: value
            for key, value in claim["data_scope"].items()
            if key != "fixture_shape"
        } == expected_scale_data_boundary
        assert claim["data_scope"]["fixture_shape"]["undesirable_outputs"] == 0

    assert scale_exact["data_scope"]["fixture_shape"] == {
        "observations": 3,
        "inputs": 1,
        "desirable_outputs": 1,
        "undesirable_outputs": 0,
    }
    assert scale_dense["data_scope"]["fixture_shape"] == {
        "observations": 6,
        "inputs": 2,
        "desirable_outputs": 2,
        "undesirable_outputs": 0,
    }

    scale_independent_test = (
        REPOSITORY_ROOT / scale["public_api_test_locator"].split("::", maxsplit=1)[0]
    ).read_text(encoding="utf-8")
    forbidden_scale_production_helpers = {
        "RadialDEA",
        "radial_phase_one_problem",
        "radial_row_scales",
        "rts_matrices",
        "compile_reference",
        "CompiledReference",
        "._fit",
        "test_radial_independent_oracle",
    }
    for helper in forbidden_scale_production_helpers:
        assert helper not in scale_independent_test

    oriented_ids = {
        "static.sbm.input.tone2001": {
            "orientation": "input",
            "exact_claim_id": "sbm.input.exact_vrs_account",
            "dense_claim_id": "sbm.input.independent_dense_compilation",
            "exact_components": {
                "native_score",
                "harmonized_efficiency",
                "active_average_normalized_slack",
                "oriented_efficiency_status",
                "generic_efficiency_status_missing",
            },
            "dense_components": {
                "native_score",
                "harmonized_efficiency",
                "active_average_normalized_slack",
                "oriented_efficiency_status",
                "generic_efficiency_status_missing",
                "component_diagnostics",
                "execution_accounting",
                "target_slack_accounting_identity",
            },
        },
        "static.sbm.output.tone2001": {
            "orientation": "output",
            "exact_claim_id": "sbm.output.exact_vrs_account",
            "dense_claim_id": "sbm.output.independent_dense_compilation",
            "exact_components": {
                "native_score",
                "harmonized_efficiency",
                "direct_output_expansion_factor",
                "active_average_normalized_slack",
                "oriented_efficiency_status",
                "generic_efficiency_status_missing",
            },
            "dense_components": {
                "native_score",
                "harmonized_efficiency",
                "direct_output_expansion_factor",
                "active_average_normalized_slack",
                "oriented_efficiency_status",
                "generic_efficiency_status_missing",
                "component_diagnostics",
                "execution_accounting",
                "target_slack_accounting_identity",
            },
        },
    }
    expected_oriented_reference_scope = {
        "requested_kind": "auto",
        "resolved_kind": "global",
        "comparison_population": "full_eligible_sample",
        "self_membership": "allowed",
    }
    expected_oriented_data_boundary = {
        "roles": ["input", "desirable_output"],
        "sign_domain": "strictly_positive",
        "time_structure": "cross_sectional",
    }
    for method_id, expected in oriented_ids.items():
        record = analytical_by_id[method_id]
        sources = record["validation"]["sources"]
        assert sources[0] == {
            "role": "defining",
            "id": "doi:10.1016/S0377-2217(99)00407-5",
        }
        assert sources[1]["role"] == "equivalence"

        oriented = record["validation"]["oracle"]["analytical_certificate"]
        oriented_claims = {claim["claim_id"]: claim for claim in oriented["claims"]}
        assert set(oriented_claims) == {
            expected["exact_claim_id"],
            expected["dense_claim_id"],
        }

        exact = oriented_claims[expected["exact_claim_id"]]
        assert exact["evidence_kind"] == "exact_primal_upper_bound"
        assert exact["parameter_scope"] == {
            "orientation": [expected["orientation"]],
            "returns_to_scale": ["vrs"],
            "evaluation_protocol": ["direct_oriented_primary_lp"],
        }
        assert exact["evaluation_scope"] == {"kind": "all_fixture_observations"}
        assert set(exact["result_components"]) == expected["exact_components"]
        assert exact["data_scope"]["fixture_shape"] == {
            "observations": 3,
            "inputs": 2,
            "desirable_outputs": 2,
            "undesirable_outputs": 0,
        }

        dense = oriented_claims[expected["dense_claim_id"]]
        assert dense["evidence_kind"] == "independent_problem_compilation"
        assert dense["parameter_scope"] == {
            "orientation": [expected["orientation"]],
            "returns_to_scale": ["crs", "vrs"],
            "evaluation_protocol": ["direct_oriented_primary_lp"],
        }
        assert dense["evaluation_scope"] == {"kind": "all_fixture_observations"}
        assert set(dense["result_components"]) == expected["dense_components"]
        assert dense["data_scope"]["fixture_shape"] == {
            "observations": 6,
            "inputs": 2,
            "desirable_outputs": 2,
            "undesirable_outputs": 0,
        }

        for claim in oriented_claims.values():
            assert claim["reference_scope"] == expected_oriented_reference_scope
            assert {
                key: value
                for key, value in claim["data_scope"].items()
                if key != "fixture_shape"
            } == expected_oriented_data_boundary
            assert set(claim["parameter_scope"]["returns_to_scale"]).issubset(
                {"crs", "vrs"}
            )
            assert "nirs" not in claim["parameter_scope"]["returns_to_scale"]
            assert "ndrs" not in claim["parameter_scope"]["returns_to_scale"]

        oriented_independent_test = (
            REPOSITORY_ROOT
            / oriented["public_api_test_locator"].split("::", maxsplit=1)[0]
        ).read_text(encoding="utf-8")
        forbidden_oriented_production_helpers = {
            "SlacksBasedDEA",
            "_transformed_rts_matrices",
            "compile_reference",
            "CompiledReference",
            "._problem",
            "._fit",
        }
        for helper in forbidden_oriented_production_helpers:
            assert helper not in oriented_independent_test


def test_zhou_ang_wang_non_chp_machine_identity_and_non_alias_relation() -> None:
    """Freeze one class, three source accounts, and no radial-DDF alias."""
    method_id = (
        "environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp"
    )
    records = {record["id"]: record for _, record in _records("methods")}
    relations = {path.name: record for path, record in _records("relations")}
    record = records[method_id]

    assert record["identifier_role"] == "method_id"
    assert record["kind"] == "preset"
    assert record["status"] == {
        "priority": "P1",
        "release_tier": 2,
        "implementation": "implemented",
        "api": "public",
    }
    assert record["names"]["api"] == {
        "canonical_symbol": "ZhouAngWangNonCHPEnergyCarbonDEA",
        "aliases": [{"symbol": "NonCHPEnergyCarbonDEA"}],
    }
    assert {
        candidate
        for candidate in records
        if candidate.startswith("environmental.directional_nonradial.energy_carbon.")
    } == {method_id}

    composition = record["composition"]
    data_roles = composition["data_roles"]["fixed"]
    assert data_roles["inputs"].startswith("exactly_one_strictly_positive")
    assert data_roles["outputs"].startswith("exactly_one_strictly_positive")
    assert data_roles["bad_outputs"].startswith("exactly_one_strictly_positive")

    technology = composition["technology"]
    assert technology["fixed"] == {
        "returns_to_scale": "crs",
        "weak_disposal": "common_factor_bad_output_equality",
        "null_jointness": True,
        "envelopment": "F_lambda_le_F_E_lambda_ge_E_C_lambda_eq_C",
        "chp_branch": "excluded_printed_programme_unbounded",
    }
    assert set(technology["components"]) == {
        "environmental.weak_disposal.common_factor.crs.chung_fare_grosskopf_1997",
        "environmental.null_jointness",
    }

    reference = composition["reference"]
    assert reference["fixed"]["kind"] == "global"
    assert reference["fixed"]["time_structure"] == ("one_cross_sectional_vintage")
    assert reference["fixed"]["focal_membership"] == "required"
    assert reference["defaults"]["comparison_population"] == {
        "scope": "all_eligible_non_chp_observations",
        "membership_rule": "all_eligible",
        "self_membership": "required",
    }
    assert "exposed" not in reference

    performance = composition["performance"]
    assert performance["components"] == ["environmental.directional_nonradial"]
    assert performance["fixed"]["account_selector"] == ("explicit_required_keyword")
    assert performance["fixed"]["allowed_source_presets"] == [
        "energy",
        "carbon",
        "integrated_energy_carbon",
    ]
    assert performance["exposed"] == ["account"]
    assert "defaults" not in performance
    assert performance["fixed"]["arbitrary_direction"] == "forbidden"
    assert performance["fixed"]["distance_direction"] == (
        "higher_is_more_unrealized_opportunity"
    )
    assert performance["fixed"]["ranking_order"] == (
        "lower_is_better_current_performance"
    )

    valuation = composition["valuation"]["fixed"]
    assert valuation["user_supplied_weights"] == "forbidden"
    assert valuation["economic_role"] == (
        "normalization_not_price_damage_or_preference"
    )

    evidence_boundary = composition["analysis"]["fixed"]["source_evidence_boundary"]
    assert evidence_boundary["certified"] == (
        "three_non_chp_accounts_one_positive_F_E_C_crs_global_self_inclusive_"
        "cross_section"
    )
    assert {
        "chp_branch_pending_first_hand_equation_correction",
        "published_126_country_application_reproduction",
        "arbitrary_directions_and_weights",
        "vrs_nirs_ndrs",
        "unique_component_target_and_peer_claims",
    } <= set(evidence_boundary["deferred_to_next_version"])

    scores = {score["id"]: score for score in record["result_contract"]["scores"]}
    assert scores["directional_nonradial_distance"]["direction"] == ("lower_is_better")
    assert scores["directional_nonradial_distance"]["efficient_value"] == 0.0
    assert scores["performance_index"]["direction"] == "higher_is_better"
    assert scores["performance_index"]["efficient_value"] == 1.0
    assert record["placement"]["book"] == []
    assert {
        "beta_fossil",
        "beta_electricity",
        "beta_carbon",
        "performance_index_name",
        "performance_index_identified",
        "component_plan_unique",
        "target_unique",
        "peer_plan_unique",
    } <= set(record["result_contract"]["components"])
    transformations = set(record["result_contract"]["transformations"])
    assert {
        (
            "energy_performance_index_equals_one_minus_beta_fossil_over_one_"
            "plus_beta_electricity"
        ),
        (
            "carbon_performance_index_equals_one_minus_beta_carbon_over_one_plus_"
            "beta_electricity"
        ),
        (
            "integrated_performance_index_equals_one_minus_half_the_sum_of_"
            "beta_fossil_and_beta_carbon_over_one_plus_beta_electricity"
        ),
        (
            "component_specific_transformations_are_not_aliases_of_one_over_"
            "one_plus_a_radial_beta"
        ),
        (
            "larger_distance_means_more_unrealized_opportunity_not_better_"
            "current_performance"
        ),
    } <= transformations

    oracle = record["validation"]["oracle"]
    certificate = oracle["analytical_certificate"]
    assert oracle["status"] == "analytically_derived"
    assert certificate["published_reproduction"] is False
    assert certificate["production_compiler_reused"] is False
    assert certificate["derivation_locator"] == (
        "specs/oracles/zhou_ang_wang_2012_non_chp_energy_carbon.md"
    )
    assert certificate["public_api_test_locator"] == (
        "tests/test_zhou_ang_wang_non_chp_source_oracle.py::"
        "test_public_non_chp_accounts_match_exact_analytical_oracle"
    )
    claims = {claim["claim_id"]: claim for claim in certificate["claims"]}
    assert set(claims) == {
        "environmental.zhou_ang_wang_2012_non_chp.exact_three_account_fixture",
        "environmental.zhou_ang_wang_2012_non_chp.independent_dense_programmes",
        "environmental.zhou_ang_wang_2012_non_chp.unit_invariance",
    }
    exact = claims[
        "environmental.zhou_ang_wang_2012_non_chp.exact_three_account_fixture"
    ]
    assert exact["evidence_kind"] == "exact_primal_upper_bound"
    assert [case["case_id"] for case in exact["evaluation_scope"]["cases"]] == [
        "environmental.zhou_ang_wang_2012_non_chp.energy_o",
        "environmental.zhou_ang_wang_2012_non_chp.carbon_o",
        "environmental.zhou_ang_wang_2012_non_chp.integrated_o",
    ]
    assert [
        case["expected"]["performance_index"]
        for case in exact["evaluation_scope"]["cases"]
    ] == ["5/8", "1/4", "3/8"]
    assert (
        claims["environmental.zhou_ang_wang_2012_non_chp.independent_dense_programmes"][
            "evidence_kind"
        ]
        == "independent_problem_compilation"
    )
    assert (
        claims["environmental.zhou_ang_wang_2012_non_chp.unit_invariance"][
            "evidence_kind"
        ]
        == "independent_problem_compilation"
    )

    expected_parameters = {
        "orientation": ["nonoriented"],
        "returns_to_scale": ["crs"],
        "evaluation_protocol": ["explicit_required_three_account_source_selector"],
        "disposability": ["common_factor_weak_bad_output_equality_with_null_jointness"],
        "direction_policy": ["observed_value_component_specific_source_presets"],
        "negative_distance_policy": [False],
        "valuation_policy": ["fixed_source_block_normalization_weights_not_prices"],
    }
    expected_reference = {
        "requested_kind": "global",
        "resolved_kind": "global",
        "comparison_population": "full_eligible_sample",
        "self_membership": "allowed",
    }
    for claim in claims.values():
        assert claim["parameter_scope"] == expected_parameters
        assert claim["reference_scope"] == expected_reference
        assert claim["data_scope"] == {
            "roles": ["input", "desirable_output", "undesirable_output"],
            "sign_domain": "strictly_positive",
            "time_structure": "cross_sectional",
            "fixture_shape": {
                "observations": 3,
                "inputs": 1,
                "desirable_outputs": 1,
                "undesirable_outputs": 1,
            },
        }

    relation = relations["environmental-zaw-nonchp-common-factor.json"]
    assert relation["source"] == method_id
    assert relation["target"] == "environmental.ddf.weak_disposal.common_factor"
    assert relation["type"] == "contrasts_with"
    assert relation["equivalence_level"] == "D"
    assert set(relation["difference_axes"]) == {
        "performance",
        "valuation",
        "evaluation_protocol",
    }
    arguments = relation["conditions"][0]["arguments"]
    assert arguments["shared_technology"] == (
        "crs_common_factor_bad_output_equality_with_null_jointness"
    )
    assert arguments["matched_numerical_value"] == (
        "does_not_create_a_method_or_target_alias"
    )
    assert arguments["alias_claim"] == "forbidden"


def test_coelli_material_inflow_certificate_freezes_source_native_boundary() -> None:
    """Bind the physical Coelli account without promoting adjacent claims."""
    records = {record["id"]: record for _, record in _records("methods")}
    record = records["environmental.material_inflow.coelli2007"]

    data_roles = record["composition"]["data_roles"]
    assert data_roles["fixed"]["bad_outputs"] == (
        "excluded_from_the_source_native_account"
    )
    assert data_roles["fixed"]["explicit_abatement"] == (
        "excluded_from_the_source_native_account"
    )
    assert data_roles["fixed"]["material_coefficients"] == (
        "common_declared_nonnegative_physical_content"
    )
    assert data_roles["fixed"]["certified_material_scope"] == "one_material_account"
    assert data_roles["fixed"]["source_multiple_pollutant_extension"] == (
        "equations_18_21_independent_validation_deferred"
    )
    assert set(
        record["composition"]["technology"]["fixed"]["supported_returns_to_scale"]
    ) == {
        "crs",
        "vrs",
    }
    assert (
        record["composition"]["performance"]["fixed"]["output_commitment"] == "observed"
    )

    valuation = record["composition"]["valuation"]["fixed"]
    assert valuation["coefficient_role"] == "physical_material_content"
    assert valuation["price_data_required"] is False
    assert valuation["damage_weights_required"] is False
    assert valuation["certified_aggregation"] == "single_material"

    evidence_boundary = record["composition"]["analysis"]["fixed"][
        "source_evidence_boundary"
    ]
    assert evidence_boundary["certified"] == (
        "single_material_self_inclusive_cross_section_crs_vrs"
    )
    assert set(evidence_boundary["deferred_to_next_version"]) == {
        "nirs_ndrs",
        "weighted_multiple_pollutant_aggregate_independent_validation",
        "heterogeneous_material_coefficients",
        "estimated_material_coefficients",
        "panel_reference_source_equivalence",
        "custom_reference_source_equivalence",
        "external_reference_source_equivalence",
        "unit_level_183_farm_reproduction",
        "welfare_claims",
        "causal_claims",
        "damage_claims",
        "actual_emission_claims",
    }

    source_ids = {source["id"] for source in record["validation"]["sources"]}
    assert {
        "doi:10.1007/s11123-007-0052-8",
        "https://economics.uq.edu.au/files/5310/WP062005.pdf",
    } <= source_ids

    oracle = record["validation"]["oracle"]
    certificate = oracle["analytical_certificate"]
    assert oracle["status"] == "analytically_derived"
    assert certificate["published_reproduction"] is False
    assert certificate["production_compiler_reused"] is False
    assert certificate["derivation_locator"] == (
        "specs/oracles/coelli-material-inflow-analytical.md"
    )
    assert certificate["public_api_test_locator"] == (
        "tests/test_material_balance_independent_oracle.py::"
        "test_public_scores_match_independently_compiled_source_programmes"
    )

    claims = {claim["claim_id"]: claim for claim in certificate["claims"]}
    assert set(claims) == {
        "environmental.material_inflow.coelli2007.crs_exact_account",
        "environmental.material_inflow.coelli2007.vrs_exact_account",
        "environmental.material_inflow.coelli2007.unit_invariance",
        "environmental.material_inflow.coelli2007.target_nonuniqueness",
    }
    crs = claims["environmental.material_inflow.coelli2007.crs_exact_account"]
    vrs = claims["environmental.material_inflow.coelli2007.vrs_exact_account"]
    invariance = claims["environmental.material_inflow.coelli2007.unit_invariance"]
    nonunique = claims["environmental.material_inflow.coelli2007.target_nonuniqueness"]
    assert crs["evidence_kind"] == "exact_primal_upper_bound"
    assert crs["parameter_scope"]["returns_to_scale"] == ["crs"]
    assert crs["test_locators"] == [
        "tests/test_material_balance_independent_oracle.py::"
        "test_public_scores_match_independently_compiled_source_programmes",
        "tests/test_material_balance_independent_oracle.py::"
        "test_crs_exact_account_targets_peers_and_surplus",
    ]
    assert vrs["evidence_kind"] == "exact_primal_upper_bound"
    assert vrs["parameter_scope"]["returns_to_scale"] == ["vrs"]
    assert vrs["test_locators"] == [
        "tests/test_material_balance_independent_oracle.py::"
        "test_vrs_book_case_has_two_economically_distinct_improvement_accounts"
    ]
    assert invariance["evidence_kind"] == "independent_problem_compilation"
    assert invariance["parameter_scope"]["returns_to_scale"] == ["crs"]
    assert nonunique["parameter_scope"]["returns_to_scale"] == ["crs", "vrs"]

    expected_reference_scope = {
        "requested_kind": "auto",
        "resolved_kind": "global",
        "comparison_population": "full_eligible_sample",
        "self_membership": "allowed",
    }
    expected_data_boundary = {
        "roles": ["input", "desirable_output"],
        "sign_domain": "nonnegative_positive_aggregates",
        "time_structure": "cross_sectional",
    }
    for claim in claims.values():
        assert claim["reference_scope"] == expected_reference_scope
        assert {
            key: value
            for key, value in claim["data_scope"].items()
            if key != "fixture_shape"
        } == expected_data_boundary
        assert claim["data_scope"]["fixture_shape"]["undesirable_outputs"] == 0
        assert "nirs" not in claim["parameter_scope"]["returns_to_scale"]
        assert "ndrs" not in claim["parameter_scope"]["returns_to_scale"]

    exact_components = {
        "technical_efficiency",
        "environmental_efficiency",
        "environmental_allocative_efficiency",
        "decomposition_identity",
        "observed_material_inflow",
        "minimum_material_inflow",
        "observed_material_surplus",
        "minimum_material_surplus",
        "technical_target",
        "material_minimum_target",
    }
    assert exact_components <= set(crs["result_components"])
    assert exact_components <= set(vrs["result_components"])

    claim_test_locators = [
        locator for claim in claims.values() for locator in claim["test_locators"]
    ]
    assert len(claim_test_locators) == len(set(claim_test_locators))
    for locator in claim_test_locators:
        _assert_pytest_node_exists(locator)
    _assert_pytest_nodes_are_collected(claim_test_locators)

    independent_test = (
        REPOSITORY_ROOT
        / certificate["public_api_test_locator"].split("::", maxsplit=1)[0]
    ).read_text(encoding="utf-8")
    for forbidden_helper in {
        "compile_reference",
        "CompiledReference",
        "rts_matrices",
        "LinearProgram",
        "._problem",
        "._fit",
    }:
        assert forbidden_helper not in independent_test

    derivation = (REPOSITORY_ROOT / certificate["derivation_locator"]).read_text(
        encoding="utf-8"
    )
    assert "**Published reproduction:** no" in derivation
    assert "**Production compiler reused:** no" in derivation
    assert "unit-level observations are not supplied" in " ".join(derivation.split())
    assert "target uniqueness" in derivation
    assert "source equations\n  (18)--(21) describe that extension" in derivation
    assert "`deferred_to_next_version`" in derivation

    source_protocol = (
        REPOSITORY_ROOT
        / "specs"
        / "source_protocols"
        / "coelli_lauwers_van_huylenbroeck_2007_material_inflow.md"
    ).read_text(encoding="utf-8")
    assert "\\(" not in source_protocol
    assert "\\)" not in source_protocol
    assert "unit-level 183-farm observations are not supplied" in source_protocol
    assert "Equations (18)--(21)" in source_protocol
    assert "`deferred_to_next_version`" in source_protocol


def test_oh_gml_certificate_freezes_source_pairwise_global_account() -> None:
    """Keep Oh's source account distinct from package enumeration and ML."""
    records = {record["id"]: record for _, record in _records("methods")}
    record = records["productivity.global_malmquist_luenberger.oh_2010"]
    composition = record["composition"]

    context = composition["context"]["fixed"]
    assert context["source_time_comparison"] == (
        "any_period_pair_within_one_fixed_global_sample"
    )
    assert context["package_transition_enumeration"] == (
        "matched_selected_forward_period_pair_identifiers_with_adjacent_default"
    )
    assert (
        "condition.adjacent_dmu_identifier_match"
        not in (composition["data_roles"]["constraints"])
    )

    technology = composition["technology"]["fixed"]
    assert technology["returns_to_scale"] == "crs"
    assert technology["bad_output_disposability"] == "weak_common_factor"
    assert technology["null_jointness"] is True
    assert technology["global_reference_construction"] == (
        "pooled_crs_conical_envelope"
    )
    assert technology["literal_union_equivalence"] == "not_claimed"

    reference = composition["reference"]
    assert reference["fixed"]["global_construction"] == (
        "all_sample_observations_pooled_in_one_crs_conical_envelope"
    )
    assert reference["fixed"]["literal_union"] == (
        "excluded_from_the_certified_computational_contract"
    )
    assert reference["defaults"]["comparison_population"] == {
        "scope": "all_declared_panel_observations_for_global_scores",
        "membership_rule": (
            "full_sample_pooled_crs_conical_envelope_with_period_specific_"
            "subsets_for_decomposition"
        ),
        "self_membership": "allowed",
    }
    assert (
        reference["defaults"]["temporal_information_set"]["historical_revision"]
        == "recompute_all_global_distances_when_periods_or_observations_change"
    )

    performance = composition["performance"]["fixed"]
    assert performance["self_contained_distance_domain"] == (
        "all_own_period_and_global_distances_nonnegative"
    )
    assert performance["off_diagonal_cross_period_distances"] == (
        "not_part_of_the_oh_gml_task_graph"
    )

    evaluation = composition["evaluation_protocol"]
    assert evaluation["fixed"]["kind"] == (
        "package_matched_selected_forward_period_pair_enumeration"
    )
    assert evaluation["fixed"]["source_pairwise_theory"] == (
        "any_period_pair_within_the_same_fixed_global_vintage"
    )
    assert evaluation["defaults"] == {
        "unbalanced": "drop",
        "comparison_pairs": "adjacent",
    }
    assert evaluation["exposed"] == ["unbalanced", "comparison_pairs"]
    assert evaluation["fixed"]["comparison_pair_contract"] == {
        "adjacent": "default_consecutive_pairs_in_declared_period_order",
        "all": ("opt_in_all_forward_i_less_than_j_pairs_in_declared_period_order"),
        "custom": (
            "ordered_nonempty_sequence_of_unique_forward_base_and_comparison_"
            "period_pairs"
        ),
    }
    assert evaluation["fixed"]["output_size"] == {
        "adjacent": "O(D_times_P)",
        "all": "O(D_times_P_squared)",
        "custom": "O(D_times_K_selected_pairs)",
    }
    assert "constraints" not in evaluation

    analysis = composition["analysis"]["fixed"]
    assert analysis["decomposition"] == (
        "productivity_change_equals_efficiency_change_times_best_practice_change"
    )
    assert analysis["best_practice_gap"] == (
        "own_period_directional_distance_factor_over_global_directional_"
        "distance_factor_at_the_same_observation"
    )
    assert analysis["best_practice_change"] == (
        "comparison_best_practice_gap_over_base_best_practice_gap"
    )
    assert analysis["historical_revision"] == (
        "recompute_global_distances_when_periods_or_observations_change"
    )
    evidence_boundary = analysis["source_evidence_boundary"]
    assert evidence_boundary["certified"] == (
        "crs_observation_scaled_common_factor_weak_disposal_fixed_global_vintage"
    )
    assert set(evidence_boundary["deferred_to_next_version"]) == {
        "published_26_country_1990_2003_application_replay",
        "literal_union_global_estimator",
        "vrs_nirs_ndrs_and_scale_decompositions",
        "alternative_directions",
        "alternative_bad_output_technologies",
        "sequential_biennial_rolling_and_prospective_references",
        "signed_interval_stochastic_and_missing_data",
        "inference_shadow_price_welfare_abatement_cost_and_causal_claims",
    }

    transformations = set(record["result_contract"]["transformations"])
    assert {
        (
            "base_best_practice_gap_equals_base_own_period_distance_factor_over_"
            "base_global_distance_factor"
        ),
        (
            "comparison_best_practice_gap_equals_comparison_own_period_distance_"
            "factor_over_comparison_global_distance_factor"
        ),
        (
            "best_practice_change_equals_comparison_best_practice_gap_over_"
            "base_best_practice_gap"
        ),
        "productivity_change_equals_efficiency_change_times_best_practice_change",
    } <= transformations

    oracle = record["validation"]["oracle"]
    certificate = oracle["analytical_certificate"]
    assert oracle["status"] == "analytically_derived"
    assert certificate["published_reproduction"] is False
    assert certificate["production_compiler_reused"] is False
    assert certificate["derivation_locator"] == (
        "specs/oracles/oh-2010-global-malmquist-luenberger-analytical.md"
    )
    assert certificate["public_api_test_locator"] == (
        "tests/test_oh_global_malmquist_luenberger_independent_oracle.py::"
        "test_exact_two_period_oh_gml_matches_independent_dense_source_lp"
    )

    claims = {claim["claim_id"]: claim for claim in certificate["claims"]}
    assert set(claims) == {
        "productivity.oh_gml.exact_two_period_account",
        "productivity.oh_gml.fixed_vintage_circularity",
        "productivity.oh_gml.unit_invariance",
    }
    exact = claims["productivity.oh_gml.exact_two_period_account"]
    circularity = claims["productivity.oh_gml.fixed_vintage_circularity"]
    invariance = claims["productivity.oh_gml.unit_invariance"]
    assert exact["evidence_kind"] == "exact_primal_upper_bound"
    assert exact["test_locators"] == [
        "tests/test_oh_global_malmquist_luenberger_independent_oracle.py::"
        "test_exact_two_period_oh_gml_matches_independent_dense_source_lp"
    ]
    assert circularity["evidence_kind"] == "exact_primal_upper_bound"
    assert circularity["test_locators"] == [
        "tests/test_oh_global_malmquist_luenberger_independent_oracle.py::"
        "test_exact_three_period_oh_gml_is_circular_within_one_global_vintage",
        "tests/test_m13_global_comparison_pairs.py::"
        "test_oh_all_pairs_adds_exact_endpoint_without_more_solves",
    ]
    assert invariance["evidence_kind"] == "independent_problem_compilation"
    assert invariance["test_locators"] == [
        "tests/test_oh_global_malmquist_luenberger_independent_oracle.py::"
        "test_oh_gml_oracle_is_invariant_to_coherent_quantity_unit_changes"
    ]

    adjacent_parameter_scope = {
        "returns_to_scale": ["crs"],
        "evaluation_protocol": ["package_matched_adjacent_transition_enumeration"],
        "disposability": ["weak_common_factor_with_null_jointness"],
        "direction_policy": ["zero_input_observed_desirable_and_bad_output"],
        "negative_distance_policy": ["nonnegative_self_contained_reference_tasks"],
        "time_aggregation": ["one_fixed_global_sample_ratio"],
    }
    pairwise_parameter_scope = {
        **adjacent_parameter_scope,
        "evaluation_protocol": [
            "adjacent_default_all_forward_and_explicit_forward_pair_enumeration"
        ],
    }
    expected_reference_scope = {
        "requested_kind": "global",
        "resolved_kind": "global",
        "comparison_population": "full_eligible_sample",
        "self_membership": "allowed",
    }
    expected_data_boundary = {
        "roles": ["input", "desirable_output", "undesirable_output"],
        "sign_domain": "strictly_positive",
        "time_structure": "panel",
    }
    for claim in claims.values():
        expected_scope = (
            pairwise_parameter_scope
            if claim is circularity
            else adjacent_parameter_scope
        )
        assert claim["parameter_scope"] == expected_scope
        assert claim["reference_scope"] == expected_reference_scope
        assert {
            key: value
            for key, value in claim["data_scope"].items()
            if key != "fixture_shape"
        } == expected_data_boundary
        assert claim["data_scope"]["fixture_shape"]["undesirable_outputs"] == 1

    assert exact["data_scope"]["fixture_shape"]["observations"] == 2
    assert circularity["data_scope"]["fixture_shape"]["observations"] == 3
    assert invariance["data_scope"]["fixture_shape"]["observations"] == 2
    assert {
        "four_own_and_global_directional_distances",
        "nonnegative_distance_domain",
        "pooled_crs_conical_global_envelope",
        "global_malmquist_luenberger_productivity_change",
        "efficiency_change",
        "best_practice_change",
        "base_best_practice_gap",
        "comparison_best_practice_gap",
        "decomposition_identity",
        "no_off_diagonal_cross_period_tasks",
    } <= set(exact["result_components"])
    assert {
        "fixed_vintage_circularity",
        "global_sample_vintage",
        "decomposition_identity",
    } <= set(circularity["result_components"])
    assert "unit_invariance" in invariance["result_components"]

    claim_test_locators = [
        locator for claim in claims.values() for locator in claim["test_locators"]
    ]
    assert len(claim_test_locators) == len(set(claim_test_locators))
    for locator in claim_test_locators:
        _assert_pytest_node_exists(locator)
    _assert_pytest_nodes_are_collected(claim_test_locators)

    independent_test = (
        REPOSITORY_ROOT
        / certificate["public_api_test_locator"].split("::", maxsplit=1)[0]
    ).read_text(encoding="utf-8")
    for forbidden_helper in {
        "compile_reference",
        "CompiledReference",
        "._phase_one_problem",
        "._fit",
    }:
        assert forbidden_helper not in independent_test

    derivation = (REPOSITORY_ROOT / certificate["derivation_locator"]).read_text(
        encoding="utf-8"
    )
    assert "**Published reproduction:** no" in derivation
    assert "**Production compiler reused:** false" in derivation
    assert "not a reproduction of the paper's 26-country application" in derivation
    assert "BPG^t" in derivation
    assert "\\frac58" in derivation.replace(" ", "")
    assert "`deferred_to_next_version`" in derivation

    source_protocol = (
        REPOSITORY_ROOT
        / "specs"
        / "source_protocols"
        / "oh_2010_global_malmquist_luenberger.md"
    ).read_text(encoding="utf-8")
    assert "\\(" not in source_protocol
    assert "\\)" not in source_protocol
    assert "pooled CRS\nconical envelope" in source_protocol
    assert "literal set union and a convex or conical envelope are not" in (
        source_protocol
    )
    assert "Adjacency is not a theoretical restriction" in source_protocol
    compact_source_protocol = "".join(source_protocol.split())
    assert "BPG^r=" in compact_source_protocol
    assert "=\\frac{F_r^r}{F_r^G}." in compact_source_protocol
    assert "no\nclaim to reproduce the published application" in source_protocol
    assert "`deferred_to_next_version`" in source_protocol


def test_mixed_oracle_records_keep_analytical_certificates_claim_scoped() -> None:
    """Do not let a reproduced base silently certify an analytical extension."""
    mixed_records = [
        record
        for _, record in _records("methods")
        if record["validation"]["oracle"]["status"] != "analytically_derived"
        and "analytical_certificate" in record["validation"]["oracle"]
    ]
    assert {record["id"] for record in mixed_records} == {
        "network.sbm.tone_tsutsui_2009"
    }

    record = mixed_records[0]
    oracle = record["validation"]["oracle"]
    certificate = oracle["analytical_certificate"]
    assert oracle["status"] == "reproduced"
    assert certificate["published_reproduction"] is False
    assert certificate["production_compiler_reused"] is False
    assert certificate["derivation_locator"] in oracle["locators"]

    claims = {claim["claim_id"]: claim for claim in certificate["claims"]}
    assert set(claims) == {
        "network_sbm.eq26.accountable_input_exact_optimum",
        "network_sbm.eq27.accountable_output_exact_optimum",
    }
    expected_cases = {
        "network_sbm.eq26.accountable_input_exact_optimum": {
            "case_id": "equation_26_input_a",
            "orientation": "input",
            "evaluated_dmu_id": "A",
            "expected": {
                "system_efficiency": "5/8",
                "supplier_efficiency": "1/2",
                "recipient_efficiency": "3/4",
                "link_slack": 1.0,
                "link_target": 1.0,
            },
        },
        "network_sbm.eq27.accountable_output_exact_optimum": {
            "case_id": "equation_27_output_a",
            "orientation": "output",
            "evaluated_dmu_id": "A",
            "expected": {
                "system_efficiency": "4/7",
                "supplier_efficiency": "2/3",
                "recipient_efficiency": "1/2",
                "link_slack": 1.0,
                "link_target": 2.0,
            },
        },
    }
    for claim_id, claim in claims.items():
        assert claim["evidence_kind"] == "exact_primal_upper_bound"
        assert claim["evaluation_scope"] == {
            "kind": "named_cases",
            "cases": [expected_cases[claim_id]],
        }
        assert certificate["public_api_test_locator"] in claim["test_locators"]
        assert claim["reference_scope"] == {
            "requested_kind": "auto",
            "resolved_kind": "global",
            "comparison_population": "full_eligible_sample",
            "self_membership": "allowed",
        }
        assert claim["data_scope"] == {
            "roles": ["input", "desirable_output", "intermediate"],
            "sign_domain": "strictly_positive",
            "time_structure": "cross_sectional",
            "fixture_shape": {
                "observations": 2,
                "inputs": 2,
                "desirable_outputs": 2,
                "undesirable_outputs": 0,
            },
        }
        for locator in claim["test_locators"]:
            _assert_pytest_node_exists(locator)
    _assert_pytest_nodes_are_collected(
        sorted(
            {locator for claim in claims.values() for locator in claim["test_locators"]}
        )
    )

    derivation = (REPOSITORY_ROOT / certificate["derivation_locator"]).read_text(
        encoding="utf-8"
    )
    assert record["id"] in derivation
    assert "**Published reproduction:** no" in derivation
    assert "**Production compiler reused:** no" in derivation
    normalized_derivation = " ".join(derivation.split())
    assert "not merely the value of one feasible plan" in normalized_derivation
    assert "attains the upper bound" in normalized_derivation


def test_oracle_schema_allows_certificates_only_for_qualified_statuses() -> None:
    """Allow mixed evidence, but reject certificates on unresolved evidence."""
    schema = _load_json(REGISTRY_ROOT / "schema" / "method-record-v1.schema.json")
    validator = Draft202012Validator(schema)
    record = next(
        record
        for _, record in _records("methods")
        if record["id"] == "network.sbm.tone_tsutsui_2009"
    )

    for status in ("reproduced", "cross_implemented", "analytically_derived"):
        qualified = deepcopy(record)
        qualified["validation"]["oracle"]["status"] = status
        assert validator.is_valid(qualified), status

    for status in ("candidate", "not_located"):
        unresolved = deepcopy(record)
        unresolved["validation"]["oracle"]["status"] = status
        assert not validator.is_valid(unresolved), status

    missing_certificate = deepcopy(record)
    missing_certificate["validation"]["oracle"]["status"] = "analytically_derived"
    del missing_certificate["validation"]["oracle"]["analytical_certificate"]
    assert not validator.is_valid(missing_certificate)


def test_classic_sbm_records_publish_certified_fail_closed_postsolve_contract() -> None:
    methods = {record["id"]: record for _, record in _records("methods")}
    classic_sbm_ids = (
        "static.sbm.input.tone2001",
        "static.sbm.output.tone2001",
        "static.sbm.nonoriented.tone2001",
        "environmental.sbm.separable_strong",
    )
    required_components = {
        "score_valid",
        "score_status",
        "solver_neutral_lp_optimality_certificate",
        "sbm_account_reconstruction_certificate",
        "atomic_fail_closed_result_release",
    }
    required_conditions = {
        "condition.optimal_primary_solve",
        "condition.successful_primal_dual_certificate",
        "condition.successful_sbm_account_reconstruction_certificate",
    }
    required_coverage = {
        "shared_solver_neutral_primal_dual_bound_kkt_certificate",
        "missing_or_malformed_row_and_bound_marginal_rejection",
        "forged_optimal_claim_fail_closed_release",
        "raw_solver_status_preserved_on_certificate_failure",
        "sbm_account_reconstruction_certificate",
        "semantic_subtables_withheld_for_uncertified_solution",
        "single_bad_dmu_failure_isolation",
    }
    required_locators = {
        "tests/test_sbm_postsolve_certification.py",
        "tests/test_sbm_postsolve_certification.py::"
        "test_uncertified_optimal_solution_withholds_every_semantic_table",
        "tests/test_sbm_postsolve_certification.py::"
        "test_economic_account_corruption_fails_closed",
        "tests/test_sbm_postsolve_certification.py::"
        "test_one_bad_dmu_does_not_abort_or_contaminate_the_next_dmu",
        "tests/test_sbm_postsolve_certification.py::"
        "test_default_highs_certifies_all_classic_orientations_and_rts",
        "tests/test_lp_certificates.py",
    }

    for method_id in classic_sbm_ids:
        record = methods[method_id]
        assert required_components.issubset(record["result_contract"]["components"])
        target = record["guarantees"]["target"]
        assert "certified" in target["feasibility"]
        assert "sbm_account_reconstruction" in target["feasibility"]
        assert required_conditions.issubset(target["conditions"])
        tests = record["validation"]["tests"]
        assert required_coverage.issubset(tests["coverage"])
        assert required_locators.issubset(tests["locators"])
        for locator in required_locators:
            _assert_locator_exists(locator)


def test_classic_radial_record_publishes_phase_scoped_postsolve_contract() -> None:
    methods = {record["id"]: record for _, record in _records("methods")}
    record = methods["static.radial"]

    required_components = {
        "score_valid",
        "score_status",
        "primary_solver_status",
        "completion_valid",
        "target_valid",
        "peer_valid",
        "dual_valid",
        "solver_neutral_primary_lp_optimality_certificate",
        "radial_primary_account_reconstruction_certificate",
        "solver_neutral_completion_lp_optimality_certificate",
        "radial_completion_account_reconstruction_certificate",
        "phase_scoped_fail_closed_result_release",
    }
    assert required_components.issubset(record["result_contract"]["components"])

    target = record["guarantees"]["target"]
    assert "certified_primary_and_completion" in target["feasibility"]
    assert {
        "condition.successful_primal_dual_certificate",
        "condition.successful_radial_primary_account_reconstruction_certificate",
        "condition.successful_radial_completion_account_reconstruction_certificate",
    }.issubset(target["conditions"])

    tests = record["validation"]["tests"]
    required_coverage = {
        "shared_solver_neutral_primal_dual_bound_kkt_certificate",
        "primary_radial_account_reconstruction_certificate",
        "completion_target_and_slack_account_reconstruction_certificate",
        "raw_solver_status_preserved_on_certificate_failure",
        "primary_failure_withholds_all_semantic_tables",
        "completion_failure_preserves_only_certified_primary_score",
        "unit_invariant_postsolve_account_checks",
        "publication_cleanup_peer_threshold_and_dual_account_checks",
    }
    required_locators = {
        "tests/test_radial_certificates.py",
        "tests/test_radial_certificates.py::"
        "test_uncertified_primary_withholds_all_claims_for_only_the_bad_dmu",
        "tests/test_radial_certificates.py::"
        "test_uncertified_completion_preserves_only_the_primary_score_for_bad_dmu",
        "tests/test_radial_certificates.py::"
        "test_default_highs_certifies_both_phases_without_extra_solves",
        "tests/test_radial_certificates.py::"
        "test_publication_cleanup_cannot_release_an_invalid_aggregate_account",
        "tests/test_radial_certificates.py::"
        "test_vrs_dual_account_includes_the_certified_convexity_marginal",
        "tests/test_lp_certificates.py",
    }
    assert required_coverage.issubset(tests["coverage"])
    assert required_locators.issubset(tests["locators"])
    for locator in required_locators:
        _assert_locator_exists(locator)


def test_radial_consumer_records_publish_component_validity_contracts() -> None:
    methods = {record["id"]: record for _, record in _records("methods")}

    scale = methods["analysis.scale_efficiency.radial_ratio"]
    assert {
        "crs_primary_solver_status",
        "vrs_primary_solver_status",
        "crs_score_valid",
        "vrs_score_valid",
        "score_valid",
        "score_status",
    }.issubset(scale["result_contract"]["components"])
    assert (
        "component_postsolve_certificates_fail_closed"
        in scale["validation"]["tests"]["coverage"]
    )

    for method_id in (
        "analysis.allocative_decomposition.cost_input_radial",
        "analysis.allocative_decomposition.revenue_output_radial",
    ):
        record = methods[method_id]
        assert {
            "technical_primary_solver_status",
            "technical_score_valid",
            "technical_score_status",
            "score_valid",
            "score_status",
            "decomposition_defined",
        }.issubset(record["result_contract"]["components"])
        assert (
            "technical_component_postsolve_certificate_fail_closed"
            in record["validation"]["tests"]["coverage"]
        )

    metafrontier = methods[
        "heterogeneity.metafrontier.radial.odonnell_rao_battese_2008"
    ]
    assert {
        "group_score_valid",
        "metafrontier_score_valid",
        "group_completion_valid",
        "metafrontier_completion_valid",
        "group_target_valid",
        "metafrontier_target_valid",
    }.issubset(metafrontier["result_contract"]["components"])

    for record in (scale, metafrontier):
        for locator in record["validation"]["tests"]["locators"]:
            _assert_locator_exists(locator)


def test_manifest_and_schemas_freeze_the_exact_eleven_axes() -> None:
    manifest = _manifest()
    assert manifest["ontology_schema_version"] == SCHEMA_VERSION
    assert manifest["registry_release"] == "2026-08-03-shadow.58"
    assert len(manifest["methods"]) == 67
    assert len(manifest["relations"]) == 43
    assert tuple(manifest["axes"]) == AXES

    method_schema = _load_json(REGISTRY_ROOT / manifest["schemas"]["method"])
    relation_schema = _load_json(REGISTRY_ROOT / manifest["schemas"]["relation"])

    assert method_schema["$schema"] == JSON_SCHEMA_DRAFT
    assert relation_schema["$schema"] == JSON_SCHEMA_DRAFT

    composition_schema = method_schema["$defs"]["composition"]
    assert tuple(composition_schema["required"]) == AXES
    assert set(composition_schema["properties"]) == set(AXES)
    assert composition_schema["additionalProperties"] is False

    relation_axes = relation_schema["$defs"]["axisName"]["enum"]
    assert tuple(relation_axes) == AXES


def test_shadow_registry_readme_inventory_matches_manifest_and_catalog() -> None:
    """Keep the current ontology summary synchronized with its live sources."""
    manifest = _manifest()
    records = [record for _, record in _records("methods")]
    public_records = [
        record
        for record in records
        if record["status"]["implementation"] == "implemented"
        and record["status"]["api"] == "public"
    ]
    prototype_records = [
        record
        for record in records
        if record["status"]["implementation"] == "prototype"
    ]
    public_role_counts = Counter(record["identifier_role"] for record in public_records)
    catalog = list_methods()
    catalog_role_counts = Counter(item.identifier_role for item in catalog)
    oracle_counts = Counter(
        record["validation"]["oracle"]["status"] for record in records
    )
    readme = " ".join((REGISTRY_ROOT / "README.md").read_text(encoding="utf-8").split())

    assert public_role_counts == {"method_id": 62, "preset_id": 1}
    assert (
        f"The `2.0.0rc1` governance target, represented by shadow-registry "
        f"manifest `{manifest['registry_release']}`, contains {len(records)} machine "
        f"method records: {len(public_records)} implemented/public records "
        f"({public_role_counts['method_id']} public `method_id` entries and "
        f"{public_role_counts['preset_id']} public `preset_id` record for APZ), and "
        f"{len(prototype_records)} deferred non-public prototypes"
    ) in readme
    assert (
        f"The same checkpoint contains {len(manifest['relations'])} typed "
        "relationship records."
    ) in readme
    assert (
        f"The public catalog therefore contains {len(catalog)} identities: "
        f"{catalog_role_counts['method_id']} `method_id`, "
        f"{catalog_role_counts['specialization_id']} `specialization_id`, and "
        f"{catalog_role_counts['preset_id']} `preset_id` entries."
    ) in readme
    assert (
        f"The {len(records)} machine records contain "
        f"{oracle_counts['analytically_derived']} `analytically_derived`, "
        f"{oracle_counts['reproduced']} `reproduced`, "
        f"{oracle_counts['cross_implemented']} `cross_implemented`, "
        f"{oracle_counts['candidate']} `candidate`, and "
        f"{oracle_counts['not_located']} `not_located` oracle records."
    ) in readme
    assert (
        f"between the {len(public_records)} implemented/public machine records and "
        "the corresponding machine-backed catalog identities: "
        f"{public_role_counts['method_id']} public `method_id` entries and the APZ "
        "public `preset_id`"
    ) in readme


def test_rc1_public_not_located_oracle_debt_is_zero() -> None:
    """Do not let a closed public oracle debt silently reappear."""
    public_not_located = {
        record["id"]
        for _, record in _records("methods")
        if record["status"]["implementation"] == "implemented"
        and record["status"]["api"] == "public"
        and record["validation"]["oracle"]["status"] == "not_located"
    }

    assert public_not_located == set()


def test_fch_and_dynamic_network_oracle_closures_remain_claim_scoped() -> None:
    methods = {record["id"]: record for _, record in _records("methods")}

    fch = methods["static.radial.fch.green_cook_2004"]["validation"]["oracle"]
    assert fch["status"] == "analytically_derived"
    fch_certificate = fch["analytical_certificate"]
    assert fch_certificate["published_reproduction"] is False
    assert fch_certificate["production_compiler_reused"] is False
    assert {claim["claim_id"] for claim in fch_certificate["claims"]} == {
        "static.radial.fch.green_cook_2004.exact_binary_subset_account"
    }

    dynamic = methods["dynamic.network_sbm.tone_tsutsui_2014"]["validation"]["oracle"]
    assert dynamic["status"] == "analytically_derived"
    dynamic_certificate = dynamic["analytical_certificate"]
    assert dynamic_certificate["published_reproduction"] is False
    assert dynamic_certificate["production_compiler_reused"] is False
    dynamic_claims = {
        claim["claim_id"]: claim for claim in dynamic_certificate["claims"]
    }
    assert set(dynamic_claims) == {
        "dynamic.network_sbm.tone_tsutsui_2014.joint_crs_exact_account",
        "dynamic.network_sbm.tone_tsutsui_2014.joint_continuity_discrimination",
    }
    exact = dynamic_claims[
        "dynamic.network_sbm.tone_tsutsui_2014.joint_crs_exact_account"
    ]
    assert exact["parameter_scope"]["orientation"] == ["nonoriented"]
    assert exact["parameter_scope"]["returns_to_scale"] == ["crs"]
    assert exact["data_scope"]["fixture_shape"]["observations"] == 2
    assert {
        "within_period_link_targets",
        "carryover_transition_targets",
        "period_process_efficiency_contributions",
    } <= set(exact["result_components"])


def test_manifest_lists_every_shadow_record_exactly_once() -> None:
    manifest = _manifest()
    declared_methods = set(manifest["methods"])
    declared_relations = set(manifest["relations"])

    actual_methods = {
        path.relative_to(REGISTRY_ROOT).as_posix()
        for path in (REGISTRY_ROOT / "methods").rglob("*.json")
    }
    actual_relations = {
        path.relative_to(REGISTRY_ROOT).as_posix()
        for path in (REGISTRY_ROOT / "relations").rglob("*.json")
    }

    assert len(manifest["methods"]) == len(declared_methods)
    assert len(manifest["relations"]) == len(declared_relations)
    assert declared_methods == actual_methods
    assert declared_relations == actual_relations


def test_every_machine_record_validates_against_its_full_json_schema() -> None:
    manifest = _manifest()
    for kind, schema_key in (("methods", "method"), ("relations", "relation")):
        schema_path = REGISTRY_ROOT / manifest["schemas"][schema_key]
        schema = _load_json(schema_path)
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)

        for path, record in _records(kind):
            errors = sorted(
                validator.iter_errors(record),
                key=lambda error: tuple(str(part) for part in error.absolute_path),
            )
            assert not errors, (
                path,
                [
                    {
                        "path": "/".join(str(part) for part in error.absolute_path),
                        "message": error.message,
                    }
                    for error in errors
                ],
            )


def test_method_records_have_unique_ids_and_complete_bindings() -> None:
    method_schema = _load_json(
        REGISTRY_ROOT / "schema" / "method-record-v1.schema.json"
    )
    required_fields = set(method_schema["required"])
    allowed_fields = set(method_schema["properties"])
    allowed_axis_fields = set(method_schema["$defs"]["axisBinding"]["properties"])

    methods = _records("methods")
    method_ids = [record["id"] for _, record in methods]
    assert len(method_ids) == len(set(method_ids))

    for path, record in methods:
        assert record["ontology_schema_version"] == SCHEMA_VERSION
        assert REGISTRY_ID.fullmatch(record["id"]), path
        assert set(record) == required_fields == allowed_fields
        assert tuple(record["composition"]) == AXES

        for axis, binding in record["composition"].items():
            assert binding, (path, axis)
            assert set(binding) <= allowed_axis_fields, (path, axis)

        reference = record["composition"]["reference"]
        reference_defaults = reference.get("defaults", {})
        assert "comparison_population" in reference_defaults, path
        assert "temporal_information_set" in reference_defaults, path

        uncertainty = record["composition"]["uncertainty"]["fixed"]
        assert set(uncertainty) == {"sampling", "data"}, path

        tests = record["validation"]["tests"]
        if tests["status"] == "present":
            assert tests["locators"], path
            for locator in tests["locators"]:
                _assert_locator_exists(locator)

        for locator in record["validation"]["benchmarks"]:
            _assert_locator_exists(locator)

        for channel in ("book", "docs"):
            for placement in record["placement"][channel]:
                if placement["state"] == "present":
                    assert placement["path"] is not None, placement
                    _assert_locator_exists(placement["path"])


def test_present_book_placements_belong_to_the_published_route() -> None:
    """Do not let docs-only leaves re-enter the handbook through the registry."""
    index = BOOK_INDEX_PATH.read_text(encoding="utf-8")
    published = {
        f"book/{entry}.md"
        for entry in re.findall(r"(?m)^((?:chapters|appendices)/\S+)$", index)
    }

    for path, record in _records("methods"):
        for placement in record["placement"]["book"]:
            if placement["state"] != "present":
                continue
            assert placement["path"] in published, (path, placement)


def test_components_and_dependencies_resolve_to_the_human_method_atlas() -> None:
    human_registry = HUMAN_REGISTRY_PATH.read_text(encoding="utf-8")
    atlas_ids = set(re.findall(r"(?m)^\| `([^`]+)` \|", human_registry))

    for path, record in _records("methods"):
        dependencies = record["implementation"]["registry_dependencies"]
        assert set(dependencies) <= atlas_ids, (path, dependencies)

        for axis, binding in record["composition"].items():
            components = binding.get("components", [])
            assert set(components) <= atlas_ids, (path, axis, components)


def test_aliases_and_relations_resolve_without_creating_duplicate_methods() -> None:
    relation_schema = _load_json(
        REGISTRY_ROOT / "schema" / "relation-record-v1.schema.json"
    )
    required_fields = set(relation_schema["required"])
    allowed_fields = set(relation_schema["properties"])

    methods = _records("methods")
    method_ids = {record["id"] for _, record in methods}
    aliases = _alias_ids(methods)
    assert aliases.isdisjoint(method_ids)
    assert aliases == {"static.erg"}

    api_alias_ids = {
        alias["alias_id"]
        for _, record in methods
        for alias in record["names"]["api"]["aliases"]
        if "alias_id" in alias
    }
    assert api_alias_ids <= aliases

    identities = method_ids | aliases
    seen_edges: set[tuple[str, str, str]] = set()
    for path, relation in _records("relations"):
        assert relation["ontology_schema_version"] == SCHEMA_VERSION
        assert set(relation) == required_fields == allowed_fields
        assert relation["source"] in identities, path
        assert relation["target"] in method_ids, path

        edge = (relation["source"], relation["target"], relation["type"])
        assert edge not in seen_edges, path
        seen_edges.add(edge)

        difference_axes = relation["difference_axes"]
        assert len(difference_axes) == len(set(difference_axes)), path
        assert set(difference_axes) <= set(AXES), path

        if relation["equivalence_level"] == "A":
            obligations = set(relation["evidence"]["proof_obligations"])
            assert obligations >= LEVEL_A_OBLIGATIONS, path

        if relation["type"] == "alias":
            assert relation["equivalence_level"] == "A", path
            assert relation["difference_axes"] == [], path

        if relation["type"] in DEPENDENCY_RELATIONS:
            assert relation["equivalence_level"] is None, path

        for locator in relation["evidence"]["tests"]:
            _assert_locator_exists(locator)


def test_shadow_status_projects_only_implemented_public_records() -> None:
    methods = _records("methods")
    catalog = {item.method_id: item for item in list_methods()}
    public_method_catalog = {
        item.method_id: item
        for item in list_methods()
        if item.identifier_role == "method_id"
    }

    implemented_public = {
        record["id"]
        for _, record in methods
        if record["status"]["implementation"] == "implemented"
        and record["status"]["api"] == "public"
    }
    non_catalog_status = {
        record["id"]
        for _, record in methods
        if record["status"]["implementation"] in {"planned", "prototype", "excluded"}
    }

    implemented_public_methods = {
        record["id"]
        for _, record in methods
        if record["id"] in implemented_public
        and record["identifier_role"] == "method_id"
    }
    implemented_public_presets = {
        record["id"]
        for _, record in methods
        if record["id"] in implemented_public
        and record["identifier_role"] == "preset_id"
    }

    assert implemented_public <= set(catalog)
    assert implemented_public_methods == set(public_method_catalog)
    assert len(implemented_public_methods) == 62
    assert implemented_public_presets == {
        "productivity.malmquist_luenberger.aparicio_pastor_zofio_2013"
    }
    assert len(implemented_public) == 63
    assert non_catalog_status.isdisjoint(catalog)

    aliases = _alias_ids(methods)
    assert aliases.isdisjoint(catalog)

    for _, record in methods:
        if record["id"] not in implemented_public:
            continue
        source_roles = {source["role"] for source in record["validation"]["sources"]}
        if record["id"] in PACKAGE_DEFINED_PUBLIC_DIAGNOSTICS:
            assert source_roles == {"critique", "predecessor", "review"}, record["id"]
            assert record["validation"]["evidence_status"] == "review_supported"
            assert record["validation"]["oracle"]["status"] == "cross_implemented"
        else:
            assert "defining" in source_roles, record["id"]
        symbols = [record["names"]["api"]["canonical_symbol"]]
        symbols.extend(alias["symbol"] for alias in record["names"]["api"]["aliases"])
        assert catalog[record["id"]].api_symbols == tuple(symbols)

        present_book = any(
            placement["state"] == "present" for placement in record["placement"]["book"]
        )
        present_docs = any(
            placement["state"] == "present" for placement in record["placement"]["docs"]
        )
        assert ("book" in catalog[record["id"]].documentation) is present_book
        assert ("api" in catalog[record["id"]].documentation) is present_docs


def test_fare_grosskopf_kao_hwang_relation_is_score_only_not_alias() -> None:
    relations = {path.name: record for path, record in _records("relations")}
    relation = relations["network-fare-grosskopf-kao-hwang-system-score.json"]

    assert relation["source"] == "network.radial.fare_grosskopf_2000"
    assert relation["target"] == "network.relational.kao_hwang_2008"
    assert relation["type"] == "exact_score_transform"
    assert relation["equivalence_level"] == "B"
    assert relation["conditions"][0]["arguments"]["claim_scope"] == (
        "primary_system_optimum_only"
    )
    assert (
        "target_and_peer_correspondence"
        not in (relation["evidence"]["proof_obligations"])
    )


def test_radial_metafrontier_freezes_pooled_hulls_ratio_and_meanings() -> None:
    methods = {record["id"]: record for _, record in _records("methods")}
    record = methods["heterogeneity.metafrontier.radial.odonnell_rao_battese_2008"]

    assert record["names"]["api"] == {
        "canonical_symbol": "RadialMetafrontierDEA",
        "aliases": [{"symbol": "MetafrontierDEA"}],
    }

    technology = record["composition"]["technology"]["fixed"]
    assert technology["meta_construction"] == {
        "vrs": "pooled_convex",
        "crs": "pooled_conic",
    }
    assert technology["nonconvex_union"] == "non_equivalent_and_unsupported"

    performance = record["composition"]["performance"]["fixed"]
    assert performance["canonical_ratio"] == "metatechnology_ratio"
    assert performance["canonical_abbreviation"] == "MTR"
    assert performance["aliases"] == {
        "technology_gap_ratio": "metatechnology_ratio",
        "TGR": "MTR",
    }

    analysis = record["composition"]["analysis"]["fixed"]
    assert analysis["within_group_efficiency_meaning"] == (
        "operating_performance_relative_to_opportunities_available_within_"
        "the_declared_group"
    )
    assert analysis["metatechnology_ratio_meaning"] == (
        "proximity_of_the_declared_group_frontier_to_the_broader_meta_"
        "opportunity_frontier_at_the_evaluated_mix"
    )
    assert analysis["causal_interpretation"] == "not_identified"

    relations = {path.name: value for path, value in _records("relations")}
    relation = relations["heterogeneity-metafrontier-static-radial-composition.json"]
    assert relation["source"] == record["id"]
    assert relation["target"] == "static.radial"
    assert relation["type"] == "composes"
    assert relation["equivalence_level"] is None
    arguments = relation["conditions"][0]["arguments"]
    assert arguments["group_comparison_population"] == "same_declared_group"
    assert arguments["meta_comparison_population"] == "all_declared_groups"
    assert arguments["nonconvex_union_equivalence"] == "forbidden"


def test_range_directional_record_freezes_source_contract_and_non_alias_relation() -> (
    None
):
    methods = {record["id"]: record for _, record in _records("methods")}

    ddf = methods["static.directional_distance"]
    assert ddf["status"] == {
        "priority": "P0",
        "release_tier": 0,
        "implementation": "implemented",
        "api": "public",
    }
    assert ddf["names"]["api"] == {
        "canonical_symbol": "DirectionalDistanceDEA",
        "aliases": [{"symbol": "DDF"}],
    }

    record = methods["static.range_directional.portela_thanassoulis_simpson_2004"]
    assert record["kind"] == "preset"
    assert record["names"]["api"] == {
        "canonical_symbol": "RangeDirectionalDEA",
        "aliases": [{"symbol": "RDM"}],
    }

    data_roles = record["composition"]["data_roles"]["fixed"]
    assert data_roles["sign_domain"] == "signed_finite"
    assert data_roles["bad_outputs"] == "excluded"
    assert data_roles["preference_direction"] == {
        "inputs": "less_is_better",
        "outputs": "more_is_better",
    }

    technology = record["composition"]["technology"]["fixed"]
    assert technology["returns_to_scale"] == "vrs"
    assert technology["convexity_identity"] == "sum_lambda_equals_one"

    reference = record["composition"]["reference"]
    assert reference["fixed"] == {
        "extrema_population": "identical_to_technology_population",
        "focal_membership": "required",
    }
    assert (
        reference["defaults"]["comparison_population"]["self_membership"] == "required"
    )

    performance = record["composition"]["performance"]["fixed"]
    assert performance["direction_policy"] == (
        "focal_to_reference_coordinatewise_ideal"
    )
    assert performance["supported_orientations"] == [
        "non-oriented",
        "input",
        "output",
    ]
    assert performance["native_score"] == "beta"
    assert performance["reported_efficiency"] == "one_minus_beta"

    protocol = record["composition"]["evaluation_protocol"]["fixed"]
    assert protocol["phase"] == "source_phase_one_only"
    assert protocol["target_status"] == "directional_not_pareto_certified"
    assert protocol["zero_active_direction"] == (
        "fail_with_unbounded_direction_diagnostic"
    )

    scores = {score["id"]: score for score in record["result_contract"]["scores"]}
    assert scores["beta"]["usual_range"] == {
        "lower": 0.0,
        "upper": 1.0,
        "conditions": [
            "condition.rdm.positive_active_range",
            "condition.rdm.extrema_technology_reference_match",
            "condition.rdm.self_inclusive_reference",
        ],
    }
    assert scores["rdm_efficiency"]["direction"] == "higher_is_better"
    assert record["result_contract"]["transformations"] == [
        "rdm_efficiency_equals_one_minus_beta"
    ]

    assert record["validation"]["sources"] == [
        {
            "role": "defining",
            "id": "doi:10.1057/palgrave.jors.2601768",
        }
    ]
    assert record["validation"]["oracle"]["status"] == "cross_implemented"
    assert any(
        "source_protocols/portela_thanassoulis_simpson_2004_rdm.md" in locator
        for locator in record["validation"]["oracle"]["locators"]
    )

    relations = {path.name: value for path, value in _records("relations")}
    relation = relations[
        "static-range-directional-directional-distance-composition.json"
    ]
    assert relation["source"] == record["id"]
    assert relation["target"] == "static.directional_distance"
    assert relation["type"] == "composes"
    assert relation["equivalence_level"] is None
    assert set(relation["difference_axes"]) == {
        "data_roles",
        "technology",
        "reference",
        "performance",
        "evaluation_protocol",
    }
    arguments = relation["conditions"][0]["arguments"]
    assert arguments["semantic_equivalence"] == "forbidden"
    assert set(arguments["non_equivalent_to"]) == {
        "generic_exogenous_direction_ddf",
        "range_adjusted_measure",
        "semi_oriented_radial_measure",
        "inverse_range_directional_measure",
        "radial_model_after_translation",
        "environmental_undesirable_output_ddf",
    }


def test_ray_directional_super_record_freezes_source_and_non_alias_boundary() -> None:
    methods = {record["id"]: record for _, record in _records("methods")}
    record = methods["evaluation.super.directional.ray_2008"]

    assert record["status"] == {
        "priority": "P1",
        "release_tier": 1,
        "implementation": "implemented",
        "api": "public",
        "publication_scope": "documentation_only",
    }
    assert record["names"]["api"] == {
        "canonical_symbol": "RayDirectionalSuperEfficiency",
        "aliases": [{"symbol": "NerloveLuenbergerSuperEfficiency"}],
    }
    assert record["composition"]["technology"]["fixed"]["returns_to_scale"] == ("vrs")
    performance = record["composition"]["performance"]["fixed"]
    assert performance["input_direction"] == "negative_evaluated_input_bundle"
    assert performance["output_direction"] == "positive_evaluated_output_bundle"
    assert performance["native_distance"] == "unrestricted_beta"
    assert performance["reported_score"] == "one_minus_beta"
    assert performance["score_direction"] == "higher_is_more_exposed"

    protocol = record["composition"]["evaluation_protocol"]["fixed"]
    assert protocol["exclusion_unit"] == "evaluated_row"
    assert protocol["self_exclusion"] == "required"
    assert protocol["direction_choice"] == "source_fixed_observed_bundle"
    assert protocol["slack_completion"] == "none_source_phase_one_only"
    assert protocol["negative_projection_policy"] == (
        "retain_certified_raw_beta_and_score_but_mark_substantive_score_and_"
        "target_invalid"
    )

    assert record["validation"]["evidence_status"] == "primary_checked"
    assert record["validation"]["oracle"]["status"] == "reproduced"
    source_ids = {source["id"] for source in record["validation"]["sources"]}
    assert "doi:10.1057/palgrave.jors.2602392" in source_ids

    relations = {path.name: value for path, value in _records("relations")}
    relation = relations["evaluation-super-directional-ddf-composition.json"]
    assert relation["source"] == record["id"]
    assert relation["target"] == "static.directional_distance"
    assert relation["type"] == "composes"
    assert relation["equivalence_level"] is None
    arguments = relation["conditions"][0]["arguments"]
    assert arguments["returns_to_scale"] == "vrs_only"
    assert arguments["semantic_equivalence"] == "forbidden"
    assert "super_sbm_peer_replacement" in arguments["non_equivalent_to"]


def test_productivity_records_do_not_overstate_source_or_result_contracts() -> None:
    methods = {record["id"]: record for _, record in _records("methods")}
    global_record = methods["productivity.global_malmquist"]
    biennial_record = methods["productivity.biennial_malmquist"]
    luenberger_record = methods["productivity.luenberger"]

    for record in (global_record, biennial_record, luenberger_record):
        assert (
            record["composition"]["technology"]["fixed"]["source_returns_to_scale"]
            == "crs"
        )

    for record in (global_record, biennial_record):
        target = record["guarantees"]["target"]
        assert "solver_reported_optimal" in target["feasibility"]
        assert "above peer_tolerance" in target["selection"]

    luenberger_target = luenberger_record["guarantees"]["target"]
    assert "solver-neutral" in luenberger_target["feasibility"]
    assert "KKT" in luenberger_target["feasibility"]
    assert (
        "all four distance and additive-account certificates"
        in (luenberger_target["selection"])
    )
    assert "above peer_tolerance" in luenberger_target["selection"]

    global_oracle = global_record["validation"]["oracle"]
    assert global_oracle["status"] == "analytically_derived"
    global_certificate = global_oracle["analytical_certificate"]
    assert global_certificate["published_reproduction"] is False
    assert global_certificate["production_compiler_reused"] is False
    assert {claim["claim_id"] for claim in global_certificate["claims"]} == {
        "productivity.pastor_lovell_global.exact_three_period_account",
        "productivity.pastor_lovell_global.fixed_vintage_circularity",
        "productivity.pastor_lovell_global.unit_invariance",
    }
    biennial_oracle = biennial_record["validation"]["oracle"]
    assert biennial_oracle["status"] == "analytically_derived"
    biennial_certificate = biennial_oracle["analytical_certificate"]
    assert biennial_certificate["published_reproduction"] is False
    assert biennial_certificate["production_compiler_reused"] is False
    assert {claim["claim_id"] for claim in biennial_certificate["claims"]} == {
        "productivity.pastor_asmild_lovell_biennial.exact_own_period_distance_roles",
        "productivity.pastor_asmild_lovell_biennial.exact_pair_pool_distance_roles",
        "productivity.pastor_asmild_lovell_biennial.exact_cross_reference_account_reconstruction",
        "productivity.pastor_asmild_lovell_biennial.exact_adjacent_pair_membership",
    }

    assert luenberger_record["validation"]["oracle"]["status"] == (
        "analytically_derived"
    )

    global_components = set(global_record["result_contract"]["components"])
    assert "global_reference_membership_metadata" in global_components
    assert "global_sample_vintage" not in global_components

    biennial_components = set(biennial_record["result_contract"]["components"])
    assert "biennial_reference_membership_metadata" in biennial_components
    assert "biennial_pair_vintage" not in biennial_components

    luenberger_performance = luenberger_record["composition"]["performance"]["fixed"]
    assert luenberger_performance["source_direction_domain"] == (
        "one_direction_fixed_across_dmus_periods_and_all_four_distance_tasks"
    )
    assert luenberger_performance["observation_specific_directions"].endswith(
        "outside_the_classic_source_guarantee"
    )
    luenberger_components = set(luenberger_record["result_contract"]["components"])
    luenberger_scores = {
        score["id"]: score for score in luenberger_record["result_contract"]["scores"]
    }
    assert luenberger_scores["productivity_change"]["direction"] == (
        "positive_is_improvement"
    )
    assert "direction_policy_labels_and_custom_parameter_signatures" in (
        luenberger_components
    )
    assert "direction_specifications" not in luenberger_components
    assert {
        "score_valid_and_score_status",
        "four_distance_lp_certificate_summary",
        "additive_account_certificate_and_residuals",
    }.issubset(luenberger_components)
    unit_contract = luenberger_record["guarantees"]["invariance"]["unit"]
    assert unit_contract["co_transform"] == ["input_direction", "output_direction"]


def test_productivity_publication_scope_and_reference_policy_relations() -> None:
    """Keep handbook routes separate from executable technical leaves."""
    methods = {record["id"]: record for _, record in _records("methods")}
    expected_scopes = {
        "productivity.malmquist.adjacent_geometric": "handbook_core",
        "productivity.global_malmquist": "supporting_reference_policy",
        "productivity.luenberger": "handbook_core",
        "productivity.malmquist_luenberger.chung_fare_grosskopf_1997": (
            "handbook_core"
        ),
        "productivity.global_malmquist_luenberger.oh_2010": ("handbook_sensitivity"),
        "productivity.hicks_moorsteen.bjurek_1996": "handbook_core",
        "productivity.biennial_malmquist": "documentation_only",
        "productivity.malmquist.decomposition.fgnz_pure_scale_extension": (
            "documentation_only"
        ),
        "productivity.malmquist.decomposition.ray_desli": "documentation_only",
        "productivity.malmquist_luenberger.aparicio_pastor_zofio_2013": (
            "documentation_only"
        ),
    }
    assert {
        method_id
        for method_id, record in methods.items()
        if record["category"] == "productivity"
    } == set(expected_scopes)
    assert {
        method_id: methods[method_id]["status"]["publication_scope"]
        for method_id in expected_scopes
    } == expected_scopes

    global_book = methods["productivity.global_malmquist"]["placement"]["book"]
    oh_book = methods["productivity.global_malmquist_luenberger.oh_2010"]["placement"][
        "book"
    ]
    assert [item["role"] for item in global_book] == ["supporting_reference_policy"]
    assert [item["role"] for item in oh_book] == ["sensitivity"]

    relations = {path.name: record for path, record in _records("relations")}
    adjacent_id = "productivity.malmquist.adjacent_geometric"
    global_id = "productivity.global_malmquist"
    biennial_id = "productivity.biennial_malmquist"

    global_adjacent = relations["productivity-global-adjacent-reference-policy.json"]
    assert (global_adjacent["source"], global_adjacent["target"]) == (
        global_id,
        adjacent_id,
    )
    assert global_adjacent["type"] == "variant_of"

    biennial_adjacent = relations[
        "productivity-biennial-adjacent-reference-policy.json"
    ]
    assert (biennial_adjacent["source"], biennial_adjacent["target"]) == (
        biennial_id,
        adjacent_id,
    )
    assert biennial_adjacent["type"] == "variant_of"

    global_biennial = relations["productivity-global-biennial-reference-policy.json"]
    assert (global_biennial["source"], global_biennial["target"]) == (
        global_id,
        biennial_id,
    )
    assert global_biennial["type"] == "contrasts_with"

    for relation in (global_adjacent, biennial_adjacent, global_biennial):
        assert relation["equivalence_level"] == "C"
        assert set(relation["difference_axes"]) == {
            "technology",
            "reference",
            "analysis",
        }
        assert relation["conditions"][0]["arguments"]["alias_claim"] == ("forbidden")


def test_network_dynamic_panel_publication_scope_and_family_roles() -> None:
    """Keep two network routes and one dynamic route smaller than the API."""
    methods = {record["id"]: record for _, record in _records("methods")}
    expected_scopes = {
        "network.radial.fare_grosskopf_2000": "handbook_core",
        "network.relational.kao_hwang_2008": "handbook_core",
        "network.additive.chen_etal_2009": "handbook_core",
        "network.additive.cook_zhu_bi_yang_2010": "handbook_core",
        "network.sbm.tone_tsutsui_2009": "handbook_core",
        "network.sequential.lewis_sexton_2004.forward_radial": ("documentation_only"),
        "network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018": (
            "documentation_only"
        ),
        "dynamic.sbm.tone_tsutsui_2010": "handbook_core",
        "dynamic.network_sbm.tone_tsutsui_2014": "documentation_only",
        "panel.multiperiod_aggregative.park_park_2009": "documentation_only",
    }
    governed_categories = {"network", "dynamic", "panel"}

    assert {
        method_id
        for method_id, record in methods.items()
        if record["category"] in governed_categories
    } == set(expected_scopes)
    assert {
        method_id: methods[method_id]["status"]["publication_scope"]
        for method_id in expected_scopes
    } == expected_scopes

    chen_book = methods["network.additive.chen_etal_2009"]["placement"]["book"]
    cook_book = methods["network.additive.cook_zhu_bi_yang_2010"]["placement"]["book"]
    assert [item["role"] for item in chen_book] == ["mention"]
    assert [item["role"] for item in cook_book] == ["primary"]

    for method_id, publication_scope in expected_scopes.items():
        book = methods[method_id]["placement"]["book"]
        if publication_scope == "handbook_core":
            assert any(item["state"] == "present" for item in book), method_id
        else:
            assert book == [], method_id


def test_heterogeneity_publication_scope_and_mtr_meaning() -> None:
    methods = {record["id"]: record for _, record in _records("methods")}
    method_id = "heterogeneity.metafrontier.radial.odonnell_rao_battese_2008"
    record = methods[method_id]

    assert {
        candidate
        for candidate, candidate_record in methods.items()
        if candidate_record["category"] == "heterogeneity"
    } == {method_id}
    assert record["status"]["publication_scope"] == "handbook_core"
    scores = {score["id"]: score for score in record["result_contract"]["scores"]}
    assert scores["group_efficiency"]["direction"] == "higher_is_better"
    assert scores["metafrontier_efficiency"]["direction"] == "higher_is_better"
    assert scores["metatechnology_ratio"]["direction"] == "higher_is_closer"
    assert record["placement"]["book"] == [
        {
            "doc_id": "book.heterogeneity.metafrontier",
            "path": "book/chapters/07-heterogeneity/23-metafrontier.md",
            "state": "present",
            "role": "primary",
        }
    ]


def test_evaluation_publication_scope_separates_api_from_handbook_routes() -> None:
    """Keep specialized appraisal APIs out of the key-model Handbook route."""
    methods = {record["id"]: record for _, record in _records("methods")}
    expected_scopes = {
        "evaluation.cross.game_nash.liang_wu_cook_zhu_2008": ("documentation_only"),
        "evaluation.super.directional.ray_2008": "documentation_only",
        "evaluation.super.sbm.tone_2002": "documentation_only",
        "evaluation.cross.crs": "next_version",
        "evaluation.super.ap_radial": "next_version",
    }

    assert {
        method_id
        for method_id, record in methods.items()
        if record["category"] == "evaluation"
    } == set(expected_scopes)
    assert {
        method_id: methods[method_id]["status"]["publication_scope"]
        for method_id in expected_scopes
    } == expected_scopes

    for method_id, publication_scope in expected_scopes.items():
        record = methods[method_id]
        assert record["placement"]["book"] == [], method_id
        if publication_scope == "documentation_only":
            assert record["status"]["implementation"] == "implemented"
            assert record["status"]["api"] == "public"
        else:
            assert record["status"]["implementation"] == "prototype"
            assert record["status"]["api"] == "none"


def test_reference_frequency_scope_and_selected_plan_semantics_do_not_drift() -> None:
    """Freeze a descriptive selected-plan account, not influence or inference."""
    methods = {record["id"]: record for _, record in _records("methods")}
    method_id = "analysis.reference_frequency.selected_plan"
    assert {
        candidate
        for candidate, record in methods.items()
        if record["category"] == "diagnostics"
    } == {method_id}

    record = methods[method_id]
    assert record["status"] == {
        "priority": "P0",
        "release_tier": 1,
        "implementation": "implemented",
        "api": "public",
        "publication_scope": "handbook_sensitivity",
    }
    assert record["names"]["api"] == {
        "canonical_symbol": "reference_frequency",
        "aliases": [],
    }
    assert record["composition"]["reference"]["fixed"]["account"] == (
        "reported_solver_selected_active_peer_edges_strictly_above_source_"
        "peer_tolerance"
    )

    performance = record["composition"]["performance"]["fixed"]
    assert performance["native_result"] == "reported_active_peer_edge_count"
    assert performance["normalized_result"] == "reference_rate"
    assert performance["count_range"] == (
        "integer_zero_to_evaluated_organization_count"
    )
    assert performance["rate_numerator"] == (
        "reference_frequency_including_self_and_other_reported_active_edges"
    )
    assert performance["rate_denominator"] == "all_evaluated_organizations"
    assert performance["reported_edge_threshold"] == (
        "lambda_strictly_above_source_peer_tolerance"
    )
    assert performance["directional_interpretation"] == "none"
    assert performance["intensity_aggregation_across_evaluations"] is False

    assert record["result_contract"]["scores"] == [
        {
            "id": "reference_rate",
            "direction": "mixed",
            "efficient_value": None,
            "usual_range": {
                "lower": 0.0,
                "upper": 1.0,
                "conditions": [
                    "condition.reference_frequency.complete_certified_peer_account",
                    "condition.reference_frequency.reported_edges_above_source_"
                    "peer_tolerance",
                ],
            },
        }
    ]
    assert record["result_contract"]["transformations"] == [
        "reference_frequency_equals_self_reference_frequency_plus_"
        "other_reference_frequency",
        "reference_rate_equals_reference_frequency_divided_by_all_"
        "evaluated_organizations",
    ]
    assert {
        "reference_frequency",
        "self_reference_frequency",
        "other_reference_frequency",
        "reference_rate",
        "source_peer_tolerance",
        "reference_rate_denominator",
        "alternate_optima_assessed_false",
        "zero_additional_solver_calls",
    }.issubset(record["result_contract"]["components"])

    analysis = record["composition"]["analysis"]["fixed"]
    assert analysis["claim"] == "one_certified_solver_selected_plan"
    assert analysis["global_reference_set_claim"] is False
    assert analysis["influence_claim"] is False
    assert analysis["outlier_claim"] is False
    assert analysis["ranking_claim"] is False
    assert analysis["literature_boundary"] == (
        "package_defined_reported_active_edge_account_not_torgersen_slack_"
        "adjusted_peer_importance_or_global_maximal_reference_set_analysis"
    )
    assert record["composition"]["uncertainty"]["fixed"] == {
        "sampling": {"kind": "none"},
        "data": {"kind": "none"},
    }
    assert record["guarantees"]["target"]["selection"] == (
        "one_solver_selected_plan_with_alternate_optima_not_assessed"
    )
    assert record["validation"]["oracle"]["status"] == "cross_implemented"
    assert (
        "source_peer_tolerance_provenance_and_strict_threshold"
        in (record["validation"]["tests"]["coverage"])
    )
    assert {
        source["id"]: source["role"] for source in record["validation"]["sources"]
    } == {
        "specs/reviews/STATISTICS_UNCERTAINTY.md#deterministic-diagnostics": ("review"),
        "doi:10.1007/BF00162048": "predecessor",
        "doi:10.1080/03155986.1995.11732281": "predecessor",
        "doi:10.1016/j.ejor.2015.03.029": "critique",
    }
    assert record["validation"]["benchmarks"] == [
        "benchmarks/benchmark_reference_frequency.py"
    ]
    assert record["placement"]["book"][0]["role"] == "sensitivity"


def test_governed_prototypes_are_machine_scoped_to_next_version() -> None:
    """A future prototype cannot masquerade as a current reader-facing leaf."""
    schema = _load_json(REGISTRY_ROOT / "schema" / "method-record-v1.schema.json")
    validator = Draft202012Validator(schema)
    source = next(
        record
        for _, record in _records("methods")
        if record["id"] == "network.radial.fare_grosskopf_2000"
    )

    for category in (
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
    ):
        for maturity in ("planned", "prototype"):
            future = deepcopy(source)
            future["category"] = category
            future["status"]["implementation"] = maturity
            future["status"]["api"] = "none"
            future["status"]["publication_scope"] = "next_version"
            assert validator.is_valid(future), (category, maturity)

            wrong_scope = deepcopy(future)
            wrong_scope["status"]["publication_scope"] = "documentation_only"
            assert not validator.is_valid(wrong_scope), (category, maturity)

            missing_scope = deepcopy(future)
            del missing_scope["status"]["publication_scope"]
            assert not validator.is_valid(missing_scope), (category, maturity)


def test_economic_records_propagate_domains_without_promoting_hyperbolic() -> None:
    methods = {record["id"]: record for _, record in _records("methods")}

    gdf = methods["static.generalized_distance.chavas_cox"]
    gdf_analysis = gdf["composition"]["analysis"]["fixed"]
    assert gdf_analysis["standard_hyperbolic_public_leaf"] == (
        "deferred_to_next_version"
    )
    assert (
        "if_a_source_native_h" in (gdf_analysis["conditional_reciprocal_path_algebra"])
    )
    assert all(
        "standard_hyperbolic_efficiency" not in transformation
        for transformation in gdf["result_contract"]["transformations"]
    )

    profitability = methods[
        "analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006"
    ]
    profitability_data_conditions = set(
        profitability["composition"]["data_roles"]["constraints"]
    )
    profitability_domain_conditions = set(
        profitability["guarantees"]["domain"]["conditions"]
    )
    required_profitability_condition = "condition.positive_reference_costs_and_revenues"
    assert required_profitability_condition in profitability_data_conditions
    assert required_profitability_condition in profitability_domain_conditions

    protocol = profitability["composition"]["evaluation_protocol"]["fixed"]
    assert protocol["components"] == [
        "economic.profitability.return_to_dollar",
        "static.generalized_distance.chavas_cox",
    ]
    assert {
        entry["returns_to_scale"]
        for entry in protocol["component_configurations"]
        if "returns_to_scale" in entry
    } == {
        "crs",
        "vrs",
    }

    nerlovian = methods["economic.nerlovian.ccf1998"]
    required_direction_condition = "condition.ddf.positive_active_direction"
    assert (
        required_direction_condition
        in (nerlovian["composition"]["data_roles"]["constraints"])
    )
    assert (
        required_direction_condition
        in (nerlovian["guarantees"]["domain"]["conditions"])
    )

    externally_validated_ids = {
        "static.generalized_distance.chavas_cox",
        "economic.cost",
        "economic.revenue",
        "economic.profit.maximum",
        "economic.nerlovian.ccf1998",
        "economic.profitability.return_to_dollar",
        "analysis.allocative_decomposition.cost_input_radial",
        "analysis.allocative_decomposition.revenue_output_radial",
        ("analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006"),
    }
    for method_id in externally_validated_ids:
        for locator in methods[method_id]["validation"]["oracle"]["locators"]:
            if locator.startswith(("https://", "http://")):
                continue
            _assert_locator_exists(locator)


def test_additive_certificate_is_locked_to_the_classic_source_profile() -> None:
    methods = {record["id"]: record for _, record in _records("methods")}
    record = methods["static.additive"]

    historical = record["names"]["historical"]
    source_spellings = {
        spelling
        for name in historical
        for spelling in name["spellings"]
        if "doi:10.1016/0304-4076(85)90133-2" in name["sources"]
    }
    assert source_spellings == {"additive DEA", "unweighted additive DEA"}
    assert "weighted additive DEA" not in source_spellings

    boundary = record["composition"]["analysis"]["fixed"]["source_evidence_boundary"]
    assert boundary["certified"] == (
        "charnes_etal_1985_equations_4_5_4_6_vrs_unit_weights_"
        "self_inclusive_cross_section"
    )
    assert set(boundary["package_extensions_without_source_identity"]) == {
        "fixed_positive_nonunit_slack_weights",
        "crs_nirs_ndrs",
        "panel_and_non_global_reference_policies",
    }
    assert {
        "charnes_etal_1985_equation_5_7_observation_specific_normalization",
        "published_numerical_table_reproduction",
    }.issubset(boundary["deferred_to_next_version"])

    certificate = record["validation"]["oracle"]["analytical_certificate"]
    claims = {claim["claim_id"]: claim for claim in certificate["claims"]}
    assert set(claims) == {
        "additive.source_displayed_pareto_shortfall",
        "additive.exact_vrs_direct_account",
    }
    for claim in claims.values():
        assert claim["parameter_scope"] == {
            "orientation": ["nonoriented"],
            "returns_to_scale": ["vrs"],
            "evaluation_protocol": ["direct_primary_lp"],
            "valuation_policy": ["unit_slack_weights"],
        }
        assert claim["reference_scope"] == {
            "requested_kind": "auto",
            "resolved_kind": "global",
            "comparison_population": "full_eligible_sample",
            "self_membership": "allowed",
        }
        assert claim["data_scope"]["time_structure"] == "cross_sectional"
        assert claim["data_scope"]["sign_domain"] == ("nonnegative_positive_aggregates")

    source_case = claims["additive.source_displayed_pareto_shortfall"][
        "evaluation_scope"
    ]
    assert source_case["kind"] == "named_cases"
    assert source_case["cases"][0]["case_id"] == "additive.source_displayed_b"
    assert source_case["cases"][0]["evaluated_dmu_id"] == "B"

    exact_case = claims["additive.exact_vrs_direct_account"]["evaluation_scope"]
    assert exact_case["kind"] == "named_cases"
    assert exact_case["cases"][0]["case_id"] == "additive.exact_vrs_d"
    assert exact_case["cases"][0]["evaluated_dmu_id"] == "D"
    assert (
        "independent_dense_compilation"
        not in claims["additive.exact_vrs_direct_account"]["result_components"]
    )

    protocol = (
        REPOSITORY_ROOT / "specs/source_protocols/charnes_etal_1985_additive.md"
    ).read_text(encoding="utf-8")
    assert "deferred_to_next_version" in protocol
    assert "Published numerical reproduction | not claimed" in protocol


def test_by_production_ddf_is_locked_to_the_source_crs_fixed_direction() -> None:
    methods = {record["id"]: record for _, record in _records("methods")}
    record = methods["environmental.by_production.ddf"]

    assert record["validation"]["evidence_status"] == "primary_checked"
    assert record["validation"]["oracle"]["status"] == "reproduced"
    assert record["composition"]["technology"]["defaults"] == {
        "intended_returns_to_scale": "crs",
        "residual_returns_to_scale": "crs",
    }
    assert record["composition"]["performance"]["defaults"] == {
        "output_direction": "ones",
        "bad_output_direction": "ones",
        "direction_scope": "fixed_across_observations",
    }
    assert record["composition"]["context"]["fixed"]["source_interpretation"] == (
        "criticized_conventional_index_not_the_authors_proposed_preferred_measure"
    )

    oracle_locators = set(record["validation"]["oracle"]["locators"])
    assert {
        "specs/source_protocols/by_production_ddf_reference.md",
        "specs/oracles/by-production-ddf-project-case.md",
        "src/deapack/datasets/_replacement_cases.py::_by_production_component_bottleneck",
        "tests/test_by_production_source_oracle.py::"
        "test_bp_ddf_matches_independent_compiler_on_project_case",
    } == oracle_locators
    for locator in oracle_locators:
        _assert_locator_exists(locator)

    protocol = (
        REPOSITORY_ROOT / "specs/source_protocols/by_production_ddf_reference.md"
    ).read_text(encoding="utf-8")
    assert "Published numerical reproduction | not shipped" in protocol
    assert "deferred_to_next_version" in protocol
    assert "not the authors' preferred summary" in protocol


def test_part_three_registry_contracts_match_reference_conditioned_runtime() -> None:
    methods = {record["id"]: record for _, record in _records("methods")}

    generic = methods["environmental.ddf.joint_production"]
    generic_protocol = generic["composition"]["evaluation_protocol"]["fixed"]
    assert generic_protocol == {
        "kind": "reference_conditioned_appraisal",
        "fitted_kind": "derived_as_self_mixed_or_external_from_reference_plan",
        "membership_assessment": (
            "structural_self_inclusion_or_strong_disposal_monotonicity_or_"
            "negative_beta_exclusion_or_beta_zero_feasibility_program"
        ),
        "efficiency_classification_domain": (
            "evaluated_plan_within_reference_technology"
        ),
    }
    generic_components = set(generic["result_contract"]["components"])
    assert {
        "self_in_reference",
        "is_within_reference_technology",
        "membership_status",
        "efficiency_denominator_valid",
        "target_status",
        "solver_neutral_reference_membership_certificate",
        "membership_solver_call_account",
        "certificate_solver_call_account",
    } <= generic_components
    assert generic["result_contract"]["scores"][1]["usual_range"]["conditions"] == [
        "condition.certified_reference_technology_membership"
    ]
    assert (
        "conditional_external_reference_beta_zero_membership_lp"
        in generic["implementation"]["backend_capabilities"]
    )

    for method_id in (
        "environmental.ddf.weak_disposal.common_factor",
        "environmental.ddf.output.chung_fare_grosskopf_1997",
    ):
        record = methods[method_id]
        assessment = record["composition"]["evaluation_protocol"]["fixed"][
            "membership_assessment"
        ]
        assert "negative_beta_exclusion" in assessment
        assert "target_status" in record["result_contract"]["components"]

    activity = methods["environmental.ddf.weak_disposal.activity_specific"]
    assert (
        "curtailment_share_one_minus_theta" in activity["result_contract"]["components"]
    )

    separable_sbm = methods["environmental.sbm.separable_strong"]
    assert (
        separable_sbm["composition"]["evaluation_protocol"]["fixed"]["fitted_kind"]
        == "derived_as_self_mixed_or_external_from_reference_plan"
    )

    by_production = methods["environmental.by_production.ddf"]
    assert (
        by_production["composition"]["performance"]["fixed"]["joint_aggregation"]
        == "minimum_of_component_distances"
    )
    assert (
        by_production["composition"]["performance"]["fixed"][
            "native_distance_interpretation"
        ]
        == "higher_is_farther"
    )
    assert (
        by_production["composition"]["performance"]["fixed"]["performance_ordering"]
        == "lower_is_better"
    )
    assert (
        "joint_beta_equals_minimum_of_component_distances"
        in by_production["result_contract"]["transformations"]
    )
