"""Repeatable benchmark for the two-stage relational network kernel.

Run from an editable development environment, for example:

    python benchmarks/benchmark_network_relational.py --n-dmus 100
    python benchmarks/benchmark_network_relational.py --n-dmus 1000 \
        --decomposition none --projection none
"""

from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.sparse import issparse

import deapack.network.kao_hwang as relational_module
from deapack import (
    DEAResult,
    KaoHwangRelationalDEA,
    NetworkData,
    TwoStageSeriesSpec,
)
from deapack.solvers import SciPyHiGHSSolver


def make_data(n_dmus: int) -> NetworkData:
    """Return a deterministic positive two-stage production system."""

    if n_dmus <= 0:
        raise ValueError("n_dmus must be positive")
    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    operating_quality = 0.70 + 0.30 * ((position % 37) / 36.0)
    conversion_quality = 0.68 + 0.32 * ((position % 29) / 28.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "staff": 20.0 + position * (1.0 + (position % 11) / 20.0),
            "budget": 30.0 + position * (1.0 + (position % 17) / 25.0),
        }
    )
    frame["cases"] = (
        np.sqrt(frame["staff"] * frame["budget"])
        * operating_quality
        * (1.0 + (position % 13) / 30.0)
    )
    frame["projects"] = (
        np.power(frame["staff"], 0.6)
        * np.power(frame["budget"], 0.4)
        * operating_quality
    )
    frame["outcomes"] = (
        np.sqrt(frame["cases"] * frame["projects"])
        * conversion_quality
        * (1.0 + (position % 19) / 35.0)
    )
    frame["quality"] = (
        np.power(frame["cases"], 0.35)
        * np.power(frame["projects"], 0.65)
        * conversion_quality
    )
    return NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=TwoStageSeriesSpec(
            inputs=("staff", "budget"),
            intermediates=("cases", "projects"),
            outputs=("outcomes", "quality"),
        ),
    )


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.phase_counts = {
            "primary": 0,
            "secondary": 0,
            "projection_fallback": 0,
        }
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        if problem.a_ub is not None and not issparse(problem.a_ub):
            raise AssertionError("relational inequality matrices must remain sparse")
        if problem.a_eq is not None and not issparse(problem.a_eq):
            raise AssertionError("relational equality matrices must remain sparse")
        self.calls += 1
        phase = _solver_phase(problem.name)
        self.phase_counts[phase] += 1
        return self._delegate.solve(problem)


@dataclass(frozen=True, slots=True)
class BenchmarkObservation:
    elapsed: float
    compile_calls: int
    solver_calls: int
    primary_solves: int
    secondary_solves: int
    projection_fallback_solves: int
    max_lp_violation: float
    max_raw_economic_violation: float
    max_published_economic_violation: float
    max_raw_target_violation: float
    max_published_target_violation: float
    max_peer_account_violation: float
    max_identity_residual: float


def _solver_phase(name: object) -> str:
    resolved = str(name)
    if resolved.endswith(":system"):
        return "primary"
    if resolved.endswith(":maximize_stage_1") or resolved.endswith(":maximize_stage_2"):
        return "secondary"
    if resolved.endswith(":projection"):
        return "projection_fallback"
    raise AssertionError(f"unclassified relational solve: {resolved!r}")


def _required_columns(
    frame: pd.DataFrame, columns: tuple[str, ...], label: str
) -> None:
    missing = sorted(set(columns).difference(frame.columns))
    if missing:
        raise AssertionError(f"{label} is missing required fields: {missing}")


def _all_true(frame: pd.DataFrame, columns: tuple[str, ...], label: str) -> None:
    _required_columns(frame, columns, label)
    for column in columns:
        if not frame[column].fillna(False).astype(bool).all():
            raise AssertionError(f"{label} failed required certificate {column}")


def _finite_max(frame: pd.DataFrame, column: str, label: str) -> float:
    _required_columns(frame, (column,), label)
    values = frame[column].to_numpy(dtype=np.float64)
    if values.size == 0 or not np.isfinite(values).all():
        raise AssertionError(f"{label} contains non-finite {column}")
    return float(np.max(values))


def _fit_with_counts(
    n_dmus: int,
    *,
    decomposition: str,
    projection: str,
) -> tuple[DEAResult, BenchmarkObservation]:
    data = make_data(n_dmus)
    solver = _CountingSolver()
    compile_calls = 0
    original_compile = relational_module.compile_two_stage_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compile_calls
        compile_calls += 1
        return original_compile(*args, **kwargs)

    relational_module.compile_two_stage_reference = counted_compile
    try:
        start = time.perf_counter()
        result = KaoHwangRelationalDEA(
            decomposition=decomposition,  # type: ignore[arg-type]
            projection=projection,  # type: ignore[arg-type]
            solver=solver,
        ).fit(data)
        elapsed = time.perf_counter() - start
    finally:
        relational_module.compile_two_stage_reference = original_compile

    phase_counts = solver.phase_counts
    multiplier_diagnostics = result.diagnostics.loc[
        result.diagnostics["phase"].isin(
            ("system", "maximize_stage_1", "maximize_stage_2")
        )
    ]
    system_diagnostics = result.diagnostics.loc[
        result.diagnostics["phase"].eq("system")
    ]
    max_identity_residual = (
        math.nan
        if decomposition == "none"
        else float(result.summary()["reconstruction_residual"].abs().max())
    )
    observation = BenchmarkObservation(
        elapsed=elapsed,
        compile_calls=compile_calls,
        solver_calls=solver.calls,
        primary_solves=phase_counts["primary"],
        secondary_solves=phase_counts["secondary"],
        projection_fallback_solves=phase_counts["projection_fallback"],
        max_lp_violation=_finite_max(
            multiplier_diagnostics,
            "max_recomputed_constraint_violation",
            "multiplier diagnostics",
        ),
        max_raw_economic_violation=_finite_max(
            multiplier_diagnostics,
            "max_raw_economic_violation",
            "multiplier diagnostics",
        ),
        max_published_economic_violation=_finite_max(
            multiplier_diagnostics,
            "max_published_economic_violation",
            "multiplier diagnostics",
        ),
        max_raw_target_violation=(
            math.nan
            if projection == "none"
            else _finite_max(
                system_diagnostics,
                "max_raw_target_account_violation",
                "system diagnostics",
            )
        ),
        max_published_target_violation=(
            math.nan
            if projection == "none"
            else _finite_max(
                system_diagnostics,
                "max_published_target_account_violation",
                "system diagnostics",
            )
        ),
        max_peer_account_violation=(
            math.nan
            if projection == "none"
            else _finite_max(
                system_diagnostics,
                "max_published_peer_account_violation",
                "system diagnostics",
            )
        ),
        max_identity_residual=max_identity_residual,
    )
    return result, observation


def _validate_result(
    result: DEAResult,
    observation: BenchmarkObservation,
    *,
    n_dmus: int,
    decomposition: str,
    projection: str,
) -> None:
    """Fail closed unless the benchmark proves every requested release gate."""

    summary = result.summary()
    diagnostics = result.diagnostics
    _required_columns(
        summary,
        (
            "score",
            "system_efficiency",
            "score_valid",
            "score_status",
            "decomposition_valid",
            "decomposition_status",
            "target_valid",
            "target_status",
            "peer_valid",
            "peer_status",
            "solver_status",
            "backend_solver_status",
            "raw_solver_status",
            "stage_1_efficiency",
            "stage_2_efficiency",
            "stage_product",
            "reconstruction_residual",
        ),
        "summary",
    )
    if len(summary) != n_dmus:
        raise AssertionError(
            f"benchmark expected {n_dmus} summary rows, observed={len(summary)}"
        )
    for status_column in (
        "solver_status",
        "backend_solver_status",
        "raw_solver_status",
    ):
        if not summary[status_column].eq("optimal").all():
            raise AssertionError(f"benchmark contains non-optimal {status_column}")
    if not summary["score_valid"].fillna(False).astype(bool).all():
        raise AssertionError("all benchmark system scores must be certified")
    if not summary["score_status"].eq("defined").all():
        raise AssertionError("all benchmark system scores must be defined")

    expected_secondary_per_dmu = {
        "none": 0,
        "maximize_stage_1": 1,
        "maximize_stage_2": 1,
        "bounds": 2,
    }[decomposition]
    expected_secondary = expected_secondary_per_dmu * n_dmus
    if decomposition == "none":
        if summary["decomposition_valid"].fillna(True).astype(bool).any():
            raise AssertionError("score-only benchmark published a decomposition")
        if not summary["decomposition_status"].eq("not_requested").all():
            raise AssertionError("score-only decomposition status is not stable")
        if (
            not summary[["stage_1_efficiency", "stage_2_efficiency", "stage_product"]]
            .isna()
            .all()
            .all()
        ):
            raise AssertionError("score-only benchmark leaked process values")
    else:
        if not summary["decomposition_valid"].fillna(False).astype(bool).all():
            raise AssertionError("requested process decompositions are not certified")
        permitted_statuses = (
            {"bounds_computed"} if decomposition == "bounds" else {"selected"}
        )
        if not set(summary["decomposition_status"]) <= permitted_statuses:
            raise AssertionError("unexpected decomposition release status")
        identity = summary["reconstruction_residual"].to_numpy(dtype=np.float64)
        if not np.isfinite(identity).all() or np.max(np.abs(identity)) > 1.0e-7:
            raise AssertionError("process multiplication account did not reconstruct")
        if not np.allclose(
            summary["stage_product"],
            summary["system_efficiency"],
            atol=1.0e-7,
            rtol=0.0,
        ):
            raise AssertionError("published process product differs from system score")

    if projection == "none":
        if summary[["target_valid", "peer_valid"]].fillna(True).any().any():
            raise AssertionError("score-only benchmark leaked target or peer validity")
        if not summary["target_status"].eq("not_requested").all():
            raise AssertionError("target status must record not_requested")
        if not summary["peer_status"].eq("not_requested").all():
            raise AssertionError("peer status must record not_requested")
        if (
            not result.targets.empty
            or not result.links.empty
            or not result.intensities.empty
        ):
            raise AssertionError("projection='none' leaked target, link, or peer rows")
    else:
        if not summary[["target_valid", "peer_valid"]].fillna(False).all().all():
            raise AssertionError("requested target or peer accounts are uncertified")
        if not summary["target_status"].eq("defined").all():
            raise AssertionError("requested targets must be defined")
        if not summary["peer_status"].eq("certified_projection_account").all():
            raise AssertionError("requested displayed peers must be certified")
        if result.targets.empty or result.links.empty or result.intensities.empty:
            raise AssertionError("certified projection omitted semantic rows")

    multiplier_phases = ("system", "maximize_stage_1", "maximize_stage_2")
    multiplier_diagnostics = diagnostics.loc[
        diagnostics["phase"].isin(multiplier_phases)
    ]
    if len(multiplier_diagnostics) != n_dmus + expected_secondary:
        raise AssertionError("diagnostic multiplier phase count is inconsistent")
    _all_true(
        multiplier_diagnostics,
        (
            "lp_postsolve_certified",
            "raw_economic_postsolve_certified",
            "published_economic_postsolve_certified",
            "economic_postsolve_certified",
            "postsolve_certified",
        ),
        "multiplier diagnostics",
    )
    system_diagnostics = diagnostics.loc[diagnostics["phase"].eq("system")]
    if len(system_diagnostics) != n_dmus:
        raise AssertionError("one system diagnostic is required per organization")
    target_certificate_columns = (
        "raw_target_account_certified",
        "published_target_account_certified",
        "published_peer_account_certified",
    )
    _required_columns(
        system_diagnostics, target_certificate_columns, "system diagnostics"
    )
    if projection == "none":
        if not system_diagnostics[list(target_certificate_columns)].isna().all().all():
            raise AssertionError("unrequested target certificates must remain missing")
    else:
        _all_true(system_diagnostics, target_certificate_columns, "system diagnostics")

    residuals = [
        observation.max_lp_violation,
        observation.max_raw_economic_violation,
        observation.max_published_economic_violation,
    ]
    if decomposition != "none":
        residuals.append(observation.max_identity_residual)
    if projection != "none":
        residuals.extend(
            [
                observation.max_raw_target_violation,
                observation.max_published_target_violation,
                observation.max_peer_account_violation,
            ]
        )
    if not np.isfinite(residuals).all() or max(residuals) > 1.0e-7:
        raise AssertionError(
            f"non-finite or excessive benchmark residuals: {residuals}"
        )

    metadata = result.metadata
    required_metadata = (
        "compiled_reference_sets",
        "primary_solves",
        "secondary_solves",
        "projection_fallback_solves",
        "solver_calls",
        "additional_solver_calls",
        "postsolve_certificate",
    )
    missing_metadata = sorted(set(required_metadata).difference(metadata))
    if missing_metadata:
        raise AssertionError(f"metadata is missing required fields: {missing_metadata}")
    independently_counted = {
        "compiled_reference_sets": observation.compile_calls,
        "primary_solves": observation.primary_solves,
        "secondary_solves": observation.secondary_solves,
        "projection_fallback_solves": observation.projection_fallback_solves,
        "solver_calls": observation.solver_calls,
        "additional_solver_calls": 0,
    }
    for field, expected in independently_counted.items():
        if metadata[field] != expected:
            raise AssertionError(
                f"metadata {field}={metadata[field]}, independently counted={expected}"
            )
    if observation.compile_calls != 1:
        raise AssertionError("one common relational reference must compile once")
    if observation.primary_solves != n_dmus:
        raise AssertionError("one primary system solve is required per organization")
    if observation.secondary_solves != expected_secondary:
        raise AssertionError("secondary solve count differs from decomposition policy")
    expected_total = (
        observation.primary_solves
        + observation.secondary_solves
        + observation.projection_fallback_solves
    )
    if observation.solver_calls != expected_total:
        raise AssertionError("total solver count does not reconcile by phase")
    certificate_policy = metadata["postsolve_certificate"]
    if "additional_solver_calls" not in certificate_policy:
        raise AssertionError("postsolve certificate omits additional solve accounting")
    if certificate_policy["additional_solver_calls"] != 0:
        raise AssertionError("postsolve certification must issue zero extra solves")


def run_case(
    n_dmus: int,
    *,
    decomposition: str,
    projection: str,
) -> BenchmarkObservation:
    result, observation = _fit_with_counts(
        n_dmus,
        decomposition=decomposition,
        projection=projection,
    )
    _validate_result(
        result,
        observation,
        n_dmus=n_dmus,
        decomposition=decomposition,
        projection=projection,
    )
    summary = result.summary()
    certified = int(summary["score_valid"].fillna(False).sum())
    decomposed = int(summary["decomposition_valid"].fillna(False).sum())
    targets = int(summary["target_valid"].fillna(False).sum())
    peers = int(summary["peer_valid"].fillna(False).sum())
    print(
        f"n={n_dmus} decomposition={decomposition} projection={projection} "
        f"elapsed={observation.elapsed:.3f}s "
        f"score_certified={certified}/{n_dmus} "
        f"decomposition_certified={decomposed}/{n_dmus} "
        f"target_certified={targets}/{n_dmus} "
        f"peer_certified={peers}/{n_dmus} "
        f"compiled_reference_sets={observation.compile_calls} "
        f"primary_solves={observation.primary_solves} "
        f"secondary_solves={observation.secondary_solves} "
        f"projection_fallback_solves={observation.projection_fallback_solves} "
        f"solver_calls={observation.solver_calls} additional_solves=0 "
        f"max_lp_violation={observation.max_lp_violation:.3e} "
        f"max_raw_economic_violation="
        f"{observation.max_raw_economic_violation:.3e} "
        f"max_published_economic_violation="
        f"{observation.max_published_economic_violation:.3e} "
        f"max_raw_target_violation={observation.max_raw_target_violation:.3e} "
        f"max_published_target_violation="
        f"{observation.max_published_target_violation:.3e} "
        f"max_peer_account_violation="
        f"{observation.max_peer_account_violation:.3e} "
        f"max_identity_residual={observation.max_identity_residual:.3e}"
    )
    return observation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument(
        "--decomposition",
        choices=("none", "maximize_stage_1", "maximize_stage_2", "bounds"),
        default="maximize_stage_1",
    )
    parser.add_argument(
        "--projection",
        choices=("none", "source_midpoint"),
        default="none",
    )
    args = parser.parse_args()
    run_case(
        args.n_dmus,
        decomposition=args.decomposition,
        projection=args.projection,
    )


if __name__ == "__main__":
    main()
