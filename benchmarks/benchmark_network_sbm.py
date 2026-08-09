"""Repeatable benchmark for the sparse Tone--Tsutsui network SBM kernel.

The deterministic five-process network has six directed handoffs.  Every
process also has at least one external input and one external output, so the
same population can exercise all three source orientations.

Run from an editable development environment, for example:

    python benchmarks/benchmark_network_sbm.py --n-dmus 100
    python benchmarks/benchmark_network_sbm.py --n-dmus 1000
    python benchmarks/benchmark_network_sbm.py \
        --n-dmus 100 --orientation all --link-policy all

The 1,000-DMU case is intended for scheduled or release benchmarking.  A
small local/CI smoke run can use ``--n-dmus 20``.
"""

from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass
from typing import Any

from benchmark_network_general_additive import make_data

import deapack.network.tone_tsutsui_sbm as network_sbm_module
from deapack import ToneTsutsuiNetworkSBM
from deapack.solvers import SciPyHiGHSSolver

_RESIDUAL_TOLERANCE = 1e-7


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


@dataclass(frozen=True, slots=True)
class BenchmarkObservation:
    elapsed: float
    compile_calls: int
    solver_calls: int
    base_rows: int
    decision_columns: int
    base_nnz: int


def _maximum_finite_residual(
    values,
    *,
    label: str,
    all_missing_is_not_applicable: bool = False,
) -> float:
    """Return a finite absolute maximum without allowing NaN to be skipped."""
    residuals = tuple(float(value) for value in values)
    if all_missing_is_not_applicable and all(
        math.isnan(residual) for residual in residuals
    ):
        return 0.0
    if not residuals or any(not math.isfinite(residual) for residual in residuals):
        raise AssertionError(f"{label} residuals must all be finite")
    return max(abs(residual) for residual in residuals)


def _fit_with_counts(
    n_dmus: int,
    *,
    orientation: str,
    link_policy: str,
) -> tuple[Any, BenchmarkObservation]:
    data = make_data(n_dmus)
    solver = _CountingSolver()
    compiled_references = []
    compile_calls = 0
    original_compile = network_sbm_module.compile_network_sbm_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compile_calls
        compile_calls += 1
        reference = original_compile(*args, **kwargs)
        compiled_references.append(reference)
        return reference

    network_sbm_module.compile_network_sbm_reference = counted_compile
    try:
        model_kwargs: dict[str, Any] = {}
        if link_policy == "accountable":
            accountable_kind = "as_input" if orientation == "input" else "as_output"
            model_kwargs["link_kinds"] = {
                link.link_id: accountable_kind for link in data.network_spec.links
            }
        else:
            model_kwargs["link_control"] = link_policy
        start = time.perf_counter()
        result = ToneTsutsuiNetworkSBM(
            orientation=orientation,
            returns_to_scale="vrs",
            solver=solver,
            **model_kwargs,
        ).fit(data)
        elapsed = time.perf_counter() - start
    finally:
        network_sbm_module.compile_network_sbm_reference = original_compile

    if compile_calls != 1 or len(compiled_references) != 1:
        raise AssertionError(
            "one global reference set must compile exactly once; "
            f"observed={compile_calls}"
        )
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("result metadata must report one compiled reference")
    if solver.calls != data.n_dmus:
        raise AssertionError(
            "network SBM must solve one primary LP per observation; "
            f"observed={solver.calls}, expected={data.n_dmus}"
        )
    expected_call_contract = {
        "primary_solver_calls": data.n_dmus,
        "secondary_solver_calls": 0,
        "solver_calls": data.n_dmus,
        "additional_solver_calls": 0,
        "certificate_extra_solver_calls": 0,
    }
    for field, expected in expected_call_contract.items():
        if result.metadata.get(field) != expected:
            raise AssertionError(
                f"metadata {field} must equal {expected}; "
                f"observed={result.metadata.get(field)!r}"
            )

    reference = compiled_references[0]
    return result, BenchmarkObservation(
        elapsed=elapsed,
        compile_calls=compile_calls,
        solver_calls=solver.calls,
        base_rows=reference.n_base_rows,
        decision_columns=reference.n_variables,
        base_nnz=int(reference.base_matrix_without_tau.nnz),
    )


def run_case(
    n_dmus: int,
    *,
    orientation: str,
    link_policy: str,
) -> None:
    """Fit one case and report the sparse compiler and score identities."""
    result, observation = _fit_with_counts(
        n_dmus,
        orientation=orientation,
        link_policy=link_policy,
    )
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
    claim_counts = {
        field: int(summary[field].fillna(False).sum())
        for field in ("target_valid", "link_valid", "peer_valid", "dual_valid")
    }
    if any(value != n_dmus for value in claim_counts.values()):
        raise AssertionError(
            "all benchmark target/link/peer/dual claims must be certified; "
            f"observed={claim_counts!r}"
        )
    maximum_score_residual = _maximum_finite_residual(
        summary["reconstruction_residual"],
        label="score reconstruction",
    )
    maximum_link_residual = _maximum_finite_residual(
        summary["max_link_continuity_residual"],
        label="link continuity",
    )
    maximum_original_unit_residual = _maximum_finite_residual(
        summary["max_original_unit_normalized_violation"],
        label="original-unit normalized economic account",
    )
    maximum_accountable_residual = _maximum_finite_residual(
        summary["max_accountable_link_balance_residual"],
        label="accountable-link balance",
        all_missing_is_not_applicable=link_policy != "accountable",
    )
    residuals = {
        "score reconstruction": maximum_score_residual,
        "link continuity": maximum_link_residual,
        "original-unit normalized economic account": (maximum_original_unit_residual),
        "accountable-link balance": maximum_accountable_residual,
    }
    for label, residual in residuals.items():
        if not math.isfinite(residual) or residual > _RESIDUAL_TOLERANCE:
            raise AssertionError(
                f"{label} residual must be finite and <= "
                f"{_RESIDUAL_TOLERANCE:.1e}; observed={residual!r}"
            )
    if link_policy == "accountable":
        expected_specialization = (
            "network.sbm.tone_tsutsui_2009.accountable_input_link"
            if orientation == "input"
            else "network.sbm.tone_tsutsui_2009.accountable_output_link"
        )
        if result.metadata.get("specialization_id") != expected_specialization:
            raise AssertionError("accountable-link specialization metadata mismatch")
    matrix_entries = observation.base_rows * (observation.decision_columns - 1)
    density = observation.base_nnz / matrix_entries
    print(
        f"n={n_dmus} processes=5 links=6 "
        f"orientation={orientation} link_policy={link_policy} "
        f"elapsed={observation.elapsed:.3f}s "
        f"optimal={optimal}/{n_dmus} "
        f"certified={certified}/{n_dmus} "
        f"target_certified={claim_counts['target_valid']}/{n_dmus} "
        f"link_certified={claim_counts['link_valid']}/{n_dmus} "
        f"peer_certified={claim_counts['peer_valid']}/{n_dmus} "
        f"dual_certified={claim_counts['dual_valid']}/{n_dmus} "
        f"compiled_reference_sets={observation.compile_calls} "
        f"primary_solves={observation.solver_calls} "
        f"base_shape={observation.base_rows}x"
        f"{observation.decision_columns - 1} "
        f"decision_columns={observation.decision_columns} "
        f"base_nnz={observation.base_nnz} "
        f"base_density={density:.6f} "
        f"max_score_residual={maximum_score_residual:.3e} "
        f"max_link_residual={maximum_link_residual:.3e} "
        f"max_original_unit_residual={maximum_original_unit_residual:.3e} "
        f"max_accountable_link_residual={maximum_accountable_residual:.3e}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--n-dmus",
        type=int,
        nargs="+",
        default=(100,),
        help="one or more population sizes; use 1000 for the release case",
    )
    parser.add_argument(
        "--orientation",
        choices=("input", "output", "non-oriented", "all"),
        default="input",
    )
    parser.add_argument(
        "--link-policy",
        "--link-control",
        dest="link_policy",
        choices=("fixed", "free", "accountable", "both", "all"),
        default="free",
        help=(
            "uniform fixed/free policy, the orientation-matched accountable "
            "policy, both fixed/free policies, or all applicable policies"
        ),
    )
    args = parser.parse_args()
    if args.orientation == "non-oriented" and args.link_policy == "accountable":
        parser.error(
            "the source does not define a non-oriented accountable-link account"
        )

    orientations = (
        ("input", "output", "non-oriented")
        if args.orientation == "all"
        else (args.orientation,)
    )
    policies = {
        "both": ("fixed", "free"),
        "all": ("fixed", "free", "accountable"),
    }.get(args.link_policy, (args.link_policy,))
    for n_dmus in args.n_dmus:
        for orientation in orientations:
            for link_policy in policies:
                if link_policy == "accountable" and orientation == "non-oriented":
                    continue
                run_case(
                    n_dmus,
                    orientation=orientation,
                    link_policy=link_policy,
                )


if __name__ == "__main__":
    main()
