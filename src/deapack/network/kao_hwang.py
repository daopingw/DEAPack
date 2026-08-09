"""Kao--Hwang relational efficiency for a basic two-stage series system."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any, Literal

import numpy as np
import pandas as pd

from .._registry import reference_spec as registry_reference_spec
from .._registry import registry_metadata
from ..enums import SolverStatus
from ..results import DEAResult
from ..solvers import (
    LinearProgram,
    LPCertificate,
    LPSolution,
    LPSolver,
    SciPyHiGHSSolver,
    certify_lp_solution,
)
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._relational import (
    CompiledTwoStageReference,
    RelationalMultiplierAccount,
    RelationalProjectionAccount,
    compile_two_stage_reference,
    envelopment_problem,
    multiplier_problem,
    relational_multiplier_account,
    relational_projection_account,
    relational_projection_reconstruction_violation,
)
from ._series import basic_shared_multiplier_series_roles
from .data import NetworkData

DecompositionPolicy = Literal[
    "none",
    "maximize_stage_1",
    "maximize_stage_2",
    "bounds",
]
ProjectionPolicy = Literal["none", "source_midpoint"]


@dataclass(frozen=True, slots=True)
class _CertifiedMultiplierTask:
    """One solved multiplier programme and its semantic release decision."""

    solution: LPSolution
    certificate: LPCertificate
    valid: bool
    status: str
    published_primal: np.ndarray | None
    raw_account: RelationalMultiplierAccount | None
    published_account: RelationalMultiplierAccount | None
    raw_economic_certified: bool | None
    published_economic_certified: bool | None
    economic_reason: str


@dataclass(frozen=True, slots=True)
class _Projection:
    """Certified target account and separately certified displayed peers."""

    status: str
    source: str
    target_valid: bool
    peer_valid: bool
    peer_status: str
    lambdas: np.ndarray | None
    mus: np.ndarray | None
    peer_lambdas: np.ndarray | None
    peer_mus: np.ndarray | None
    raw_account: RelationalProjectionAccount | None
    published_account: RelationalProjectionAccount | None
    raw_economic_certified: bool | None
    published_economic_certified: bool | None
    peer_economic_certified: bool | None
    peer_violation: float
    message: str
    fallback_solver_calls: int
    fallback_diagnostic: dict[str, Any] | None


_SUMMARY_COLUMNS = (
    "dmu_id",
    "period",
    "score",
    "efficiency",
    "distance",
    "system_efficiency",
    "stage_1_efficiency",
    "stage_2_efficiency",
    "stage_1_efficiency_lower",
    "stage_1_efficiency_upper",
    "stage_2_efficiency_lower",
    "stage_2_efficiency_upper",
    "stage_product",
    "reconstruction_residual",
    "is_relationally_efficient",
    "is_stage_1_efficient",
    "is_stage_2_efficient",
    "is_efficient",
    "is_within_reference_technology",
    "score_valid",
    "decomposition_valid",
    "process_decomposition_valid",
    "decomposition_status",
    "decomposition_unique",
    "target_valid",
    "target_status",
    "peer_valid",
    "peer_status",
    "solver_status",
    "backend_solver_status",
    "raw_solver_status",
    "score_status",
    "model_family",
    "returns_to_scale",
    "reference_size",
    "upstream_omitted_intensity_sum",
    "downstream_omitted_intensity_sum",
)
_COMPONENT_COLUMNS = (
    "dmu_id",
    "period",
    "component_kind",
    "component_id",
    "score",
    "efficiency",
    "score_lower",
    "score_upper",
    "is_measure_efficient",
    "selection_policy",
    "valid",
    "status",
)
_MULTIPLIER_COLUMNS = (
    "dmu_id",
    "period",
    "phase",
    "role",
    "variable",
    "scaled_multiplier",
    "multiplier",
    "observed",
    "virtual_contribution",
    "shared_between",
    "valid",
    "status",
    "is_zero_for_display",
)
_INTENSITY_COLUMNS = (
    "dmu_id",
    "period",
    "process_id",
    "intensity_kind",
    "reference_dmu_id",
    "reference_period",
    "intensity",
    "lambda",
    "valid",
    "status",
)
_TARGET_COLUMNS = (
    "dmu_id",
    "period",
    "process_id",
    "role",
    "variable",
    "observed",
    "target",
    "target_lower",
    "target_upper",
    "valid",
    "status",
    "projection_policy",
)
_LINK_COLUMNS = (
    "dmu_id",
    "period",
    "link_id",
    "variable",
    "observed",
    "downstream_requirement",
    "upstream_supply",
    "target_lower",
    "target_upper",
    "target",
    "disposable_surplus",
    "projection_policy",
    "balance_residual",
    "valid",
    "status",
)
_DIAGNOSTIC_COLUMNS = (
    "dmu_id",
    "period",
    "phase",
    "solver_status",
    "backend_solver_status",
    "raw_solver_status",
    "message",
    "iterations",
    "max_primal_violation",
    "lp_postsolve_certified",
    "raw_economic_postsolve_certified",
    "published_economic_postsolve_certified",
    "economic_postsolve_certified",
    "postsolve_certified",
    "certification_status",
    "certificate_reason",
    "economic_certification_reason",
    "max_recomputed_constraint_violation",
    "max_constraint_violation",
    "equality_violation",
    "max_bound_violation",
    "objective_residual",
    "duality_gap",
    "max_dual_violation",
    "complementarity_violation",
    "bound_marginals_used",
    "max_raw_economic_violation",
    "max_published_economic_violation",
    "raw_target_account_certified",
    "published_target_account_certified",
    "published_peer_account_certified",
    "max_raw_target_account_violation",
    "max_published_target_account_violation",
    "max_published_peer_account_violation",
)


def _multiplier_diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    phase: str,
    task: _CertifiedMultiplierTask,
) -> dict[str, Any]:
    solution = task.solution
    certificate = task.certificate
    raw_violation = (
        math.nan if task.raw_account is None else task.raw_account.max_violation
    )
    published_violation = (
        math.nan
        if task.published_account is None
        else task.published_account.max_violation
    )
    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": phase,
        "solver_status": solution.status.value,
        "backend_solver_status": solution.status.value,
        "raw_solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
        "lp_postsolve_certified": certificate.certified,
        "raw_economic_postsolve_certified": task.raw_economic_certified,
        "published_economic_postsolve_certified": (task.published_economic_certified),
        "economic_postsolve_certified": task.valid,
        "postsolve_certified": task.valid,
        "certification_status": "certified" if task.valid else "failed",
        "certificate_reason": (
            certificate.reason if not certificate.certified else task.economic_reason
        ),
        "economic_certification_reason": task.economic_reason,
        "max_recomputed_constraint_violation": (certificate.max_constraint_violation),
        "max_constraint_violation": certificate.max_constraint_violation,
        "equality_violation": certificate.equality_violation,
        "max_bound_violation": certificate.max_bound_violation,
        "objective_residual": certificate.objective_residual,
        "duality_gap": certificate.duality_gap,
        "max_dual_violation": certificate.max_dual_violation,
        "complementarity_violation": certificate.complementarity_violation,
        "bound_marginals_used": certificate.bound_marginals_used,
        "max_raw_economic_violation": raw_violation,
        "max_published_economic_violation": published_violation,
        "raw_target_account_certified": pd.NA,
        "published_target_account_certified": pd.NA,
        "published_peer_account_certified": pd.NA,
        "max_raw_target_account_violation": np.nan,
        "max_published_target_account_violation": np.nan,
        "max_published_peer_account_violation": np.nan,
    }


def _projection_diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    phase: str,
    solution: LPSolution,
    certificate: LPCertificate,
) -> dict[str, Any]:
    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": phase,
        "solver_status": solution.status.value,
        "backend_solver_status": solution.status.value,
        "raw_solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
        "lp_postsolve_certified": certificate.certified,
        "raw_economic_postsolve_certified": pd.NA,
        "published_economic_postsolve_certified": pd.NA,
        "economic_postsolve_certified": pd.NA,
        "postsolve_certified": certificate.certified,
        "certification_status": ("certified" if certificate.certified else "failed"),
        "certificate_reason": certificate.reason,
        "economic_certification_reason": "not_applicable_projection_lp",
        "max_recomputed_constraint_violation": (certificate.max_constraint_violation),
        "max_constraint_violation": certificate.max_constraint_violation,
        "equality_violation": certificate.equality_violation,
        "max_bound_violation": certificate.max_bound_violation,
        "objective_residual": certificate.objective_residual,
        "duality_gap": certificate.duality_gap,
        "max_dual_violation": certificate.max_dual_violation,
        "complementarity_violation": certificate.complementarity_violation,
        "bound_marginals_used": certificate.bound_marginals_used,
        "max_raw_economic_violation": np.nan,
        "max_published_economic_violation": np.nan,
        "raw_target_account_certified": pd.NA,
        "published_target_account_certified": pd.NA,
        "published_peer_account_certified": pd.NA,
        "max_raw_target_account_violation": np.nan,
        "max_published_target_account_violation": np.nan,
        "max_published_peer_account_violation": np.nan,
    }


class KaoHwangRelationalDEA:
    """CRS relational efficiency for a basic two-stage production process.

    External resources enter stage 1, every stage-1 result is handed to stage
    2 as an intermediate, and stage 2 produces final outcomes. A shared set of
    intermediate multipliers makes the two stages use one internal accounting
    convention. The system score is the product of the selected stage scores;
    this identity is specific to this relational model, not to network DEA in
    general.
    """

    _registry_method_id = "network.relational.kao_hwang_2008"

    def __init__(
        self,
        *,
        reference: ReferenceSpec | str | None = None,
        decomposition: DecompositionPolicy = "maximize_stage_1",
        projection: ProjectionPolicy = "source_midpoint",
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        valid_decompositions = {
            "none",
            "maximize_stage_1",
            "maximize_stage_2",
            "bounds",
        }
        if decomposition not in valid_decompositions:
            raise ValueError(
                "decomposition must be one of: "
                + ", ".join(sorted(valid_decompositions))
            )
        if projection not in {"none", "source_midpoint"}:
            raise ValueError("projection must be 'none' or 'source_midpoint'")
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        if not math.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be positive and finite")
        resolved_peer_tolerance = (
            tolerance if peer_tolerance is None else peer_tolerance
        )
        if not math.isfinite(resolved_peer_tolerance) or resolved_peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive and finite")

        self.decomposition = decomposition
        self.projection = projection
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.tolerance = float(tolerance)
        self.peer_tolerance = float(resolved_peer_tolerance)

    def _certify_multiplier_task(
        self,
        *,
        problem: LinearProgram,
        solution: LPSolution,
        reference: CompiledTwoStageReference,
        x_o: np.ndarray,
        z_o: np.ndarray,
        y_o: np.ndarray,
        stage_objective: str | None,
        fixed_system_score: float | None,
        self_in_reference: bool,
    ) -> _CertifiedMultiplierTask:
        """Certify one existing solve without issuing another optimization."""

        certificate = certify_lp_solution(
            problem,
            solution,
            tolerance=self.tolerance,
        )
        if not certificate.certified or solution.primal is None:
            return _CertifiedMultiplierTask(
                solution=solution,
                certificate=certificate,
                valid=False,
                status=(
                    "solver_failed"
                    if solution.status is not SolverStatus.OPTIMAL
                    else "unavailable_uncertified_program"
                ),
                published_primal=None,
                raw_account=None,
                published_account=None,
                raw_economic_certified=None,
                published_economic_certified=None,
                economic_reason="not_checked_uncertified_source_program",
            )

        assert solution.objective is not None
        raw_primal = np.asarray(solution.primal, dtype=np.float64)
        raw_account = relational_multiplier_account(
            reference,
            x_o,
            z_o,
            y_o,
            raw_primal,
            reported_objective=float(solution.objective),
            stage_objective=stage_objective,
            fixed_system_score=fixed_system_score,
            self_in_reference=self_in_reference,
        )
        raw_certified = bool(
            math.isfinite(raw_account.max_violation)
            and raw_account.max_violation <= self.tolerance
        )
        if not raw_certified:
            return _CertifiedMultiplierTask(
                solution=solution,
                certificate=certificate,
                valid=False,
                status="unavailable_uncertified_program",
                published_primal=None,
                raw_account=raw_account,
                published_account=None,
                raw_economic_certified=False,
                published_economic_certified=None,
                economic_reason="raw_relational_account_reconstruction_failed",
            )

        published_primal = raw_primal.copy()
        numerical_negative = (published_primal < 0.0) & (
            published_primal >= -self.tolerance
        )
        published_primal[numerical_negative] = 0.0
        published_account = relational_multiplier_account(
            reference,
            x_o,
            z_o,
            y_o,
            published_primal,
            reported_objective=float(solution.objective),
            stage_objective=stage_objective,
            fixed_system_score=fixed_system_score,
            self_in_reference=self_in_reference,
        )
        published_certified = bool(
            math.isfinite(published_account.max_violation)
            and published_account.max_violation <= self.tolerance
        )
        return _CertifiedMultiplierTask(
            solution=solution,
            certificate=certificate,
            valid=published_certified,
            status=(
                "defined" if published_certified else "unavailable_uncertified_program"
            ),
            published_primal=(published_primal if published_certified else None),
            raw_account=raw_account,
            published_account=published_account,
            raw_economic_certified=True,
            published_economic_certified=published_certified,
            economic_reason=(
                "certified"
                if published_certified
                else "published_relational_account_reconstruction_failed"
            ),
        )

    def _certify_projection_values(
        self,
        *,
        reference: CompiledTwoStageReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        system_score: float,
        raw_lambdas: np.ndarray,
        raw_mus: np.ndarray,
        source: str,
        message: str,
        fallback_solver_calls: int,
        fallback_diagnostic: dict[str, Any] | None,
        factor_residual: float = 0.0,
    ) -> _Projection:
        raw_account = relational_projection_account(
            reference,
            x_o,
            y_o,
            system_score,
            raw_lambdas,
            raw_mus,
        )
        raw_violation = max(raw_account.max_violation, factor_residual)
        raw_account = replace(raw_account, max_violation=raw_violation)
        raw_certified = bool(
            math.isfinite(raw_violation) and raw_violation <= self.tolerance
        )
        if not raw_certified:
            return _Projection(
                status="raw_target_account_certificate_failed",
                source=source,
                target_valid=False,
                peer_valid=False,
                peer_status="not_available_without_certified_targets",
                lambdas=None,
                mus=None,
                peer_lambdas=None,
                peer_mus=None,
                raw_account=raw_account,
                published_account=None,
                raw_economic_certified=False,
                published_economic_certified=None,
                peer_economic_certified=None,
                peer_violation=math.nan,
                message=message,
                fallback_solver_calls=fallback_solver_calls,
                fallback_diagnostic=fallback_diagnostic,
            )

        lambdas = np.asarray(raw_lambdas, dtype=np.float64).copy()
        mus = np.asarray(raw_mus, dtype=np.float64).copy()
        lambdas[(lambdas < 0.0) & (lambdas >= -self.tolerance)] = 0.0
        mus[(mus < 0.0) & (mus >= -self.tolerance)] = 0.0
        published_account = relational_projection_account(
            reference,
            x_o,
            y_o,
            system_score,
            lambdas,
            mus,
        )
        published_certified = bool(
            math.isfinite(published_account.max_violation)
            and published_account.max_violation <= self.tolerance
        )
        if not published_certified:
            return _Projection(
                status="published_target_account_certificate_failed",
                source=source,
                target_valid=False,
                peer_valid=False,
                peer_status="not_available_without_certified_targets",
                lambdas=None,
                mus=None,
                peer_lambdas=None,
                peer_mus=None,
                raw_account=raw_account,
                published_account=published_account,
                raw_economic_certified=True,
                published_economic_certified=False,
                peer_economic_certified=None,
                peer_violation=math.nan,
                message=message,
                fallback_solver_calls=fallback_solver_calls,
                fallback_diagnostic=fallback_diagnostic,
            )

        peer_lambdas = lambdas.copy()
        peer_mus = mus.copy()
        peer_lambdas[peer_lambdas <= self.peer_tolerance] = 0.0
        peer_mus[peer_mus <= self.peer_tolerance] = 0.0
        peer_account = relational_projection_account(
            reference,
            x_o,
            y_o,
            system_score,
            peer_lambdas,
            peer_mus,
        )
        peer_violation = max(
            peer_account.max_violation,
            relational_projection_reconstruction_violation(
                reference,
                published_account,
                peer_account,
            ),
        )
        peer_valid = bool(
            math.isfinite(peer_violation) and peer_violation <= self.tolerance
        )
        return _Projection(
            status="defined",
            source=source,
            target_valid=True,
            peer_valid=peer_valid,
            peer_status=(
                "certified_projection_account"
                if peer_valid
                else "unavailable_after_peer_reporting_threshold"
            ),
            lambdas=lambdas,
            mus=mus,
            peer_lambdas=peer_lambdas if peer_valid else None,
            peer_mus=peer_mus if peer_valid else None,
            raw_account=raw_account,
            published_account=published_account,
            raw_economic_certified=True,
            published_economic_certified=True,
            peer_economic_certified=peer_valid,
            peer_violation=peer_violation,
            message=message,
            fallback_solver_calls=fallback_solver_calls,
            fallback_diagnostic=fallback_diagnostic,
        )

    def _recover_projection(
        self,
        *,
        reference: CompiledTwoStageReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        system_score: float,
        primary: _CertifiedMultiplierTask,
        name: str,
        dmu_id: object,
        period: object | None,
    ) -> _Projection:
        marginals = primary.solution.inequality_marginals
        if marginals is not None and marginals.size == 2 * reference.size:
            projection = self._certify_projection_values(
                reference=reference,
                x_o=x_o,
                y_o=y_o,
                system_score=system_score,
                raw_lambdas=(
                    -marginals[: reference.size] / reference.stage_1_row_scales
                ),
                raw_mus=(-marginals[reference.size :] / reference.stage_2_row_scales),
                source="primary_dual_marginals",
                message="projection recovered from the certified primal-dual pair",
                fallback_solver_calls=0,
                fallback_diagnostic=None,
            )
            if projection.target_valid:
                return projection

        problem = envelopment_problem(
            reference,
            x_o,
            y_o,
            name=f"{name}:projection",
        )
        solution = self.solver.solve(problem)
        certificate = certify_lp_solution(
            problem,
            solution,
            tolerance=self.tolerance,
        )
        diagnostic = _projection_diagnostic(
            dmu_id=dmu_id,
            period=period,
            phase="projection_fallback",
            solution=solution,
            certificate=certificate,
        )
        if not certificate.certified or solution.primal is None:
            return _Projection(
                status=(
                    "projection_solver_failed"
                    if solution.status is not SolverStatus.OPTIMAL
                    else "projection_lp_certificate_failed"
                ),
                source="explicit_envelopment_fallback",
                target_valid=False,
                peer_valid=False,
                peer_status="not_available_without_certified_targets",
                lambdas=None,
                mus=None,
                peer_lambdas=None,
                peer_mus=None,
                raw_account=None,
                published_account=None,
                raw_economic_certified=None,
                published_economic_certified=None,
                peer_economic_certified=None,
                peer_violation=math.nan,
                message=solution.message,
                fallback_solver_calls=1,
                fallback_diagnostic=diagnostic,
            )
        n = reference.size
        factor = float(solution.primal[-1])
        factor_residual = abs(factor - system_score) / max(
            1.0,
            abs(factor),
            abs(system_score),
        )
        return self._certify_projection_values(
            reference=reference,
            x_o=x_o,
            y_o=y_o,
            system_score=system_score,
            raw_lambdas=np.asarray(solution.primal[:n], dtype=np.float64),
            raw_mus=np.asarray(solution.primal[n : 2 * n], dtype=np.float64),
            source="explicit_envelopment_fallback",
            message=solution.message,
            fallback_solver_calls=1,
            fallback_diagnostic=diagnostic,
            factor_residual=factor_residual,
        )

    def _failure_row(
        self,
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        solver_status: str,
        backend_solver_status: str,
        score_status: str,
        within_reference: bool | Any = pd.NA,
    ) -> dict[str, Any]:
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "system_efficiency": np.nan,
            "stage_1_efficiency": np.nan,
            "stage_2_efficiency": np.nan,
            "stage_1_efficiency_lower": np.nan,
            "stage_1_efficiency_upper": np.nan,
            "stage_2_efficiency_lower": np.nan,
            "stage_2_efficiency_upper": np.nan,
            "stage_product": np.nan,
            "reconstruction_residual": np.nan,
            "is_relationally_efficient": pd.NA,
            "is_stage_1_efficient": pd.NA,
            "is_stage_2_efficient": pd.NA,
            "is_efficient": pd.NA,
            "is_within_reference_technology": within_reference,
            "score_valid": False,
            "decomposition_valid": False,
            "process_decomposition_valid": False,
            "decomposition_status": "not_available_without_certified_system",
            "decomposition_unique": pd.NA,
            "target_valid": False,
            "target_status": "not_available_without_certified_system",
            "peer_valid": False,
            "peer_status": "not_available_without_certified_targets",
            "solver_status": solver_status,
            "backend_solver_status": backend_solver_status,
            "raw_solver_status": backend_solver_status,
            "score_status": score_status,
            "model_family": "network_relational",
            "returns_to_scale": "crs",
            "reference_size": reference_size,
            "upstream_omitted_intensity_sum": np.nan,
            "downstream_omitted_intensity_sum": np.nan,
        }

    def fit(self, data: NetworkData) -> DEAResult:
        """Estimate system and process performance for every observation."""

        if not isinstance(data, NetworkData):
            raise TypeError("KaoHwangRelationalDEA.fit expects NetworkData")
        data.ensure_nonnegative()
        roles = basic_shared_multiplier_series_roles(
            data,
            model_name="Kao--Hwang relational DEA",
        )
        inputs = data.matrix(roles.inputs)
        intermediates = data.matrix(roles.intermediates)
        outputs = data.matrix(roles.outputs)
        reference_plan = build_reference_plan(data, self.reference)
        compiled: dict[int, CompiledTwoStageReference] = {}

        summary_rows: list[dict[str, Any]] = []
        component_rows: list[dict[str, Any]] = []
        multiplier_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        link_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        primary_solver_calls = 0
        secondary_solver_calls = 0
        projection_fallback_solver_calls = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                reference = compile_two_stage_reference(
                    inputs,
                    intermediates,
                    outputs,
                    reference_rows,
                )
                compiled[set_id] = reference

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = inputs[observation]
            z_o = intermediates[observation]
            y_o = outputs[observation]
            if x_o.sum() <= 0:
                failure = self._failure_row(
                    dmu_id=dmu_id,
                    period=period,
                    reference_size=reference.size,
                    solver_status=SolverStatus.FAILED.value,
                    backend_solver_status="not_run",
                    score_status="undefined_input_normalizer",
                )
                failure["decomposition_status"] = "undefined_input_normalizer"
                failure["target_status"] = "not_computed"
                summary_rows.append(failure)
                continue

            self_in_reference = bool(np.any(reference.rows == observation))
            primary_problem = multiplier_problem(
                reference,
                x_o,
                z_o,
                y_o,
                system_score=None,
                stage_objective=None,
                name=f"{name}:system",
            )
            primary_solution = self.solver.solve(primary_problem)
            primary_solver_calls += 1
            primary = self._certify_multiplier_task(
                problem=primary_problem,
                solution=primary_solution,
                reference=reference,
                x_o=x_o,
                z_o=z_o,
                y_o=y_o,
                stage_objective=None,
                fixed_system_score=None,
                self_in_reference=self_in_reference,
            )
            primary_diagnostic = _multiplier_diagnostic(
                dmu_id=dmu_id,
                period=period,
                phase="system",
                task=primary,
            )
            if (
                not primary.valid
                or primary.published_primal is None
                or primary.published_account is None
            ):
                diagnostic_rows.append(primary_diagnostic)
                summary_rows.append(
                    self._failure_row(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        solver_status=primary_solution.status.value,
                        backend_solver_status=primary_solution.status.value,
                        score_status=primary.status,
                        within_reference=(
                            False
                            if primary_solution.status is SolverStatus.INFEASIBLE
                            else pd.NA
                        ),
                    )
                )
                continue

            system_score = primary.published_account.output_virtual_value
            if -self.tolerance <= system_score < 0.0:
                system_score = 0.0
            if not math.isfinite(system_score) or system_score < 0.0:
                primary = replace(
                    primary,
                    valid=False,
                    status="invalid_system_score",
                    economic_reason="invalid_published_system_score",
                )
                diagnostic_rows.append(
                    _multiplier_diagnostic(
                        dmu_id=dmu_id,
                        period=period,
                        phase="system",
                        task=primary,
                    )
                )
                summary_rows.append(
                    self._failure_row(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        solver_status=primary_solution.status.value,
                        backend_solver_status=primary_solution.status.value,
                        score_status="invalid_system_score",
                        within_reference=False,
                    )
                )
                continue

            diagnostic_rows.append(primary_diagnostic)
            selected = primary
            selected_policy = "none"
            decomposition_status = "not_requested"
            decomposition_valid = False
            lower_stage_1 = np.nan
            upper_stage_1 = np.nan
            stage_2_lower = np.nan
            stage_2_upper = np.nan
            decomposition_unique: bool | Any = pd.NA
            stage_1 = np.nan
            stage_2 = np.nan

            maximum: _CertifiedMultiplierTask | None = None
            minimum: _CertifiedMultiplierTask | None = None
            if self.decomposition in {"maximize_stage_1", "bounds"}:
                maximum_problem = multiplier_problem(
                    reference,
                    x_o,
                    z_o,
                    y_o,
                    system_score=system_score,
                    stage_objective="maximize_stage_1",
                    name=f"{name}:maximize_stage_1",
                )
                maximum_solution = self.solver.solve(maximum_problem)
                secondary_solver_calls += 1
                maximum = self._certify_multiplier_task(
                    problem=maximum_problem,
                    solution=maximum_solution,
                    reference=reference,
                    x_o=x_o,
                    z_o=z_o,
                    y_o=y_o,
                    stage_objective="maximize_stage_1",
                    fixed_system_score=system_score,
                    self_in_reference=self_in_reference,
                )
                diagnostic_rows.append(
                    _multiplier_diagnostic(
                        dmu_id=dmu_id,
                        period=period,
                        phase="maximize_stage_1",
                        task=maximum,
                    )
                )
            if self.decomposition in {"maximize_stage_2", "bounds"}:
                minimum_problem = multiplier_problem(
                    reference,
                    x_o,
                    z_o,
                    y_o,
                    system_score=system_score,
                    stage_objective="minimize_stage_1",
                    name=f"{name}:maximize_stage_2",
                )
                minimum_solution = self.solver.solve(minimum_problem)
                secondary_solver_calls += 1
                minimum = self._certify_multiplier_task(
                    problem=minimum_problem,
                    solution=minimum_solution,
                    reference=reference,
                    x_o=x_o,
                    z_o=z_o,
                    y_o=y_o,
                    stage_objective="minimize_stage_1",
                    fixed_system_score=system_score,
                    self_in_reference=self_in_reference,
                )
                diagnostic_rows.append(
                    _multiplier_diagnostic(
                        dmu_id=dmu_id,
                        period=period,
                        phase="maximize_stage_2",
                        task=minimum,
                    )
                )

            if self.decomposition == "maximize_stage_1":
                if maximum is not None and maximum.valid:
                    selected = maximum
                    selected_policy = "maximize_stage_1_given_system_optimum"
                    decomposition_status = "selected"
                else:
                    decomposition_status = (
                        "selection_solver_failed"
                        if maximum is not None
                        and maximum.solution.status is not SolverStatus.OPTIMAL
                        else "selection_postsolve_failed"
                    )
                    selected_policy = "unavailable"
            elif self.decomposition == "maximize_stage_2":
                if minimum is not None and minimum.valid:
                    selected = minimum
                    selected_policy = "maximize_stage_2_given_system_optimum"
                    decomposition_status = "selected"
                else:
                    decomposition_status = (
                        "selection_solver_failed"
                        if minimum is not None
                        and minimum.solution.status is not SolverStatus.OPTIMAL
                        else "selection_postsolve_failed"
                    )
                    selected_policy = "unavailable"
            elif self.decomposition == "bounds":
                if (
                    maximum is not None
                    and maximum.valid
                    and maximum.published_account is not None
                    and minimum is not None
                    and minimum.valid
                    and minimum.published_account is not None
                ):
                    selected = maximum
                    selected_policy = "maximize_stage_1_with_complete_bounds"
                    decomposition_status = "bounds_computed"
                    lower_stage_1 = minimum.published_account.stage_1_efficiency
                    upper_stage_1 = maximum.published_account.stage_1_efficiency
                    stage_2_lower = maximum.published_account.stage_2_efficiency
                    stage_2_upper = minimum.published_account.stage_2_efficiency
                    if math.isfinite(lower_stage_1) and math.isfinite(upper_stage_1):
                        decomposition_unique = bool(
                            upper_stage_1 - lower_stage_1 <= self.tolerance
                        )
                else:
                    decomposition_status = (
                        "selection_solver_failed"
                        if any(
                            task is not None
                            and task.solution.status is not SolverStatus.OPTIMAL
                            for task in (maximum, minimum)
                        )
                        else "selection_postsolve_failed"
                    )
                    selected_policy = "unavailable"

            selected_account = selected.published_account
            if (
                self.decomposition != "none"
                and decomposition_status in {"selected", "bounds_computed"}
                and selected.valid
                and selected_account is not None
                and selected_account.intermediate_virtual_value > self.tolerance
            ):
                stage_1 = selected_account.stage_1_efficiency
                stage_2 = selected_account.stage_2_efficiency
                stage_product = stage_1 * stage_2
                reconstruction_residual = system_score - stage_product
                interval_valid = True
                if self.decomposition == "bounds":
                    interval_valid = bool(
                        math.isfinite(lower_stage_1)
                        and math.isfinite(upper_stage_1)
                        and math.isfinite(stage_2_lower)
                        and math.isfinite(stage_2_upper)
                        and lower_stage_1 <= upper_stage_1 + self.tolerance
                        and stage_2_lower <= stage_2_upper + self.tolerance
                    )
                decomposition_valid = bool(
                    math.isfinite(stage_product)
                    and math.isfinite(reconstruction_residual)
                    and abs(reconstruction_residual) <= self.tolerance
                    and interval_valid
                )
                if not decomposition_valid:
                    decomposition_status = "process_account_certificate_failed"
            else:
                stage_product = np.nan
                reconstruction_residual = np.nan
                if (
                    self.decomposition != "none"
                    and decomposition_status in {"selected", "bounds_computed"}
                    and selected.valid
                    and selected_account is not None
                    and selected_account.intermediate_virtual_value <= self.tolerance
                ):
                    decomposition_status = "undefined_intermediate_virtual_value"

            if not decomposition_valid and self.decomposition != "none":
                stage_1 = np.nan
                stage_2 = np.nan
                stage_product = np.nan
                reconstruction_residual = np.nan
                lower_stage_1 = np.nan
                upper_stage_1 = np.nan
                stage_2_lower = np.nan
                stage_2_upper = np.nan
                decomposition_unique = pd.NA

            projection = _Projection(
                status="not_requested",
                source="none",
                target_valid=False,
                peer_valid=False,
                peer_status="not_requested",
                lambdas=None,
                mus=None,
                peer_lambdas=None,
                peer_mus=None,
                raw_account=None,
                published_account=None,
                raw_economic_certified=None,
                published_economic_certified=None,
                peer_economic_certified=None,
                peer_violation=math.nan,
                message="projection was not requested",
                fallback_solver_calls=0,
                fallback_diagnostic=None,
            )
            if self.projection == "source_midpoint":
                projection = self._recover_projection(
                    reference=reference,
                    x_o=x_o,
                    y_o=y_o,
                    system_score=system_score,
                    primary=primary,
                    name=name,
                    dmu_id=dmu_id,
                    period=period,
                )
                projection_fallback_solver_calls += projection.fallback_solver_calls
                if projection.fallback_diagnostic is not None:
                    diagnostic_rows.append(projection.fallback_diagnostic)

            primary_diagnostic.update(
                {
                    "raw_target_account_certified": (projection.raw_economic_certified),
                    "published_target_account_certified": (
                        projection.published_economic_certified
                    ),
                    "published_peer_account_certified": (
                        projection.peer_economic_certified
                    ),
                    "max_raw_target_account_violation": (
                        np.nan
                        if projection.raw_account is None
                        else projection.raw_account.max_violation
                    ),
                    "max_published_target_account_violation": (
                        np.nan
                        if projection.published_account is None
                        else projection.published_account.max_violation
                    ),
                    "max_published_peer_account_violation": (projection.peer_violation),
                }
            )

            within_reference = bool(system_score <= 1.0 + self.tolerance)
            is_relationally_efficient = bool(
                within_reference and abs(system_score - 1.0) <= self.tolerance
            )
            is_stage_1_efficient: bool | Any = (
                bool(abs(stage_1 - 1.0) <= self.tolerance)
                if decomposition_valid
                else pd.NA
            )
            is_stage_2_efficient: bool | Any = (
                bool(abs(stage_2 - 1.0) <= self.tolerance)
                if decomposition_valid
                else pd.NA
            )

            component_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "component_kind": "system",
                    "component_id": "system",
                    "score": system_score,
                    "efficiency": system_score,
                    "score_lower": system_score,
                    "score_upper": system_score,
                    "is_measure_efficient": is_relationally_efficient,
                    "selection_policy": "maximize_system_efficiency",
                    "valid": True,
                    "status": "defined",
                }
            )
            if decomposition_valid:
                for component_id, value, lower, upper, efficient in (
                    (
                        roles.stage_1,
                        stage_1,
                        lower_stage_1,
                        upper_stage_1,
                        is_stage_1_efficient,
                    ),
                    (
                        roles.stage_2,
                        stage_2,
                        stage_2_lower,
                        stage_2_upper,
                        is_stage_2_efficient,
                    ),
                ):
                    component_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "component_kind": "process",
                            "component_id": component_id,
                            "score": value,
                            "efficiency": value,
                            "score_lower": lower,
                            "score_upper": upper,
                            "is_measure_efficient": efficient,
                            "selection_policy": selected_policy,
                            "valid": True,
                            "status": decomposition_status,
                        }
                    )

            publish_multiplier = bool(
                selected.valid
                and selected.published_primal is not None
                and selected.published_account is not None
                and (self.decomposition == "none" or decomposition_valid)
            )
            if publish_multiplier:
                assert selected.published_primal is not None
                assert selected.published_account is not None
                phase = "system" if self.decomposition == "none" else "stage_selection"
                scaled_weights = (
                    selected.published_primal[: len(roles.inputs)],
                    selected.published_primal[
                        len(roles.inputs) : len(roles.inputs) + len(roles.intermediates)
                    ],
                    selected.published_primal[
                        len(roles.inputs) + len(roles.intermediates) :
                    ],
                )
                multiplier_groups = (
                    selected.published_account.input_multipliers,
                    selected.published_account.intermediate_multipliers,
                    selected.published_account.output_multipliers,
                )
                assert all(group is not None for group in multiplier_groups)
                for role, names, observed, scaled, weights, shared in (
                    (
                        "external_input",
                        roles.inputs,
                        x_o,
                        scaled_weights[0],
                        multiplier_groups[0],
                        None,
                    ),
                    (
                        "intermediate",
                        roles.intermediates,
                        z_o,
                        scaled_weights[1],
                        multiplier_groups[1],
                        f"{roles.stage_1}.output|{roles.stage_2}.input",
                    ),
                    (
                        "final_output",
                        roles.outputs,
                        y_o,
                        scaled_weights[2],
                        multiplier_groups[2],
                        None,
                    ),
                ):
                    assert weights is not None
                    for variable, value, scaled_weight, weight in zip(
                        names,
                        observed,
                        scaled,
                        weights,
                        strict=True,
                    ):
                        multiplier_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "phase": phase,
                                "role": role,
                                "variable": variable,
                                "scaled_multiplier": float(scaled_weight),
                                "multiplier": float(weight),
                                "observed": float(value),
                                "virtual_contribution": float(weight) * float(value),
                                "shared_between": shared,
                                "valid": True,
                                "status": "certified_published_account",
                                "is_zero_for_display": bool(
                                    abs(scaled_weight) <= self.tolerance
                                ),
                            }
                        )

            upstream_omitted_intensity_sum = np.nan
            downstream_omitted_intensity_sum = np.nan
            if (
                projection.target_valid
                and projection.lambdas is not None
                and projection.mus is not None
                and projection.published_account is not None
            ):
                account = projection.published_account
                assert account.input_targets is not None
                assert account.upstream_supply is not None
                assert account.downstream_requirement is not None
                assert account.output_targets is not None
                input_targets = account.input_targets
                upstream_supply = account.upstream_supply
                downstream_requirement = account.downstream_requirement
                output_targets = account.output_targets
                link_targets = 0.5 * (upstream_supply + downstream_requirement)

                upstream_omitted_intensity_sum = float(
                    projection.lambdas[projection.lambdas <= self.peer_tolerance].sum()
                )
                downstream_omitted_intensity_sum = float(
                    projection.mus[projection.mus <= self.peer_tolerance].sum()
                )
                if (
                    projection.peer_valid
                    and projection.peer_lambdas is not None
                    and projection.peer_mus is not None
                ):
                    for process_id, kind, values in (
                        (roles.stage_1, "upstream_lambda", projection.peer_lambdas),
                        (roles.stage_2, "downstream_mu", projection.peer_mus),
                    ):
                        for local_position, intensity in enumerate(values):
                            if intensity <= 0.0:
                                continue
                            reference_position = reference.rows[local_position]
                            intensity_rows.append(
                                {
                                    "dmu_id": dmu_id,
                                    "period": period,
                                    "process_id": process_id,
                                    "intensity_kind": kind,
                                    "reference_dmu_id": data.dmu_ids[
                                        reference_position
                                    ],
                                    "reference_period": (
                                        None
                                        if data.periods is None
                                        else data.periods[reference_position]
                                    ),
                                    "intensity": float(intensity),
                                    "lambda": float(intensity),
                                    "valid": True,
                                    "status": projection.peer_status,
                                }
                            )

                for variable, observed, target in zip(
                    roles.inputs,
                    x_o,
                    input_targets,
                    strict=True,
                ):
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "process_id": roles.stage_1,
                            "role": "external_input",
                            "variable": variable,
                            "observed": float(observed),
                            "target": float(target),
                            "target_lower": float(target),
                            "target_upper": float(target),
                            "valid": True,
                            "status": projection.status,
                            "projection_policy": "lim_zhu_dual",
                        }
                    )
                for variable, observed, lower, upper, target in zip(
                    roles.intermediates,
                    z_o,
                    downstream_requirement,
                    upstream_supply,
                    link_targets,
                    strict=True,
                ):
                    for process_id, role in (
                        (roles.stage_1, "intermediate_output"),
                        (roles.stage_2, "intermediate_input"),
                    ):
                        target_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "process_id": process_id,
                                "role": role,
                                "variable": variable,
                                "observed": float(observed),
                                "target": float(target),
                                "target_lower": float(lower),
                                "target_upper": float(upper),
                                "valid": True,
                                "status": projection.status,
                                "projection_policy": "source_midpoint",
                            }
                        )
                    link_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "link_id": roles.link_id,
                            "variable": variable,
                            "observed": float(observed),
                            "downstream_requirement": float(lower),
                            "upstream_supply": float(upper),
                            "target_lower": float(lower),
                            "target_upper": float(upper),
                            "target": float(target),
                            "disposable_surplus": float(upper - lower),
                            "projection_policy": "source_midpoint",
                            "balance_residual": float(upper - lower),
                            "valid": True,
                            "status": projection.status,
                        }
                    )
                for variable, observed, target in zip(
                    roles.outputs,
                    y_o,
                    output_targets,
                    strict=True,
                ):
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "process_id": roles.stage_2,
                            "role": "final_output",
                            "variable": variable,
                            "observed": float(observed),
                            "target": float(target),
                            "target_lower": float(target),
                            "target_upper": float(target),
                            "valid": True,
                            "status": projection.status,
                            "projection_policy": "lim_zhu_dual",
                        }
                    )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": system_score,
                    "efficiency": system_score,
                    "distance": np.nan,
                    "system_efficiency": system_score,
                    "stage_1_efficiency": stage_1,
                    "stage_2_efficiency": stage_2,
                    "stage_1_efficiency_lower": lower_stage_1,
                    "stage_1_efficiency_upper": upper_stage_1,
                    "stage_2_efficiency_lower": stage_2_lower,
                    "stage_2_efficiency_upper": stage_2_upper,
                    "stage_product": stage_product,
                    "reconstruction_residual": reconstruction_residual,
                    "is_relationally_efficient": is_relationally_efficient,
                    "is_stage_1_efficient": is_stage_1_efficient,
                    "is_stage_2_efficient": is_stage_2_efficient,
                    "is_efficient": pd.NA,
                    "is_within_reference_technology": within_reference,
                    "score_valid": True,
                    "decomposition_valid": decomposition_valid,
                    "process_decomposition_valid": decomposition_valid,
                    "decomposition_status": decomposition_status,
                    "decomposition_unique": decomposition_unique,
                    "target_valid": projection.target_valid,
                    "target_status": projection.status,
                    "peer_valid": projection.peer_valid,
                    "peer_status": projection.peer_status,
                    "solver_status": primary_solution.status.value,
                    "backend_solver_status": primary_solution.status.value,
                    "raw_solver_status": primary_solution.status.value,
                    "score_status": "defined",
                    "model_family": "network_relational",
                    "returns_to_scale": "crs",
                    "reference_size": reference.size,
                    "upstream_omitted_intensity_sum": (upstream_omitted_intensity_sum),
                    "downstream_omitted_intensity_sum": (
                        downstream_omitted_intensity_sum
                    ),
                }
            )

        total_solver_calls = (
            primary_solver_calls
            + secondary_solver_calls
            + projection_fallback_solver_calls
        )
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows, columns=_SUMMARY_COLUMNS),
            targets=pd.DataFrame(target_rows, columns=_TARGET_COLUMNS),
            intensities=pd.DataFrame(intensity_rows, columns=_INTENSITY_COLUMNS),
            components=pd.DataFrame(component_rows, columns=_COMPONENT_COLUMNS),
            multipliers=pd.DataFrame(multiplier_rows, columns=_MULTIPLIER_COLUMNS),
            links=pd.DataFrame(link_rows, columns=_LINK_COLUMNS),
            diagnostics=pd.DataFrame(
                diagnostic_rows,
                columns=_DIAGNOSTIC_COLUMNS,
            ),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": "joint_system_and_process_accountability",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {
                            "kind": "series",
                            "processes": [roles.stage_1, roles.stage_2],
                            "link": {
                                "id": roles.link_id,
                                "quantity": "observed_once",
                                "multiplier_policy": "shared",
                                "intensity_policy": "process_specific",
                                "envelopment_balance": (
                                    "upstream_supply_greater_than_or_equal_to_"
                                    "downstream_requirement"
                                ),
                            },
                        },
                        "data_roles": {
                            "variables": {
                                "external_inputs": list(roles.inputs),
                                "intermediates": list(roles.intermediates),
                                "final_outputs": list(roles.outputs),
                            },
                            "counts": {
                                "external_inputs": len(roles.inputs),
                                "intermediates": len(roles.intermediates),
                                "final_outputs": len(roles.outputs),
                            },
                            "panel": data.is_panel,
                            "grouped": data.groups is not None,
                        },
                        "technology": {
                            "family": "relational_network_envelopment",
                            "returns_to_scale": "crs",
                            "process_relationship": "series",
                            "link_disposal": "upstream_surplus_allowed",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_multiplier_envelopment_dual",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                        ),
                        "performance": {
                            "family": "kao_hwang_multiplicative_relational",
                            "orientation": "input_system",
                            "system_identity": "stage_1_times_stage_2",
                            "decomposition": self.decomposition,
                        },
                        "valuation": {
                            "kind": "endogenous_multiplier",
                            "intermediate_weights": "shared_between_processes",
                            "weight_floor": "nonnegative_limit_no_numeric_epsilon",
                        },
                        "evaluation_protocol": {
                            "kind": "self_appraisal",
                            "stage_selection": self.decomposition,
                            "projection": self.projection,
                            "strong_slack_completion": False,
                        },
                        "analysis": {"kind": "direct_network_fit_with_process_account"},
                        "uncertainty": {
                            "sampling": {"kind": "none"},
                            "data": {"kind": "none"},
                        },
                    },
                ),
                "solver": self.solver.name,
                "projection_policy": self.projection,
                "decomposition_policy": self.decomposition,
                "graph_fingerprint": data.graph_fingerprint,
                "stage_scores_are_attributions": True,
                "stage_scores_are_causal_contributions": False,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": len(compiled),
                "primary_solves": primary_solver_calls,
                "secondary_solves": secondary_solver_calls,
                "projection_fallback_solves": projection_fallback_solver_calls,
                "solver_calls": total_solver_calls,
                "additional_solver_calls": 0,
                "intensity_reporting": {
                    "rule": "strictly_above_peer_tolerance",
                    "targets_use_unthresholded_intensities": True,
                    "omitted_sums_reported_in_summary": True,
                    "failure_policy": (
                        "withhold_peer_rows_when_thresholded_account_fails"
                    ),
                },
                "postsolve_certificate": {
                    "lp": "solver_neutral_primal_dual_kkt_and_strong_duality",
                    "economic": (
                        "raw_and_published_original_quantity_relational_accounts"
                    ),
                    "target": "raw_and_published_original_quantity_projection",
                    "peer": "thresholded_peer_target_and_link_reconstruction",
                    "failure_policy": "per_observation_atomic_semantic_release",
                    "additional_solver_calls": 0,
                },
            },
        )


KaoHwangDEA = KaoHwangRelationalDEA


__all__ = ["KaoHwangDEA", "KaoHwangRelationalDEA"]
