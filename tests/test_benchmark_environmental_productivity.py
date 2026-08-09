from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = REPOSITORY_ROOT / "benchmarks" / "benchmark_environmental_productivity.py"
LOCATOR = "benchmarks/benchmark_environmental_productivity.py"
METHOD_RECORDS = (
    "productivity/productivity.malmquist_luenberger.chung_fare_grosskopf_1997.json",
    "productivity/productivity.global_malmquist_luenberger.oh_2010.json",
)
MODULE_SPEC = importlib.util.spec_from_file_location(
    "benchmark_environmental_productivity",
    BENCHMARK,
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
benchmark = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(benchmark)


def test_environmental_productivity_benchmark_has_two_direct_locators() -> None:
    registry_methods = REPOSITORY_ROOT / "specs" / "registry" / "methods"
    for relative in METHOD_RECORDS:
        with (registry_methods / relative).open(encoding="utf-8") as stream:
            record = json.load(stream)
        assert record["validation"]["benchmarks"] == [LOCATOR]


def test_environmental_productivity_cli_smoke_runs_both_source_presets() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK),
            "--n-dmus",
            "4",
            "--periods",
            "4",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = completed.stdout
    for operator in ("ml", "gml"):
        assert f"operator={operator} " in output


def test_gml_all_pairs_benchmark_keeps_linear_solve_graph() -> None:
    data = benchmark.make_panel(4, periods=4)
    adjacent = benchmark.run_case(
        data,
        operator="gml",
        n_organizations=4,
        periods=4,
        comparison_pairs="adjacent",
    )
    all_pairs = benchmark.run_case(
        data,
        operator="gml",
        n_organizations=4,
        periods=4,
        comparison_pairs="all",
    )

    assert len(adjacent.summary()) == 4 * (4 - 1)
    assert len(all_pairs.summary()) == 4 * 4 * (4 - 1) // 2
    assert adjacent.metadata["unique_distance_solves"] == 2 * 4 * 4
    assert (
        all_pairs.metadata["unique_distance_solves"]
        == (adjacent.metadata["unique_distance_solves"])
    )
    assert all_pairs.metadata["requested_distance_tasks"] == (
        4 * len(all_pairs.summary())
    )
    assert all_pairs.metadata["comparison_output_size_complexity"] == "O(D*P^2)"
    assert all_pairs.metadata["additional_solver_calls"] == 0
