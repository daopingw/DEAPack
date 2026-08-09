from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _load_benchmark(name: str) -> ModuleType:
    path = REPOSITORY_ROOT / "benchmarks" / f"benchmark_{name}.py"
    spec = importlib.util.spec_from_file_location(f"benchmark_contract_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_directional_super_benchmark_rejects_source_account_drift() -> None:
    benchmark = _load_benchmark("directional_super_efficiency")
    data = benchmark.make_data(6)
    solver = benchmark._CountingSolver()
    model = benchmark.RayDirectionalSuperEfficiency(solver=solver)
    result = model.fit(data)

    benchmark._assert_benchmark_contract(
        result,
        data=data,
        model=model,
        solver=solver,
    )
    result.diagnostics.loc[0, "source_account_residual"] = 10.0 * model.tolerance

    with pytest.raises(AssertionError, match="source-account residual exceeds"):
        benchmark._assert_benchmark_contract(
            result,
            data=data,
            model=model,
            solver=solver,
        )


def test_environmental_network_benchmark_rejects_uncertified_score() -> None:
    benchmark = _load_benchmark("environmental_network")
    data = benchmark.make_data(6)
    solver = benchmark._SparseCountingSolver()
    model = benchmark.KalhorKazemiMatinNetworkDEA(solver=solver)
    result = model.fit(data)

    benchmark._assert_benchmark_contract(
        result,
        data=data,
        model=model,
        solver=solver,
    )
    result.diagnostics.loc[0, "certification_status"] = "failed"

    with pytest.raises(AssertionError, match="certificate must pass"):
        benchmark._assert_benchmark_contract(
            result,
            data=data,
            model=model,
            solver=solver,
        )


def test_sequential_network_benchmark_rejects_link_shortfall() -> None:
    benchmark = _load_benchmark("network_sequential")
    data = benchmark.make_data(6)
    solver = benchmark._CountingSolver()
    model = benchmark.LewisSextonSequentialNetworkDEA(solver=solver)
    result = model.fit(data)
    expected_programmes = 4 * data.n_dmus

    benchmark._assert_benchmark_contract(
        result,
        data=data,
        model=model,
        solver=solver,
        expected_programmes=expected_programmes,
    )
    link = result.links.loc[0]
    scale = max(
        1.0,
        abs(float(link["observed"])),
        abs(float(link["upstream_supply_target"])),
        abs(float(link["downstream_requirement_target"])),
    )
    result.links.loc[0, "balance_residual"] = -10.0 * model.tolerance * scale

    with pytest.raises(AssertionError, match="link shortfall exceeds"):
        benchmark._assert_benchmark_contract(
            result,
            data=data,
            model=model,
            solver=solver,
            expected_programmes=expected_programmes,
        )


def test_generalized_distance_benchmark_rejects_search_contract_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    benchmark = _load_benchmark("generalized_distance")
    real_model = benchmark.GDF

    class _InvalidGDF:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.delegate = real_model(*args, **kwargs)

        def fit(self, data):  # type: ignore[no-untyped-def]
            result = self.delegate.fit(data)
            result.summary_frame.loc[0, "search_upper_bound"] = 2.0
            result.summary_frame.loc[0, "search_lower_bound"] = 0.0
            result.summary_frame.loc[0, "search_absolute_gap"] = 2.0
            result.summary_frame.loc[0, "search_converged"] = True
            return result

    monkeypatch.setattr(benchmark, "GDF", _InvalidGDF)
    with pytest.raises(AssertionError, match="interval-tolerance contract"):
        benchmark.run_case(
            benchmark.make_data(6),
            alpha=0.5,
            returns_to_scale="crs",
            compute_slacks=False,
            search_tolerance=1e-7,
        )


def test_profitability_benchmark_rejects_ratio_residual(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    benchmark = _load_benchmark("profitability")
    real_model = benchmark.ReturnToDollarEfficiency

    class _InvalidReturnToDollar:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.delegate = real_model(*args, **kwargs)

        def fit(self, data, prices):  # type: ignore[no-untyped-def]
            result = self.delegate.fit(data, prices)
            result.diagnostics.loc[0, "ratio_reconstruction_residual"] = 10.0 * float(
                result.metadata["tolerance"]
            )
            return result

    monkeypatch.setattr(
        benchmark,
        "ReturnToDollarEfficiency",
        _InvalidReturnToDollar,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(benchmark.__file__),
            "--n-dmus",
            "6",
            "--price-scope",
            "common",
            "--returns-to-scale",
            "crs",
        ],
    )

    with pytest.raises(AssertionError, match="ratio reconstruction failed"):
        benchmark.main()
