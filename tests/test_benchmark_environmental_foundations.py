from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = REPOSITORY_ROOT / "benchmarks" / "benchmark_environmental_foundations.py"
REGISTRY_METHODS = REPOSITORY_ROOT / "specs" / "registry" / "methods" / "environmental"
MODULE_SPEC = importlib.util.spec_from_file_location(
    "benchmark_environmental_foundations",
    BENCHMARK,
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
benchmark = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(benchmark)


def test_environmental_fixtures_do_not_repeat_exact_production_rows() -> None:
    environmental = benchmark.make_environmental_data(12)
    environmental_rows = np.column_stack(
        [
            environmental.inputs,
            environmental.outputs,
            environmental.bad_outputs,
        ]
    )
    material, _ = benchmark.make_material_data(12)
    material_rows = np.column_stack([material.inputs, material.outputs])
    nonseparable = benchmark.make_nonseparable_sbm_data(12)
    nonseparable_rows = np.column_stack(
        [
            nonseparable.inputs,
            nonseparable.outputs,
            nonseparable.bad_outputs,
        ]
    )

    assert np.unique(environmental_rows, axis=0).shape[0] == 12
    assert np.unique(material_rows, axis=0).shape[0] == 12
    assert np.unique(nonseparable_rows, axis=0).shape[0] == 12


def test_environmental_benchmark_rejects_missing_finite_diagnostics() -> None:
    with pytest.raises(AssertionError, match="no finite benchmark values"):
        benchmark._maximum_finite_absolute(
            pd.DataFrame({"residual": [np.nan, np.nan]}),
            "residual",
        )


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    assert isinstance(value, dict)
    return value


@pytest.mark.parametrize("method_id", benchmark.METHOD_IDS)
def test_each_environmental_benchmark_calls_its_named_public_method(
    method_id: str,
) -> None:
    result = benchmark.run_case(method_id, 3)

    assert result.metadata["method_id"] == method_id
    assert result.metadata["compiled_reference_sets"] == 1
    assert (result.summary()["solver_status"] == "optimal").all()


def test_cfg_benchmark_covers_full_two_phase_execution_account() -> None:
    result = benchmark.run_case(
        "environmental.ddf.output.chung_fare_grosskopf_1997",
        3,
        compute_slacks=True,
    )

    assert result.metadata["phase_one_solver_calls"] == 3
    assert result.metadata["phase_two_solver_calls"] == 3
    assert result.metadata["solver_calls"] == 6
    assert set(result.diagnostics["phase"]) == {1, 2}


@pytest.mark.parametrize(
    "method_id",
    (
        "environmental.ddf.joint_production",
        "environmental.ddf.output.chung_fare_grosskopf_1997",
        "environmental.ddf.weak_disposal.common_factor",
        "environmental.sbm.separable_strong",
    ),
)
def test_environmental_peer_eligibility_benchmark_deduplicates_populations(
    method_id: str,
) -> None:
    result = benchmark.run_peer_eligibility_case(method_id, 8, 4)

    assert result.metadata["compiled_reference_sets"] == 4
    assert result.metadata["solver_calls"] == 8
    assert result.metadata["peer_eligibility"]["effective_unique_reference_sets"] == 4


@pytest.mark.parametrize(
    ("method_id", "compute_slacks"),
    [
        ("environmental.ddf.weak_disposal.activity_specific", True),
        ("environmental.sbm.separable_strong", False),
    ],
)
def test_strengthened_part_three_benchmarks_require_all_public_claims(
    method_id: str,
    compute_slacks: bool,
) -> None:
    result = benchmark.run_case(
        method_id,
        3,
        compute_slacks=compute_slacks,
    )

    summary = result.summary()
    for validity_column in (
        "score_valid",
        "target_valid",
        "peer_valid",
        "dual_valid",
    ):
        assert summary[validity_column].fillna(False).all()
    assert summary["is_within_reference_technology"].fillna(False).all()
    assert not result.targets.empty
    assert not result.intensities.empty
    assert not result.duals.empty


def test_environmental_foundation_registry_locators_are_direct() -> None:
    expected = ["benchmarks/benchmark_environmental_foundations.py"]
    for method_id in benchmark.METHOD_IDS:
        record = _load_json(REGISTRY_METHODS / f"{method_id}.json")
        assert record["id"] == method_id
        assert record["validation"]["benchmarks"] == expected


def test_environmental_foundations_cli_all_smoke() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK),
            "--n-dmus",
            "3",
            "--method",
            "all",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    for method_id in benchmark.METHOD_IDS:
        assert f"method={method_id} " in completed.stdout
