"""Repeatable benchmark for the radial DEA metafrontier decomposition.

The source-qualified score-only profile solves each observation once against
its declared group and once against the pooled metafrontier.  With ``n``
observations and ``K`` groups, the exact budget is therefore ``2n`` LPs and
``K + 1`` compiled reference populations.

Run the development baseline with:

    python benchmarks/benchmark_metafrontier.py --n-dmus 200 --n-groups 4
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

import deapack.models.radial as radial_module
from deapack import DEAData, MetafrontierDEA
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


def make_data(n_dmus: int, n_groups: int) -> DEAData:
    """Create deterministic positive heterogeneous production data."""

    if n_groups < 2:
        raise ValueError("n-groups must be at least two")
    if n_dmus < 2 * n_groups:
        raise ValueError("n-dmus must provide at least two rows per group")

    position = np.arange(n_dmus, dtype=np.float64)
    group_index = np.arange(n_dmus, dtype=np.int64) % n_groups
    scale = 1.0 + position / max(n_dmus / 7.0, 1.0)
    labor = scale * (8.0 + position % 13.0)
    capital = scale * (12.0 + (3.0 * position) % 17.0)
    energy = scale * (5.0 + (5.0 * position) % 11.0)
    capacity = np.power(labor, 0.35) * np.power(capital, 0.40) * np.power(energy, 0.25)
    opportunity = 0.72 + 0.28 * group_index / max(n_groups - 1, 1)
    management = 0.70 + 0.30 * ((position % 31.0) / 30.0)

    frame = pd.DataFrame(
        {
            "dmu": [f"MF{index:06d}" for index in range(n_dmus)],
            "technology_group": [f"group_{index + 1}" for index in group_index],
            "labor": labor,
            "capital": capital,
            "energy": energy,
            "service_volume": (
                capacity * opportunity * management * (0.90 + position % 7.0 / 40.0)
            ),
            "service_quality": (
                capacity
                * opportunity
                * management
                * (0.55 + (7.0 * position) % 13.0 / 55.0)
            ),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        group="technology_group",
        inputs=("labor", "capital", "energy"),
        outputs=("service_volume", "service_quality"),
    )


def _maximum_finite_absolute(frame: pd.DataFrame, column: str) -> float:
    values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    finite = np.abs(values[np.isfinite(values)])
    return float(finite.max(initial=0.0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=200)
    parser.add_argument("--n-groups", type=int, default=4)
    args = parser.parse_args()

    data = make_data(args.n_dmus, args.n_groups)
    solver = _CountingSolver()
    compilations = 0
    original_compile = radial_module.compile_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compilations
        compilations += 1
        return original_compile(*args, **kwargs)

    radial_module.compile_reference = counted_compile
    try:
        started = time.perf_counter()
        result = MetafrontierDEA(
            orientation="output",
            returns_to_scale="vrs",
            solver=solver,
            compute_slacks=False,
        ).fit(data)
        elapsed = time.perf_counter() - started
    finally:
        radial_module.compile_reference = original_compile

    expected_solves = 2 * data.n_dmus
    expected_compilations = args.n_groups + 1
    if solver.calls != expected_solves:
        raise AssertionError(
            "score-only radial metafrontier must solve two LPs per observation; "
            f"observed={solver.calls}, expected={expected_solves}"
        )
    if result.metadata["solver_calls"] != expected_solves:
        raise AssertionError("result metadata does not match counted solver calls")
    if result.metadata["phase_one_solves"] != expected_solves:
        raise AssertionError("every component must have one phase-one solve")
    if result.metadata["phase_two_solves"] != 0:
        raise AssertionError("score-only benchmark must not launch slack phases")
    if result.metadata["primary_solver_calls"] != expected_solves:
        raise AssertionError("primary-solve metadata does not match the source budget")
    if result.metadata["secondary_solver_calls"] != 0:
        raise AssertionError("score-only benchmark must not launch secondary solves")
    if result.metadata["additional_solver_calls"] != 0:
        raise AssertionError("postsolve certification must not launch extra LPs")
    if result.metadata["certificate_extra_solver_calls"] != 0:
        raise AssertionError("certificate checks must remain solve-free")
    if compilations != expected_compilations:
        raise AssertionError(
            "one pooled and one reference per group must be compiled; "
            f"observed={compilations}, expected={expected_compilations}"
        )
    if result.metadata["compiled_reference_sets"] != expected_compilations:
        raise AssertionError("compiled-reference metadata is inconsistent")

    summary = result.summary()
    if not (summary["solver_status"] == "optimal").all():
        raise AssertionError("every benchmark decomposition must be certified")
    if not summary["score_valid"].eq(True).all():
        raise AssertionError("every benchmark MTR must pass its explicit score gate")
    if not summary["score_status"].eq("defined").all():
        raise AssertionError("every benchmark MTR must have defined score status")
    component_gates = summary[
        [
            "group_score_valid",
            "metafrontier_score_valid",
            "group_peer_valid",
            "metafrontier_peer_valid",
            "group_dual_valid",
            "metafrontier_dual_valid",
        ]
    ]
    if not component_gates.all(axis=None):
        raise AssertionError("every benchmark component claim must be certified")
    if not summary["decomposition_certified"].all():
        raise AssertionError("every multiplicative identity must be certified")
    if not (summary["meta_efficiency"] <= summary["group_efficiency"] + 1e-9).all():
        raise AssertionError("the pooled metafrontier must envelop every group")

    max_identity_residual = _maximum_finite_absolute(
        summary,
        "reconstruction_residual",
    )
    max_nesting_violation = _maximum_finite_absolute(
        summary,
        "nesting_violation",
    )
    max_solver_violation = _maximum_finite_absolute(
        result.diagnostics,
        "max_primal_violation",
    )
    print(
        f"n={data.n_dmus} groups={args.n_groups} "
        f"inputs={data.n_inputs} outputs={data.n_outputs} "
        f"orientation=output rts=vrs elapsed={elapsed:.3f}s "
        f"group_solves={data.n_dmus} meta_solves={data.n_dmus} "
        f"total_solves={solver.calls} compilations={compilations} "
        f"max_solver_violation={max_solver_violation:.3e} "
        f"max_nesting_violation={max_nesting_violation:.3e} "
        f"max_identity_residual={max_identity_residual:.3e}"
    )


if __name__ == "__main__":
    main()
