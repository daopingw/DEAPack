"""Repeatable benchmark for seven productivity operators.

The benchmark fits a deterministic balanced panel and audits the public
distance-task graph. Requested tasks are counted from retained diagnostic
roles. Unique tasks are independently reconstructed from the evaluated
observation and declared reference technology, then compared with both the
public metadata and a counting solver.

Examples:

    python benchmarks/benchmark_productivity_operators.py
    python benchmarks/benchmark_productivity_operators.py --operator global
    python benchmarks/benchmark_productivity_operators.py \
        --operator global --comparison-pairs all --n-dmus 100 --periods 8
    python benchmarks/benchmark_productivity_operators.py \
        --operator all --n-dmus 1000 --periods 4
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Hashable, Sequence
from typing import Literal

import numpy as np
import pandas as pd

import deapack.analysis._pooled_malmquist as pooled_module
import deapack.analysis.biennial_malmquist as biennial_module
import deapack.analysis.environmental_productivity as environmental_module
import deapack.analysis.global_malmquist as global_module
import deapack.analysis.luenberger as luenberger_module
import deapack.analysis.productivity as productivity_module
from deapack import (
    APZMalmquistLuenbergerProductivityIndex,
    BiennialMalmquistProductivityIndex,
    DEAData,
    FGNZEnhancedMalmquistProductivityIndex,
    GlobalMalmquistProductivityIndex,
    LuenbergerProductivityIndicator,
    MalmquistProductivityIndex,
    RayDesliMalmquistProductivityIndex,
)
from deapack.results import DEAResult
from deapack.solvers import SciPyHiGHSSolver

_OPERATORS = (
    "malmquist",
    "fgnz_enhanced",
    "ray_desli",
    "global",
    "biennial",
    "luenberger",
    "apz",
)
_FULL_CERTIFICATE_MALMQUIST_OPERATORS = ("malmquist", "global", "biennial")
ComparisonPairMode = Literal["adjacent", "all"]
_DISTANCE_ROLES = {
    "malmquist": {
        "base_on_base",
        "comparison_on_base",
        "base_on_comparison",
        "comparison_on_comparison",
    },
    "fgnz_enhanced": {
        "base_on_base",
        "comparison_on_base",
        "base_on_comparison",
        "comparison_on_comparison",
    },
    "ray_desli": {
        "base_on_base",
        "comparison_on_base",
        "base_on_comparison",
        "comparison_on_comparison",
    },
    "global": {
        "base_on_base",
        "comparison_on_comparison",
        "base_on_global",
        "comparison_on_global",
    },
    "biennial": {
        "base_on_base",
        "comparison_on_comparison",
        "base_on_biennial",
        "comparison_on_biennial",
    },
    "luenberger": {
        "base_on_base",
        "comparison_on_base",
        "base_on_comparison",
        "comparison_on_comparison",
    },
    "apz": {
        "base_on_base",
        "comparison_on_base",
        "base_on_comparison",
        "comparison_on_comparison",
    },
}


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


def make_panel(
    n_dmus: int,
    periods: int = 4,
    *,
    ray_desli: bool = False,
    environmental: bool = False,
) -> DEAData:
    """Create a deterministic, strictly positive balanced production panel."""
    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")
    if periods < 2:
        raise ValueError("periods must be at least two")

    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 4.0, 1.0)
    labor = scale * (8.0 + position % 7.0)
    capital = scale * (10.0 + (2.0 * position) % 9.0)
    capacity = np.sqrt(labor * capital)
    practice = 0.72 + 0.28 * ((position % 5.0) / 4.0)

    frames = []
    for period in range(periods):
        period_frame = pd.DataFrame(
            {
                "dmu": [f"P{index:06d}" for index in range(n_dmus)],
                "period": period,
                # Holding the two input profiles fixed gives the
                # source-qualified Ray--Desli benchmark a feasible VRS
                # cross-period witness in both directions. The other
                # operators retain the mildly changing-input panel.
                "labor": (
                    labor
                    if ray_desli or environmental
                    else labor * (1.0 + 0.010 * period)
                ),
                "capital": (
                    capital
                    if ray_desli or environmental
                    else capital * (1.0 + 0.015 * period)
                ),
                "service": (
                    capacity
                    * practice
                    * (1.030**period)
                    * (1.0 + (position % 3.0) / 10.0)
                ),
                "quality": (
                    capacity
                    * practice
                    * (1.020**period)
                    * (0.6 + (position % 4.0) / 12.0)
                ),
            }
        )
        if environmental:
            # One strictly positive CRS ray keeps every APZ own/cross task
            # feasible while retaining a multi-input, multi-good benchmark.
            # The workload still grows with the full period reference matrix.
            period_frame["labor"] = 10.0 * scale
            period_frame["capital"] = 12.0 * scale
            period_frame["service"] = 8.0 * scale * (1.020**period)
            period_frame["quality"] = 5.0 * scale * (1.020**period)
            period_frame["residual"] = 6.0 * scale * (0.980**period)
        frames.append(period_frame)

    return DEAData.from_frame(
        pd.concat(frames, ignore_index=True),
        dmu="dmu",
        period="period",
        inputs=("labor", "capital"),
        outputs="service" if ray_desli else ("service", "quality"),
        bad_outputs="residual" if environmental else None,
    )


def _reference_signature(row: dict[str, object]) -> tuple[object, ...]:
    reference_kind = row.get("reference_kind")
    if reference_kind is None:
        return ("contemporaneous", row["technology_period"])
    if reference_kind == "contemporaneous":
        return ("contemporaneous", row["technology_period"])
    technology_periods = row["technology_periods"]
    if not isinstance(technology_periods, tuple):
        raise AssertionError("pooled task must retain its technology-period tuple")
    return (reference_kind, *technology_periods)


def _distance_task_key(row: dict[str, object]) -> tuple[Hashable, ...]:
    dmu_id = row["dmu_id"]
    evaluated_period = row["evaluated_period"]
    if not isinstance(dmu_id, Hashable) or not isinstance(evaluated_period, Hashable):
        raise AssertionError("distance-task identifiers must be hashable")
    returns_to_scale = row.get("returns_to_scale")
    return (
        dmu_id,
        evaluated_period,
        *_reference_signature(row),
        returns_to_scale,
    )


def _maximum_finite_absolute(frame: pd.DataFrame, column: str) -> float:
    values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    finite = np.abs(values[np.isfinite(values)])
    return float(finite.max(initial=0.0))


def _maximum_required_absolute(
    frame: pd.DataFrame,
    columns: Sequence[str],
) -> float:
    """Require complete finite benchmark evidence and return its maximum."""

    maximum = 0.0
    for column in columns:
        values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise AssertionError(
                f"core productivity benchmark requires finite {column} evidence"
            )
        maximum = max(maximum, float(np.abs(values).max(initial=0.0)))
    return maximum


def _model(
    operator: str,
    solver: _CountingSolver,
    comparison_pairs: ComparisonPairMode,
):  # type: ignore[no-untyped-def]
    if operator == "malmquist":
        return MalmquistProductivityIndex(solver=solver)
    if operator == "fgnz_enhanced":
        return FGNZEnhancedMalmquistProductivityIndex(solver=solver)
    if operator == "ray_desli":
        return RayDesliMalmquistProductivityIndex(solver=solver)
    if operator == "global":
        return GlobalMalmquistProductivityIndex(
            comparison_pairs=comparison_pairs,
            solver=solver,
        )
    if operator == "biennial":
        return BiennialMalmquistProductivityIndex(solver=solver)
    if operator == "luenberger":
        return LuenbergerProductivityIndicator(solver=solver)
    if operator == "apz":
        return APZMalmquistLuenbergerProductivityIndex(solver=solver)
    raise ValueError(f"unsupported productivity operator: {operator!r}")


def _fit_with_compilation_count(
    operator: str,
    model,
    data: DEAData,
):  # type: ignore[no-untyped-def]
    modules = {
        "malmquist": (productivity_module,),
        "fgnz_enhanced": (productivity_module,),
        "ray_desli": (productivity_module,),
        "global": (pooled_module, global_module),
        "biennial": (pooled_module, biennial_module),
        "luenberger": (luenberger_module,),
        "apz": (environmental_module,),
    }[operator]
    compilations = 0
    originals = [(module, module.compile_reference) for module in modules]

    def counted(original):  # type: ignore[no-untyped-def]
        def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
            nonlocal compilations
            compilations += 1
            return original(*args, **kwargs)

        return wrapper

    for module, original in originals:
        module.compile_reference = counted(original)
    try:
        result = model.fit(data)
    finally:
        for module, original in originals:
            module.compile_reference = original
    return result, compilations


def run_case(
    data: DEAData,
    *,
    operator: str,
    comparison_pairs: ComparisonPairMode = "adjacent",
) -> DEAResult:
    """Fit one public operator and enforce its task and identity contracts."""
    if operator != "global" and comparison_pairs != "adjacent":
        raise ValueError("comparison_pairs='all' is benchmarked only for global")
    solver = _CountingSolver()
    model = _model(operator, solver, comparison_pairs)
    started = time.perf_counter()
    result, compilations = _fit_with_compilation_count(operator, model, data)
    elapsed = time.perf_counter() - started

    summary = result.summary()
    diagnostics = result.diagnostics
    if not (summary["solver_status"] == "optimal").all():
        raise AssertionError("every productivity transition must resolve")
    if not (diagnostics["solver_status"] == "optimal").all():
        raise AssertionError("every requested distance task must resolve")
    if set(diagnostics["distance_role"]) != _DISTANCE_ROLES[operator]:
        raise AssertionError("the retained distance-role graph changed")

    certificate_report = ""
    if operator in _FULL_CERTIFICATE_MALMQUIST_OPERATORS:
        if not summary["score_valid"].all():
            raise AssertionError("every certified Malmquist transition must be valid")
        if not summary["score_status"].eq("defined").all():
            raise AssertionError("every certified Malmquist score must be defined")
        if not summary["postsolve_certified"].all():
            raise AssertionError("every four-distance transition must be certified")
        if not summary["multiplicative_account_certified"].all():
            raise AssertionError("every multiplicative account must reconstruct")
        if not summary["raw_multiplicative_account_certified"].all():
            raise AssertionError("every raw multiplicative account must reconstruct")
        if not summary["published_multiplicative_account_certified"].all():
            raise AssertionError(
                "every published multiplicative account must reconstruct"
            )
        if not summary["peer_valid"].all():
            raise AssertionError("every four-distance peer account must reconstruct")

        transition_gate_columns = (
            "all_four_distance_programs_certified",
            "all_four_economic_distance_claims_certified",
            "all_four_peer_accounts_certified",
        )
        for column in transition_gate_columns:
            if not summary[column].all():
                raise AssertionError(f"certified transition failed {column}")
        transition_count_columns = (
            "lp_certified_distance_count",
            "certified_distance_count",
            "economic_certified_distance_count",
            "peer_certified_distance_count",
        )
        for column in transition_count_columns:
            if not summary[column].eq(4).all():
                raise AssertionError(
                    f"every certified transition requires four roles in {column}"
                )

        diagnostic_gate_columns = (
            "lp_postsolve_certified",
            "raw_economic_postsolve_certified",
            "published_output_account_certified",
            "economic_postsolve_certified",
            "published_peer_account_certified",
            "postsolve_certified",
        )
        for column in diagnostic_gate_columns:
            if not diagnostics[column].eq(True).all():
                raise AssertionError(f"certified distance task failed {column}")

        if result.metadata["solver_calls"] != solver.calls:
            raise AssertionError(
                "reported solver calls disagree with the counting backend"
            )
        if result.metadata["additional_solver_calls"] != 0:
            raise AssertionError("Malmquist certification must add no solve")
        certificate_policy = result.metadata["postsolve_certificate"]
        if certificate_policy["additional_solver_calls"] != 0:
            raise AssertionError("postsolve certification must add no solver task")

        diagnostic_residual_columns = (
            "max_constraint_violation",
            "equality_violation",
            "max_bound_violation",
            "objective_residual",
            "duality_gap",
            "max_dual_violation",
            "complementarity_violation",
            "max_raw_economic_violation",
            "max_published_account_violation",
            "max_published_peer_account_violation",
        )
        transition_residual_columns = (
            "max_raw_multiplicative_account_residual",
            "max_published_multiplicative_account_residual",
            "max_multiplicative_account_residual",
        )
        max_certificate_residual = max(
            _maximum_required_absolute(
                diagnostics,
                diagnostic_residual_columns,
            ),
            _maximum_required_absolute(
                summary,
                transition_residual_columns,
            ),
        )
        if max_certificate_residual > float(result.metadata["tolerance"]):
            raise AssertionError(
                "a Malmquist LP, economic, peer, or multiplicative "
                "certificate exceeds tolerance"
            )
        certificate_report = (
            f" certified_lp_roles={int(diagnostics['lp_postsolve_certified'].sum())}"
            f" certified_economic_roles="
            f"{int(diagnostics['economic_postsolve_certified'].sum())}"
            f" certified_peer_roles="
            f"{int(diagnostics['published_peer_account_certified'].sum())}"
            f" certified_multiplicative_accounts="
            f"{int(summary['multiplicative_account_certified'].sum())}"
            f" additional_solves=0"
            f" max_certificate_residual={max_certificate_residual:.3e}"
        )
    elif operator == "luenberger":
        if not summary["score_valid"].all():
            raise AssertionError("every Luenberger transition must be certified")
        if not summary["score_status"].eq("defined").all():
            raise AssertionError("every Luenberger score must be defined")
        if not summary["postsolve_certified"].all():
            raise AssertionError("every Luenberger transition must be certified")
        if not summary["peer_valid"].all():
            raise AssertionError("every Luenberger peer account must reconstruct")
        for column in (
            "all_four_distance_programs_certified",
            "all_four_economic_distance_claims_certified",
            "all_four_peer_accounts_certified",
        ):
            if not summary[column].all():
                raise AssertionError(f"Luenberger transition failed {column}")
        for column in (
            "lp_certified_distance_count",
            "certified_distance_count",
            "economic_certified_distance_count",
            "peer_certified_distance_count",
        ):
            if not summary[column].eq(4).all():
                raise AssertionError(
                    f"every Luenberger transition requires four roles in {column}"
                )
        for column in (
            "lp_postsolve_certified",
            "postsolve_certified",
            "raw_economic_postsolve_certified",
            "published_output_account_certified",
            "economic_postsolve_certified",
            "published_peer_account_certified",
        ):
            if not diagnostics[column].eq(True).all():
                raise AssertionError(f"Luenberger distance task failed {column}")
        if not diagnostics["economic_postsolve_certified"].all():
            raise AssertionError(
                "every Luenberger signed-distance claim must be certified"
            )
        if not summary["additive_account_certified"].all():
            raise AssertionError("every Luenberger additive account must reconstruct")
        certificate_policy = result.metadata["postsolve_certificate"]
        if result.metadata["solver_calls"] != solver.calls:
            raise AssertionError(
                "reported Luenberger solver calls disagree with counting backend"
            )
        if result.metadata["additional_solver_calls"] != 0:
            raise AssertionError("Luenberger certification must add no solve")
        if certificate_policy["additional_solver_calls"] != 0:
            raise AssertionError("Luenberger certification must add no solver task")
        certificate_columns = (
            "max_constraint_violation",
            "equality_violation",
            "max_bound_violation",
            "objective_residual",
            "duality_gap",
            "max_dual_violation",
            "complementarity_violation",
            "max_raw_economic_violation",
            "max_published_account_violation",
            "max_published_peer_account_violation",
        )
        max_certificate_residual = max(
            _maximum_required_absolute(diagnostics, certificate_columns),
            _maximum_required_absolute(
                summary,
                ("max_additive_account_residual",),
            ),
        )
        if max_certificate_residual > float(result.metadata["tolerance"]):
            raise AssertionError("a Luenberger postsolve certificate exceeds tolerance")
        certificate_report = (
            f" certified_lp_roles={int(diagnostics['lp_postsolve_certified'].sum())}"
            f" certified_economic_roles="
            f"{int(diagnostics['economic_postsolve_certified'].sum())}"
            f" certified_peer_roles="
            f"{int(diagnostics['published_peer_account_certified'].sum())}"
            f" certified_additive_accounts="
            f"{int(summary['additive_account_certified'].sum())}"
            f" additional_solves=0"
            f" max_certificate_residual={max_certificate_residual:.3e}"
        )
    elif operator == "apz":
        if not summary["score_valid"].all():
            raise AssertionError("every APZ transition must be certified")
        if not summary["score_status"].eq("defined").all():
            raise AssertionError("every APZ score must be defined")
        if not summary["multiplicative_account_certified"].all():
            raise AssertionError("every APZ multiplicative account must reconstruct")
        if not summary["peer_valid"].all():
            raise AssertionError("every APZ peer account must reconstruct")
        if not diagnostics["postsolve_certified"].all():
            raise AssertionError("every APZ distance LP must be certified")
        if not diagnostics["economic_postsolve_certified"].all():
            raise AssertionError("every APZ production account must be certified")
        certificate_policy = result.metadata["postsolve_certificate"]
        if certificate_policy["additional_solver_calls"] != 0:
            raise AssertionError("APZ certification must add no solver task")
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
        max_certificate_residual = max(
            _maximum_finite_absolute(diagnostics, column)
            for column in certificate_columns
        )
        max_certificate_residual = max(
            max_certificate_residual,
            _maximum_finite_absolute(
                summary,
                "max_multiplicative_account_residual",
            ),
        )
        if max_certificate_residual > 1e-7:
            raise AssertionError("an APZ postsolve certificate exceeds tolerance")
        certificate_report = f" max_certificate_residual={max_certificate_residual:.3e}"

    requested_tasks = len(diagnostics)
    tasks_per_transition = {
        "fgnz_enhanced": 6,
        "ray_desli": 8,
    }.get(operator, 4)
    expected_requested = tasks_per_transition * len(summary)
    if requested_tasks != expected_requested:
        raise AssertionError(
            "each transition must retain its declared distance-task graph: "
            f"observed={requested_tasks}, expected={expected_requested}"
        )

    task_keys = {
        _distance_task_key(row) for row in diagnostics.to_dict(orient="records")
    }
    unique_tasks = len(task_keys)
    metadata_unique = result.metadata["unique_distance_solves"]
    if metadata_unique != unique_tasks:
        raise AssertionError(
            "unique-distance metadata disagrees with retained task identities: "
            f"metadata={metadata_unique}, reconstructed={unique_tasks}"
        )
    if solver.calls != unique_tasks:
        raise AssertionError(
            "the solver must run exactly once per unique distance task: "
            f"calls={solver.calls}, unique={unique_tasks}"
        )
    if unique_tasks > requested_tasks:
        raise AssertionError("unique tasks cannot exceed requested task roles")

    periods = len(data.period_order)
    expected_compilations = {
        "malmquist": periods,
        "fgnz_enhanced": periods,
        "ray_desli": periods,
        "global": periods + 1,
        "biennial": 2 * periods - 1,
        "luenberger": periods,
        "apz": periods,
    }[operator]
    if compilations != expected_compilations:
        raise AssertionError(
            "reference compilation count disagrees with the operator graph: "
            f"observed={compilations}, expected={expected_compilations}"
        )
    metadata_compilations = result.metadata["compiled_reference_sets"]
    if metadata_compilations != compilations:
        raise AssertionError(
            "compiled-reference metadata disagrees with intercepted calls: "
            f"metadata={metadata_compilations}, counted={compilations}"
        )

    if operator == "global":
        expected_complexity = "O(D*P^2)" if comparison_pairs == "all" else "O(D*P)"
        if result.metadata.get("comparison_pair_mode") != comparison_pairs:
            raise AssertionError("Global comparison-pair metadata drifted")
        if result.metadata.get("comparison_output_size_complexity") != (
            expected_complexity
        ):
            raise AssertionError("Global comparison output-size disclosure drifted")

    if operator == "luenberger":
        reconstructed = summary["efficiency_change"] + summary["technical_change"]
        reported_residual_column = "decomposition_residual"
    elif operator == "ray_desli":
        reconstructed = (
            summary["pure_efficiency_change"]
            * summary["vrs_technical_change"]
            * summary["ray_desli_scale_change"]
        )
        reported_residual_column = "ray_desli_decomposition_residual"
    elif operator == "fgnz_enhanced":
        reconstructed = (
            summary["technical_change"]
            * summary["pure_efficiency_change"]
            * summary["fgnz_scale_change"]
        )
        reported_residual_column = "fgnz_enhanced_decomposition_residual"
    else:
        reconstructed = summary["efficiency_change"] * summary["technical_change"]
        reported_residual_column = "decomposition_residual"
    reconstruction_residual = summary["productivity_change"] - reconstructed
    max_reconstruction_residual = float(
        np.abs(reconstruction_residual.to_numpy(dtype=float)).max(initial=0.0)
    )
    max_reported_residual = _maximum_finite_absolute(
        summary,
        reported_residual_column,
    )
    if max_reconstruction_residual > 1e-8 or max_reported_residual > 1e-8:
        raise AssertionError("the productivity decomposition identity failed")

    max_primal_violation = _maximum_finite_absolute(
        diagnostics,
        "max_primal_violation",
    )
    if max_primal_violation > 1e-7:
        raise AssertionError("a distance task exceeds the primal-feasibility gate")

    organizations = len(set(data.dmu_ids.tolist()))
    pair_mode = result.metadata.get("comparison_pair_mode", "adjacent")
    output_size = result.metadata.get("comparison_output_size_complexity", "O(D*P)")
    print(
        f"operator={operator} n={organizations} periods={len(data.period_order)} "
        f"comparison_pair_mode={pair_mode} output_size={output_size} "
        f"transitions={len(summary)} elapsed={elapsed:.3f}s "
        f"requested_distance_tasks={requested_tasks} "
        f"unique_distance_solves={unique_tasks} solver_calls={solver.calls} "
        f"compiled_reference_sets={compilations} "
        f"max_reconstruction_residual={max_reconstruction_residual:.3e} "
        f"max_reported_residual={max_reported_residual:.3e} "
        f"max_primal_violation={max_primal_violation:.3e}"
        f"{certificate_report}"
    )
    return result


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--operator",
        choices=(*_OPERATORS, "all"),
        default="all",
    )
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument("--periods", type=int, default=4)
    parser.add_argument(
        "--comparison-pairs",
        choices=("adjacent", "all"),
        default="adjacent",
        help="Global-only result enumeration; all is opt-in O(D*P^2) output.",
    )
    parser.add_argument(
        "--include-global-all-pairs",
        action="store_true",
        help="Also audit opt-in Global all-pairs output after the selected cases.",
    )
    arguments = parser.parse_args(argv)

    if arguments.comparison_pairs != "adjacent" and arguments.operator != "global":
        parser.error("--comparison-pairs all requires --operator global")
    if arguments.include_global_all_pairs and arguments.operator not in {
        "all",
        "global",
    }:
        parser.error("--include-global-all-pairs requires --operator all or global")

    operators = _OPERATORS if arguments.operator == "all" else (arguments.operator,)
    for operator in operators:
        data = make_panel(
            arguments.n_dmus,
            arguments.periods,
            ray_desli=operator == "ray_desli",
            environmental=operator == "apz",
        )
        run_case(
            data,
            operator=operator,
            comparison_pairs=arguments.comparison_pairs,
        )
    if arguments.include_global_all_pairs and arguments.comparison_pairs == "adjacent":
        data = make_panel(arguments.n_dmus, arguments.periods)
        run_case(data, operator="global", comparison_pairs="all")


if __name__ == "__main__":
    main()
