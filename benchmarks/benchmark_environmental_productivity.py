"""Deterministic benchmark for environmental productivity task graphs.

The balanced panel keeps every quantity strictly positive.  Desirable outputs
share one modest green-technology growth factor while undesirable output
falls by its reciprocal.  This preserves feasible cross-period comparisons
for the source-qualified CRS common-factor weak-disposal presets.

Run the routine two-preset benchmark with:

    python benchmarks/benchmark_environmental_productivity.py \
        --n-dmus 100 --periods 4

Run one operator or a larger release case with:

    python benchmarks/benchmark_environmental_productivity.py \
        --operator gml --n-dmus 500 --periods 4

Audit opt-in all-forward reporting with:

    python benchmarks/benchmark_environmental_productivity.py \
        --operator gml --comparison-pairs all --n-dmus 100 --periods 8
"""

from __future__ import annotations

import argparse
import time
from typing import Literal

import numpy as np
import pandas as pd

import deapack.analysis.environmental_productivity as productivity_module
from deapack import (
    DEAData,
    GlobalMalmquistLuenbergerProductivityIndex,
    MalmquistLuenbergerProductivityIndex,
)
from deapack.results import DEAResult
from deapack.solvers import SciPyHiGHSSolver

_OPERATORS = ("ml", "gml")
ComparisonPairMode = Literal["adjacent", "all"]
_NUMERICAL_TOLERANCE = 1e-7
_IDENTITY_TOLERANCE = 1e-10
_COMMON_FACTOR_TECHNOLOGY = (
    "environmental.weak_disposal.common_factor.crs.chung_fare_grosskopf_1997"
)


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


def make_panel(n_dmus: int, periods: int) -> DEAData:
    """Create a deterministic positive balanced environmental panel."""
    if n_dmus < 4:
        raise ValueError("n-dmus must be at least four")
    if periods < 2:
        raise ValueError("periods must be at least two")

    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 5.0, 1.0)
    management = 0.72 + 0.28 * ((position % 17.0) / 16.0)
    labor = scale * (8.0 + position % 13.0)
    capital = scale * (11.0 + position % 11.0)
    capacity = np.sqrt(labor * capital)
    base_routine = capacity * management * (0.88 + (position % 7.0) / 25.0)
    base_complex = capacity * management * (0.56 + (position % 5.0) / 20.0)
    base_emissions = capacity * (0.45 + 0.18 * ((position % 9.0) / 8.0))

    frames: list[pd.DataFrame] = []
    for period in range(periods):
        green_factor = 1.02**period
        frames.append(
            pd.DataFrame(
                {
                    "dmu": [f"E{index:06d}" for index in range(n_dmus)],
                    "period": period,
                    "labor": labor,
                    "capital": capital,
                    "routine_service": base_routine * green_factor,
                    "complex_service": base_complex * green_factor,
                    "emissions": base_emissions / green_factor,
                }
            )
        )

    return DEAData.from_frame(
        pd.concat(frames, ignore_index=True),
        dmu="dmu",
        period="period",
        inputs=("labor", "capital"),
        outputs=("routine_service", "complex_service"),
        bad_outputs="emissions",
    )


def _maximum_finite_absolute(frame: pd.DataFrame, column: str) -> float:
    values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    finite = np.abs(values[np.isfinite(values)])
    if finite.size == 0:
        raise AssertionError(f"{column} has no finite benchmark values")
    return float(finite.max())


def _fit_with_compilation_count(model, data: DEAData):  # type: ignore[no-untyped-def]
    compilations = 0
    original = productivity_module.compile_reference

    def counted(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compilations
        compilations += 1
        return original(*args, **kwargs)

    productivity_module.compile_reference = counted
    try:
        result = model.fit(data)
    finally:
        productivity_module.compile_reference = original
    return result, compilations


def _assert_named_preset_metadata(operator: str, result: DEAResult) -> None:
    metadata = result.metadata
    expected = {
        "ml": (
            "productivity.malmquist_luenberger.chung_fare_grosskopf_1997",
            "chung_fare_grosskopf_geometric",
        ),
        "gml": (
            "productivity.global_malmquist_luenberger.oh_2010",
            "oh_global_malmquist_luenberger",
        ),
    }
    method_id, variant = expected[operator]
    required = {
        "method_id": method_id,
        "variant": variant,
        "returns_to_scale": "crs",
        "bad_output_disposability": "weak_common_factor",
        "bad_output_constraint": "equality",
        "environmental_technology": _COMMON_FACTOR_TECHNOLOGY,
        "named_weak_disposal_equivalence": "source_exact_under_crs",
        "input_direction": "zeros",
        "output_direction": "observed",
        "bad_output_direction": "observed",
    }
    for key, value in required.items():
        if metadata.get(key) != value:
            raise AssertionError(
                f"{operator} preset metadata drifted at {key!r}; "
                f"observed={metadata.get(key)!r}, expected={value!r}"
            )
    if metadata.get("null_jointness") is not True:
        raise AssertionError(f"{operator} preset must retain null jointness")


def run_case(
    data: DEAData,
    *,
    operator: str,
    n_organizations: int,
    periods: int,
    comparison_pairs: ComparisonPairMode = "adjacent",
) -> DEAResult:
    if operator != "gml" and comparison_pairs != "adjacent":
        raise ValueError("comparison_pairs='all' is benchmarked only for gml")
    solver = _CountingSolver()
    if operator == "ml":
        model = MalmquistLuenbergerProductivityIndex(solver=solver)
        expected_solves = n_organizations * (3 * periods - 2)
        expected_compilations = periods
    elif operator == "gml":
        model = GlobalMalmquistLuenbergerProductivityIndex(
            comparison_pairs=comparison_pairs,
            solver=solver,
        )
        expected_solves = 2 * n_organizations * periods
        expected_compilations = periods + 1
    else:
        raise ValueError(
            f"unknown source-qualified environmental productivity preset {operator!r}"
        )

    started = time.perf_counter()
    result, compilations = _fit_with_compilation_count(model, data)
    elapsed = time.perf_counter() - started

    summary = result.summary()
    diagnostics = result.diagnostics
    expected_transitions = n_organizations * (
        periods * (periods - 1) // 2
        if operator == "gml" and comparison_pairs == "all"
        else periods - 1
    )
    if len(summary) != expected_transitions:
        raise AssertionError(
            "balanced panel transition count is inconsistent; "
            f"observed={len(summary)}, expected={expected_transitions}"
        )
    if not (summary["solver_status"] == "optimal").all():
        raise AssertionError(f"{operator} produced unresolved productivity rows")
    if not (diagnostics["solver_status"] == "optimal").all():
        raise AssertionError(f"{operator} produced unresolved distance tasks")
    if not np.isfinite(diagnostics["directional_distance"]).all():
        raise AssertionError(f"{operator} produced non-finite directional distances")
    for field in (
        "score_valid",
        "postsolve_certified",
        "all_four_distance_programs_certified",
        "all_four_economic_distance_claims_certified",
        "multiplicative_account_certified",
        "economic_postsolve_certified",
        "peer_valid",
    ):
        if not summary[field].astype("boolean").fillna(False).all():
            raise AssertionError(
                f"{operator} did not certify every transition field {field!r}"
            )
    if not summary["score_status"].eq("defined").all():
        raise AssertionError(f"{operator} produced an undefined certified score")
    for field in (
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "economic_postsolve_certified",
        "published_peer_account_certified",
    ):
        if not diagnostics[field].astype("boolean").fillna(False).all():
            raise AssertionError(
                f"{operator} did not certify every distance-task field {field!r}"
            )
    if result.metadata.get("additional_solver_calls") != 0:
        raise AssertionError(f"{operator} certification added a solver call")
    certificate_policy = result.metadata.get("postsolve_certificate", {})
    if certificate_policy.get("additional_solver_calls") != 0:
        raise AssertionError(
            f"{operator} certificate metadata does not preserve the solve budget"
        )

    minimum_factor = float((1.0 + diagnostics["directional_distance"]).min())
    if minimum_factor <= 0:
        raise AssertionError(
            f"{operator} violates the positive 1 + beta domain; "
            f"minimum={minimum_factor:.6g}"
        )

    if solver.calls != expected_solves:
        raise AssertionError(
            f"{operator} solve graph is inconsistent; "
            f"observed={solver.calls}, expected={expected_solves}"
        )
    if result.metadata["unique_distance_solves"] != solver.calls:
        raise AssertionError(
            f"{operator} metadata does not match counted unique distance solves"
        )
    if compilations != expected_compilations:
        raise AssertionError(
            f"{operator} reference compilation count is inconsistent; "
            f"observed={compilations}, expected={expected_compilations}"
        )
    if result.metadata["compiled_reference_sets"] != compilations:
        raise AssertionError(
            f"{operator} metadata does not match counted reference compilations"
        )

    reconstructed = summary["efficiency_change"] * summary["technical_change"]
    independent_residual = summary["productivity_change"] - reconstructed
    maximum_independent_residual = float(
        np.abs(independent_residual.to_numpy(dtype=float)).max(initial=0.0)
    )
    maximum_reported_residual = _maximum_finite_absolute(
        summary,
        "decomposition_residual",
    )
    if (
        maximum_independent_residual > _IDENTITY_TOLERANCE
        or maximum_reported_residual > _IDENTITY_TOLERANCE
    ):
        raise AssertionError(
            f"{operator} decomposition residual exceeds tolerance; "
            f"independent={maximum_independent_residual:.3e}, "
            f"reported={maximum_reported_residual:.3e}"
        )
    maximum_solver_violation = _maximum_finite_absolute(
        diagnostics,
        "max_primal_violation",
    )
    if maximum_solver_violation > _NUMERICAL_TOLERANCE:
        raise AssertionError(
            f"{operator} primal violation exceeds tolerance; "
            f"observed={maximum_solver_violation:.3e}"
        )
    certificate_columns = (
        "max_constraint_violation",
        "equality_violation",
        "max_bound_violation",
        "objective_residual",
        "duality_gap",
        "max_dual_violation",
        "complementarity_violation",
        "max_economic_violation",
        "max_published_peer_account_violation",
    )
    maximum_certificate_residual = max(
        _maximum_finite_absolute(diagnostics, column) for column in certificate_columns
    )
    maximum_certificate_residual = max(
        maximum_certificate_residual,
        _maximum_finite_absolute(summary, "max_multiplicative_account_residual"),
    )
    if maximum_certificate_residual > _NUMERICAL_TOLERANCE:
        raise AssertionError(
            f"{operator} postsolve certificate exceeds tolerance; "
            f"observed={maximum_certificate_residual:.3e}"
        )

    _assert_named_preset_metadata(operator, result)
    if operator == "gml":
        if result.metadata.get("cross_period_directional_solves") != 0:
            raise AssertionError("GML must not request cross-period solves")
        expected_complexity = "O(D*P^2)" if comparison_pairs == "all" else "O(D*P)"
        if result.metadata.get("comparison_pair_mode") != comparison_pairs:
            raise AssertionError("GML comparison-pair metadata drifted")
        if result.metadata.get("comparison_output_size_complexity") != (
            expected_complexity
        ):
            raise AssertionError("GML comparison output-size disclosure drifted")
    elif result.metadata.get("cross_period_negative_distance") != (
        "allowed_and_required"
    ):
        raise AssertionError("ML must retain cross-period distances")

    pair_mode = result.metadata.get("comparison_pair_mode", "adjacent")
    output_size = result.metadata.get("comparison_output_size_complexity", "O(D*P)")
    print(
        f"operator={operator} organizations={n_organizations} periods={periods} "
        f"comparison_pair_mode={pair_mode} output_size={output_size} "
        f"observations={data.n_dmus} transitions={expected_transitions} "
        f"elapsed={elapsed:.3f}s requested_distance_tasks={len(diagnostics)} "
        f"unique_distance_solves={solver.calls} "
        f"compiled_reference_sets={compilations} "
        f"min_one_plus_beta={minimum_factor:.6f} "
        f"max_independent_residual={maximum_independent_residual:.3e} "
        f"max_reported_residual={maximum_reported_residual:.3e} "
        f"max_solver_violation={maximum_solver_violation:.3e} "
        f"max_certificate_residual={maximum_certificate_residual:.3e}"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument("--periods", type=int, default=4)
    parser.add_argument(
        "--operator",
        choices=(*_OPERATORS, "all"),
        nargs="+",
        default=["all"],
    )
    parser.add_argument(
        "--comparison-pairs",
        choices=("adjacent", "all"),
        default="adjacent",
        help="GML-only result enumeration; all is opt-in O(D*P^2) output.",
    )
    parser.add_argument(
        "--include-gml-all-pairs",
        action="store_true",
        help="Also audit opt-in GML all-pairs output after the selected cases.",
    )
    args = parser.parse_args()

    try:
        data = make_panel(args.n_dmus, args.periods)
    except ValueError as error:
        parser.error(str(error))
    selected = _OPERATORS if "all" in args.operator else tuple(args.operator)
    if args.comparison_pairs != "adjacent" and selected != ("gml",):
        parser.error("--comparison-pairs all requires --operator gml")
    if args.include_gml_all_pairs and "gml" not in selected:
        parser.error("--include-gml-all-pairs requires an operator selection with gml")
    for operator in selected:
        run_case(
            data,
            operator=operator,
            n_organizations=args.n_dmus,
            periods=args.periods,
            comparison_pairs=args.comparison_pairs,
        )
    if args.include_gml_all_pairs and args.comparison_pairs == "adjacent":
        run_case(
            data,
            operator="gml",
            n_organizations=args.n_dmus,
            periods=args.periods,
            comparison_pairs="all",
        )


if __name__ == "__main__":
    main()
