from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmarks" / "benchmark_ebm.py"
SPECIFICATION = importlib.util.spec_from_file_location("benchmark_ebm", BENCHMARK)
assert SPECIFICATION is not None and SPECIFICATION.loader is not None
benchmark = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(benchmark)


def test_ebm_benchmark_enforces_one_compile_and_one_solve_per_dmu() -> None:
    compilations, solves = benchmark.run_case(8)

    assert compilations == 1
    assert solves == 8


def test_ebm_benchmark_cli_smoke() -> None:
    completed = subprocess.run(
        [sys.executable, str(BENCHMARK), "--n-dmus", "8"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "compile_reference_calls=1" in completed.stdout
    assert "solver_calls=8/8" in completed.stdout
    assert "secondary_solver_calls=0" in completed.stdout
