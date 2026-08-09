"""Deterministic benchmark for six classical foundation methods.

The benchmark checks computational structure and numerical identities rather
than imposing machine-specific elapsed-time thresholds.  Run the routine
cross-method smoke case with:

    python benchmarks/benchmark_classical_foundations.py --n-dmus 100

Larger release and FDH scan cases can be run with:

    python benchmarks/benchmark_classical_foundations.py \
        --method ddf --n-dmus 1000 --score-only
    python benchmarks/benchmark_classical_foundations.py \
        --method fdh --n-dmus 5000 --chunk-size 256
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Callable

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from scipy.sparse import issparse

import deapack.models.additive as additive_module
import deapack.models.directional as directional_module
import deapack.models.radial as radial_module
from deapack import (
    AdditiveDEA,
    DEAData,
    DirectionalDistanceDEA,
    FreeDisposalHullDEA,
    MultiplicativeDEA,
    RangeAdjustedDEA,
    scale_efficiency,
)
from deapack.results import DEAResult
from deapack.solvers import SciPyHiGHSSolver

_METHODS = ("additive", "ram", "multiplicative", "ddf", "fdh", "scale")
_NUMERICAL_TOLERANCE = 1e-7

_ADDITIVE_SUMMARY_STATUS = {
    "score_status": "defined",
    "target_status": "certified_published_quantity_account",
    "peer_status": "certified_thresholded_peer_account",
    "dual_status": "certified_original_unit_dual_account",
}
_ADDITIVE_DIAGNOSTIC_CERTIFICATES = (
    "lp_postsolve_certified",
    "postsolve_certified",
    "raw_account_certified",
    "published_account_certified",
    "published_quantity_account_certified",
    "published_weighted_slack_account_certified",
    "economic_postsolve_certified",
    "published_peer_account_certified",
    "published_dual_account_certified",
)
_ADDITIVE_DIAGNOSTIC_RESIDUALS = (
    "max_constraint_violation",
    "equality_violation",
    "max_bound_violation",
    "objective_residual",
    "duality_gap",
    "max_dual_violation",
    "complementarity_violation",
    "max_raw_economic_violation",
    "max_published_economic_violation",
    "max_published_peer_account_violation",
    "max_published_dual_account_violation",
    "original_unit_dual_objective_residual",
)


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


class _SparseCountingSolver(_CountingSolver):
    """Count solves while failing closed if a DDF LP materializes dense matrices."""

    def solve(self, problem):  # type: ignore[no-untyped-def]
        for attribute in ("a_ub", "a_eq"):
            matrix = getattr(problem, attribute)
            if matrix is not None and not issparse(matrix):
                raise AssertionError(
                    f"DDF benchmark requires sparse {attribute}; "
                    f"observed={type(matrix).__name__}"
                )
        return super().solve(problem)


def make_data(n_dmus: int) -> DEAData:
    """Create a positive deterministic three-input, two-output population."""
    if n_dmus < 8:
        raise ValueError("n-dmus must be at least eight")

    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 6.0, 1.0)
    management = 0.68 + 0.32 * ((position % 23.0) / 22.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"F{index:06d}" for index in range(n_dmus)],
            "labor": scale * (8.0 + position % 17.0),
            "capital": scale * (11.0 + position % 13.0),
            "materials": scale * (6.0 + position % 11.0),
        }
    )
    capacity = np.cbrt(frame["labor"] * frame["capital"] * frame["materials"])
    frame["routine_service"] = capacity * management * (0.85 + (position % 7.0) / 22.0)
    frame["complex_service"] = capacity * management * (0.55 + (position % 5.0) / 18.0)
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labor", "capital", "materials"),
        outputs=("routine_service", "complex_service"),
    )


def _maximum_finite_absolute(frame: pd.DataFrame, column: str) -> float:
    values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    finite = np.abs(values[np.isfinite(values)])
    if finite.size == 0:
        raise AssertionError(f"{column} has no finite benchmark values")
    return float(finite.max())


def _maximum_required_finite_absolute(
    frame: pd.DataFrame,
    column: str,
    *,
    expected_rows: int,
) -> float:
    """Return an absolute maximum while rejecting missing or nonfinite evidence."""

    if column not in frame:
        raise AssertionError(f"diagnostics is missing required field {column!r}")
    values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    if values.shape != (expected_rows,):
        raise AssertionError(
            f"{column} row count mismatch: "
            f"observed={len(values)}, expected={expected_rows}"
        )
    if not np.isfinite(values).all():
        raise AssertionError(f"{column} must be finite for every benchmark row")
    return float(np.abs(values).max(initial=0.0))


def _require_columns(
    frame: pd.DataFrame,
    required: set[str],
    *,
    table: str,
) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise AssertionError(f"{table} is missing required fields: {sorted(missing)!r}")


def _validate_additive_family_release(
    result: DEAResult,
    *,
    method: str,
    n_dmus: int,
    measured_solver_calls: int,
    measured_compilations: int,
    tolerance: float = _NUMERICAL_TOLERANCE,
) -> dict[str, float]:
    """Enforce the complete Additive/RAM runtime publication contract."""

    summary = result.summary()
    diagnostics = result.diagnostics
    _require_columns(
        summary,
        {
            "score_valid",
            "score_status",
            "target_valid",
            "target_status",
            "peer_valid",
            "peer_status",
            "dual_valid",
            "dual_status",
            "solver_status",
            "backend_solver_status",
            "raw_solver_status",
        },
        table="summary",
    )
    if len(summary) != n_dmus:
        raise AssertionError(
            f"{method} summary row count mismatch: "
            f"observed={len(summary)}, expected={n_dmus}"
        )
    for field in ("score_valid", "target_valid", "peer_valid", "dual_valid"):
        if not summary[field].eq(True).all():
            raise AssertionError(f"every {method} row requires {field}=True")
    for field, expected in _ADDITIVE_SUMMARY_STATUS.items():
        if not summary[field].eq(expected).all():
            raise AssertionError(f"every {method} {field} must equal {expected!r}")
    for field in ("solver_status", "backend_solver_status", "raw_solver_status"):
        if not summary[field].eq("optimal").all():
            raise AssertionError(f"every {method} row requires {field}=optimal")
    if not summary["backend_solver_status"].equals(summary["raw_solver_status"]):
        raise AssertionError(f"{method} backend/raw solver statuses disagree")

    required_diagnostics = (
        set(_ADDITIVE_DIAGNOSTIC_CERTIFICATES)
        .union(_ADDITIVE_DIAGNOSTIC_RESIDUALS)
        .union({"solver_status", "backend_solver_status", "raw_solver_status"})
    )
    _require_columns(diagnostics, required_diagnostics, table="diagnostics")
    if len(diagnostics) != n_dmus:
        raise AssertionError(
            f"{method} diagnostic row count mismatch: "
            f"observed={len(diagnostics)}, expected={n_dmus}"
        )
    if not diagnostics[list(_ADDITIVE_DIAGNOSTIC_CERTIFICATES)].eq(True).all().all():
        raise AssertionError(
            f"every {method} solve must pass every runtime publication certificate"
        )
    for field in ("solver_status", "backend_solver_status", "raw_solver_status"):
        if not diagnostics[field].eq("optimal").all():
            raise AssertionError(
                f"every {method} diagnostic row requires {field}=optimal"
            )
    if not diagnostics["backend_solver_status"].equals(
        diagnostics["raw_solver_status"]
    ):
        raise AssertionError(f"{method} diagnostic backend/raw statuses disagree")
    maxima = {
        field: _maximum_required_finite_absolute(
            diagnostics,
            field,
            expected_rows=n_dmus,
        )
        for field in _ADDITIVE_DIAGNOSTIC_RESIDUALS
    }
    for field, value in maxima.items():
        if value > tolerance:
            raise AssertionError(
                f"{method} {field} exceeds tolerance: "
                f"observed={value:.12g}, tolerance={tolerance:.12g}"
            )

    expected_dmus = set(summary["dmu_id"])
    for table_name in ("slacks", "targets", "intensities", "duals"):
        table = getattr(result, table_name)
        if table.empty or "dmu_id" not in table:
            raise AssertionError(f"certified {method} {table_name} must be published")
        if set(table["dmu_id"]) != expected_dmus:
            raise AssertionError(
                f"certified {method} {table_name} does not cover every observation"
            )

    metadata = result.metadata
    expected_counts = {
        "compiled_reference_sets": 1,
        "primary_solver_calls": n_dmus,
        "secondary_solver_calls": 0,
        "solver_calls": n_dmus,
        "additional_solver_calls": 0,
        "certificate_extra_solver_calls": 0,
    }
    missing_metadata = set(expected_counts).difference(metadata)
    if missing_metadata:
        raise AssertionError(
            f"{method} metadata is missing execution fields: "
            f"{sorted(missing_metadata)!r}"
        )
    for field, expected in expected_counts.items():
        if metadata[field] != expected:
            raise AssertionError(
                f"{method} {field} mismatch: "
                f"observed={metadata[field]}, expected={expected}"
            )
    if measured_solver_calls != n_dmus:
        raise AssertionError(
            f"{method} counting backend mismatch: "
            f"observed={measured_solver_calls}, expected={n_dmus}"
        )
    if measured_compilations != 1:
        raise AssertionError(
            f"{method} must compile one global reference exactly once; "
            f"observed={measured_compilations}"
        )
    return maxima


def _assert_all_optimal(result: DEAResult) -> None:
    summary = result.summary()
    if not (summary["solver_status"] == "optimal").all():
        failures = summary.loc[
            summary["solver_status"] != "optimal",
            ["dmu_id", "solver_status"],
        ]
        raise AssertionError(f"benchmark produced non-optimal rows:\n{failures}")


def _assert_solver_residual(result: DEAResult) -> float:
    maximum = _maximum_finite_absolute(
        result.diagnostics,
        "max_primal_violation",
    )
    if maximum > _NUMERICAL_TOLERANCE:
        raise AssertionError(
            "maximum primal violation exceeds benchmark tolerance; "
            f"observed={maximum:.3e}, tolerance={_NUMERICAL_TOLERANCE:.3e}"
        )
    return maximum


def _slack_target_residual(
    result: DEAResult,
    expected_target: Callable[[pd.DataFrame], pd.Series],
) -> float:
    key_columns = ["dmu_id", "period", "role", "variable"]
    target_keys = list(result.targets[key_columns].itertuples(index=False, name=None))
    slack_keys = list(result.slacks[key_columns].itertuples(index=False, name=None))
    if len(target_keys) != len(set(target_keys)):
        raise AssertionError("benchmark target keys must be unique")
    if len(slack_keys) != len(set(slack_keys)):
        raise AssertionError("benchmark slack keys must be unique")
    if set(target_keys) != set(slack_keys):
        missing_slacks = sorted(set(target_keys) - set(slack_keys), key=repr)
        missing_targets = sorted(set(slack_keys) - set(target_keys), key=repr)
        raise AssertionError(
            "target and slack keys must match exactly; "
            f"missing_slacks={missing_slacks[:5]!r}, "
            f"missing_targets={missing_targets[:5]!r}"
        )
    rows = result.targets.merge(
        result.slacks[[*key_columns, "slack"]],
        on=key_columns,
        how="inner",
        validate="one_to_one",
    )
    if rows.empty:
        raise AssertionError("benchmark expected target and slack rows")
    residual = rows["target"] - expected_target(rows)
    maximum = float(residual.abs().max())
    if maximum > _NUMERICAL_TOLERANCE:
        raise AssertionError(
            "target reconstruction exceeds benchmark tolerance; "
            f"observed={maximum:.3e}, tolerance={_NUMERICAL_TOLERANCE:.3e}"
        )
    return maximum


def _count_compilations(module, fit: Callable[[], DEAResult]):  # type: ignore[no-untyped-def]
    compilations = 0
    original = module.compile_reference

    def counted(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compilations
        compilations += 1
        return original(*args, **kwargs)

    module.compile_reference = counted
    try:
        result = fit()
    finally:
        module.compile_reference = original
    return result, compilations


def run_additive(data: DEAData) -> DEAResult:
    solver = _CountingSolver()
    started = time.perf_counter()
    result, compilations = _count_compilations(
        additive_module,
        lambda: AdditiveDEA(
            returns_to_scale="vrs",
            input_weights={"labor": 0.7, "capital": 1.1, "materials": 0.9},
            output_weights={"routine_service": 1.2, "complex_service": 0.8},
            reference="global",
            solver=solver,
        ).fit(data),
    )
    elapsed = time.perf_counter() - started

    maxima = _validate_additive_family_release(
        result,
        method="additive",
        n_dmus=data.n_dmus,
        measured_solver_calls=solver.calls,
        measured_compilations=compilations,
    )
    max_solver_residual = _assert_solver_residual(result)

    reconstructed = (
        result.slacks.assign(
            weighted_slack=lambda frame: frame["slack"] * frame["weight"]
        )
        .groupby("dmu_id", sort=False)["weighted_slack"]
        .sum()
    )
    summary = result.summary().set_index("dmu_id")
    max_identity_residual = float(
        (summary["distance"] - reconstructed.reindex(summary.index)).abs().max()
    )
    if max_identity_residual > _NUMERICAL_TOLERANCE:
        raise AssertionError("additive weighted-slack identity failed")

    max_target_residual = _slack_target_residual(
        result,
        lambda rows: np.where(
            rows["role"] == "input",
            rows["observed"] - rows["slack"],
            rows["observed"] + rows["slack"],
        ),
    )
    max_lp_violation = max(
        maxima[field] for field in _ADDITIVE_DIAGNOSTIC_RESIDUALS[:7]
    )
    max_raw_account = maxima["max_raw_economic_violation"]
    max_published_account = maxima["max_published_economic_violation"]
    max_peer_account = maxima["max_published_peer_account_violation"]
    max_dual_account = maxima["max_published_dual_account_violation"]
    print(
        f"method=additive n={data.n_dmus} elapsed={elapsed:.3f}s "
        f"score_certified={int(result.summary()['score_valid'].sum())}/{data.n_dmus} "
        f"target_certified={int(result.summary()['target_valid'].sum())}/{data.n_dmus} "
        f"peer_certified={int(result.summary()['peer_valid'].sum())}/{data.n_dmus} "
        f"dual_certified={int(result.summary()['dual_valid'].sum())}/{data.n_dmus} "
        f"primary_solves={solver.calls} secondary_solves=0 "
        f"total_solves={solver.calls} additional_solves=0 "
        f"reference_compilations={compilations} "
        f"max_identity_residual={max_identity_residual:.3e} "
        f"max_target_residual={max_target_residual:.3e} "
        f"max_lp_violation={max_lp_violation:.3e} "
        f"max_raw_account_violation={max_raw_account:.3e} "
        f"max_published_account_violation={max_published_account:.3e} "
        f"max_peer_account_violation={max_peer_account:.3e} "
        f"max_dual_account_violation={max_dual_account:.3e} "
        f"max_solver_violation={max_solver_residual:.3e}"
    )
    return result


def run_ram(data: DEAData) -> DEAResult:
    solver = _CountingSolver()
    started = time.perf_counter()
    result, compilations = _count_compilations(
        additive_module,
        lambda: RangeAdjustedDEA(reference="global", solver=solver).fit(data),
    )
    elapsed = time.perf_counter() - started

    maxima = _validate_additive_family_release(
        result,
        method="ram",
        n_dmus=data.n_dmus,
        measured_solver_calls=solver.calls,
        measured_compilations=compilations,
    )
    max_solver_residual = _assert_solver_residual(result)

    summary = result.summary()
    max_identity_residual = float(
        np.abs(summary["efficiency"] - (1.0 - summary["distance"])).max()
    )
    if max_identity_residual > _NUMERICAL_TOLERANCE:
        raise AssertionError("RAM efficiency = 1 - distance identity failed")
    max_target_residual = _slack_target_residual(
        result,
        lambda rows: np.where(
            rows["role"] == "input",
            rows["observed"] - rows["slack"],
            rows["observed"] + rows["slack"],
        ),
    )
    max_lp_violation = max(
        maxima[field] for field in _ADDITIVE_DIAGNOSTIC_RESIDUALS[:7]
    )
    max_raw_account = maxima["max_raw_economic_violation"]
    max_published_account = maxima["max_published_economic_violation"]
    max_peer_account = maxima["max_published_peer_account_violation"]
    max_dual_account = maxima["max_published_dual_account_violation"]
    print(
        f"method=ram n={data.n_dmus} elapsed={elapsed:.3f}s "
        f"score_certified={int(result.summary()['score_valid'].sum())}/{data.n_dmus} "
        f"target_certified={int(result.summary()['target_valid'].sum())}/{data.n_dmus} "
        f"peer_certified={int(result.summary()['peer_valid'].sum())}/{data.n_dmus} "
        f"dual_certified={int(result.summary()['dual_valid'].sum())}/{data.n_dmus} "
        f"primary_solves={solver.calls} secondary_solves=0 "
        f"total_solves={solver.calls} additional_solves=0 "
        f"reference_compilations={compilations} "
        f"max_identity_residual={max_identity_residual:.3e} "
        f"max_target_residual={max_target_residual:.3e} "
        f"max_lp_violation={max_lp_violation:.3e} "
        f"max_raw_account_violation={max_raw_account:.3e} "
        f"max_published_account_violation={max_published_account:.3e} "
        f"max_peer_account_violation={max_peer_account:.3e} "
        f"max_dual_account_violation={max_dual_account:.3e} "
        f"max_solver_violation={max_solver_residual:.3e}"
    )
    return result


def run_multiplicative(data: DEAData) -> None:
    solver = _SparseCountingSolver()
    started = time.perf_counter()
    result = MultiplicativeDEA(reference="global", solver=solver).fit(data)
    elapsed = time.perf_counter() - started

    _assert_all_optimal(result)
    max_solver_residual = _assert_solver_residual(result)
    if solver.calls != data.n_dmus:
        raise AssertionError(
            "multiplicative DEA must solve one LP per observation; "
            f"observed={solver.calls}, expected={data.n_dmus}"
        )
    compilations = result.metadata["compiled_reference_sets"]
    if compilations != 1:
        raise AssertionError(
            "one global multiplicative reference must compile once; "
            f"observed={compilations}"
        )

    summary = result.summary()
    max_identity_residual = float(
        np.abs(summary["efficiency"] - np.exp(-summary["distance"])).max()
    )
    if max_identity_residual > _NUMERICAL_TOLERANCE:
        raise AssertionError("multiplicative exp(-distance) identity failed")
    max_target_residual = float(
        np.abs(
            result.targets["target"]
            - result.targets["observed"] * result.targets["target_factor"]
        ).max()
    )
    if max_target_residual > _NUMERICAL_TOLERANCE:
        raise AssertionError("multiplicative original-unit target identity failed")
    max_account_violation = _maximum_finite_absolute(
        result.diagnostics,
        "economic_account_violation",
    )
    max_multiplier_violation = max(
        _maximum_finite_absolute(
            result.diagnostics,
            "multiplier_max_reference_violation",
        ),
        _maximum_finite_absolute(
            result.diagnostics,
            "multiplier_objective_residual",
        ),
    )
    if max(max_account_violation, max_multiplier_violation) > _NUMERICAL_TOLERANCE:
        raise AssertionError("multiplicative postsolve account certificate failed")
    print(
        f"method=multiplicative n={data.n_dmus} elapsed={elapsed:.3f}s "
        f"solver_calls={solver.calls} reference_compilations={compilations} "
        f"max_identity_residual={max_identity_residual:.3e} "
        f"max_target_residual={max_target_residual:.3e} "
        f"max_account_violation={max_account_violation:.3e} "
        f"max_multiplier_violation={max_multiplier_violation:.3e} "
        f"max_solver_violation={max_solver_residual:.3e}"
    )


def run_ddf(data: DEAData, *, compute_slacks: bool) -> None:
    solver = _SparseCountingSolver()
    started = time.perf_counter()
    result, compilations = _count_compilations(
        directional_module,
        lambda: DirectionalDistanceDEA(
            input_direction="mean",
            output_direction="mean",
            returns_to_scale="vrs",
            reference="global",
            compute_slacks=compute_slacks,
            solver=solver,
        ).fit(data),
    )
    elapsed = time.perf_counter() - started

    _assert_all_optimal(result)
    max_solver_residual = _assert_solver_residual(result)
    expected_calls = data.n_dmus * (2 if compute_slacks else 1)
    if solver.calls != expected_calls:
        raise AssertionError(
            "unexpected DDF solve count; "
            f"observed={solver.calls}, expected={expected_calls}"
        )
    if compilations != 1:
        raise AssertionError(
            f"one global DDF reference must compile once; observed={compilations}"
        )
    expected_phase_two_calls = data.n_dmus if compute_slacks else 0
    expected_metadata = {
        "phase_one_solver_calls": data.n_dmus,
        "phase_two_solver_calls": expected_phase_two_calls,
        "solver_calls": expected_calls,
        "compiled_reference_sets": compilations,
        "additional_solver_calls": 0,
    }
    observed_metadata = {key: result.metadata.get(key) for key in expected_metadata}
    if observed_metadata != expected_metadata:
        raise AssertionError(
            "DDF result metadata must match measured execution; "
            f"observed={observed_metadata!r}, expected={expected_metadata!r}"
        )

    summary = result.summary()
    if not summary["score_valid"].fillna(False).all():
        raise AssertionError("every DDF score must pass its primary release gate")
    if not summary["peer_valid"].fillna(False).all():
        raise AssertionError("every displayed DDF peer account must certify")
    if not summary["dual_valid"].fillna(False).all():
        raise AssertionError("every displayed DDF dual account must be complete")
    if compute_slacks:
        if not summary["completion_valid"].fillna(False).all():
            raise AssertionError("every requested DDF completion must certify")
        if not summary["target_valid"].fillna(False).all():
            raise AssertionError("every requested DDF target must certify")
    if not result.diagnostics["postsolve_certified"].fillna(False).all():
        raise AssertionError("every executed DDF phase must pass postsolve release")
    max_economic_violation = _maximum_finite_absolute(
        result.diagnostics,
        "max_economic_violation",
    )
    if max_economic_violation > _NUMERICAL_TOLERANCE:
        raise AssertionError("DDF production-account certificate failed")
    if (summary["distance"] < -_NUMERICAL_TOLERANCE).any():
        raise AssertionError("self-inclusive DDF benchmark returned negative distance")
    expected_efficiency = 1.0 / (1.0 + summary["distance"])
    max_identity_residual = float(
        np.abs(summary["efficiency"] - expected_efficiency).max()
    )
    if max_identity_residual > _NUMERICAL_TOLERANCE:
        raise AssertionError("DDF reciprocal efficiency identity failed")

    max_target_residual = float("nan")
    if compute_slacks:
        max_target_residual = _slack_target_residual(
            result,
            lambda rows: np.where(
                rows["role"] == "input",
                rows["observed"] - rows["directional_change"] - rows["slack"],
                rows["observed"] + rows["directional_change"] + rows["slack"],
            ),
        )
    target_residual_label = (
        f"{max_target_residual:.3e}" if compute_slacks else "not_computed"
    )
    print(
        f"method=ddf n={data.n_dmus} full={compute_slacks} "
        f"elapsed={elapsed:.3f}s solver_calls={solver.calls} "
        f"reference_compilations={compilations} "
        f"max_identity_residual={max_identity_residual:.3e} "
        f"max_target_residual={target_residual_label} "
        f"max_economic_violation={max_economic_violation:.3e} "
        f"max_solver_violation={max_solver_residual:.3e}"
    )


def _comparable_fdh_frame(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        column
        for column in (
            "dmu_id",
            "period",
            "role",
            "variable",
            "reference_dmu_id",
            "reference_period",
            "score",
            "efficiency",
            "candidate_count",
            "tied_peer_count",
            "observed",
            "target",
            "slack",
            "lambda",
            "alternative_rank",
            "is_primary",
            "phase",
            "solver_status",
            "iterations",
            "max_primal_violation",
            "algorithm",
        )
        if column in frame
    ]
    if not columns:
        return frame.copy()
    return frame[columns].reset_index(drop=True)


def run_fdh(
    data: DEAData,
    *,
    orientation: str,
    compute_slacks: bool,
    chunk_size: int,
) -> None:
    alternate_chunk_size = chunk_size + 1
    started = time.perf_counter()
    result = FreeDisposalHullDEA(
        orientation=orientation,
        reference="global",
        compute_slacks=compute_slacks,
        chunk_size=chunk_size,
    ).fit(data)
    alternate = FreeDisposalHullDEA(
        orientation=orientation,
        reference="global",
        compute_slacks=compute_slacks,
        chunk_size=alternate_chunk_size,
    ).fit(data)
    elapsed = time.perf_counter() - started

    _assert_all_optimal(result)
    _assert_all_optimal(alternate)
    max_solver_residual = _assert_solver_residual(result)
    _assert_solver_residual(alternate)
    if result.metadata["solver"] != "none_direct_dominance_scan":
        raise AssertionError("FDH benchmark unexpectedly used an optimization solver")
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("one global FDH comparison population is expected")

    for first, second in (
        (result.summary(), alternate.summary()),
        (result.intensities, alternate.intensities),
        (result.targets, alternate.targets),
        (result.slacks, alternate.slacks),
        (result.diagnostics, alternate.diagnostics),
    ):
        assert_frame_equal(
            _comparable_fdh_frame(first),
            _comparable_fdh_frame(second),
            check_exact=False,
            atol=1e-12,
            rtol=0.0,
        )

    max_target_residual = float("nan")
    if compute_slacks:
        score = result.summary()[["dmu_id", "score"]]

        def expected(rows: pd.DataFrame) -> pd.Series:
            joined = rows.merge(score, on="dmu_id", how="left", validate="many_to_one")
            if orientation == "input":
                return np.where(
                    joined["role"] == "input",
                    joined["score"] * joined["observed"] - joined["slack"],
                    joined["observed"] + joined["slack"],
                )
            return np.where(
                joined["role"] == "input",
                joined["observed"] - joined["slack"],
                joined["score"] * joined["observed"] + joined["slack"],
            )

        max_target_residual = _slack_target_residual(result, expected)

    target_residual_label = (
        f"{max_target_residual:.3e}" if compute_slacks else "not_computed"
    )
    print(
        f"method=fdh n={data.n_dmus} orientation={orientation} "
        f"full={compute_slacks} elapsed_two_scans={elapsed:.3f}s "
        f"solver_calls=0 reference_populations=1 chunk_size={chunk_size} "
        f"alternate_chunk_size={alternate_chunk_size} "
        f"max_target_residual={target_residual_label} "
        f"max_solver_violation={max_solver_residual:.3e}"
    )


def run_scale(data: DEAData, *, orientation: str) -> None:
    solver = _CountingSolver()
    started = time.perf_counter()
    result, compilations = _count_compilations(
        radial_module,
        lambda: scale_efficiency(
            data,
            orientation=orientation,
            reference="global",
            solver=solver,
        ),
    )
    elapsed = time.perf_counter() - started

    _assert_all_optimal(result)
    max_solver_residual = _assert_solver_residual(result)
    expected_calls = 2 * data.n_dmus
    if solver.calls != expected_calls:
        raise AssertionError(
            "scale efficiency must solve matched CRS and VRS tasks; "
            f"observed={solver.calls}, expected={expected_calls}"
        )
    if compilations != 1:
        raise AssertionError(
            "matched CRS/VRS scale efficiency must share one compilation; "
            f"observed={compilations}, expected=1"
        )
    if result.metadata["component_solver_calls"] != {
        "crs_efficiency": data.n_dmus,
        "vrs_efficiency": data.n_dmus,
    }:
        raise AssertionError("component solver-call metadata changed")
    if result.metadata["solver_calls"] != expected_calls:
        raise AssertionError("total solver-call metadata changed")
    if result.metadata["component_reference_sets"] != {"crs": 1, "vrs": 1}:
        raise AssertionError("logical component reference-set metadata changed")
    if result.metadata["compiled_reference_sets"] != compilations:
        raise AssertionError("shared compilation metadata changed")

    summary = result.summary()
    reconstructed = summary["crs_efficiency"] / summary["vrs_efficiency"]
    max_identity_residual = float(
        np.abs(summary["scale_efficiency"] - reconstructed).max()
    )
    if max_identity_residual > _NUMERICAL_TOLERANCE:
        raise AssertionError("scale-efficiency ratio identity failed")
    print(
        f"method=scale n={data.n_dmus} orientation={orientation} "
        f"elapsed={elapsed:.3f}s solver_calls={solver.calls} "
        f"reference_compilations={compilations} "
        f"max_identity_residual={max_identity_residual:.3e} "
        f"max_solver_violation={max_solver_residual:.3e}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument(
        "--method",
        choices=(*_METHODS, "all"),
        nargs="+",
        default=["all"],
    )
    parser.add_argument(
        "--orientation",
        choices=("input", "output"),
        default="input",
        help="orientation used by FDH and scale efficiency",
    )
    parser.add_argument(
        "--score-only",
        action="store_true",
        help="skip DDF and FDH slack completion",
    )
    parser.add_argument("--chunk-size", type=int, default=256)
    args = parser.parse_args()

    if args.chunk_size <= 0:
        parser.error("--chunk-size must be positive")
    selected = set(_METHODS if "all" in args.method else args.method)
    data = make_data(args.n_dmus)
    compute_slacks = not args.score_only

    if "additive" in selected:
        run_additive(data)
    if "ram" in selected:
        run_ram(data)
    if "multiplicative" in selected:
        run_multiplicative(data)
    if "ddf" in selected:
        run_ddf(data, compute_slacks=compute_slacks)
    if "fdh" in selected:
        run_fdh(
            data,
            orientation=args.orientation,
            compute_slacks=compute_slacks,
            chunk_size=args.chunk_size,
        )
    if "scale" in selected:
        run_scale(data, orientation=args.orientation)


if __name__ == "__main__":
    main()
