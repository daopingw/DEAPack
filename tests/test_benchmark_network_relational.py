from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = REPOSITORY_ROOT / "benchmarks" / "benchmark_network_relational.py"
LOCATOR = "benchmarks/benchmark_network_relational.py"
METHOD_RECORD = (
    REPOSITORY_ROOT
    / "specs"
    / "registry"
    / "methods"
    / "network"
    / "network.relational.kao_hwang_2008.json"
)
MODULE_SPEC = importlib.util.spec_from_file_location(
    "benchmark_network_relational",
    BENCHMARK,
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
benchmark = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = benchmark
MODULE_SPEC.loader.exec_module(benchmark)


def test_relational_benchmark_has_direct_registry_locator() -> None:
    with METHOD_RECORD.open(encoding="utf-8") as stream:
        record = json.load(stream)
    assert record["validation"]["benchmarks"] == [LOCATOR]


@pytest.mark.parametrize(
    ("decomposition", "projection", "secondary_per_dmu"),
    [
        ("none", "none", 0),
        ("maximize_stage_1", "source_midpoint", 1),
        ("maximize_stage_2", "source_midpoint", 1),
        ("bounds", "source_midpoint", 2),
    ],
)
def test_relational_benchmark_enforces_certificate_and_solve_graph(
    decomposition: str,
    projection: str,
    secondary_per_dmu: int,
) -> None:
    observation = benchmark.run_case(
        4,
        decomposition=decomposition,
        projection=projection,
    )

    assert observation.compile_calls == 1
    assert observation.primary_solves == 4
    assert observation.secondary_solves == secondary_per_dmu * 4
    assert observation.projection_fallback_solves == 0
    assert observation.solver_calls == 4 + secondary_per_dmu * 4
    assert observation.max_lp_violation <= 1.0e-7
    assert observation.max_raw_economic_violation <= 1.0e-7
    assert observation.max_published_economic_violation <= 1.0e-7


@pytest.mark.parametrize(
    "corruption",
    ["missing_summary_validity", "missing_diagnostic_certificate", "missing_count"],
)
def test_relational_benchmark_fails_closed_on_missing_trust_fields(
    corruption: str,
) -> None:
    result, observation = benchmark._fit_with_counts(
        3,
        decomposition="maximize_stage_1",
        projection="source_midpoint",
    )
    if corruption == "missing_summary_validity":
        corrupted = replace(
            result,
            summary_frame=result.summary().drop(columns=["score_valid"]),
        )
        message = "summary is missing required fields"
    elif corruption == "missing_diagnostic_certificate":
        corrupted = replace(
            result,
            diagnostics=result.diagnostics.drop(
                columns=["raw_economic_postsolve_certified"]
            ),
        )
        message = "multiplier diagnostics is missing required fields"
    else:
        metadata = dict(result.metadata)
        metadata.pop("additional_solver_calls")
        corrupted = replace(result, metadata=metadata)
        message = "metadata is missing required fields"

    with pytest.raises(AssertionError, match=message):
        benchmark._validate_result(
            corrupted,
            observation,
            n_dmus=3,
            decomposition="maximize_stage_1",
            projection="source_midpoint",
        )


def test_relational_benchmark_rejects_false_optimal_certificate() -> None:
    result, observation = benchmark._fit_with_counts(
        3,
        decomposition="maximize_stage_1",
        projection="source_midpoint",
    )
    diagnostics = result.diagnostics.copy()
    selected = diagnostics["phase"].eq("system")
    diagnostics.loc[selected, "postsolve_certified"] = False
    corrupted = replace(result, diagnostics=diagnostics)

    with pytest.raises(AssertionError, match="postsolve_certified"):
        benchmark._validate_result(
            corrupted,
            observation,
            n_dmus=3,
            decomposition="maximize_stage_1",
            projection="source_midpoint",
        )


def test_relational_benchmark_cli_covers_full_and_score_only_paths() -> None:
    cases = (
        ("maximize_stage_1", "source_midpoint", "score_certified=4/4"),
        ("none", "none", "decomposition_certified=0/4"),
    )
    for decomposition, projection, expected in cases:
        completed = subprocess.run(
            [
                sys.executable,
                str(BENCHMARK),
                "--n-dmus",
                "4",
                "--decomposition",
                decomposition,
                "--projection",
                projection,
            ],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        output = completed.stdout
        assert expected in output
        assert "compiled_reference_sets=1" in output
        assert "projection_fallback_solves=0" in output
        assert "additional_solves=0" in output
