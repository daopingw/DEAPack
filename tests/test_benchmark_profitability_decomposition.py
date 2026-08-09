from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = REPOSITORY_ROOT / "benchmarks" / "benchmark_profitability_decomposition.py"
MODULE_SPEC = importlib.util.spec_from_file_location(
    "benchmark_profitability_decomposition",
    BENCHMARK,
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
benchmark = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(benchmark)


@pytest.mark.parametrize("price_scope", ["common", "by_observation"])
def test_profitability_decomposition_benchmark_runs_complete_composition(
    price_scope: str,
) -> None:
    data = benchmark.make_data(4)
    result = benchmark.run_case(
        data,
        benchmark.make_prices(data, price_scope),
        price_scope=price_scope,
    )

    assert result.metadata["compiled_reference_sets"] == 1
    assert result.summary()["decomposition_defined"].all()
    assert set(result.diagnostics["component"]) == {
        "profitability_efficiency",
        "crs_gdf",
        "vrs_gdf",
        "decomposition_identity",
    }


def test_profitability_decomposition_cli_smoke_covers_both_price_scopes() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK),
            "--n-dmus",
            "4",
            "--prices",
            "both",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = completed.stdout
    assert "prices=common " in output
    assert "prices=by_observation " in output
    assert output.count("compiled_reference_sets=1") == 2
