"""Repeatable benchmark for the complete GDF profitability decomposition.

The public operator jointly fits the closed-form return-to-dollar benchmark,
the exact CRS Chavas--Cox GDF reduction, and the interior-alpha VRS GDF
feasibility search. This script audits the complete composition rather than
running its constituents separately.

Examples:

    python benchmarks/benchmark_profitability_decomposition.py
    python benchmarks/benchmark_profitability_decomposition.py \
        --n-dmus 100 --prices common
    python benchmarks/benchmark_profitability_decomposition.py \
        --n-dmus 100 --prices by_observation
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence

import numpy as np
import pandas as pd

import deapack.models.generalized_distance as gdf_module
from deapack import (
    DEAData,
    GDFProfitabilityDecomposition,
    PriceData,
    SolverOptions,
)
from deapack.results import DEAResult
from deapack.solvers import SciPyHiGHSSolver

_PRICE_SCOPES = ("common", "by_observation")
_GDF_COMPONENTS = ("crs_gdf", "vrs_gdf")


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver(
            SolverOptions(
                primal_feasibility_tolerance=1e-8,
                dual_feasibility_tolerance=1e-8,
            )
        )

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


def make_data(n_dmus: int) -> DEAData:
    """Create deterministic strictly positive quantities."""
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
            "dmu": [f"PD{index:06d}" for index in range(n_dmus)],
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
    """Create common or key-aligned observation-specific positive prices."""
    if scope == "common":
        return PriceData.common(
            input_prices={"labor": 2.0, "capital": 1.4, "energy": 1.1},
            output_prices={"service_volume": 3.2, "service_quality": 2.3},
        )
    if scope != "by_observation":
        raise ValueError("scope must be 'common' or 'by_observation'")

    position = np.arange(data.n_dmus, dtype=np.float64)
    price_frame = pd.DataFrame(
        {
            "dmu": data.dmu_ids[::-1],
            "w_labor": 1.8 + 0.020 * position[::-1],
            "w_capital": 1.2 + 0.015 * position[::-1],
            "w_energy": 0.9 + 0.010 * position[::-1],
            "p_volume": 2.8 + 0.025 * position[::-1],
            "p_quality": 2.0 + 0.020 * position[::-1],
        }
    )
    return PriceData.from_frame(
        price_frame,
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


def run_case(
    data: DEAData,
    prices: PriceData,
    *,
    price_scope: str,
) -> DEAResult:
    """Run the complete public composition and enforce its execution contract."""
    solver = _CountingSolver()
    compilation_calls = 0
    original_compile = gdf_module.compile_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compilation_calls
        compilation_calls += 1
        return original_compile(*args, **kwargs)

    gdf_module.compile_reference = counted_compile
    try:
        started = time.perf_counter()
        result = GDFProfitabilityDecomposition(
            alpha=0.5,
            solver=solver,
            compute_slacks=True,
        ).fit(data, prices)
        elapsed = time.perf_counter() - started
    finally:
        gdf_module.compile_reference = original_compile

    summary = result.summary()
    component_statuses = (
        "profitability_solver_status",
        "crs_solver_status",
        "vrs_solver_status",
        "solver_status",
    )
    for column in component_statuses:
        if not (summary[column] == "optimal").all():
            raise AssertionError(f"component status failed: {column}")
    if not summary["decomposition_defined"].all():
        raise AssertionError("every matched decomposition must be defined")
    if not (summary["crs_target_status"] == "defined").all():
        raise AssertionError("every CRS strong target must resolve")
    if not (summary["vrs_target_status"] == "defined").all():
        raise AssertionError("every VRS strong target must resolve")

    profitability = summary["profitability_efficiency"].to_numpy(dtype=float)
    crs_technical = summary["crs_technical_efficiency"].to_numpy(dtype=float)
    vrs_technical = summary["vrs_technical_efficiency"].to_numpy(dtype=float)
    scale = summary["scale_efficiency"].to_numpy(dtype=float)
    allocative = summary["allocative_efficiency"].to_numpy(dtype=float)
    crs_identity = profitability - crs_technical * allocative
    vrs_identity = profitability - vrs_technical * scale * allocative
    scale_identity = scale - crs_technical / vrs_technical
    max_crs_identity = float(np.abs(crs_identity).max(initial=0.0))
    max_vrs_identity = float(np.abs(vrs_identity).max(initial=0.0))
    max_scale_identity = float(np.abs(scale_identity).max(initial=0.0))
    max_reported_crs = _maximum_finite_absolute(
        summary,
        "crs_reconstruction_residual",
    )
    max_reported_vrs = _maximum_finite_absolute(
        summary,
        "vrs_reconstruction_residual",
    )
    max_ordering_residual = _maximum_finite_absolute(
        summary,
        "crs_vrs_ordering_residual",
    )
    if (
        max(
            max_crs_identity,
            max_vrs_identity,
            max_scale_identity,
            max_reported_crs,
            max_reported_vrs,
            max_ordering_residual,
        )
        > 1e-8
    ):
        raise AssertionError("a profitability decomposition identity failed")

    diagnostics = result.diagnostics
    gdf_diagnostics = diagnostics.loc[diagnostics["component"].isin(_GDF_COMPONENTS)]
    phase_one = gdf_diagnostics.loc[gdf_diagnostics["phase"] == 1]
    phase_two = gdf_diagnostics.loc[gdf_diagnostics["phase"] == 2]
    feasibility_solves = int(
        pd.to_numeric(phase_one["feasibility_solves"], errors="raise").sum()
    )
    target_solves = len(phase_two)
    accounted_solver_calls = feasibility_solves + target_solves
    if solver.calls != accounted_solver_calls:
        raise AssertionError(
            "GDF diagnostic solve accounting disagrees with the counting solver: "
            f"calls={solver.calls}, accounted={accounted_solver_calls}"
        )
    if target_solves != 2 * data.n_dmus:
        raise AssertionError("CRS and VRS must each complete one target per DMU")

    crs_phase_one = phase_one.loc[phase_one["component"] == "crs_gdf"]
    vrs_phase_one = phase_one.loc[phase_one["component"] == "vrs_gdf"]
    crs_feasibility_solves = int(crs_phase_one["feasibility_solves"].sum())
    vrs_feasibility_solves = int(vrs_phase_one["feasibility_solves"].sum())
    if crs_feasibility_solves != data.n_dmus:
        raise AssertionError("the exact CRS reduction must use one LP per DMU")
    if set(crs_phase_one["solver_strategy"]) != {"exact_crs_input_radial_transform"}:
        raise AssertionError("the CRS component left its exact reduction")
    if set(vrs_phase_one["solver_strategy"]) != {"monotone_lp_feasibility_bisection"}:
        raise AssertionError("the VRS component left its feasibility-search path")
    if vrs_feasibility_solves <= data.n_dmus:
        raise AssertionError("the interior-alpha VRS search was not exercised")

    if compilation_calls != 1:
        raise AssertionError(
            "CRS and VRS components must reuse one compiled global reference"
        )
    if result.metadata["compiled_reference_sets"] != compilation_calls:
        raise AssertionError(
            "compiled-reference metadata disagrees with instrumentation"
        )

    profitability_diagnostics = diagnostics.loc[
        diagnostics["component"] == "profitability_efficiency"
    ]
    kernel_calls = int(
        (~profitability_diagnostics["solution_reused"].astype(bool)).sum()
    )
    expected_kernel_calls = 1 if price_scope == "common" else data.n_dmus
    if kernel_calls != expected_kernel_calls:
        raise AssertionError(
            "price-valued profitability cache contract changed: "
            f"observed={kernel_calls}, expected={expected_kernel_calls}"
        )

    max_primal_violation = _maximum_finite_absolute(
        gdf_diagnostics,
        "max_primal_violation",
    )
    max_ratio_residual = _maximum_finite_absolute(
        profitability_diagnostics,
        "ratio_reconstruction_residual",
    )
    if max_primal_violation > 1e-7 or max_ratio_residual > 1e-8:
        raise AssertionError("a component feasibility or value residual failed")

    print(
        f"prices={price_scope} n={data.n_dmus} elapsed={elapsed:.3f}s "
        f"solver_calls={solver.calls} "
        f"crs_feasibility_solves={crs_feasibility_solves} "
        f"vrs_feasibility_solves={vrs_feasibility_solves} "
        f"target_solves={target_solves} "
        f"compiled_reference_sets={compilation_calls} "
        f"profitability_kernel_calls={kernel_calls} "
        f"max_crs_identity_residual={max_crs_identity:.3e} "
        f"max_vrs_identity_residual={max_vrs_identity:.3e} "
        f"max_scale_identity_residual={max_scale_identity:.3e} "
        f"max_primal_violation={max_primal_violation:.3e} "
        f"max_ratio_residual={max_ratio_residual:.3e}"
    )
    return result


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument(
        "--prices",
        choices=(*_PRICE_SCOPES, "both"),
        default="both",
    )
    arguments = parser.parse_args(argv)

    data = make_data(arguments.n_dmus)
    scopes = _PRICE_SCOPES if arguments.prices == "both" else (arguments.prices,)
    for scope in scopes:
        run_case(
            data,
            make_prices(data, scope),
            price_scope=scope,
        )


if __name__ == "__main__":
    main()
