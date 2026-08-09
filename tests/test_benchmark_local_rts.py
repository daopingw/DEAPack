from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = REPOSITORY_ROOT / "benchmarks" / "benchmark_local_rts.py"
LOCATOR = "benchmarks/benchmark_local_rts.py"
REGISTRY_METHODS = REPOSITORY_ROOT / "specs" / "registry" / "methods" / "analysis"
METHOD_RECORDS = (
    "analysis.returns_to_scale.local.banker_thrall_1992.json",
    "analysis.scale_elasticity.local.radial_vrs.json",
)
MODULE_SPEC = importlib.util.spec_from_file_location("benchmark_local_rts", BENCHMARK)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
benchmark = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = benchmark
MODULE_SPEC.loader.exec_module(benchmark)


def test_local_scale_registry_records_use_the_direct_benchmark() -> None:
    for filename in METHOD_RECORDS:
        with (REGISTRY_METHODS / filename).open(encoding="utf-8") as stream:
            record = json.load(stream)
        assert record["validation"]["benchmarks"] == [LOCATOR]


@pytest.mark.parametrize("operator", ["local-rts", "scale-elasticity"])
@pytest.mark.parametrize("orientation", ["input", "output"])
def test_local_scale_benchmark_enforces_complete_certified_task_graph(
    operator: str,
    orientation: str,
) -> None:
    result, observation = benchmark._fit_with_counts(
        4,
        orientation=orientation,
        operator=operator,
    )
    benchmark._validate_result(
        result,
        observation,
        n_dmus=4,
        operator=operator,
    )

    assert observation.solver_calls == 16
    assert observation.projection_reference_compilations == 1
    assert observation.support_reference_compilations == 1
    assert observation.phase_one_template_compilations == 1
    assert result.metadata["additional_solver_calls"] == 0
    assert result.summary()["analysis_valid"].all()


def test_local_rts_benchmark_fails_closed_on_missing_finite_lp_certificate() -> None:
    result, observation = benchmark._fit_with_counts(
        4,
        orientation="input",
        operator="local-rts",
    )
    result.summary_frame.drop(
        columns="support_intercept_lower_lp_postsolve_certified",
        inplace=True,
    )

    with pytest.raises(AssertionError, match="missing certificate columns"):
        benchmark._validate_result(
            result,
            observation,
            n_dmus=4,
            operator="local-rts",
        )


def test_scale_elasticity_benchmark_fails_closed_on_missing_transform_certificate() -> (
    None
):
    result, observation = benchmark._fit_with_counts(
        4,
        orientation="output",
        operator="scale-elasticity",
    )
    result.summary_frame.loc[0, "scale_elasticity_valid"] = False

    with pytest.raises(AssertionError, match="scale-elasticity summary failed"):
        benchmark._validate_result(
            result,
            observation,
            n_dmus=4,
            operator="scale-elasticity",
        )


@pytest.mark.parametrize("operator", ["local-rts", "scale-elasticity"])
def test_local_scale_cli_smoke_preserves_both_orientation_interface(
    operator: str,
) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK),
            "--operator",
            operator,
            "--orientation",
            "both",
            "--n-dmus",
            "4",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout.count(f"operator={operator} ") == 2
    assert "orientation=input" in completed.stdout
    assert "orientation=output" in completed.stdout
    assert completed.stdout.count("certified=4/4") == 2
    assert completed.stdout.count("solver_calls=16") == 2
    assert completed.stdout.count("additional_solves=0") == 2
