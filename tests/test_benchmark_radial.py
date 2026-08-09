from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = REPOSITORY_ROOT / "benchmarks" / "benchmark_radial.py"


def test_radial_benchmark_enforces_template_and_solver_counts() -> None:
    completed = subprocess.run(
        [sys.executable, str(BENCHMARK), "--n-dmus", "12"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = completed.stdout
    assert "optimal=12/12" in output
    assert "solver_calls=12" in output
    assert "reference_compilations=1" in output
    assert "phase_one_template_compilations=1" in output
    assert "phase_one_bindings=12" in output
    assert "ordinary_statistic_compilations=1" in output
    assert "absolute_statistic_compilations=0" in output
    for metric in (
        "reference_compile_seconds=",
        "template_compile_seconds=",
        "phase_one_binding_seconds=",
        "solver_seconds=",
        "other_seconds=",
        "max_constraint_nonzeros=",
    ):
        assert metric in output
