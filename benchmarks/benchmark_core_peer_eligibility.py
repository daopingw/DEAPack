"""Structural benchmark for comparison rights across classical DEA models.

The workload creates ``K`` repeated, source-neutral comparison populations
for ``N`` evaluated organizations.  Every model must compile each distinct
population once, solve exactly once per organization in its score-only/direct
programme, retain compact provenance, and publish no peer outside the declared
population.

Run the routine and release workloads with, for example::

    python benchmarks/benchmark_core_peer_eligibility.py \
        --n-dmus 24 --eligibility-cohorts 4
    python benchmarks/benchmark_core_peer_eligibility.py \
        --n-dmus 1000 --eligibility-cohorts 20
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import issparse

import deapack.models.additive as additive_module
import deapack.models.directional as directional_module
import deapack.models.sbm as sbm_module
from deapack import (
    DDF,
    RAM,
    SBM,
    AdditiveDEA,
    DEAData,
    InputSBM,
    OutputSBM,
    PeerEligibility,
    PeerEligibilityProvenance,
)
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    """Count sparse LP calls while delegating to the release solver."""

    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.seconds = 0.0
        self.max_constraint_nonzeros = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem: Any) -> Any:
        for matrix_name in ("a_ub", "a_eq"):
            matrix = getattr(problem, matrix_name)
            if matrix is None:
                continue
            if not issparse(matrix):
                raise AssertionError(
                    f"classical DEA matrix {matrix_name} must remain sparse"
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
    """Return a deterministic, strictly positive management dataset."""
    if n_dmus <= 0:
        raise ValueError("n_dmus must be positive")
    position = np.arange(n_dmus, dtype=np.float64)
    scale = 1.0 + position / max(float(n_dmus), 1.0)
    labor = scale * (12.0 + position % 17)
    capital = scale * (18.0 + position % 23)
    energy = scale * (8.0 + position % 13)
    capacity = np.power(labor, 0.40) * np.power(capital, 0.35) * np.power(energy, 0.25)
    management = 0.72 + 0.28 * ((position % 29) / 28.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "labor": labor,
            "capital": capital,
            "energy": energy,
            "service_volume": capacity * management,
            "service_quality": (
                capacity * management * (0.60 + (position % 19) / 50.0)
            ),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labor", "capital", "energy"),
        outputs=("service_volume", "service_quality"),
    )


def make_peer_eligibility(data: DEAData, n_cohorts: int) -> PeerEligibility:
    """Declare ``n_cohorts`` repeated populations without naming categories."""
    if n_cohorts <= 0 or n_cohorts > data.n_dmus:
        raise ValueError("eligibility cohorts must lie between one and n_dmus")
    if data.n_dmus % n_cohorts:
        raise ValueError("n_dmus must be divisible by eligibility cohorts")
    cohorts = tuple(
        tuple(range(cohort, data.n_dmus, n_cohorts)) for cohort in range(n_cohorts)
    )
    return PeerEligibility.by_row(
        tuple(cohorts[row % n_cohorts] for row in range(data.n_dmus)),
        provenance=PeerEligibilityProvenance(
            rule_name=f"benchmark_repeated_comparison_populations_{n_cohorts}",
            source="deterministic benchmark fixture",
            comparison_population=(f"{data.n_dmus} synthetic service organizations"),
            decision_owner="DEAPack benchmark contract",
            validity_period="fixture schema v1",
        ),
    )


def _model_cases() -> tuple[
    tuple[str, Any, Callable[[PeerEligibility, _CountingSolver], Any]], ...
]:
    return (
        (
            "additive",
            additive_module,
            lambda policy, solver: AdditiveDEA(
                peer_eligibility=policy,
                solver=solver,
            ),
        ),
        (
            "ram",
            additive_module,
            lambda policy, solver: RAM(
                peer_eligibility=policy,
                solver=solver,
            ),
        ),
        (
            "sbm-non-oriented",
            sbm_module,
            lambda policy, solver: SBM(
                peer_eligibility=policy,
                solver=solver,
            ),
        ),
        (
            "sbm-input",
            sbm_module,
            lambda policy, solver: InputSBM(
                peer_eligibility=policy,
                solver=solver,
            ),
        ),
        (
            "sbm-output",
            sbm_module,
            lambda policy, solver: OutputSBM(
                peer_eligibility=policy,
                solver=solver,
            ),
        ),
        (
            "ddf-score-only",
            directional_module,
            lambda policy, solver: DDF(
                peer_eligibility=policy,
                compute_slacks=False,
                solver=solver,
            ),
        ),
    )


def _assert_no_peer_leakage(result: Any, n_cohorts: int) -> None:
    for row in result.intensities.itertuples(index=False):
        evaluated = int(str(row.dmu_id)[1:])
        reference = int(str(row.reference_dmu_id)[1:])
        if evaluated % n_cohorts != reference % n_cohorts:
            raise AssertionError(
                "a published peer falls outside the declared comparison population"
            )


def run_case(
    *,
    name: str,
    module: Any,
    factory: Callable[[PeerEligibility, _CountingSolver], Any],
    data: DEAData,
    policy: PeerEligibility,
    n_cohorts: int,
) -> tuple[int, int]:
    """Run one mother-model case and enforce the structural release contract."""
    solver = _CountingSolver()
    compile_calls = 0
    original_compile = module.compile_reference

    def counted_compile(*args: Any, **kwargs: Any) -> Any:
        nonlocal compile_calls
        compile_calls += 1
        return original_compile(*args, **kwargs)

    module.compile_reference = counted_compile
    try:
        started = time.perf_counter()
        result = factory(policy, solver).fit(data)
        elapsed = time.perf_counter() - started
    finally:
        module.compile_reference = original_compile

    summary = result.summary()
    if len(summary) != data.n_dmus or not summary["score_valid"].all():
        raise AssertionError(f"{name} did not certify every benchmark score")
    if not (summary["solver_status"] == "optimal").all():
        raise AssertionError(f"{name} did not solve every benchmark programme")
    if not (summary["base_reference_size"] == data.n_dmus).all():
        raise AssertionError(f"{name} lost the global base-population account")
    expected_reference_size = data.n_dmus // n_cohorts
    if not (summary["reference_size"] == expected_reference_size).all():
        raise AssertionError(f"{name} reported an incorrect effective population")
    if not summary["self_in_reference"].astype(bool).all():
        raise AssertionError(f"{name} silently removed a benchmark focal unit")
    if compile_calls != n_cohorts:
        raise AssertionError(
            f"{name} compiled {compile_calls} references; expected {n_cohorts}"
        )
    if result.metadata["compiled_reference_sets"] != compile_calls:
        raise AssertionError(f"{name} compilation metadata disagrees with execution")
    if solver.calls != data.n_dmus:
        raise AssertionError(
            f"{name} made {solver.calls} solver calls; expected {data.n_dmus}"
        )
    if result.metadata["solver_calls"] != solver.calls:
        raise AssertionError(f"{name} solve metadata disagrees with execution")
    if result.metadata.get("additional_solver_calls", 0) != 0:
        raise AssertionError(f"{name} added an undeclared certification solve")

    audit = result.metadata.get("peer_eligibility")
    if not isinstance(audit, dict):
        raise AssertionError(f"{name} omitted comparison-population provenance")
    expanded_audit = result.metadata["expanded_spec"]["reference"].get(
        "peer_eligibility"
    )
    if json.loads(json.dumps(audit)) != json.loads(json.dumps(expanded_audit)):
        raise AssertionError(f"{name} duplicated inconsistent policy provenance")
    if audit["effective_unique_reference_sets"] != n_cohorts:
        raise AssertionError(f"{name} eligibility audit lost cohort deduplication")
    expected_edges = data.n_dmus * expected_reference_size
    if audit["effective_edge_count"] != expected_edges:
        raise AssertionError(f"{name} eligibility edge account is inconsistent")
    if audit["categorical_interpretation"] != "not_claimed":
        raise AssertionError(f"{name} inferred an unsupported categorical model")
    if len(json.dumps(audit, sort_keys=True)) > 4096:
        raise AssertionError(f"{name} copied the full eligibility relation to metadata")
    if result.metadata["expanded_spec"]["evaluation_protocol"]["kind"] != (
        "self_appraisal"
    ):
        raise AssertionError(f"{name} misclassified the fitted appraisal protocol")
    if name == "ram":
        if result.metadata["range_population"] != (
            "base_global_data_before_peer_eligibility"
        ):
            raise AssertionError("RAM did not separate normalization population")
        if result.metadata["source_profile"] != "deapack_ram_extension":
            raise AssertionError("restricted RAM retained an exact-source claim")

    _assert_no_peer_leakage(result, n_cohorts)
    print(
        f"model={name} n={data.n_dmus} cohorts={n_cohorts} "
        f"elapsed={elapsed:.3f}s compile_calls={compile_calls} "
        f"solver_calls={solver.calls} solver_seconds={solver.seconds:.3f} "
        f"effective_edges={expected_edges} "
        f"metadata_bytes={len(json.dumps(audit, sort_keys=True))} "
        f"max_constraint_nonzeros={solver.max_constraint_nonzeros}"
    )
    return compile_calls, solver.calls


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=24)
    parser.add_argument("--eligibility-cohorts", type=int, default=4)
    args = parser.parse_args()

    data = make_data(args.n_dmus)
    policy = make_peer_eligibility(data, args.eligibility_cohorts)
    total_compilations = 0
    total_solver_calls = 0
    for name, module, factory in _model_cases():
        compilations, solver_calls = run_case(
            name=name,
            module=module,
            factory=factory,
            data=data,
            policy=policy,
            n_cohorts=args.eligibility_cohorts,
        )
        total_compilations += compilations
        total_solver_calls += solver_calls
    print(
        f"models={len(_model_cases())} total_compilations={total_compilations} "
        f"total_solver_calls={total_solver_calls}"
    )


if __name__ == "__main__":
    main()
