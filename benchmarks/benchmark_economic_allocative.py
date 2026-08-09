"""Repeatable benchmark for direct and decomposed cost/revenue efficiency.

The score-only direct models solve one LP per observation.  Their matched
technical--allocative decompositions add one radial LP per observation, so the
exact budgets are respectively ``n`` and ``2n`` solves.  One global reference
population is compiled and shared inside each fitted result.

Examples:

    python benchmarks/benchmark_economic_allocative.py --n-dmus 100
    python benchmarks/benchmark_economic_allocative.py --prices by_observation
    python benchmarks/benchmark_economic_allocative.py \
        --objective revenue --mode decomposition
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from types import ModuleType

import numpy as np
import pandas as pd

import deapack.economics.cost as cost_module
import deapack.economics.revenue as revenue_module
import deapack.models.radial as radial_module
from deapack import (
    AllocativeDecomposition,
    CostEfficiency,
    DEAData,
    PriceData,
    RevenueAllocativeDecomposition,
    RevenueEfficiency,
)
from deapack.results import DEAResult
from deapack.solvers import SciPyHiGHSSolver

_OBJECTIVES = ("cost", "revenue")
_MODES = ("direct", "decomposition")


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


def make_data(n_dmus: int) -> DEAData:
    """Create deterministic strictly positive production observations."""
    if n_dmus < 3:
        raise ValueError("n-dmus must be at least three")

    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 5.0, 1.0)
    labor = scale * (8.0 + position % 11.0)
    capital = scale * (12.0 + (3.0 * position) % 13.0)
    energy = scale * (5.0 + (5.0 * position) % 7.0)
    capacity = np.power(labor, 0.40) * np.power(capital, 0.35) * np.power(energy, 0.25)
    management = 0.68 + 0.32 * ((position % 17.0) / 16.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"EA{index:06d}" for index in range(n_dmus)],
            "labor": labor,
            "capital": capital,
            "energy": energy,
            "service_volume": capacity * management,
            "service_quality": (
                capacity * management * (0.55 + (position % 9.0) / 24.0)
            ),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labor", "capital", "energy"),
        outputs=("service_volume", "service_quality"),
    )


def make_prices(data: DEAData, scope: str) -> PriceData:
    """Return common or key-aligned observation-specific positive prices."""
    if scope == "common":
        return PriceData.common(
            input_prices={"labor": 2.0, "capital": 1.4, "energy": 1.1},
            output_prices={"service_volume": 3.2, "service_quality": 2.3},
        )
    if scope != "by_observation":
        raise ValueError("scope must be 'common' or 'by_observation'")

    position = np.arange(data.n_dmus, dtype=np.float64)
    frame = pd.DataFrame(
        {
            "dmu": data.dmu_ids.tolist(),
            "w_labor": 1.8 + 0.02 * position,
            "w_capital": 1.2 + 0.015 * position,
            "w_energy": 0.9 + 0.01 * position,
            "p_volume": 2.8 + 0.025 * position,
            "p_quality": 2.0 + 0.02 * position,
        }
    )
    return PriceData.from_frame(
        frame,
        dmu="dmu",
        input_prices={
            "labor": "w_labor",
            "capital": "w_capital",
            "energy": "w_energy",
        },
        output_prices={
            "service_volume": "p_volume",
            "service_quality": "p_quality",
        },
    )


def _maximum_finite_absolute(frame: pd.DataFrame, column: str) -> float:
    values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    finite = np.abs(values[np.isfinite(values)])
    if finite.size == 0:
        raise AssertionError(f"{column} has no finite benchmark values")
    return float(finite.max())


def _fit_with_compilation_count(
    modules: tuple[ModuleType, ...],
    fit,  # type: ignore[no-untyped-def]
) -> tuple[DEAResult, int]:
    compilations = 0
    originals: list[tuple[ModuleType, object]] = []
    try:
        for module in modules:
            original = module.compile_reference
            originals.append((module, original))

            def module_counted(
                *args,
                _original=original,
                **kwargs,
            ):  # type: ignore[no-untyped-def]
                nonlocal compilations
                compilations += 1
                return _original(*args, **kwargs)

            module.compile_reference = module_counted
        return fit(), compilations
    finally:
        for module, original in originals:
            module.compile_reference = original


def run_case(
    data: DEAData,
    prices: PriceData,
    *,
    objective: str,
    mode: str,
    price_scope: str,
) -> DEAResult:
    """Run one public API and enforce its computational and accounting contract."""
    solver = _CountingSolver()
    if objective == "cost" and mode == "direct":
        model = CostEfficiency(returns_to_scale="vrs", solver=solver)
    elif objective == "cost" and mode == "decomposition":
        model = AllocativeDecomposition(returns_to_scale="vrs", solver=solver)
    elif objective == "revenue" and mode == "direct":
        model = RevenueEfficiency(returns_to_scale="vrs", solver=solver)
    elif objective == "revenue" and mode == "decomposition":
        model = RevenueAllocativeDecomposition(
            returns_to_scale="vrs",
            solver=solver,
        )
    else:
        raise ValueError(f"unsupported case: objective={objective!r}, mode={mode!r}")

    compiler_modules = (
        (cost_module, radial_module)
        if objective == "cost" and mode == "decomposition"
        else (revenue_module, radial_module)
        if objective == "revenue" and mode == "decomposition"
        else (cost_module,)
        if objective == "cost"
        else (revenue_module,)
    )
    started = time.perf_counter()
    result, compilation_calls = _fit_with_compilation_count(
        compiler_modules,
        lambda: model.fit(data, prices),
    )
    elapsed = time.perf_counter() - started

    expected_solves = data.n_dmus * (2 if mode == "decomposition" else 1)
    if solver.calls != expected_solves:
        raise AssertionError(
            f"{objective} {mode} solve budget changed: "
            f"observed={solver.calls}, expected={expected_solves}"
        )
    if result.metadata["solver_calls"] != expected_solves:
        raise AssertionError("result solver-call metadata disagrees with the solver")
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("the global benchmark must compile one reference set")
    if compilation_calls != 1:
        raise AssertionError(
            "the global economic reference must be compiled once and shared; "
            f"observed={compilation_calls}"
        )

    objective_count_key = (
        "cached_economic_objective_vectors"
        if mode == "decomposition"
        else "cached_objective_vectors"
    )
    expected_objectives = 1 if price_scope == "common" else data.n_dmus
    if result.metadata[objective_count_key] != expected_objectives:
        raise AssertionError(
            "economic objective caching changed: "
            f"observed={result.metadata[objective_count_key]}, "
            f"expected={expected_objectives}"
        )

    summary = result.summary()
    if not (summary["solver_status"] == "optimal").all():
        raise AssertionError("every benchmark observation must solve optimally")
    if not summary["score_valid"].astype("boolean").fillna(False).all():
        raise AssertionError("every benchmark score must pass its release contract")
    max_identity_residual = 0.0
    if mode == "decomposition":
        max_identity_residual = _maximum_finite_absolute(
            summary,
            "reconstruction_residual",
        )
        if max_identity_residual > 1e-8:
            raise AssertionError("the allocative decomposition identity failed")

    if mode == "decomposition":
        component = f"{objective}_efficiency"
        economic_diagnostics = result.diagnostics.loc[
            result.diagnostics["component"] == component
        ]
        if len(economic_diagnostics) != data.n_dmus:
            raise AssertionError(
                f"{component} diagnostics must contain one row per observation; "
                f"observed={len(economic_diagnostics)}, expected={data.n_dmus}"
            )
    else:
        economic_diagnostics = result.diagnostics
        for validity_column in ("target_valid", "peer_valid", "dual_valid"):
            if not summary[validity_column].astype("boolean").fillna(False).all():
                raise AssertionError(
                    f"every direct {objective} {validity_column} claim must be valid"
                )
        if result.metadata["additional_solver_calls"] != 0:
            raise AssertionError("postsolve certificates must add zero solver calls")
    for certificate_column in (
        "lp_postsolve_certified",
        "economic_postsolve_certified",
        "postsolve_certified",
    ):
        if not (
            economic_diagnostics[certificate_column]
            .astype("boolean")
            .fillna(False)
            .all()
        ):
            raise AssertionError(
                f"every economic component must pass {certificate_column}"
            )
    max_economic_violation = _maximum_finite_absolute(
        economic_diagnostics,
        "max_economic_violation",
    )
    if max_economic_violation > 1e-8:
        raise AssertionError("the certified economic account failed reconstruction")
    max_objective_residual = _maximum_finite_absolute(
        economic_diagnostics,
        "objective_reconstruction_residual",
    )
    feasibility_column = (
        "maximum_output_commitment_violation"
        if objective == "cost"
        else "maximum_input_capacity_violation"
    )
    max_feasibility_violation = _maximum_finite_absolute(
        economic_diagnostics,
        feasibility_column,
    )
    if max_objective_residual > 1e-8:
        raise AssertionError("target values do not reconstruct the LP objective")
    if max_feasibility_violation > 1e-8:
        raise AssertionError("economic targets violate capacity or commitments")

    print(
        f"objective={objective} mode={mode} prices={price_scope} "
        f"n={data.n_dmus} elapsed={elapsed:.3f}s "
        f"solver_calls={solver.calls}/{expected_solves} "
        f"reference_set_count={result.metadata['compiled_reference_sets']} "
        f"compile_reference_calls={compilation_calls} "
        f"cached_objectives={result.metadata[objective_count_key]} "
        f"max_objective_residual={max_objective_residual:.3e} "
        f"max_feasibility_violation={max_feasibility_violation:.3e} "
        f"max_economic_violation={max_economic_violation:.3e} "
        f"max_identity_residual={max_identity_residual:.3e}"
    )
    return result


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument(
        "--prices",
        choices=("common", "by_observation"),
        default="common",
    )
    parser.add_argument(
        "--objective",
        choices=("cost", "revenue", "both"),
        default="both",
    )
    parser.add_argument(
        "--mode",
        choices=("direct", "decomposition", "all"),
        default="all",
    )
    args = parser.parse_args(argv)

    data = make_data(args.n_dmus)
    prices = make_prices(data, args.prices)
    objectives = _OBJECTIVES if args.objective == "both" else (args.objective,)
    modes = _MODES if args.mode == "all" else (args.mode,)
    for objective in objectives:
        for mode in modes:
            run_case(
                data,
                prices,
                objective=objective,
                mode=mode,
                price_scope=args.prices,
            )


if __name__ == "__main__":
    main()
