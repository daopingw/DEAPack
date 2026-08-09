from __future__ import annotations

import importlib.util
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from deapack import RAM, AdditiveDEA
from deapack.results import DEAResult

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = REPOSITORY_ROOT / "benchmarks" / "benchmark_classical_foundations.py"
MODULE_SPEC = importlib.util.spec_from_file_location(
    "benchmark_classical_foundations",
    BENCHMARK,
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
benchmark = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(benchmark)


def test_classical_foundations_cli_smoke_runs_every_direct_method() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK),
            "--n-dmus",
            "8",
            "--chunk-size",
            "3",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = completed.stdout
    for method in ("additive", "ram", "ddf", "fdh", "scale"):
        assert f"method={method} " in output
    assert output.count("score_certified=8/8") == 2
    assert output.count("target_certified=8/8") == 2
    assert output.count("peer_certified=8/8") == 2
    assert output.count("dual_certified=8/8") == 2
    assert output.count("primary_solves=8 secondary_solves=0") == 2
    assert output.count("total_solves=8 additional_solves=0") == 2


def test_directional_score_only_benchmark_enforces_its_execution_budget(
    capsys: pytest.CaptureFixture[str],
) -> None:
    benchmark.run_ddf(benchmark.make_data(8), compute_slacks=False)

    output = capsys.readouterr().out
    assert "method=ddf " in output
    assert "full=False" in output
    assert "solver_calls=8" in output
    assert "reference_compilations=1" in output
    assert "max_target_residual=not_computed" in output


def test_classical_target_check_fails_closed_on_a_missing_slack_row() -> None:
    fitted = AdditiveDEA().fit(benchmark.make_data(8))
    corrupted = DEAResult(
        summary_frame=fitted.summary(),
        targets=fitted.targets.copy(),
        slacks=fitted.slacks.iloc[:-1].copy(),
    )

    with pytest.raises(AssertionError, match="target and slack keys must match"):
        benchmark._slack_target_residual(
            corrupted,
            lambda rows: rows["target"],
        )


def _fit_additive_family(method: str) -> DEAResult:
    data = benchmark.make_data(8)
    if method == "additive":
        return AdditiveDEA(reference="global").fit(data)
    return RAM(reference="global").fit(data)


def _validate_additive_family(result: DEAResult, method: str) -> None:
    benchmark._validate_additive_family_release(
        result,
        method=method,
        n_dmus=8,
        measured_solver_calls=8,
        measured_compilations=1,
    )


@pytest.mark.parametrize("method", ["additive", "ram"])
def test_additive_family_benchmark_rejects_a_missing_certificate_field(
    method: str,
) -> None:
    fitted = _fit_additive_family(method)
    diagnostics = fitted.diagnostics.drop(columns=["published_peer_account_certified"])
    corrupted = replace(fitted, diagnostics=diagnostics)

    with pytest.raises(AssertionError, match="missing required fields"):
        _validate_additive_family(corrupted, method)


@pytest.mark.parametrize("method", ["additive", "ram"])
def test_additive_family_benchmark_rejects_a_corrupted_certificate_residual(
    method: str,
) -> None:
    fitted = _fit_additive_family(method)
    diagnostics = fitted.diagnostics.copy()
    diagnostics.loc[diagnostics.index[0], "max_published_economic_violation"] = 1.0
    corrupted = replace(fitted, diagnostics=diagnostics)

    with pytest.raises(
        AssertionError,
        match="max_published_economic_violation exceeds tolerance",
    ):
        _validate_additive_family(corrupted, method)


@pytest.mark.parametrize("method", ["additive", "ram"])
def test_additive_family_benchmark_rejects_a_forged_execution_count(
    method: str,
) -> None:
    fitted = _fit_additive_family(method)
    metadata = dict(fitted.metadata)
    metadata["solver_calls"] = 9
    corrupted = replace(fitted, metadata=metadata)

    with pytest.raises(AssertionError, match="solver_calls mismatch"):
        _validate_additive_family(corrupted, method)


@pytest.mark.parametrize("method", ["additive", "ram"])
def test_additive_family_benchmark_rejects_nonfinite_certificate_evidence(
    method: str,
) -> None:
    fitted = _fit_additive_family(method)
    diagnostics = fitted.diagnostics.copy()
    diagnostics.loc[diagnostics.index[0], "duality_gap"] = pd.NA
    corrupted = replace(fitted, diagnostics=diagnostics)

    with pytest.raises(AssertionError, match="duality_gap must be finite"):
        _validate_additive_family(corrupted, method)
