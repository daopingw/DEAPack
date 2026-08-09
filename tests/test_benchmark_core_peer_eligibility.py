from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmarks" / "benchmark_core_peer_eligibility.py"


def test_core_peer_eligibility_benchmark_enforces_structural_counts() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK),
            "--n-dmus",
            "24",
            "--eligibility-cohorts",
            "4",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = completed.stdout
    for name in (
        "additive",
        "ram",
        "sbm-non-oriented",
        "sbm-input",
        "sbm-output",
        "ddf-score-only",
    ):
        assert f"model={name} n=24 cohorts=4" in output
    assert output.count("compile_calls=4") == 6
    assert output.count("solver_calls=24") == 6
    assert output.count("effective_edges=144") == 6
    assert "models=6 total_compilations=24 total_solver_calls=144" in output
