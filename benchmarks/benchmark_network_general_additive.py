"""Repeatable benchmark for the Cook et al. general additive network kernel.

The deterministic graph is an open five-process DAG.  Resources enter every
process, services may leave before the terminal process, two branches merge,
and one link skips an adjacent process.

Run from an editable development environment, for example:

    python benchmarks/benchmark_network_general_additive.py --n-dmus 100
    python benchmarks/benchmark_network_general_additive.py --n-dmus 1000
    python benchmarks/benchmark_network_general_additive.py \
        --n-dmus 100 1000

A small local/CI smoke run can use ``--n-dmus 20``.  The 1,000-DMU case is a
scheduled or release benchmark rather than a routine test.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

import deapack.network.cook_additive as cook_module
from deapack import (
    CookZhuBiYangAdditiveDEA,
    LinkSpec,
    NetworkData,
    NetworkSpec,
    ProcessSpec,
)
from deapack.solvers import SciPyHiGHSSolver


def make_data(n_dmus: int) -> NetworkData:
    """Return a deterministic positive open-network benchmark population."""
    if n_dmus <= 0:
        raise ValueError("n_dmus must be positive")

    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 5.0, 1.0)
    intake_quality = 0.70 + 0.30 * ((position % 37) / 36.0)
    screening_quality = 0.68 + 0.32 * ((position % 31) / 30.0)
    treatment_quality = 0.66 + 0.34 * ((position % 29) / 28.0)
    support_quality = 0.69 + 0.31 * ((position % 23) / 22.0)
    integration_quality = 0.67 + 0.33 * ((position % 41) / 40.0)

    frame = pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "staff": scale * (20.0 + (position % 17)),
            "capital": scale * (25.0 + (position % 19)),
            "screening_budget": scale * (8.0 + (position % 13)),
            "clinical_labor": scale * (12.0 + (position % 11)),
            "support_budget": scale * (7.0 + (position % 7)),
            "coordination": scale * (5.0 + (position % 5)),
        }
    )
    intake_capacity = np.sqrt(frame["staff"] * frame["capital"])
    frame["cases"] = intake_capacity * intake_quality * (1.0 + (position % 13) / 35.0)
    frame["direct_referrals"] = (
        np.power(frame["staff"], 0.6)
        * np.power(frame["capital"], 0.4)
        * intake_quality
        * (0.55 + (position % 11) / 40.0)
    )
    frame["early_service"] = (
        intake_capacity * intake_quality * (0.30 + (position % 9) / 50.0)
    )

    screening_capacity = np.sqrt(frame["cases"] * frame["screening_budget"])
    frame["assessed_cases"] = (
        screening_capacity * screening_quality * (0.90 + (position % 7) / 30.0)
    )
    frame["support_referrals"] = (
        screening_capacity * screening_quality * (0.45 + (position % 5) / 25.0)
    )
    frame["screening_outcome"] = (
        screening_capacity * screening_quality * (0.25 + (position % 11) / 60.0)
    )

    treatment_capacity = (
        np.power(frame["assessed_cases"], 0.45)
        * np.power(frame["direct_referrals"], 0.20)
        * np.power(frame["clinical_labor"], 0.35)
    )
    frame["followup"] = (
        treatment_capacity * treatment_quality * (0.75 + (position % 13) / 45.0)
    )
    frame["recovered"] = (
        treatment_capacity * treatment_quality * (0.55 + (position % 17) / 50.0)
    )

    support_capacity = np.sqrt(frame["support_referrals"] * frame["support_budget"])
    frame["supported_cases"] = (
        support_capacity * support_quality * (0.80 + (position % 7) / 35.0)
    )
    frame["support_outcome"] = (
        support_capacity * support_quality * (0.50 + (position % 13) / 55.0)
    )

    integration_capacity = (
        np.power(frame["followup"], 0.35)
        * np.power(frame["supported_cases"], 0.35)
        * np.power(frame["coordination"], 0.30)
    )
    frame["final_quality"] = (
        integration_capacity * integration_quality * (0.90 + (position % 19) / 50.0)
    )
    frame["durable_outcome"] = (
        integration_capacity * integration_quality * (0.70 + (position % 17) / 45.0)
    )

    specification = NetworkSpec(
        processes=(
            ProcessSpec(
                "integration",
                inputs=("followup", "supported_cases", "coordination"),
                outputs=("final_quality", "durable_outcome"),
            ),
            ProcessSpec(
                "support",
                inputs=("support_referrals", "support_budget"),
                outputs=("supported_cases", "support_outcome"),
            ),
            ProcessSpec(
                "intake",
                inputs=("staff", "capital"),
                outputs=("cases", "direct_referrals", "early_service"),
            ),
            ProcessSpec(
                "treatment",
                inputs=(
                    "assessed_cases",
                    "direct_referrals",
                    "clinical_labor",
                ),
                outputs=("followup", "recovered"),
            ),
            ProcessSpec(
                "screening",
                inputs=("cases", "screening_budget"),
                outputs=(
                    "assessed_cases",
                    "support_referrals",
                    "screening_outcome",
                ),
            ),
        ),
        links=(
            LinkSpec(
                "support_to_integration",
                source="support",
                target="integration",
                variables="supported_cases",
            ),
            LinkSpec(
                "intake_to_treatment",
                source="intake",
                target="treatment",
                variables="direct_referrals",
            ),
            LinkSpec(
                "screening_to_support",
                source="screening",
                target="support",
                variables="support_referrals",
            ),
            LinkSpec(
                "intake_to_screening",
                source="intake",
                target="screening",
                variables="cases",
            ),
            LinkSpec(
                "treatment_to_integration",
                source="treatment",
                target="integration",
                variables="followup",
            ),
            LinkSpec(
                "screening_to_treatment",
                source="screening",
                target="treatment",
                variables="assessed_cases",
            ),
        ),
    )
    return NetworkData.from_frame(frame, dmu="dmu", spec=specification)


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


@dataclass(frozen=True, slots=True)
class BenchmarkObservation:
    elapsed: float
    compile_calls: int
    solver_calls: int
    primary_solves: int
    secondary_solves: int
    projection_fallback_solves: int
    constraint_rows: int
    multiplier_columns: int
    constraint_nnz: int
    max_lp_violation: float
    max_raw_economic_violation: float
    max_published_economic_violation: float
    max_process_constraint_violation: float
    max_link_balance_violation: float


def _maximum_finite_absolute(frame: Any, field: str) -> float:
    values = np.asarray(frame[field], dtype=np.float64)
    finite = np.abs(values[np.isfinite(values)])
    if not finite.size:
        raise AssertionError(f"no finite benchmark values for {field!r}")
    return float(finite.max(initial=0.0))


def _require_columns(frame: Any, required: set[str], *, table: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise AssertionError(f"{table} is missing required fields: {sorted(missing)!r}")


def _fit_with_counts(
    data: NetworkData,
) -> tuple[Any, BenchmarkObservation]:
    solver = _CountingSolver()
    compiled_references = []
    compile_calls = 0
    original_compile = cook_module.compile_general_additive_reference

    def counted_compile(*args, **kwargs):
        nonlocal compile_calls
        compile_calls += 1
        reference = original_compile(*args, **kwargs)
        compiled_references.append(reference)
        return reference

    cook_module.compile_general_additive_reference = counted_compile
    try:
        start = time.perf_counter()
        result = CookZhuBiYangAdditiveDEA(solver=solver).fit(data)
        elapsed = time.perf_counter() - start
    finally:
        cook_module.compile_general_additive_reference = original_compile

    if compile_calls != 1 or len(compiled_references) != 1:
        raise AssertionError(
            "one global reference set must compile exactly once; "
            f"observed={compile_calls}"
        )
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("result metadata must report one compiled reference")
    if solver.calls != data.n_dmus:
        raise AssertionError(
            "general additive system appraisal must solve one primary LP per "
            f"observation; observed={solver.calls}, expected={data.n_dmus}"
        )
    phase_counts = result.diagnostics["phase"].value_counts().to_dict()
    if phase_counts != {"system": data.n_dmus}:
        raise AssertionError(f"unexpected diagnostic solve phases: {phase_counts!r}")

    reference = compiled_references[0]
    constraints = reference.process_constraints
    return result, BenchmarkObservation(
        elapsed=elapsed,
        compile_calls=compile_calls,
        solver_calls=solver.calls,
        primary_solves=int(result.metadata["primary_solver_calls"]),
        secondary_solves=int(result.metadata["secondary_solver_calls"]),
        projection_fallback_solves=int(
            result.metadata["projection_fallback_solver_calls"]
        ),
        constraint_rows=int(constraints.shape[0]),
        multiplier_columns=int(constraints.shape[1]),
        constraint_nnz=int(constraints.nnz),
        max_lp_violation=max(
            _maximum_finite_absolute(
                result.diagnostics,
                "max_constraint_violation",
            ),
            _maximum_finite_absolute(result.diagnostics, "equality_violation"),
            _maximum_finite_absolute(result.diagnostics, "max_bound_violation"),
            _maximum_finite_absolute(result.diagnostics, "objective_residual"),
            _maximum_finite_absolute(result.diagnostics, "duality_gap"),
            _maximum_finite_absolute(result.diagnostics, "max_dual_violation"),
            _maximum_finite_absolute(
                result.diagnostics,
                "complementarity_violation",
            ),
        ),
        max_raw_economic_violation=_maximum_finite_absolute(
            result.diagnostics,
            "max_raw_economic_violation",
        ),
        max_published_economic_violation=_maximum_finite_absolute(
            result.diagnostics,
            "max_published_economic_violation",
        ),
        max_process_constraint_violation=_maximum_finite_absolute(
            result.diagnostics,
            "max_process_constraint_violation",
        ),
        max_link_balance_violation=_maximum_finite_absolute(
            result.diagnostics,
            "link_balance_violation",
        ),
    )


def _validate_result(
    result: Any,
    observation: BenchmarkObservation,
    *,
    n_dmus: int,
    tolerance: float = 1.0e-7,
) -> None:
    summary = result.summary()
    _require_columns(
        summary,
        {
            "score_valid",
            "score_status",
            "process_account_valid",
            "process_account_status",
            "link_account_valid",
            "link_account_status",
            "target_valid",
            "target_status",
            "peer_valid",
            "peer_status",
            "solver_status",
            "backend_solver_status",
            "raw_solver_status",
        },
        table="summary",
    )
    if len(summary) != n_dmus:
        raise AssertionError(
            f"summary row count mismatch: observed={len(summary)}, expected={n_dmus}"
        )
    for field in ("score_valid", "process_account_valid", "link_account_valid"):
        if not summary[field].eq(True).all():
            raise AssertionError(f"every benchmark row requires {field}=True")
    for field in ("score_status", "process_account_status", "link_account_status"):
        if not summary[field].eq("defined").all():
            raise AssertionError(f"every benchmark row requires {field}=defined")
    for field in ("target_valid", "peer_valid"):
        if not summary[field].eq(False).all():
            raise AssertionError(f"{field} must remain false without a source contract")
    for field in ("target_status", "peer_status"):
        if not summary[field].eq("not_available_in_source_contract").all():
            raise AssertionError(f"{field} must expose the source boundary")
    for field in ("solver_status", "backend_solver_status", "raw_solver_status"):
        if not summary[field].eq("optimal").all():
            raise AssertionError(f"every benchmark row requires {field}=optimal")

    diagnostics = result.diagnostics
    required_diagnostics = {
        "lp_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_economic_postsolve_certified",
        "economic_postsolve_certified",
        "published_process_account_certified",
        "published_link_account_certified",
        "published_peer_account_certified",
        "postsolve_certified",
        "max_constraint_violation",
        "equality_violation",
        "max_bound_violation",
        "objective_residual",
        "duality_gap",
        "max_dual_violation",
        "complementarity_violation",
        "max_raw_economic_violation",
        "max_published_economic_violation",
        "max_process_constraint_violation",
        "normalization_violation",
        "objective_account_violation",
        "minimum_share_violation",
        "link_balance_violation",
    }
    _require_columns(diagnostics, required_diagnostics, table="diagnostics")
    certified_fields = (
        "lp_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_economic_postsolve_certified",
        "economic_postsolve_certified",
        "published_process_account_certified",
        "published_link_account_certified",
        "postsolve_certified",
    )
    if not diagnostics[list(certified_fields)].eq(True).all().all():
        raise AssertionError("every general-additive account must be certified")
    if not diagnostics["published_peer_account_certified"].isna().all():
        raise AssertionError("the source contract must not fabricate peer certificates")

    metadata = result.metadata
    required_metadata = {
        "compiled_reference_sets",
        "primary_solver_calls",
        "secondary_solver_calls",
        "projection_fallback_solver_calls",
        "solver_calls",
        "additional_solver_calls",
        "certificate_extra_solver_calls",
    }
    missing_metadata = required_metadata.difference(metadata)
    if missing_metadata:
        raise AssertionError(
            f"metadata is missing required fields: {sorted(missing_metadata)!r}"
        )
    expected_counts = {
        "primary_solver_calls": n_dmus,
        "secondary_solver_calls": 0,
        "projection_fallback_solver_calls": 0,
        "solver_calls": n_dmus,
        "additional_solver_calls": 0,
        "certificate_extra_solver_calls": 0,
    }
    for field, expected in expected_counts.items():
        if metadata[field] != expected:
            raise AssertionError(
                f"{field} mismatch: observed={metadata[field]}, expected={expected}"
            )
    if observation.compile_calls != 1 or metadata["compiled_reference_sets"] != 1:
        raise AssertionError("one global reference must compile exactly once")
    if (
        observation.solver_calls != n_dmus
        or observation.primary_solves != n_dmus
        or observation.secondary_solves != 0
        or observation.projection_fallback_solves != 0
    ):
        raise AssertionError("counting backend solve graph is inconsistent")
    for field, value in (
        ("max_lp_violation", observation.max_lp_violation),
        ("max_raw_economic_violation", observation.max_raw_economic_violation),
        (
            "max_published_economic_violation",
            observation.max_published_economic_violation,
        ),
        (
            "max_process_constraint_violation",
            observation.max_process_constraint_violation,
        ),
        ("max_link_balance_violation", observation.max_link_balance_violation),
    ):
        if not np.isfinite(value) or value > tolerance:
            raise AssertionError(f"{field} exceeds tolerance: {value:.12g}")


def run_case(n_dmus: int) -> BenchmarkObservation:
    data = make_data(n_dmus)
    result, observation = _fit_with_counts(data)
    _validate_result(result, observation, n_dmus=n_dmus)
    summary = result.summary()
    optimal = int((summary["solver_status"] == "optimal").sum())
    if optimal != n_dmus:
        raise AssertionError(
            f"all benchmark fits should be optimal; observed={optimal}/{n_dmus}"
        )
    certified = int(summary["score_valid"].fillna(False).sum())
    if certified != n_dmus:
        raise AssertionError(
            "all benchmark fits must pass both postsolve certificates; "
            f"observed={certified}/{n_dmus}"
        )
    maximum_residual = float(summary["reconstruction_residual"].abs().max())
    matrix_entries = observation.constraint_rows * observation.multiplier_columns
    density = observation.constraint_nnz / matrix_entries
    print(
        f"n={n_dmus} processes=5 links=6 variables=18 "
        f"elapsed={observation.elapsed:.3f}s "
        f"optimal={optimal}/{n_dmus} "
        f"certified={certified}/{n_dmus} "
        f"compiled_reference_sets={observation.compile_calls} "
        f"primary_solves={observation.primary_solves} "
        f"secondary_solves={observation.secondary_solves} "
        f"projection_fallback_solves={observation.projection_fallback_solves} "
        f"total_solves={observation.solver_calls} additional_solves=0 "
        f"constraint_shape="
        f"{observation.constraint_rows}x{observation.multiplier_columns} "
        f"constraint_nnz={observation.constraint_nnz} "
        f"constraint_density={density:.6f} "
        f"max_identity_residual={maximum_residual:.3e} "
        f"max_lp_violation={observation.max_lp_violation:.3e} "
        f"max_raw_account_violation="
        f"{observation.max_raw_economic_violation:.3e} "
        f"max_published_account_violation="
        f"{observation.max_published_economic_violation:.3e}"
    )
    return observation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--n-dmus",
        type=int,
        nargs="+",
        default=(100,),
        help="one or more population sizes; use 1000 for the release case",
    )
    args = parser.parse_args()

    for n_dmus in args.n_dmus:
        run_case(n_dmus)


if __name__ == "__main__":
    main()
