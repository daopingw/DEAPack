"""Repeatable benchmark for local RTS and its scale-elasticity transform.

Both public operators solve four LPs per evaluated observation when every
component succeeds: one VRS radial fit, one Pareto-completion problem, and the
lower and upper endpoints of the supporting-intercept interval. Scale
elasticity transforms that shared result without another fit. Reference
matrices are compiled once per distinct comparison set.

Run a local smoke case with:

    python benchmarks/benchmark_local_rts.py --n-dmus 100

Exercise the scale-elasticity wrapper with:

    python benchmarks/benchmark_local_rts.py --operator scale-elasticity \
        --n-dmus 100

The 1,000-DMU case is intended for scheduled or release benchmarking:

    python benchmarks/benchmark_local_rts.py --n-dmus 1000
"""

from __future__ import annotations

import argparse
import importlib
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import issparse

from deapack import DEAData, local_returns_to_scale, scale_elasticity
from deapack.solvers import SciPyHiGHSSolver

local_rts_module = importlib.import_module("deapack.analysis.local_rts")
radial_module = importlib.import_module("deapack.models.radial")


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.problems = []
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        if problem.a_ub is not None and not issparse(problem.a_ub):
            raise AssertionError("local-scale inequality matrices must be sparse")
        if problem.a_eq is not None and not issparse(problem.a_eq):
            raise AssertionError("local-scale equality matrices must be sparse")
        self.calls += 1
        self.problems.append(problem)
        return self._delegate.solve(problem)


@dataclass(frozen=True, slots=True)
class BenchmarkObservation:
    """Independently counted workload and certificate residuals."""

    elapsed: float
    solver_calls: int
    projection_reference_compilations: int
    support_reference_compilations: int
    phase_one_template_compilations: int
    max_projection_lp_violation: float
    max_projection_economic_violation: float
    max_projection_peer_violation: float
    max_endpoint_lp_violation: float
    max_endpoint_economic_violation: float
    max_unbounded_ray_violation: float
    max_elasticity_transform_violation: float


def make_data(n_dmus: int) -> DEAData:
    """Return deterministic positive two-input, two-output benchmark data."""
    if n_dmus < 2:
        raise ValueError("n_dmus must be at least two")

    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 5.0, 1.0)
    operating_quality = 0.70 + 0.30 * ((position % 31) / 30.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "labour": scale * (12.0 + position % 17),
            "capital": scale * (20.0 + position % 23),
        }
    )
    productive_capacity = np.sqrt(frame["labour"] * frame["capital"])
    frame["service"] = (
        productive_capacity * operating_quality * (0.85 + (position % 19) / 45.0)
    )
    frame["quality"] = (
        productive_capacity * operating_quality * (0.55 + (position % 13) / 35.0)
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labour", "capital"),
        outputs=("service", "quality"),
    )


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise AssertionError(f"{label} missing certificate columns: {missing}")


def _maximum_finite(frame: pd.DataFrame, columns: tuple[str, ...], label: str) -> float:
    """Return a maximum residual and reject missing/non-finite evidence."""

    _require_columns(frame, columns, label)
    values = frame.loc[:, columns].to_numpy(dtype=np.float64)
    if values.size == 0 or not np.isfinite(values).all():
        raise AssertionError(f"{label} residual evidence must be finite and non-empty")
    return float(np.abs(values).max(initial=0.0))


def _fit_with_counts(
    n_dmus: int,
    *,
    orientation: str,
    operator: str,
) -> tuple[Any, BenchmarkObservation]:
    """Fit once while independently counting solves and compilations."""

    data = make_data(n_dmus)
    solver = _CountingSolver()
    projection_reference_compilations = 0
    support_reference_compilations = 0
    phase_one_template_compilations = 0
    original_projection_compile = radial_module.compile_reference
    original_support_compile = local_rts_module.compile_reference
    original_template_compile = radial_module.compile_radial_phase_one_template

    def counted_projection_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal projection_reference_compilations
        projection_reference_compilations += 1
        return original_projection_compile(*args, **kwargs)

    def counted_support_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal support_reference_compilations
        support_reference_compilations += 1
        return original_support_compile(*args, **kwargs)

    def counted_template_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal phase_one_template_compilations
        phase_one_template_compilations += 1
        return original_template_compile(*args, **kwargs)

    radial_module.compile_reference = counted_projection_compile
    local_rts_module.compile_reference = counted_support_compile
    radial_module.compile_radial_phase_one_template = counted_template_compile
    try:
        fit = (
            scale_elasticity
            if operator == "scale-elasticity"
            else local_returns_to_scale
        )
        start = time.perf_counter()
        result = fit(data, orientation=orientation, solver=solver)
        elapsed = time.perf_counter() - start
    finally:
        radial_module.compile_reference = original_projection_compile
        local_rts_module.compile_reference = original_support_compile
        radial_module.compile_radial_phase_one_template = original_template_compile

    diagnostics = result.diagnostics
    projection_diagnostics = diagnostics.loc[
        diagnostics["component"].eq("vrs_selected_projection")
    ]
    endpoint_diagnostics = diagnostics.loc[
        diagnostics["component"].eq("banker_thrall_support_interval")
    ]
    finite_endpoint_diagnostics = endpoint_diagnostics.loc[
        endpoint_diagnostics["backend_solver_status"].eq("optimal")
    ]
    unbounded_diagnostics = endpoint_diagnostics.loc[
        endpoint_diagnostics["backend_solver_status"].eq("unbounded")
    ]
    max_unbounded_ray_violation = _maximum_finite(
        unbounded_diagnostics,
        ("max_unbounded_ray_violation",),
        "unbounded endpoint ray",
    )
    summary = result.summary()
    max_elasticity_transform_violation = (
        _maximum_finite(
            summary,
            ("scale_elasticity_max_transform_violation",),
            "scale-elasticity transform",
        )
        if operator == "scale-elasticity"
        else 0.0
    )
    observation = BenchmarkObservation(
        elapsed=elapsed,
        solver_calls=solver.calls,
        projection_reference_compilations=projection_reference_compilations,
        support_reference_compilations=support_reference_compilations,
        phase_one_template_compilations=phase_one_template_compilations,
        max_projection_lp_violation=_maximum_finite(
            projection_diagnostics,
            (
                "max_constraint_violation",
                "equality_violation",
                "max_bound_violation",
                "objective_residual",
                "duality_gap",
                "max_dual_violation",
                "complementarity_violation",
            ),
            "projection LP",
        ),
        max_projection_economic_violation=_maximum_finite(
            projection_diagnostics,
            (
                "max_raw_economic_violation",
                "max_published_account_violation",
            ),
            "projection economic account",
        ),
        max_projection_peer_violation=_maximum_finite(
            projection_diagnostics,
            ("max_published_peer_account_violation",),
            "projection peer account",
        ),
        max_endpoint_lp_violation=_maximum_finite(
            finite_endpoint_diagnostics,
            (
                "max_constraint_violation",
                "equality_violation",
                "max_bound_violation",
                "objective_residual",
                "duality_gap",
                "max_dual_violation",
                "complementarity_violation",
            ),
            "finite support endpoint LP",
        ),
        max_endpoint_economic_violation=_maximum_finite(
            endpoint_diagnostics,
            ("max_economic_violation",),
            "support endpoint economic account",
        ),
        max_unbounded_ray_violation=max_unbounded_ray_violation,
        max_elasticity_transform_violation=max_elasticity_transform_violation,
    )
    return result, observation


def _validate_result(
    result: Any,
    observation: BenchmarkObservation,
    *,
    n_dmus: int,
    operator: str,
    tolerance: float = 1.0e-7,
) -> None:
    """Fail closed unless every published scale account is certified."""

    summary = result.summary()
    diagnostics = result.diagnostics
    endpoint_diagnostics = diagnostics.loc[
        diagnostics["component"].eq("banker_thrall_support_interval")
    ]
    projection_diagnostics = diagnostics.loc[
        diagnostics["component"].eq("vrs_selected_projection")
    ]
    if len(summary) != n_dmus or len(endpoint_diagnostics) != 2 * n_dmus:
        raise AssertionError(
            "benchmark result does not contain the complete task graph"
        )

    summary_true_columns = (
        "analysis_valid",
        "support_domain_valid",
        "support_interval_valid",
        "economic_classification_certified",
        "projection_score_valid",
        "projection_completion_valid",
        "projection_target_valid",
        "projection_peer_valid",
        "completion_valid",
        "target_valid",
        "peer_valid",
        "selected_target_domain_valid",
        "support_intercept_lower_valid",
        "support_intercept_upper_valid",
    )
    _require_columns(summary, summary_true_columns, "summary")
    for column in summary_true_columns:
        if not summary[column].fillna(False).all():
            raise AssertionError(f"benchmark summary failed certificate {column}")
    if not summary["solver_status"].eq("optimal").all():
        raise AssertionError("all benchmark scale classifications must resolve")
    if summary["rts_classification"].eq("indeterminate").any():
        raise AssertionError("benchmark must not publish an indeterminate RTS label")

    endpoint_summary_columns = (
        *(
            f"support_intercept_{side}_{suffix}"
            for side in ("lower", "upper")
            for suffix in (
                "backend_status",
                "raw_status",
                "status",
                "valid",
                "lp_postsolve_certified",
                "dual_postsolve_certified",
                "economic_postsolve_certified",
                "unbounded_ray_certified",
            )
        ),
        "support_intercept_lower",
        "support_intercept_upper",
    )
    _require_columns(summary, endpoint_summary_columns, "endpoint summary")
    for side in ("lower", "upper"):
        backend = summary[f"support_intercept_{side}_backend_status"]
        raw = summary[f"support_intercept_{side}_raw_status"]
        legacy = summary[f"support_intercept_{side}_status"]
        if not backend.equals(raw) or not backend.equals(legacy):
            raise AssertionError(f"{side} endpoint backend/raw statuses diverge")
        finite = backend.eq("optimal")
        unbounded = backend.eq("unbounded")
        if not (finite | unbounded).all():
            raise AssertionError(f"{side} endpoint has unresolved backend status")
        for suffix in (
            "lp_postsolve_certified",
            "dual_postsolve_certified",
            "economic_postsolve_certified",
        ):
            certificate = summary[f"support_intercept_{side}_{suffix}"]
            if suffix == "economic_postsolve_certified":
                valid = certificate.fillna(False)
            else:
                valid = certificate.loc[finite].fillna(False)
                if not certificate.loc[unbounded].isna().all():
                    raise AssertionError(
                        f"{side} unbounded endpoint must not claim finite {suffix}"
                    )
            if not valid.all():
                raise AssertionError(f"{side} endpoint failed {suffix}")
        ray = summary[f"support_intercept_{side}_unbounded_ray_certified"]
        if (
            not ray.loc[unbounded].fillna(False).all()
            or not ray.loc[finite].isna().all()
        ):
            raise AssertionError(f"{side} endpoint ray certificate is inconsistent")
        values = summary[f"support_intercept_{side}"]
        if not np.isfinite(values.loc[finite].to_numpy(dtype=np.float64)).all():
            raise AssertionError(f"{side} finite endpoint is not finite")
        expected_infinity = -np.inf if side == "lower" else np.inf
        if not values.loc[unbounded].eq(expected_infinity).all():
            raise AssertionError(f"{side} unbounded endpoint has the wrong sign")

    expected_backend = np.where(
        summary["support_intercept_lower_backend_status"].eq("unbounded")
        | summary["support_intercept_upper_backend_status"].eq("unbounded"),
        "unbounded",
        "optimal",
    )
    if not np.array_equal(summary["backend_solver_status"], expected_backend):
        raise AssertionError(
            "aggregate backend status does not preserve endpoint status"
        )
    if not summary["backend_solver_status"].equals(summary["raw_solver_status"]):
        raise AssertionError("aggregate backend and raw statuses diverge")
    if not summary["projection_backend_solver_status"].eq("optimal").all():
        raise AssertionError("projection backend status must remain optimal")
    if not summary["projection_backend_solver_status"].equals(
        summary["projection_raw_solver_status"]
    ):
        raise AssertionError("projection backend and raw statuses diverge")

    projection_certificate_columns = (
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "economic_postsolve_certified",
        "published_output_account_certified",
        "published_peer_account_certified",
        "dual_postsolve_certified",
    )
    _require_columns(
        projection_diagnostics,
        projection_certificate_columns,
        "projection diagnostics",
    )
    for column in projection_certificate_columns:
        if not projection_diagnostics[column].fillna(False).all():
            raise AssertionError(f"projection diagnostics failed {column}")
    endpoint_certificate_columns = (
        "economic_postsolve_certified",
        "endpoint_postsolve_certified",
    )
    _require_columns(
        endpoint_diagnostics,
        endpoint_certificate_columns,
        "endpoint diagnostics",
    )
    for column in endpoint_certificate_columns:
        if not endpoint_diagnostics[column].fillna(False).all():
            raise AssertionError(f"endpoint diagnostics failed {column}")

    finite_diagnostics = endpoint_diagnostics["backend_solver_status"].eq("optimal")
    for column in ("lp_postsolve_certified", "dual_postsolve_certified"):
        if not endpoint_diagnostics.loc[finite_diagnostics, column].fillna(False).all():
            raise AssertionError(f"finite endpoint diagnostics failed {column}")
    unbounded_diagnostics = endpoint_diagnostics["backend_solver_status"].eq(
        "unbounded"
    )
    if (
        not endpoint_diagnostics.loc[
            unbounded_diagnostics,
            "unbounded_ray_certified",
        ]
        .fillna(False)
        .all()
    ):
        raise AssertionError("unbounded endpoint diagnostics lack a certified ray")

    expected_solver_calls = 4 * n_dmus
    expected_counts = {
        "projection_solver_calls": 2 * n_dmus,
        "support_endpoint_solver_calls": 2 * n_dmus,
        "solver_calls": expected_solver_calls,
        "additional_solver_calls": 0,
        "compiled_reference_sets": 1,
    }
    for field, expected in expected_counts.items():
        if result.metadata.get(field) != expected:
            raise AssertionError(
                f"metadata {field}={result.metadata.get(field)}, expected={expected}"
            )
    if observation.solver_calls != expected_solver_calls:
        raise AssertionError(
            "independent solver count disagrees with four-task scale kernel"
        )
    compile_counts = (
        observation.projection_reference_compilations,
        observation.support_reference_compilations,
        observation.phase_one_template_compilations,
    )
    if compile_counts != (1, 1, 1):
        raise AssertionError(
            "common-reference benchmark must compile projection/reference/support "
            f"templates once; observed={compile_counts}"
        )
    local_metadata = (
        result.metadata["components"]["local_returns_to_scale"]
        if operator == "scale-elasticity"
        else result.metadata
    )
    if local_metadata["postsolve_certificate"]["additional_solver_calls"] != 0:
        raise AssertionError("local RTS certificate must add zero solver calls")
    if result.metadata["postsolve_certificate"]["additional_solver_calls"] != 0:
        raise AssertionError("public operator certificate must add zero solver calls")

    residuals = (
        observation.max_projection_lp_violation,
        observation.max_projection_economic_violation,
        observation.max_projection_peer_violation,
        observation.max_endpoint_lp_violation,
        observation.max_endpoint_economic_violation,
        observation.max_unbounded_ray_violation,
        observation.max_elasticity_transform_violation,
    )
    if not np.isfinite(residuals).all() or max(residuals) > tolerance:
        raise AssertionError(
            f"non-finite or excessive certificate residuals: {residuals}"
        )

    if operator == "scale-elasticity":
        elasticity_columns = (
            "scale_elasticity_valid",
            "scale_elasticity_domain_valid",
            "scale_elasticity_economic_postsolve_certified",
            "scale_elasticity_right_valid",
            "scale_elasticity_left_valid",
        )
        _require_columns(summary, elasticity_columns, "scale-elasticity summary")
        for column in elasticity_columns:
            if not summary[column].fillna(False).all():
                raise AssertionError(f"scale-elasticity summary failed {column}")


def run_case(
    n_dmus: int,
    *,
    orientation: str,
    operator: str,
) -> Any:
    """Fit, certify, and report one sparse four-task scale case."""

    result, observation = _fit_with_counts(
        n_dmus,
        orientation=orientation,
        operator=operator,
    )
    _validate_result(
        result,
        observation,
        n_dmus=n_dmus,
        operator=operator,
    )
    summary = result.summary()
    classifications = (
        summary["rts_classification"].value_counts().sort_index().to_dict()
    )
    unbounded_endpoints = int(
        summary["support_intercept_lower"].abs().eq(np.inf).sum()
        + summary["support_intercept_upper"].abs().eq(np.inf).sum()
    )
    print(
        f"operator={operator} n={n_dmus} orientation={orientation} "
        f"elapsed={observation.elapsed:.3f}s "
        f"certified={int(summary['analysis_valid'].sum())}/{n_dmus} "
        f"solver_calls={observation.solver_calls} "
        f"projection_reference_compilations="
        f"{observation.projection_reference_compilations} "
        f"support_reference_compilations="
        f"{observation.support_reference_compilations} "
        f"phase_one_template_compilations="
        f"{observation.phase_one_template_compilations} "
        f"additional_solves=0 "
        f"unbounded_endpoints={unbounded_endpoints} "
        f"max_projection_lp_violation="
        f"{observation.max_projection_lp_violation:.3e} "
        f"max_projection_economic_violation="
        f"{observation.max_projection_economic_violation:.3e} "
        f"max_projection_peer_violation="
        f"{observation.max_projection_peer_violation:.3e} "
        f"max_endpoint_lp_violation="
        f"{observation.max_endpoint_lp_violation:.3e} "
        f"max_endpoint_economic_violation="
        f"{observation.max_endpoint_economic_violation:.3e} "
        f"max_unbounded_ray_violation="
        f"{observation.max_unbounded_ray_violation:.3e} "
        f"max_elasticity_transform_violation="
        f"{observation.max_elasticity_transform_violation:.3e} "
        f"classifications={classifications}"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, nargs="+", default=(100,))
    parser.add_argument(
        "--orientation",
        choices=("input", "output", "both"),
        default="input",
    )
    parser.add_argument(
        "--operator",
        choices=("local-rts", "scale-elasticity"),
        default="local-rts",
    )
    args = parser.parse_args()

    orientations = (
        ("input", "output") if args.orientation == "both" else (args.orientation,)
    )
    for n_dmus in args.n_dmus:
        for orientation in orientations:
            run_case(
                n_dmus,
                orientation=orientation,
                operator=args.operator,
            )


if __name__ == "__main__":
    main()
