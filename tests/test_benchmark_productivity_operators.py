from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = REPOSITORY_ROOT / "benchmarks" / "benchmark_productivity_operators.py"
LOCATOR = "benchmarks/benchmark_productivity_operators.py"
METHOD_RECORDS = (
    "productivity/productivity.malmquist_luenberger.aparicio_pastor_zofio_2013.json",
    "productivity/productivity.malmquist.adjacent_geometric.json",
    "productivity/productivity.malmquist.decomposition.fgnz_pure_scale_extension.json",
    "productivity/productivity.malmquist.decomposition.ray_desli.json",
    "productivity/productivity.global_malmquist.json",
    "productivity/productivity.biennial_malmquist.json",
    "productivity/productivity.luenberger.json",
)
MODULE_SPEC = importlib.util.spec_from_file_location(
    "benchmark_productivity_operators",
    BENCHMARK,
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
benchmark = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(benchmark)


def test_productivity_benchmark_has_seven_direct_locators() -> None:
    registry_methods = REPOSITORY_ROOT / "specs" / "registry" / "methods"
    for relative in METHOD_RECORDS:
        with (registry_methods / relative).open(encoding="utf-8") as stream:
            record = json.load(stream)
        assert record["validation"]["benchmarks"] == [LOCATOR]


@pytest.mark.parametrize(
    ("operator", "expected_unique"),
    [
        ("malmquist", 30),
        ("apz", 30),
        ("fgnz_enhanced", 42),
        ("ray_desli", 60),
        ("global", 24),
        ("biennial", 30),
        ("luenberger", 30),
    ],
)
def test_productivity_benchmark_enforces_real_task_graph(
    operator: str,
    expected_unique: int,
) -> None:
    data = benchmark.make_panel(
        3,
        periods=4,
        ray_desli=operator == "ray_desli",
        environmental=operator == "apz",
    )
    result = benchmark.run_case(data, operator=operator)

    assert len(result.summary()) == 9
    expected_diagnostics = {
        "fgnz_enhanced": 54,
        "ray_desli": 72,
    }.get(operator, 36)
    assert len(result.diagnostics) == expected_diagnostics
    assert result.metadata["unique_distance_solves"] == expected_unique


def test_global_all_pairs_benchmark_keeps_linear_solve_graph() -> None:
    data = benchmark.make_panel(3, periods=4)
    adjacent = benchmark.run_case(
        data,
        operator="global",
        comparison_pairs="adjacent",
    )
    all_pairs = benchmark.run_case(
        data,
        operator="global",
        comparison_pairs="all",
    )

    assert len(adjacent.summary()) == 3 * (4 - 1)
    assert len(all_pairs.summary()) == 3 * 4 * (4 - 1) // 2
    assert adjacent.metadata["unique_distance_solves"] == 2 * 3 * 4
    assert (
        all_pairs.metadata["unique_distance_solves"]
        == (adjacent.metadata["unique_distance_solves"])
    )
    assert all_pairs.metadata["requested_distance_tasks"] == (
        4 * len(all_pairs.summary())
    )
    assert all_pairs.metadata["comparison_output_size_complexity"] == "O(D*P^2)"
    assert all_pairs.metadata["additional_solver_calls"] == 0


def test_productivity_operators_cli_smoke_covers_all_public_paths() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK),
            "--operator",
            "all",
            "--n-dmus",
            "3",
            "--periods",
            "4",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = completed.stdout
    for operator in benchmark._OPERATORS:
        assert f"operator={operator} " in output
    assert output.count("requested_distance_tasks=36") == 5
    assert output.count("requested_distance_tasks=54") == 1
    assert output.count("requested_distance_tasks=72") == 1
    assert output.count("certified_multiplicative_accounts=9") == 3
