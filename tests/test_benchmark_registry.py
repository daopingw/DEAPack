from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ROOT = REPOSITORY_ROOT / "specs" / "registry"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    assert isinstance(value, dict), path
    return value


def _method_records() -> dict[str, dict[str, Any]]:
    manifest = _load_json(REGISTRY_ROOT / "registry-manifest.json")
    return {
        record["id"]: record
        for relative in manifest["methods"]
        for record in [_load_json(REGISTRY_ROOT / relative)]
    }


def test_benchmark_locators_follow_direct_method_execution_boundaries() -> None:
    """Keep direct benchmarks attached without promoting component coverage."""
    methods = _method_records()
    direct_benchmarks = {
        "analysis.reference_frequency.selected_plan": [
            "benchmarks/benchmark_reference_frequency.py"
        ],
        "analysis.allocative_decomposition.cost_input_radial": [
            "benchmarks/benchmark_economic_allocative.py"
        ],
        "analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006": [
            "benchmarks/benchmark_profitability_decomposition.py"
        ],
        "analysis.allocative_decomposition.revenue_output_radial": [
            "benchmarks/benchmark_economic_allocative.py"
        ],
        "economic.cost": ["benchmarks/benchmark_economic_allocative.py"],
        "economic.revenue": ["benchmarks/benchmark_economic_allocative.py"],
        "static.ebm.input.tone_tsutsui_2010.crs.declared": [
            "benchmarks/benchmark_ebm.py"
        ],
        "evaluation.super.ap_radial": ["benchmarks/benchmark_super_efficiency.py"],
        "evaluation.super.directional.ray_2008": [
            "benchmarks/benchmark_directional_super_efficiency.py"
        ],
        (
            "environmental.directional_nonradial.energy_carbon."
            "zhou_ang_wang_2012_non_chp"
        ): ["benchmarks/benchmark_zhou_ang_wang_non_chp.py"],
        "network.sequential.lewis_sexton_2004.forward_radial": [
            "benchmarks/benchmark_network_sequential.py"
        ],
        "productivity.hicks_moorsteen.bjurek_1996": [
            "benchmarks/benchmark_hicks_moorsteen.py"
        ],
        "analysis.scale_efficiency.radial_ratio": [
            "benchmarks/benchmark_classical_foundations.py"
        ],
        "static.additive": [
            "benchmarks/benchmark_classical_foundations.py",
            "benchmarks/benchmark_core_peer_eligibility.py",
        ],
        "static.directional_distance": [
            "benchmarks/benchmark_classical_foundations.py",
            "benchmarks/benchmark_core_peer_eligibility.py",
        ],
        "static.multiplicative": ["benchmarks/benchmark_classical_foundations.py"],
        "static.radial": ["benchmarks/benchmark_radial.py"],
        "static.radial.fdh": ["benchmarks/benchmark_classical_foundations.py"],
        "static.ram": [
            "benchmarks/benchmark_classical_foundations.py",
            "benchmarks/benchmark_core_peer_eligibility.py",
        ],
        "static.range_directional.portela_thanassoulis_simpson_2004": [
            "benchmarks/benchmark_range_directional.py"
        ],
        "static.sbm.input.tone2001": [
            "benchmarks/benchmark_sbm_orientations.py",
            "benchmarks/benchmark_core_peer_eligibility.py",
        ],
        "static.sbm.nonoriented.tone2001": [
            "benchmarks/benchmark_sbm_orientations.py",
            "benchmarks/benchmark_core_peer_eligibility.py",
        ],
        "static.sbm.output.tone2001": [
            "benchmarks/benchmark_sbm_orientations.py",
            "benchmarks/benchmark_core_peer_eligibility.py",
        ],
    }
    for method_id, locators in direct_benchmarks.items():
        assert methods[method_id]["validation"]["benchmarks"] == locators


def test_every_implemented_public_method_has_a_direct_benchmark() -> None:
    methods = _method_records()
    missing = sorted(
        method_id
        for method_id, record in methods.items()
        if record["status"]["implementation"] == "implemented"
        and record["status"]["api"] == "public"
        and not record["validation"]["benchmarks"]
    )
    assert missing == []


def test_every_benchmark_script_is_referenced_by_a_machine_method() -> None:
    methods = _method_records()
    referenced = {
        locator
        for record in methods.values()
        for locator in record["validation"]["benchmarks"]
    }
    scripts = {
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in (REPOSITORY_ROOT / "benchmarks").glob("benchmark_*.py")
    }
    assert scripts <= referenced


def test_every_machine_benchmark_locator_is_a_present_benchmark_script() -> None:
    methods = _method_records()
    for method_id, record in methods.items():
        for locator in record["validation"]["benchmarks"]:
            path = Path(locator)
            assert path.parent == Path("benchmarks"), (method_id, locator)
            assert path.match("benchmarks/benchmark_*.py"), (method_id, locator)
            assert (REPOSITORY_ROOT / path).is_file(), (method_id, locator)
