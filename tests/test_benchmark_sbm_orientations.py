from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = REPOSITORY_ROOT / "benchmarks" / "benchmark_sbm_orientations.py"
MODULE_SPEC = importlib.util.spec_from_file_location(
    "benchmark_sbm_orientations",
    BENCHMARK,
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
benchmark = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(benchmark)


def test_sbm_orientation_benchmark_enforces_each_execution_budget(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for orientation in ("input", "output", "non-oriented"):
        benchmark.run_case(8, orientation)

    output = capsys.readouterr().out
    for orientation in ("input", "output", "non-oriented"):
        assert f"orientation={orientation} " in output
    assert output.count("optimal=8/8") == 3
    assert output.count("compile_calls=1") == 3
    assert output.count("primary_solves=8") == 3
    assert output.count("max_target_residual=0.000e+00") == 3


def test_sbm_orientation_benchmark_cli_smoke() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK),
            "--n-dmus",
            "8",
            "--orientation",
            "input",
            "output",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "orientation=input " in completed.stdout
    assert "orientation=output " in completed.stdout
