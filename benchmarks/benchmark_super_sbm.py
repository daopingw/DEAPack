"""Repeatable benchmark for Tone's slacks-based super-efficiency measure.

The benchmark uses the source-qualified non-oriented CRS formulation on
strictly positive data.  Every observation first receives one ordinary SBM
screening LP.  Only strongly SBM-efficient observations then receive one
leave-one-out super-SBM LP.

Run the development baseline with:

    python benchmarks/benchmark_super_sbm.py --n-dmus 200
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

import deapack.evaluation.super_sbm as super_sbm_module
import deapack.models.sbm as sbm_module
from deapack import DEAData, ToneSuperSBM
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.screening_calls = 0
        self.super_calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        if problem.name.startswith("super_sbm_peer_replacement:"):
            self.super_calls += 1
        else:
            self.screening_calls += 1
        return self._delegate.solve(problem)


def make_data(n_dmus: int) -> DEAData:
    """Create deterministic positive data with three inputs and two outputs."""

    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")

    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 6.0, 1.0)
    labor = scale * (9.0 + position % 17.0)
    capital = scale * (14.0 + (3.0 * position) % 19.0)
    energy = scale * (6.0 + (5.0 * position) % 13.0)
    capacity = np.power(labor, 0.35) * np.power(capital, 0.40) * np.power(energy, 0.25)
    management = 0.72 + 0.28 * ((position % 37.0) / 36.0)

    frame = pd.DataFrame(
        {
            "dmu": [f"SS{index:06d}" for index in range(n_dmus)],
            "labor": labor,
            "capital": capital,
            "energy": energy,
            "service_volume": (
                capacity * management * (0.88 + (position % 11.0) / 50.0)
            ),
            "service_quality": (
                capacity * management * (0.52 + ((7.0 * position) % 17.0) / 60.0)
            ),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labor", "capital", "energy"),
        outputs=("service_volume", "service_quality"),
    )


def _maximum_finite_absolute(
    frame: pd.DataFrame,
    columns: tuple[str, ...],
) -> float:
    values = frame.loc[:, list(columns)].apply(pd.to_numeric).to_numpy(dtype=float)
    finite = np.abs(values[np.isfinite(values)])
    return float(finite.max(initial=0.0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=200)
    args = parser.parse_args()

    data = make_data(args.n_dmus)
    solver = _CountingSolver()
    screening_compilations = 0
    super_compilations = 0
    original_screen_compile = sbm_module.compile_reference
    original_super_compile = super_sbm_module.compile_reference

    def counted_screen_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal screening_compilations
        screening_compilations += 1
        return original_screen_compile(*args, **kwargs)

    def counted_super_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal super_compilations
        super_compilations += 1
        return original_super_compile(*args, **kwargs)

    sbm_module.compile_reference = counted_screen_compile
    super_sbm_module.compile_reference = counted_super_compile
    try:
        started = time.perf_counter()
        result = ToneSuperSBM(
            orientation="non-oriented",
            returns_to_scale="crs",
            reference="global",
            solver=solver,
        ).fit(data)
        elapsed = time.perf_counter() - started
    finally:
        sbm_module.compile_reference = original_screen_compile
        super_sbm_module.compile_reference = original_super_compile

    summary = result.summary()
    diagnostics = result.diagnostics
    eligible = int(result.metadata["eligible_observations"])
    expected_calls = data.n_dmus + eligible
    if eligible <= 0:
        raise AssertionError("the benchmark must exercise at least one super-SBM LP")
    if solver.screening_calls != data.n_dmus:
        raise AssertionError(
            "ordinary SBM screening must solve one LP per observation; "
            f"observed={solver.screening_calls}, expected={data.n_dmus}"
        )
    if solver.super_calls != eligible:
        raise AssertionError(
            "eligible observations must receive one super-SBM LP; "
            f"observed={solver.super_calls}, expected={eligible}"
        )
    if solver.calls != expected_calls:
        raise AssertionError(
            "Tone super-SBM must use n + eligible LP solves; "
            f"observed={solver.calls}, expected={expected_calls}"
        )
    if result.metadata["solver_calls"] != expected_calls:
        raise AssertionError("result metadata does not match counted solver calls")
    if result.metadata["screening_solves"] != data.n_dmus:
        raise AssertionError("screening solve metadata does not match the population")
    if result.metadata["super_solves"] != eligible:
        raise AssertionError("super solve metadata does not match eligibility")

    base_reference_sets = int(result.metadata["base_reference_sets"])
    if screening_compilations != base_reference_sets:
        raise AssertionError(
            "ordinary SBM must compile each base reference set once; "
            f"observed={screening_compilations}, expected={base_reference_sets}"
        )
    if super_compilations != eligible:
        raise AssertionError(
            "each eligible observation must compile one self-excluded reference; "
            f"observed={super_compilations}, expected={eligible}"
        )
    eligible_summary = summary.loc[summary["is_sbm_eligible"].fillna(False)]
    if not (eligible_summary["reference_size"] == data.n_dmus - 1).all():
        raise AssertionError(
            "global super-SBM references must exclude the evaluated row"
        )

    solved = diagnostics.loc[diagnostics["postsolve_certified"].fillna(False)]
    if solved.shape[0] != expected_calls:
        raise AssertionError(
            "every solved LP must retain a valid postsolve certificate"
        )
    completed_super = diagnostics.loc[
        (diagnostics["phase_name"] == "super_sbm_peer_replacement")
        & (diagnostics["phase_status"] == "completed")
    ]
    if completed_super.shape[0] != eligible:
        raise AssertionError("every eligible super-SBM appraisal must be certified")
    if not completed_super["economic_postsolve_certified"].all():
        raise AssertionError("every recovered super-SBM account must be certified")

    max_certificate_violation = _maximum_finite_absolute(
        solved,
        (
            "max_constraint_violation",
            "equality_violation",
            "max_bound_violation",
            "objective_residual",
            "duality_gap",
            "max_dual_violation",
        ),
    )
    max_economic_violation = _maximum_finite_absolute(
        completed_super,
        ("max_economic_violation",),
    )
    print(
        f"n={data.n_dmus} inputs={data.n_inputs} outputs={data.n_outputs} "
        f"orientation=non-oriented rts=crs elapsed={elapsed:.3f}s "
        f"screening_solves={solver.screening_calls} "
        f"eligible_super_solves={solver.super_calls} "
        f"total_solves={solver.calls} "
        f"base_reference_sets={base_reference_sets} "
        f"screening_compilations={screening_compilations} "
        f"leave_one_out_compilations={super_compilations} "
        f"max_certificate_violation={max_certificate_violation:.3e} "
        f"max_economic_violation={max_economic_violation:.3e}"
    )


if __name__ == "__main__":
    main()
