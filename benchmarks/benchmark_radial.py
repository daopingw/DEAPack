"""Repeatable radial-DEA performance smoke benchmark.

Run from an editable development environment, for example:

    python benchmarks/benchmark_radial.py --n-dmus 1000
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd
from scipy.sparse import isspmatrix_csc

import deapack.models._common as common_module
import deapack.models.radial as radial_module
from deapack import BCC, DEAData, PeerEligibility, PeerEligibilityProvenance
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.seconds = 0.0
        self.max_constraint_nonzeros = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        for matrix_name in ("a_ub", "a_eq"):
            matrix = getattr(problem, matrix_name)
            if matrix is not None:
                if not isspmatrix_csc(matrix):
                    raise AssertionError(
                        f"radial solver matrix {matrix_name} must be CSC"
                    )
                self.max_constraint_nonzeros = max(
                    self.max_constraint_nonzeros,
                    int(matrix.nnz),
                )
        self.calls += 1
        started = time.perf_counter()
        result = self._delegate.solve(problem)
        self.seconds += time.perf_counter() - started
        return result


def make_data(n_dmus: int) -> DEAData:
    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "x1": 1.0 + position / max(n_dmus / 5.0, 1.0),
            "x2": 1.0 + (position % 37) / 10.0,
        }
    )
    frontier = np.sqrt(frame["x1"] * frame["x2"])
    relative_efficiency = 0.70 + 0.30 * ((position % 23) / 22.0)
    frame["y1"] = frontier * relative_efficiency
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("x1", "x2"),
        outputs="y1",
    )


def make_peer_eligibility(
    data: DEAData,
    n_cohorts: int,
) -> PeerEligibility | None:
    """Build repeated sparse populations without inferring category semantics."""
    if n_cohorts == 0:
        return None
    if n_cohorts < 0 or n_cohorts > data.n_dmus:
        raise ValueError("eligibility cohorts must lie between zero and n_dmus")
    cohorts = tuple(
        tuple(range(cohort, data.n_dmus, n_cohorts)) for cohort in range(n_cohorts)
    )
    rows_by_observation = tuple(
        cohorts[observation % n_cohorts] for observation in range(data.n_dmus)
    )
    return PeerEligibility.by_row(
        rows_by_observation,
        provenance=PeerEligibilityProvenance(
            rule_name=f"benchmark_repeated_cohorts_{n_cohorts}",
            source="deterministic benchmark fixture",
            comparison_population=f"{data.n_dmus} synthetic benchmark DMUs",
            decision_owner="DEAPack benchmark contract",
            validity_period="fixture schema v1",
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=1000)
    parser.add_argument("--full", action="store_true", help="run the slack phase")
    parser.add_argument(
        "--eligibility-cohorts",
        type=int,
        default=0,
        help="compose this many repeated source-neutral candidate populations",
    )
    args = parser.parse_args()

    data = make_data(args.n_dmus)
    peer_eligibility = make_peer_eligibility(data, args.eligibility_cohorts)
    solver = _CountingSolver()
    compile_calls = 0
    reference_compile_seconds = 0.0
    template_compile_calls = 0
    template_compile_seconds = 0.0
    phase_one_bindings = 0
    phase_one_binding_seconds = 0.0
    ordinary_statistic_compilations = 0
    absolute_statistic_compilations = 0
    original_compile = radial_module.compile_reference
    original_template_compile = radial_module.compile_radial_phase_one_template
    original_ordinary = common_module._compile_reference_ordinary_row_statistics
    original_absolute = common_module._compile_reference_absolute_row_statistics

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compile_calls, reference_compile_seconds
        compile_calls += 1
        started = time.perf_counter()
        compiled = original_compile(*args, **kwargs)
        reference_compile_seconds += time.perf_counter() - started
        return compiled

    def counted_template_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal template_compile_calls, template_compile_seconds
        template_compile_calls += 1
        started = time.perf_counter()
        compiled = original_template_compile(*args, **kwargs)
        template_compile_seconds += time.perf_counter() - started

        class _TimedTemplate:
            def bind(self, *bind_args, **bind_kwargs):  # type: ignore[no-untyped-def]
                nonlocal phase_one_bindings, phase_one_binding_seconds
                phase_one_bindings += 1
                bind_started = time.perf_counter()
                problem = compiled.bind(*bind_args, **bind_kwargs)
                phase_one_binding_seconds += time.perf_counter() - bind_started
                return problem

        return _TimedTemplate()

    def counted_ordinary(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal ordinary_statistic_compilations
        ordinary_statistic_compilations += 1
        return original_ordinary(*args, **kwargs)

    def counted_absolute(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal absolute_statistic_compilations
        absolute_statistic_compilations += 1
        return original_absolute(*args, **kwargs)

    radial_module.compile_reference = counted_compile
    radial_module.compile_radial_phase_one_template = counted_template_compile
    common_module._compile_reference_ordinary_row_statistics = counted_ordinary
    common_module._compile_reference_absolute_row_statistics = counted_absolute
    try:
        model = BCC(
            compute_slacks=args.full,
            peer_eligibility=peer_eligibility,
            solver=solver,
        )
        start = time.perf_counter()
        result = model.fit(data)
        elapsed = time.perf_counter() - start
    finally:
        radial_module.compile_reference = original_compile
        radial_module.compile_radial_phase_one_template = original_template_compile
        common_module._compile_reference_ordinary_row_statistics = original_ordinary
        common_module._compile_reference_absolute_row_statistics = original_absolute

    optimal = int((result.summary()["solver_status"] == "optimal").sum())
    expected_solver_calls = args.n_dmus * (2 if args.full else 1)
    expected_compilations = max(args.eligibility_cohorts, 1)
    if compile_calls != expected_compilations:
        raise AssertionError(
            "each distinct effective reference must compile once; "
            f"observed={compile_calls}, expected={expected_compilations}"
        )
    if ordinary_statistic_compilations != compile_calls:
        raise AssertionError(
            "ordinary row maxima must compile once per unique reference; "
            f"ordinary={ordinary_statistic_compilations}, references={compile_calls}"
        )
    if absolute_statistic_compilations != 0:
        raise AssertionError(
            "ordinary radial DEA must not compile absolute row maxima; "
            f"absolute={absolute_statistic_compilations}"
        )
    if solver.calls != expected_solver_calls:
        raise AssertionError(
            "unexpected radial solve count; "
            f"observed={solver.calls}, expected={expected_solver_calls}"
        )
    if template_compile_calls != compile_calls:
        raise AssertionError(
            "one radial phase-one template must compile per reference; "
            f"templates={template_compile_calls}, references={compile_calls}"
        )
    if phase_one_bindings != args.n_dmus:
        raise AssertionError(
            "one radial phase-one task must bind per observation; "
            f"bindings={phase_one_bindings}, observations={args.n_dmus}"
        )
    if result.metadata["phase_one_template_compilations"] != template_compile_calls:
        raise AssertionError("template-compilation metadata disagrees with execution")
    if result.metadata["phase_one_task_bindings"] != phase_one_bindings:
        raise AssertionError("phase-one binding metadata disagrees with execution")
    eligibility_edges = 0
    if peer_eligibility is not None:
        eligibility_metadata = result.metadata.get("peer_eligibility")
        if not isinstance(eligibility_metadata, dict):
            raise AssertionError("peer-eligibility metadata is unavailable")
        if eligibility_metadata["effective_unique_reference_sets"] != (
            expected_compilations
        ):
            raise AssertionError("eligibility metadata disagrees with compilations")
        eligibility_edges = int(eligibility_metadata["effective_edge_count"])
        summary = result.summary()
        if not (summary["base_reference_size"] == args.n_dmus).all():
            raise AssertionError("global base-reference sizes were not preserved")
        if int(summary["reference_size"].sum()) != eligibility_edges:
            raise AssertionError("effective eligibility edge count is inconsistent")
    accounted = (
        reference_compile_seconds
        + template_compile_seconds
        + phase_one_binding_seconds
        + solver.seconds
    )
    other_seconds = max(elapsed - accounted, 0.0)
    print(
        f"n={args.n_dmus} full={args.full} "
        f"eligibility_cohorts={args.eligibility_cohorts} "
        f"eligibility_edges={eligibility_edges} elapsed={elapsed:.3f}s "
        f"optimal={optimal}/{args.n_dmus} solver_calls={solver.calls} "
        f"reference_compilations={compile_calls} "
        f"phase_one_template_compilations={template_compile_calls} "
        f"phase_one_bindings={phase_one_bindings} "
        f"ordinary_statistic_compilations={ordinary_statistic_compilations} "
        f"absolute_statistic_compilations={absolute_statistic_compilations} "
        f"reference_compile_seconds={reference_compile_seconds:.6f} "
        f"template_compile_seconds={template_compile_seconds:.6f} "
        f"phase_one_binding_seconds={phase_one_binding_seconds:.6f} "
        f"solver_seconds={solver.seconds:.6f} "
        f"other_seconds={other_seconds:.6f} "
        f"max_constraint_nonzeros={solver.max_constraint_nonzeros}"
    )


if __name__ == "__main__":
    main()
