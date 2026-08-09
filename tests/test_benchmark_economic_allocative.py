from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = REPOSITORY_ROOT / "benchmarks" / "benchmark_economic_allocative.py"
MODULE_SPEC = importlib.util.spec_from_file_location(
    "benchmark_economic_allocative",
    BENCHMARK,
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
benchmark = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(benchmark)


def test_economic_benchmark_rejects_missing_finite_diagnostics() -> None:
    with pytest.raises(AssertionError, match="no finite benchmark values"):
        benchmark._maximum_finite_absolute(
            pd.DataFrame({"residual": [np.nan, np.nan]}),
            "residual",
        )


@pytest.mark.parametrize("price_scope", ["common", "by_observation"])
@pytest.mark.parametrize("objective", ["cost", "revenue"])
@pytest.mark.parametrize("mode", ["direct", "decomposition"])
def test_economic_benchmark_enforces_solve_and_cache_contracts(
    price_scope: str,
    objective: str,
    mode: str,
) -> None:
    data = benchmark.make_data(5)
    result = benchmark.run_case(
        data,
        benchmark.make_prices(data, price_scope),
        objective=objective,
        mode=mode,
        price_scope=price_scope,
    )

    expected_component = f"{objective}_efficiency"
    if mode == "decomposition":
        technical_component = (
            "input_radial_efficiency"
            if objective == "cost"
            else "output_radial_efficiency"
        )
        assert result.metadata["component_solver_calls"] == {
            expected_component: data.n_dmus,
            technical_component: data.n_dmus,
        }
        assert result.metadata["solver_calls"] == 2 * data.n_dmus
    else:
        assert result.metadata["solver_calls"] == data.n_dmus


def test_economic_allocative_cli_smoke_covers_all_public_paths() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK),
            "--n-dmus",
            "4",
            "--prices",
            "by_observation",
            "--objective",
            "both",
            "--mode",
            "all",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = completed.stdout
    for objective in ("cost", "revenue"):
        for mode in ("direct", "decomposition"):
            assert f"objective={objective} mode={mode} prices=by_observation" in output
