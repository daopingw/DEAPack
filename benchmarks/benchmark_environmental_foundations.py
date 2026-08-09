"""Direct smoke benchmark for the public environmental foundation methods.

Each case calls its own public estimator.  The benchmark uses one strictly
positive environmental production fixture for DDF, weak-disposal,
by-production, and separable undesirable-output SBM methods.  Separate fixtures
exercise Tone's mixed separable/non-separable account and Coelli's
material-inflow model because their declared data roles differ.

Examples:

    python benchmarks/benchmark_environmental_foundations.py --n-dmus 20
    python benchmarks/benchmark_environmental_foundations.py \
        --method environmental.by_production.fgl --n-dmus 8
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.sparse import issparse

import deapack.models.by_production as by_production_module
import deapack.models.by_production_fgl as by_production_fgl_module
import deapack.models.environmental as environmental_module
import deapack.models.material_balance as material_balance_module
import deapack.models.nonseparable_sbm as nonseparable_sbm_module
import deapack.models.sbm as sbm_module
import deapack.models.weak_disposal as weak_disposal_module
from deapack import (
    ActivitySpecificWeakDisposalDDF,
    ByProductionDDF,
    ByProductionFGL,
    ChungFareGrosskopfDDF,
    CommonFactorWeakDisposalDDF,
    DEAData,
    EnvironmentalDirectionalDistanceDEA,
    MaterialBalanceCoefficients,
    MaterialBalanceDEA,
    PeerEligibility,
    PeerEligibilityProvenance,
    ToneNonSeparableSBM,
    UndesirableSBM,
)
from deapack.results import DEAResult
from deapack.solvers import SciPyHiGHSSolver

METHOD_IDS = (
    "environmental.ddf.joint_production",
    "environmental.ddf.output.chung_fare_grosskopf_1997",
    "environmental.ddf.weak_disposal.common_factor",
    "environmental.ddf.weak_disposal.activity_specific",
    "environmental.by_production.ddf",
    "environmental.by_production.fgl",
    "environmental.material_inflow.coelli2007",
    "environmental.sbm.separable_strong",
    "environmental.sbm.nonseparable_hybrid.tone_2003",
)
_COMPILER_MODULE_BY_ID = {
    "environmental.ddf.joint_production": environmental_module,
    "environmental.ddf.output.chung_fare_grosskopf_1997": environmental_module,
    "environmental.ddf.weak_disposal.common_factor": environmental_module,
    "environmental.ddf.weak_disposal.activity_specific": weak_disposal_module,
    "environmental.by_production.ddf": by_production_module,
    "environmental.by_production.fgl": by_production_fgl_module,
    "environmental.material_inflow.coelli2007": material_balance_module,
    "environmental.sbm.separable_strong": sbm_module,
    "environmental.sbm.nonseparable_hybrid.tone_2003": (nonseparable_sbm_module),
}
_DDF_METHOD_IDS = frozenset(
    {
        "environmental.ddf.joint_production",
        "environmental.ddf.output.chung_fare_grosskopf_1997",
        "environmental.ddf.weak_disposal.common_factor",
        "environmental.ddf.weak_disposal.activity_specific",
    }
)
_CERTIFIED_SHARED_KERNEL_DDF_IDS = frozenset(
    {
        "environmental.ddf.joint_production",
        "environmental.ddf.output.chung_fare_grosskopf_1997",
        "environmental.ddf.weak_disposal.common_factor",
    }
)
_CERTIFIED_ACTIVITY_SPECIFIC_DDF_IDS = frozenset(
    {
        "environmental.ddf.weak_disposal.activity_specific",
    }
)
_CERTIFIED_BY_PRODUCTION_IDS = frozenset(
    {
        "environmental.by_production.ddf",
    }
)
_CERTIFIED_SEPARABLE_SBM_IDS = frozenset(
    {
        "environmental.sbm.separable_strong",
    }
)
_CERTIFIED_ENVIRONMENTAL_IDS = (
    _CERTIFIED_SHARED_KERNEL_DDF_IDS
    | _CERTIFIED_ACTIVITY_SPECIFIC_DDF_IDS
    | _CERTIFIED_BY_PRODUCTION_IDS
    | _CERTIFIED_SEPARABLE_SBM_IDS
)
_PEER_ELIGIBILITY_METHOD_IDS = (
    "environmental.ddf.joint_production",
    "environmental.ddf.output.chung_fare_grosskopf_1997",
    "environmental.ddf.weak_disposal.common_factor",
    "environmental.sbm.separable_strong",
)


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        for name in ("a_ub", "a_eq"):
            matrix = getattr(problem, name)
            if matrix is not None and not issparse(matrix):
                raise AssertionError(
                    f"{problem.name} {name} must remain sparse in the benchmark"
                )
        self.calls += 1
        return self._delegate.solve(problem)


def _cycled(values: Sequence[float], n_dmus: int) -> np.ndarray:
    return np.resize(np.asarray(values, dtype=np.float64), n_dmus)


def make_environmental_data(n_dmus: int) -> DEAData:
    """Return positive quantities with an explicit pollution-generating input."""
    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")
    position = np.arange(n_dmus, dtype=np.float64)
    frame = pd.DataFrame(
        {
            "dmu": [f"EF{index:06d}" for index in range(n_dmus)],
            "energy": _cycled((1.0, 1.0, 1.2, 1.3), n_dmus) * (1.0 + 0.0010 * position),
            "labor": _cycled((1.0, 1.2, 1.1, 1.4), n_dmus) * (1.0 + 0.0013 * position),
            "electricity": _cycled((2.0, 1.0, 1.5, 1.1), n_dmus)
            * (1.0 + 0.0007 * position),
            "co2": _cycled((1.0, 2.0, 1.4, 1.8), n_dmus) * (1.0 + 0.0011 * position),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("energy", "labor"),
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )


def make_peer_eligibility(data: DEAData, n_cohorts: int) -> PeerEligibility:
    """Declare repeated environmental comparison populations for auditing."""
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
            rule_name=(f"benchmark_environmental_comparison_populations_{n_cohorts}"),
            source="deterministic environmental benchmark fixture",
            comparison_population=(
                f"{data.n_dmus} synthetic environmental operating units"
            ),
            decision_owner="DEAPack benchmark contract",
            validity_period="fixture schema v1",
        ),
    )


def make_material_data(n_dmus: int) -> tuple[DEAData, MaterialBalanceCoefficients]:
    """Return the separate positive material-inflow production account."""
    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")
    position = np.arange(n_dmus, dtype=np.float64)
    frame = pd.DataFrame(
        {
            "dmu": [f"MF{index:06d}" for index in range(n_dmus)],
            "fertilizer_a": _cycled((1.0, 3.0, 2.0, 4.0), n_dmus)
            * (1.0 + 0.0010 * position),
            "fertilizer_b": _cycled((3.0, 1.0, 2.0, 4.0), n_dmus)
            * (1.0 + 0.0014 * position),
            "crop": 1.0 + 0.0005 * position,
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("fertilizer_a", "fertilizer_b"),
        outputs="crop",
    )
    coefficients = MaterialBalanceCoefficients(
        inputs={
            "nutrient": {
                "fertilizer_a": 1.0,
                "fertilizer_b": 3.0,
            }
        },
        outputs={"nutrient": {"crop": 1.0}},
    )
    return data, coefficients


def make_nonseparable_sbm_data(n_dmus: int) -> DEAData:
    """Return a positive mixed separable/non-separable output account."""
    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")
    position = np.arange(n_dmus, dtype=np.float64)
    frame = pd.DataFrame(
        {
            "dmu": [f"NS{index:06d}" for index in range(n_dmus)],
            "energy": _cycled((2.0, 6.0, 4.0, 7.0), n_dmus) * (1.0 + 0.0010 * position),
            "labor": _cycled((3.0, 9.0, 5.0, 8.0), n_dmus) * (1.0 + 0.0013 * position),
            "joint_service": _cycled((11.0, 17.0, 14.0, 20.0), n_dmus)
            * (1.0 + 0.0008 * position),
            "separable_service": _cycled((13.0, 7.0, 16.0, 10.0), n_dmus)
            * (1.0 + 0.0006 * position),
            "joint_residual": _cycled((3.0, 9.0, 5.0, 11.0), n_dmus)
            * (1.0 + 0.0011 * position),
            "separable_residual": _cycled((2.0, 8.0, 4.0, 9.0), n_dmus)
            * (1.0 + 0.0015 * position),
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("energy", "labor"),
        outputs=("joint_service", "separable_service"),
        bad_outputs=("joint_residual", "separable_residual"),
    )


def _model_and_data(
    method_id: str,
    n_dmus: int,
    solver: _CountingSolver,
    *,
    compute_slacks: bool = False,
    peer_eligibility: PeerEligibility | None = None,
) -> tuple[object, DEAData]:
    if method_id == "environmental.material_inflow.coelli2007":
        data, coefficients = make_material_data(n_dmus)
        return (
            MaterialBalanceDEA(
                coefficients,
                returns_to_scale="vrs",
                solver=solver,
            ),
            data,
        )
    if method_id == "environmental.sbm.nonseparable_hybrid.tone_2003":
        data = make_nonseparable_sbm_data(n_dmus)
        return (
            ToneNonSeparableSBM(
                nonseparable_outputs="joint_service",
                nonseparable_bad_outputs="joint_residual",
                alpha_min=0.7,
                returns_to_scale="vrs",
                solver=solver,
            ),
            data,
        )

    data = make_environmental_data(n_dmus)
    if method_id == "environmental.ddf.joint_production":
        model = EnvironmentalDirectionalDistanceDEA(
            disposability="strong",
            null_jointness=False,
            returns_to_scale="vrs",
            compute_slacks=compute_slacks,
            peer_eligibility=peer_eligibility,
            solver=solver,
        )
    elif method_id == "environmental.ddf.output.chung_fare_grosskopf_1997":
        model = ChungFareGrosskopfDDF(
            compute_slacks=compute_slacks,
            peer_eligibility=peer_eligibility,
            solver=solver,
        )
    elif method_id == "environmental.ddf.weak_disposal.common_factor":
        model = CommonFactorWeakDisposalDDF(
            compute_slacks=compute_slacks,
            peer_eligibility=peer_eligibility,
            solver=solver,
        )
    elif method_id == "environmental.ddf.weak_disposal.activity_specific":
        model = ActivitySpecificWeakDisposalDDF(
            compute_slacks=compute_slacks,
            solver=solver,
        )
    elif method_id == "environmental.by_production.ddf":
        model = ByProductionDDF(solver=solver)
    elif method_id == "environmental.by_production.fgl":
        model = ByProductionFGL(solver=solver)
    elif method_id == "environmental.sbm.separable_strong":
        model = UndesirableSBM(
            returns_to_scale="vrs",
            peer_eligibility=peer_eligibility,
            solver=solver,
        )
    else:
        raise ValueError(f"unknown environmental benchmark method: {method_id}")
    return model, data


def _maximum_finite_absolute(frame: pd.DataFrame, column: str) -> float:
    values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    finite = np.abs(values[np.isfinite(values)])
    if finite.size == 0:
        raise AssertionError(f"{column} has no finite benchmark values")
    return float(finite.max())


def _assert_accounting_identity(method_id: str, result: DEAResult) -> float:
    summary = result.summary()
    if method_id.startswith("environmental.ddf."):
        reconstructed = 1.0 / (1.0 + summary["distance"])
        residual = summary["efficiency"] - reconstructed
    elif method_id == "environmental.by_production.ddf":
        reconstructed_distance = np.minimum(
            summary["intended_distance"],
            summary["environmental_distance"],
        )
        residual = np.maximum(
            np.abs(summary["distance"] - reconstructed_distance),
            np.abs(summary["efficiency"] - 1.0 / (1.0 + summary["distance"])),
        )
    elif method_id == "environmental.by_production.fgl":
        reconstructed = 0.5 * (
            summary["productive_efficiency"] + summary["environmental_efficiency"]
        )
        residual = np.maximum(
            np.abs(summary["efficiency"] - reconstructed),
            np.abs(summary["fgl_optimality_gap"]),
        )
    elif method_id == "environmental.material_inflow.coelli2007":
        reconstructed = (
            summary["technical_efficiency"]
            * summary["environmental_allocative_efficiency"]
        )
        residual = summary["efficiency"] - reconstructed
    elif method_id in {
        "environmental.sbm.separable_strong",
        "environmental.sbm.nonseparable_hybrid.tone_2003",
    }:
        reconstructed = (1.0 - summary["input_inefficiency"]) / (
            1.0 + summary["output_inefficiency"]
        )
        residual = summary["efficiency"] - reconstructed
    else:
        raise AssertionError(f"no accounting identity for {method_id}")

    residual_values = np.abs(np.asarray(residual, dtype=np.float64))
    finite_residuals = residual_values[np.isfinite(residual_values)]
    if finite_residuals.size != len(summary):
        raise AssertionError(
            f"{method_id} identity must be defined for every benchmark observation"
        )
    maximum = float(finite_residuals.max())
    if maximum > 1e-7:
        raise AssertionError(
            f"{method_id} accounting identity failed: residual={maximum:.3e}"
        )
    return maximum


def run_case(
    method_id: str,
    n_dmus: int,
    *,
    compute_slacks: bool = False,
) -> DEAResult:
    """Run one direct public method and validate only its native contracts."""
    solver = _CountingSolver()
    model, data = _model_and_data(
        method_id,
        n_dmus,
        solver,
        compute_slacks=compute_slacks,
    )

    compiler_module = _COMPILER_MODULE_BY_ID[method_id]
    original_compile = compiler_module.compile_reference
    compilation_calls = 0

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compilation_calls
        compilation_calls += 1
        return original_compile(*args, **kwargs)

    compiler_module.compile_reference = counted_compile
    started = time.perf_counter()
    try:
        result = model.fit(data)  # type: ignore[attr-defined]
    finally:
        compiler_module.compile_reference = original_compile
    elapsed = time.perf_counter() - started

    if result.metadata["method_id"] != method_id:
        raise AssertionError("benchmark reached a component instead of the named API")
    if result.metadata["compiled_reference_sets"] != 1:
        raise AssertionError("the global fixture must compile one reference set")
    if compilation_calls != 1:
        raise AssertionError(
            "the global environmental reference must be compiled once; "
            f"observed={compilation_calls}"
        )
    if not (result.summary()["solver_status"] == "optimal").all():
        raise AssertionError("every benchmark observation must solve optimally")
    certification_report = ""
    if method_id in _CERTIFIED_ENVIRONMENTAL_IDS:
        certified = int(result.summary()["score_valid"].fillna(False).sum())
        if certified != data.n_dmus:
            raise AssertionError(
                "every certified environmental score must pass the "
                f"postsolve certificate; observed={certified}/{data.n_dmus}"
            )
        if not result.diagnostics["postsolve_certified"].fillna(False).all():
            raise AssertionError(
                "every executed environmental DDF phase must pass both the LP "
                "and economic-account certificates"
            )
        additional_solver_calls = result.metadata.get(
            "additional_solver_calls",
            result.metadata.get("postsolve_certificate", {}).get(
                "additional_solver_calls"
            ),
        )
        if additional_solver_calls != 0:
            raise AssertionError("postsolve certification must not add solver calls")
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
            _maximum_finite_absolute(result.diagnostics, column)
            for column in certificate_columns
        )
        certification_report = (
            f"certified={certified}/{data.n_dmus} "
            f"max_certificate_residual={maximum_certificate_residual:.3e} "
        )
    if method_id in _CERTIFIED_ACTIVITY_SPECIFIC_DDF_IDS:
        required_claims = ["score_valid", "peer_valid", "dual_valid"]
        if compute_slacks:
            required_claims.append("target_valid")
        for validity_column in required_claims:
            if not result.summary()[validity_column].fillna(False).all():
                raise AssertionError(
                    "activity-specific weak disposal must certify "
                    f"{validity_column} for every row"
                )
        if not result.summary()["is_within_reference_technology"].fillna(False).all():
            raise AssertionError(
                "the self-inclusive activity-specific benchmark must certify "
                "reference-technology membership"
            )
        if result.metadata["membership_solver_calls"] != 0:
            raise AssertionError(
                "structural self membership must not add a feasibility solve"
            )
        if result.intensities.empty or result.duals.empty:
            raise AssertionError(
                "certified activity-specific benchmark must publish activities "
                "and complete original-unit duals"
            )
        if compute_slacks and result.targets.empty:
            raise AssertionError(
                "the certified full activity-specific benchmark must publish targets"
            )
    if method_id in _CERTIFIED_BY_PRODUCTION_IDS:
        for validity_column in ("target_valid", "peer_valid", "dual_valid"):
            if not result.summary()[validity_column].fillna(False).all():
                raise AssertionError(
                    f"by-production must certify {validity_column} for every row"
                )
        if result.targets.empty or result.intensities.empty or result.duals.empty:
            raise AssertionError(
                "certified by-production benchmark must publish all result accounts"
            )
    if method_id in _CERTIFIED_SEPARABLE_SBM_IDS:
        for validity_column in (
            "score_valid",
            "target_valid",
            "peer_valid",
            "dual_valid",
        ):
            if not result.summary()[validity_column].fillna(False).all():
                raise AssertionError(
                    "separable undesirable-output SBM must certify "
                    f"{validity_column} for every row"
                )
        if not result.summary()["is_within_reference_technology"].fillna(False).all():
            raise AssertionError(
                "the self-inclusive separable SBM benchmark must certify "
                "reference-technology membership"
            )
        if result.targets.empty or result.intensities.empty or result.duals.empty:
            raise AssertionError(
                "certified separable SBM benchmark must publish all result accounts"
            )

    if method_id in _DDF_METHOD_IDS:
        expected_calls = data.n_dmus * (2 if compute_slacks else 1)
    elif method_id in {
        "environmental.sbm.separable_strong",
        "environmental.sbm.nonseparable_hybrid.tone_2003",
    }:
        expected_calls = data.n_dmus
    elif method_id in {
        "environmental.by_production.ddf",
        "environmental.material_inflow.coelli2007",
    }:
        expected_calls = 2 * data.n_dmus
    else:
        intended = result.diagnostics.loc[
            result.diagnostics["subtechnology"] == "intended_production",
            "iterations",
        ]
        expected_calls = int(intended.sum()) + data.n_dmus

    if solver.calls != expected_calls:
        raise AssertionError(
            f"{method_id} solve/iteration accounting changed: "
            f"observed={solver.calls}, expected={expected_calls}"
        )
    if method_id in _DDF_METHOD_IDS:
        expected_phase_two = data.n_dmus if compute_slacks else 0
        assert result.metadata["phase_one_solver_calls"] == data.n_dmus
        assert result.metadata["phase_two_solver_calls"] == expected_phase_two
        assert result.metadata.get("membership_solver_calls", 0) == 0
        assert result.metadata["solver_calls"] == expected_calls
    elif method_id in _CERTIFIED_BY_PRODUCTION_IDS:
        assert result.metadata["intended_solver_calls"] == data.n_dmus
        assert result.metadata["residual_solver_calls"] == data.n_dmus
        assert result.metadata["solver_calls"] == expected_calls
    maximum_identity_residual = _assert_accounting_identity(method_id, result)
    maximum_solver_violation = _maximum_finite_absolute(
        result.diagnostics,
        "max_primal_violation",
    )
    if maximum_solver_violation > 1e-7:
        raise AssertionError(
            f"{method_id} primal violation exceeds tolerance; "
            f"observed={maximum_solver_violation:.3e}"
        )
    execution_mode = (
        "full" if method_id in _DDF_METHOD_IDS and compute_slacks else "score"
    )
    print(
        f"method={method_id} n={data.n_dmus} elapsed={elapsed:.3f}s "
        f"mode={execution_mode} "
        f"{certification_report}"
        f"solver_calls={solver.calls}/{expected_calls} "
        f"reference_set_count={result.metadata['compiled_reference_sets']} "
        f"compile_reference_calls={compilation_calls} "
        f"max_solver_violation={maximum_solver_violation:.3e} "
        f"max_identity_residual={maximum_identity_residual:.3e}"
    )
    return result


def run_peer_eligibility_case(
    method_id: str,
    n_dmus: int,
    n_cohorts: int,
) -> DEAResult:
    """Audit K compiled environmental populations and N direct score solves."""
    if method_id not in _PEER_ELIGIBILITY_METHOD_IDS:
        raise ValueError(
            "peer eligibility is authorized only for the four environmental "
            f"mother-model routes; received {method_id!r}"
        )
    data = make_environmental_data(n_dmus)
    policy = make_peer_eligibility(data, n_cohorts)
    solver = _CountingSolver()
    model, _fixture_data = _model_and_data(
        method_id,
        n_dmus,
        solver,
        peer_eligibility=policy,
    )

    compiler_module = _COMPILER_MODULE_BY_ID[method_id]
    original_compile = compiler_module.compile_reference
    compilation_calls = 0

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compilation_calls
        compilation_calls += 1
        return original_compile(*args, **kwargs)

    compiler_module.compile_reference = counted_compile
    started = time.perf_counter()
    try:
        result = model.fit(data)  # type: ignore[attr-defined]
    finally:
        compiler_module.compile_reference = original_compile
    elapsed = time.perf_counter() - started

    summary = result.summary()
    expected_reference_size = data.n_dmus // n_cohorts
    if len(summary) != data.n_dmus or not summary["score_valid"].fillna(False).all():
        raise AssertionError("every environmental policy benchmark score must certify")
    if not (summary["solver_status"] == "optimal").all():
        raise AssertionError("every environmental policy programme must be optimal")
    if not (summary["base_reference_size"] == data.n_dmus).all():
        raise AssertionError("the global base population must remain auditable")
    if not (summary["reference_size"] == expected_reference_size).all():
        raise AssertionError("the effective environmental population is incorrect")
    if not summary["self_in_reference"].astype(bool).all():
        raise AssertionError("the fixture must retain each focal operation")
    if compilation_calls != n_cohorts:
        raise AssertionError(
            "each unique environmental population must compile once; "
            f"observed={compilation_calls}, expected={n_cohorts}"
        )
    if result.metadata["compiled_reference_sets"] != n_cohorts:
        raise AssertionError("environmental compilation metadata disagrees")
    if solver.calls != data.n_dmus or result.metadata["solver_calls"] != solver.calls:
        raise AssertionError("environmental policy solve accounting changed")

    audit = result.metadata.get("peer_eligibility")
    if not isinstance(audit, dict):
        raise AssertionError("environmental result omitted policy provenance")
    expanded = result.metadata["expanded_spec"]["reference"].get("peer_eligibility")
    if json.loads(json.dumps(audit)) != json.loads(json.dumps(expanded)):
        raise AssertionError("environmental policy provenance is inconsistent")
    if audit["effective_unique_reference_sets"] != n_cohorts:
        raise AssertionError("environmental cohort compilation was not deduplicated")
    expected_edges = data.n_dmus * expected_reference_size
    if audit["effective_edge_count"] != expected_edges:
        raise AssertionError("environmental policy edge accounting is inconsistent")
    if len(json.dumps(audit, sort_keys=True)) > 4096:
        raise AssertionError("environmental metadata copied the full edge relation")
    if result.metadata["expanded_spec"]["evaluation_protocol"]["kind"] != (
        "self_appraisal"
    ):
        raise AssertionError("environmental policy fixture misclassified appraisal")

    for row in result.intensities.itertuples(index=False):
        evaluated = int(str(row.dmu_id)[2:])
        reference = int(str(row.reference_dmu_id)[2:])
        if evaluated % n_cohorts != reference % n_cohorts:
            raise AssertionError(
                "a published environmental peer falls outside its declared population"
            )
    print(
        f"method={method_id} n={data.n_dmus} cohorts={n_cohorts} "
        f"elapsed={elapsed:.3f}s compile_reference_calls={compilation_calls} "
        f"solver_calls={solver.calls} effective_edges={expected_edges} "
        f"metadata_bytes={len(json.dumps(audit, sort_keys=True))}"
    )
    return result


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=20)
    parser.add_argument(
        "--method",
        choices=(*METHOD_IDS, "all", "peer-eligibility"),
        default="all",
    )
    parser.add_argument(
        "--peer-eligibility-cohorts",
        type=int,
        default=None,
        help=(
            "run the authorized environmental comparison-population audit; "
            "n-dmus must be divisible by this number"
        ),
    )
    parser.add_argument(
        "--ddf-mode",
        choices=("score", "full", "both"),
        default="both",
        help="execution mode for environmental DDF cases",
    )
    args = parser.parse_args(argv)

    methods = (
        _PEER_ELIGIBILITY_METHOD_IDS
        if args.method == "peer-eligibility"
        else (METHOD_IDS if args.method == "all" else (args.method,))
    )
    if args.peer_eligibility_cohorts is not None:
        unsupported = set(methods) - set(_PEER_ELIGIBILITY_METHOD_IDS)
        if unsupported:
            raise ValueError(
                "--peer-eligibility-cohorts requires --method peer-eligibility "
                "or one authorized environmental mother-model route; unsupported="
                f"{sorted(unsupported)}"
            )
        for method_id in methods:
            run_peer_eligibility_case(
                method_id,
                args.n_dmus,
                args.peer_eligibility_cohorts,
            )
        return
    for method_id in methods:
        if method_id not in _DDF_METHOD_IDS:
            run_case(method_id, args.n_dmus)
            continue
        modes = {
            "score": (False,),
            "full": (True,),
            "both": (False, True),
        }[args.ddf_mode]
        for compute_slacks in modes:
            run_case(
                method_id,
                args.n_dmus,
                compute_slacks=compute_slacks,
            )


if __name__ == "__main__":
    main()
