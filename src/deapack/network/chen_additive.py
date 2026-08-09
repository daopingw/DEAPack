"""Chen--Cook--Li--Zhu additive efficiency decomposition for two stages."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any, Literal

import numpy as np
import pandas as pd

from .._registry import reference_spec as registry_reference_spec
from .._registry import registry_metadata
from ..enums import ReturnsToScale, SolverStatus, parse_enum
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
from ._additive import (
    CompiledAdditiveReference,
    compile_additive_reference,
    envelopment_problem,
    primary_problem,
    secondary_problem,
)
from ._series import TwoStageSeriesRoles, basic_shared_multiplier_series_roles
from .data import NetworkData

DecompositionPolicy = Literal[
    "none",
    "maximize_stage_1",
    "maximize_stage_2",
    "both_priorities",
]
ProjectionPolicy = Literal["none", "source"]


@dataclass(frozen=True, slots=True)
class _Account:
    solution: LPSolution
    input_virtual: float
    intermediate_virtual: float
    final_virtual: float
    stage_1_intercept: float
    stage_2_intercept: float
    stage_1_output: float
    stage_2_output: float
    stage_1_efficiency: float
    stage_2_efficiency: float
    stage_1_weight: float
    stage_2_weight: float
    reconstructed_system: float


@dataclass(frozen=True, slots=True)
class _CertifiedAdditiveSolve:
    """One solved multiplier programme and its publication certificate."""

    solution: LPSolution
    certificate: LPCertificate
    account: _Account | None
    valid: bool
    status: str
    raw_economic_certified: bool | None
    published_economic_certified: bool | None
    raw_economic_violation: float
    published_economic_violation: float
    max_process_constraint_violation: float
    normalization_violation: float
    objective_account_violation: float
    reconstruction_violation: float
    minimum_share_violation: float
    economic_certification_reason: str


@dataclass(frozen=True, slots=True)
class _AccountAudit:
    account: _Account
    max_violation: float
    max_process_constraint_violation: float
    normalization_violation: float
    objective_account_violation: float
    reconstruction_violation: float
    minimum_share_violation: float


@dataclass(frozen=True, slots=True)
class _Projection:
    target_valid: bool
    target_status: str
    source: str
    target_lambdas: np.ndarray | None
    target_mus: np.ndarray | None
    peer_valid: bool
    peer_status: str
    peer_lambdas: np.ndarray | None
    peer_mus: np.ndarray | None
    message: str
    raw_account_certified: bool | None
    published_account_certified: bool | None
    raw_account_violation: float
    published_account_violation: float
    peer_account_violation: float


_COMPONENT_COLUMNS = (
    "dmu_id",
    "period",
    "component_kind",
    "component_id",
    "score",
    "efficiency",
    "aggregation_weight",
    "weight_origin",
    "virtual_input",
    "virtual_output",
    "intercept",
    "is_measure_efficient",
    "selection_policy",
    "status",
    "account_valid",
    "account_status",
)
_MULTIPLIER_COLUMNS = (
    "dmu_id",
    "period",
    "phase",
    "process_id",
    "role",
    "variable",
    "scaled_multiplier",
    "multiplier",
    "observed",
    "virtual_contribution",
    "shared_between",
    "selection_policy",
    "is_zero_for_display",
    "account_valid",
    "account_status",
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
    "peer_valid",
    "peer_status",
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
    "projection_policy",
    "target_valid",
    "target_status",
)
_LINK_COLUMNS = (
    "dmu_id",
    "period",
    "link_id",
    "source_process_id",
    "target_process_id",
    "variable",
    "observed_source",
    "observed_target",
    "source_target",
    "target_target",
    "upstream_supply",
    "downstream_requirement",
    "target_lower",
    "target_upper",
    "target",
    "required_disposition",
    "disposed_quantity",
    "disposable_surplus",
    "balance_residual",
    "projection_policy",
    "target_valid",
    "target_status",
    "link_account_valid",
    "link_account_status",
)


def _diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    phase: str,
    task: _CertifiedAdditiveSolve,
) -> dict[str, Any]:
    solution = task.solution
    certificate = task.certificate
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
        "certification_reason": (
            certificate.reason
            if not certificate.certified
            else task.economic_certification_reason
        ),
        "economic_certification_reason": task.economic_certification_reason,
        "max_constraint_violation": certificate.max_constraint_violation,
        "equality_violation": certificate.equality_violation,
        "max_bound_violation": certificate.max_bound_violation,
        "objective_residual": certificate.objective_residual,
        "duality_gap": certificate.duality_gap,
        "max_dual_violation": certificate.max_dual_violation,
        "complementarity_violation": certificate.complementarity_violation,
        "bound_marginals_used": certificate.bound_marginals_used,
        "max_raw_economic_violation": task.raw_economic_violation,
        "max_published_economic_violation": task.published_economic_violation,
        "max_economic_violation": (
            task.published_economic_violation
            if task.published_economic_certified is not None
            else task.raw_economic_violation
        ),
        "max_process_constraint_violation": (task.max_process_constraint_violation),
        "normalization_violation": task.normalization_violation,
        "objective_account_violation": task.objective_account_violation,
        "reconstruction_violation": task.reconstruction_violation,
        "minimum_share_violation": task.minimum_share_violation,
        "published_target_account_certified": pd.NA,
        "published_peer_account_certified": pd.NA,
        "max_raw_target_account_violation": np.nan,
        "max_published_target_account_violation": np.nan,
        "max_published_peer_account_violation": np.nan,
    }


def _safe_ratio(numerator: float, denominator: float, tolerance: float) -> float:
    if denominator <= tolerance:
        return np.nan
    return float(numerator / denominator)


def _account(
    solution: LPSolution,
    reference: CompiledAdditiveReference,
    x_o: np.ndarray,
    z_o: np.ndarray,
    y_o: np.ndarray,
    tolerance: float,
) -> _Account:
    if solution.primal is None:
        raise ValueError("an optimal primal solution is required")
    x_bar_o = x_o / reference.input_scales
    z_bar_o = z_o / reference.intermediate_scales
    y_bar_o = y_o / reference.output_scales
    m = x_bar_o.size
    q = z_bar_o.size

    input_virtual = float(solution.primal[:m] @ x_bar_o)
    intermediate_virtual = float(solution.primal[m : m + q] @ z_bar_o)
    final_virtual = float(solution.primal[m + q : -2] @ y_bar_o)
    stage_1_intercept = float(solution.primal[-2])
    stage_2_intercept = float(solution.primal[-1])
    stage_1_output = intermediate_virtual + stage_1_intercept
    stage_2_output = final_virtual + stage_2_intercept
    total_virtual_input = input_virtual + intermediate_virtual
    stage_1_weight = _safe_ratio(
        input_virtual,
        total_virtual_input,
        tolerance,
    )
    stage_2_weight = _safe_ratio(
        intermediate_virtual,
        total_virtual_input,
        tolerance,
    )
    stage_1_efficiency = _safe_ratio(
        stage_1_output,
        input_virtual,
        tolerance,
    )
    stage_2_efficiency = _safe_ratio(
        stage_2_output,
        intermediate_virtual,
        tolerance,
    )
    reconstructed_system = _safe_ratio(
        stage_1_output + stage_2_output,
        total_virtual_input,
        tolerance,
    )
    return _Account(
        solution=solution,
        input_virtual=input_virtual,
        intermediate_virtual=intermediate_virtual,
        final_virtual=final_virtual,
        stage_1_intercept=stage_1_intercept,
        stage_2_intercept=stage_2_intercept,
        stage_1_output=stage_1_output,
        stage_2_output=stage_2_output,
        stage_1_efficiency=stage_1_efficiency,
        stage_2_efficiency=stage_2_efficiency,
        stage_1_weight=stage_1_weight,
        stage_2_weight=stage_2_weight,
        reconstructed_system=reconstructed_system,
    )


class ChenCookLiZhuAdditiveDEA:
    """Weighted-additive stage decomposition for a closed two-stage system.

    Here ``additive`` means that system efficiency is an endogenous
    virtual-resource-share-weighted arithmetic mean of two radial stage
    efficiencies. It is not the slack-sum objective implemented by
    :class:`deapack.AdditiveDEA`.
    """

    _registry_method_id = "network.additive.chen_etal_2009"

    def __init__(
        self,
        *,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        reference: ReferenceSpec | str | None = None,
        decomposition: DecompositionPolicy = "both_priorities",
        projection: ProjectionPolicy = "source",
        minimum_stage_share: float = 0.0,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.returns_to_scale = parse_enum(
            returns_to_scale,
            ReturnsToScale,
            "returns_to_scale",
        )
        if self.returns_to_scale not in {
            ReturnsToScale.CRS,
            ReturnsToScale.VRS,
        }:
            raise ValueError(
                "ChenCookLiZhuAdditiveDEA supports only source-defined CRS or VRS"
            )
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
            "both_priorities",
        }
        if decomposition not in valid_decompositions:
            raise ValueError(
                "decomposition must be one of: "
                + ", ".join(sorted(valid_decompositions))
            )
        if projection not in {"none", "source"}:
            raise ValueError("projection must be 'none' or 'source'")
        if (
            not math.isfinite(minimum_stage_share)
            or minimum_stage_share < 0
            or minimum_stage_share > 0.5
        ):
            raise ValueError("minimum_stage_share must be finite and in [0, 0.5]")
        if minimum_stage_share > 0 and projection != "none":
            raise ValueError(
                "source projections are unavailable when minimum_stage_share "
                "changes the defining multiplier programme; use projection='none'"
            )
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
        self.minimum_stage_share = float(minimum_stage_share)
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.tolerance = float(tolerance)
        self.peer_tolerance = float(resolved_peer_tolerance)

    def _audit_account(
        self,
        *,
        solution: LPSolution,
        reference: CompiledAdditiveReference,
        x_o: np.ndarray,
        z_o: np.ndarray,
        y_o: np.ndarray,
        phase: str,
        fixed_system_score: float | None,
        self_in_reference: bool,
    ) -> _AccountAudit:
        """Rebuild all virtual accounts from the original declared quantities."""

        account = _account(
            solution,
            reference,
            x_o,
            z_o,
            y_o,
            self.tolerance,
        )
        assert solution.primal is not None
        primal = np.asarray(solution.primal, dtype=np.float64)
        m = x_o.size
        q = z_o.size
        input_multipliers = primal[:m] / reference.input_scales
        link_multipliers = primal[m : m + q] / reference.intermediate_scales
        output_multipliers = primal[m + q : -2] / reference.output_scales
        stage_1_slacks = (
            reference.inputs @ input_multipliers
            - reference.intermediates @ link_multipliers
            - account.stage_1_intercept
        )
        stage_2_slacks = (
            reference.intermediates @ link_multipliers
            - reference.outputs @ output_multipliers
            - account.stage_2_intercept
        )
        process_constraint_violation = float(
            max(
                np.maximum(-stage_1_slacks, 0.0).max(initial=0.0),
                np.maximum(-stage_2_slacks, 0.0).max(initial=0.0),
            )
        )
        nonnegative_violation = float(np.maximum(-primal[:-2], 0.0).max(initial=0.0))
        total_virtual_input = account.input_virtual + account.intermediate_virtual
        if phase == "primary":
            normalization_violation = abs(total_virtual_input - 1.0)
            expected_objective = -(account.stage_1_output + account.stage_2_output)
            expected_system_score = -float(solution.objective)
        elif phase == "stage_1":
            normalization_violation = abs(account.input_virtual - 1.0)
            expected_objective = -account.stage_1_output
            expected_system_score = fixed_system_score
        elif phase == "stage_2":
            normalization_violation = abs(account.intermediate_virtual - 1.0)
            expected_objective = -account.stage_2_output
            expected_system_score = fixed_system_score
        else:
            raise ValueError(f"unknown additive account phase: {phase!r}")
        objective_account_violation = abs(
            float(solution.objective) - expected_objective
        ) / max(1.0, abs(float(solution.objective)), abs(expected_objective))
        reconstruction_violation = (
            math.inf
            if expected_system_score is None
            or not math.isfinite(account.reconstructed_system)
            else abs(account.reconstructed_system - expected_system_score)
            / max(
                1.0,
                abs(account.reconstructed_system),
                abs(expected_system_score),
            )
        )
        minimum_share_violation = 0.0
        if self.minimum_stage_share > 0.0:
            minimum_share_violation = max(
                self.minimum_stage_share - account.stage_1_weight,
                self.minimum_stage_share - account.stage_2_weight,
                0.0,
            )
        self_reference_violation = (
            max(account.reconstructed_system - 1.0, 0.0)
            if self_in_reference and phase == "primary"
            else 0.0
        )
        score_domain_violation = (
            max(-account.reconstructed_system, 0.0)
            if math.isfinite(account.reconstructed_system)
            else math.inf
        )
        finite_account = bool(
            np.isfinite(input_multipliers).all()
            and np.isfinite(link_multipliers).all()
            and np.isfinite(output_multipliers).all()
            and np.isfinite(stage_1_slacks).all()
            and np.isfinite(stage_2_slacks).all()
            and math.isfinite(account.input_virtual)
            and math.isfinite(account.intermediate_virtual)
            and math.isfinite(account.final_virtual)
            and math.isfinite(account.reconstructed_system)
        )
        maximum = (
            max(
                nonnegative_violation,
                process_constraint_violation,
                normalization_violation,
                objective_account_violation,
                reconstruction_violation,
                minimum_share_violation,
                self_reference_violation,
                score_domain_violation,
            )
            if finite_account
            else math.inf
        )
        return _AccountAudit(
            account=account,
            max_violation=float(maximum),
            max_process_constraint_violation=process_constraint_violation,
            normalization_violation=normalization_violation,
            objective_account_violation=objective_account_violation,
            reconstruction_violation=reconstruction_violation,
            minimum_share_violation=minimum_share_violation,
        )

    def _publication_primal(
        self,
        *,
        solution: LPSolution,
        reference: CompiledAdditiveReference,
        x_o: np.ndarray,
        z_o: np.ndarray,
        y_o: np.ndarray,
    ) -> np.ndarray:
        """Clean only numerically small values with a bounded account effect."""

        assert solution.primal is not None
        published = np.asarray(solution.primal, dtype=np.float64).copy()
        assessed = np.concatenate(
            [
                np.abs(x_o / reference.input_scales),
                np.abs(z_o / reference.intermediate_scales),
                np.abs(y_o / reference.output_scales),
                np.ones(2, dtype=np.float64),
            ]
        )
        reference_max = np.concatenate(
            [
                np.max(np.abs(reference.scaled_inputs), axis=0),
                np.max(np.abs(reference.scaled_intermediates), axis=0),
                np.max(np.abs(reference.scaled_outputs), axis=0),
                np.ones(2, dtype=np.float64),
            ]
        )
        coefficient_scale = np.maximum(1.0, np.maximum(assessed, reference_max))
        thresholds = self.tolerance / (max(1, published.size) * coefficient_scale)
        published[np.abs(published) <= thresholds] = 0.0
        return published

    def _certify_solve(
        self,
        *,
        problem: LinearProgram,
        solution: LPSolution,
        reference: CompiledAdditiveReference,
        x_o: np.ndarray,
        z_o: np.ndarray,
        y_o: np.ndarray,
        phase: str,
        fixed_system_score: float | None,
        self_in_reference: bool,
        certificate_override: LPCertificate | None = None,
    ) -> _CertifiedAdditiveSolve:
        """Certify an already solved source programme with zero extra solves."""

        certificate = (
            certify_lp_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )
            if certificate_override is None
            else certificate_override
        )
        unavailable = f"unavailable_without_certified_{phase}_program"

        def failed(
            *,
            status: str,
            raw_certified: bool | None,
            published_certified: bool | None,
            raw_violation: float,
            published_violation: float,
            reason: str,
            audit: _AccountAudit | None = None,
        ) -> _CertifiedAdditiveSolve:
            return _CertifiedAdditiveSolve(
                solution=solution,
                certificate=certificate,
                account=None,
                valid=False,
                status=status,
                raw_economic_certified=raw_certified,
                published_economic_certified=published_certified,
                raw_economic_violation=raw_violation,
                published_economic_violation=published_violation,
                max_process_constraint_violation=(
                    math.nan
                    if audit is None
                    else audit.max_process_constraint_violation
                ),
                normalization_violation=(
                    math.nan if audit is None else audit.normalization_violation
                ),
                objective_account_violation=(
                    math.nan if audit is None else audit.objective_account_violation
                ),
                reconstruction_violation=(
                    math.nan if audit is None else audit.reconstruction_violation
                ),
                minimum_share_violation=(
                    math.nan if audit is None else audit.minimum_share_violation
                ),
                economic_certification_reason=reason,
            )

        if not certificate.certified or solution.primal is None:
            return failed(
                status=(
                    "solver_failed"
                    if solution.status is not SolverStatus.OPTIMAL
                    else f"unavailable_uncertified_{phase}_program"
                ),
                raw_certified=None,
                published_certified=None,
                raw_violation=math.nan,
                published_violation=math.nan,
                reason=f"not_checked_{unavailable}",
            )

        raw_audit = self._audit_account(
            solution=solution,
            reference=reference,
            x_o=x_o,
            z_o=z_o,
            y_o=y_o,
            phase=phase,
            fixed_system_score=fixed_system_score,
            self_in_reference=self_in_reference,
        )
        if raw_audit.max_violation > self.tolerance:
            return failed(
                status=f"unavailable_uncertified_{phase}_program",
                raw_certified=False,
                published_certified=None,
                raw_violation=raw_audit.max_violation,
                published_violation=math.nan,
                reason="raw_additive_account_reconstruction_failed",
                audit=raw_audit,
            )

        published_solution = replace(
            solution,
            primal=self._publication_primal(
                solution=solution,
                reference=reference,
                x_o=x_o,
                z_o=z_o,
                y_o=y_o,
            ),
        )
        published_audit = self._audit_account(
            solution=published_solution,
            reference=reference,
            x_o=x_o,
            z_o=z_o,
            y_o=y_o,
            phase=phase,
            fixed_system_score=fixed_system_score,
            self_in_reference=self_in_reference,
        )
        if published_audit.max_violation > self.tolerance:
            return failed(
                status=f"unavailable_uncertified_{phase}_program",
                raw_certified=True,
                published_certified=False,
                raw_violation=raw_audit.max_violation,
                published_violation=published_audit.max_violation,
                reason="published_additive_account_reconstruction_failed",
                audit=published_audit,
            )
        return _CertifiedAdditiveSolve(
            solution=solution,
            certificate=certificate,
            account=published_audit.account,
            valid=True,
            status="defined",
            raw_economic_certified=True,
            published_economic_certified=True,
            raw_economic_violation=raw_audit.max_violation,
            published_economic_violation=published_audit.max_violation,
            max_process_constraint_violation=(
                published_audit.max_process_constraint_violation
            ),
            normalization_violation=published_audit.normalization_violation,
            objective_account_violation=(published_audit.objective_account_violation),
            reconstruction_violation=published_audit.reconstruction_violation,
            minimum_share_violation=published_audit.minimum_share_violation,
            economic_certification_reason="certified",
        )

    def _projection_certificate(
        self,
        reference: CompiledAdditiveReference,
        x_o: np.ndarray,
        z_o: np.ndarray,
        y_o: np.ndarray,
        system_score: float,
        lambdas: np.ndarray,
        mus: np.ndarray,
    ) -> float:
        values = np.concatenate([lambdas, mus])
        if (
            lambdas.shape != (reference.size,)
            or mus.shape != (reference.size,)
            or not np.isfinite(values).all()
            or not math.isfinite(system_score)
        ):
            return math.inf
        input_targets = reference.inputs.T @ lambdas
        upstream_targets = reference.intermediates.T @ lambdas
        downstream_targets = reference.intermediates.T @ mus
        output_targets = reference.outputs.T @ mus
        input_violation = np.maximum(
            (input_targets - system_score * x_o) / reference.input_scales,
            0.0,
        )
        link_violation = np.maximum(
            ((1.0 - system_score) * z_o - (upstream_targets - downstream_targets))
            / reference.intermediate_scales,
            0.0,
        )
        output_violation = np.maximum(
            (y_o - output_targets) / reference.output_scales,
            0.0,
        )
        convexity_violation = 0.0
        if self.returns_to_scale is ReturnsToScale.VRS:
            convexity_violation = max(
                abs(float(lambdas.sum()) - 1.0),
                abs(float(mus.sum()) - 1.0),
            )
        return float(
            max(
                input_violation.max(initial=0.0),
                link_violation.max(initial=0.0),
                output_violation.max(initial=0.0),
                convexity_violation,
                np.maximum(-values, 0.0).max(initial=0.0),
            )
        )

    def _projection_publication_intensities(
        self,
        reference: CompiledAdditiveReference,
        lambdas: np.ndarray,
        mus: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Remove only noise with a bounded effect on every target account."""

        n = reference.size
        lambda_scale = np.maximum.reduce(
            [
                np.max(np.abs(reference.scaled_inputs), axis=1),
                np.max(np.abs(reference.scaled_intermediates), axis=1),
                np.ones(n, dtype=np.float64),
            ]
        )
        mu_scale = np.maximum.reduce(
            [
                np.max(np.abs(reference.scaled_intermediates), axis=1),
                np.max(np.abs(reference.scaled_outputs), axis=1),
                np.ones(n, dtype=np.float64),
            ]
        )
        budget = max(1, 2 * n)
        lambda_threshold = self.tolerance / (budget * lambda_scale)
        mu_threshold = self.tolerance / (budget * mu_scale)
        published_lambdas = np.asarray(lambdas, dtype=np.float64).copy()
        published_mus = np.asarray(mus, dtype=np.float64).copy()
        published_lambdas[np.abs(published_lambdas) <= lambda_threshold] = 0.0
        published_mus[np.abs(published_mus) <= mu_threshold] = 0.0
        return published_lambdas, published_mus

    def _peer_reconstruction_violation(
        self,
        reference: CompiledAdditiveReference,
        target_lambdas: np.ndarray,
        target_mus: np.ndarray,
        peer_lambdas: np.ndarray,
        peer_mus: np.ndarray,
    ) -> float:
        differences = (
            reference.scaled_inputs.T @ (target_lambdas - peer_lambdas),
            reference.scaled_intermediates.T @ (target_lambdas - peer_lambdas),
            reference.scaled_intermediates.T @ (target_mus - peer_mus),
            reference.scaled_outputs.T @ (target_mus - peer_mus),
        )
        convexity = 0.0
        if self.returns_to_scale is ReturnsToScale.VRS:
            convexity = max(
                abs(float(target_lambdas.sum() - peer_lambdas.sum())),
                abs(float(target_mus.sum() - peer_mus.sum())),
            )
        if not all(np.isfinite(values).all() for values in differences):
            return math.inf
        return float(
            max(
                *(np.abs(values).max(initial=0.0) for values in differences),
                convexity,
            )
        )

    def _recover_projection(
        self,
        *,
        reference: CompiledAdditiveReference,
        x_o: np.ndarray,
        z_o: np.ndarray,
        y_o: np.ndarray,
        system_score: float,
        primary: LPSolution,
        name: str,
        dmu_id: object,
        period: object | None,
        diagnostics: list[dict[str, Any]],
    ) -> _Projection:
        marginals = primary.inequality_marginals
        if marginals is not None and marginals.size == 2 * reference.size:
            raw_lambdas = -marginals[: reference.size] / reference.stage_1_row_scales
            raw_mus = -marginals[reference.size :] / reference.stage_2_row_scales
            raw_violation = self._projection_certificate(
                reference,
                x_o,
                z_o,
                y_o,
                system_score,
                raw_lambdas,
                raw_mus,
            )
            if raw_violation <= self.tolerance:
                target_lambdas, target_mus = self._projection_publication_intensities(
                    reference,
                    raw_lambdas,
                    raw_mus,
                )
                published_violation = self._projection_certificate(
                    reference,
                    x_o,
                    z_o,
                    y_o,
                    system_score,
                    target_lambdas,
                    target_mus,
                )
                published_nonnegative = bool(
                    np.all(target_lambdas >= 0.0) and np.all(target_mus >= 0.0)
                )
                if published_violation <= self.tolerance and published_nonnegative:
                    peer_lambdas = target_lambdas.copy()
                    peer_mus = target_mus.copy()
                    peer_lambdas[peer_lambdas <= self.peer_tolerance] = 0.0
                    peer_mus[peer_mus <= self.peer_tolerance] = 0.0
                    peer_violation = max(
                        self._projection_certificate(
                            reference,
                            x_o,
                            z_o,
                            y_o,
                            system_score,
                            peer_lambdas,
                            peer_mus,
                        ),
                        self._peer_reconstruction_violation(
                            reference,
                            target_lambdas,
                            target_mus,
                            peer_lambdas,
                            peer_mus,
                        ),
                    )
                    peer_valid = bool(peer_violation <= self.tolerance)
                    return _Projection(
                        target_valid=True,
                        target_status="defined",
                        source="primary_dual_marginals",
                        target_lambdas=target_lambdas,
                        target_mus=target_mus,
                        peer_valid=peer_valid,
                        peer_status=(
                            "defined"
                            if peer_valid
                            else "unavailable_after_peer_reporting_threshold"
                        ),
                        peer_lambdas=peer_lambdas if peer_valid else None,
                        peer_mus=peer_mus if peer_valid else None,
                        message=(
                            "projection recovered from the certified primary "
                            "primal-dual pair"
                        ),
                        raw_account_certified=True,
                        published_account_certified=True,
                        raw_account_violation=raw_violation,
                        published_account_violation=published_violation,
                        peer_account_violation=peer_violation,
                    )
                return _Projection(
                    target_valid=False,
                    target_status="unavailable_uncertified_projection_account",
                    source="primary_dual_marginals",
                    target_lambdas=None,
                    target_mus=None,
                    peer_valid=False,
                    peer_status="not_available_without_certified_target_account",
                    peer_lambdas=None,
                    peer_mus=None,
                    message="published projection account failed certification",
                    raw_account_certified=True,
                    published_account_certified=False,
                    raw_account_violation=raw_violation,
                    published_account_violation=published_violation,
                    peer_account_violation=math.nan,
                )

        # Preserve the established source-projection fallback.  This solve is
        # part of the requested projection contract, not certificate overhead.
        primal = self.solver.solve(
            envelopment_problem(
                reference,
                x_o,
                z_o,
                y_o,
                returns_to_scale=self.returns_to_scale,
                name=f"{name}:projection",
            )
        )
        diagnostics.append(
            {
                "dmu_id": dmu_id,
                "period": period,
                "phase": "projection_fallback",
                "solver_status": primal.status.value,
                "backend_solver_status": primal.status.value,
                "raw_solver_status": primal.status.value,
                "message": primal.message,
                "iterations": primal.iterations,
                "max_primal_violation": primal.max_primal_violation,
            }
        )
        expected_primal_size = 2 * reference.size + 1
        if (
            not primal.is_optimal
            or primal.primal is None
            or np.asarray(primal.primal).shape != (expected_primal_size,)
            or not np.isfinite(primal.primal).all()
        ):
            return _Projection(
                target_valid=False,
                target_status="solver_failed",
                source="explicit_envelopment_fallback",
                target_lambdas=None,
                target_mus=None,
                peer_valid=False,
                peer_status="not_available_without_certified_target_account",
                peer_lambdas=None,
                peer_mus=None,
                message=primal.message,
                raw_account_certified=None,
                published_account_certified=None,
                raw_account_violation=math.nan,
                published_account_violation=math.nan,
                peer_account_violation=math.nan,
            )
        n = reference.size
        lambdas = np.asarray(primal.primal[:n], dtype=np.float64).copy()
        mus = np.asarray(primal.primal[n : 2 * n], dtype=np.float64).copy()
        violation = max(
            abs(float(primal.primal[-1]) - system_score),
            self._projection_certificate(
                reference,
                x_o,
                z_o,
                y_o,
                system_score,
                lambdas,
                mus,
            ),
        )
        if violation > self.tolerance:
            return _Projection(
                target_valid=False,
                target_status="unavailable_uncertified_projection_account",
                source="explicit_envelopment_fallback",
                target_lambdas=None,
                target_mus=None,
                peer_valid=False,
                peer_status="not_available_without_certified_target_account",
                peer_lambdas=None,
                peer_mus=None,
                message="the additive envelopment projection failed its certificate",
                raw_account_certified=False,
                published_account_certified=None,
                raw_account_violation=violation,
                published_account_violation=math.nan,
                peer_account_violation=math.nan,
            )
        target_lambdas, target_mus = self._projection_publication_intensities(
            reference,
            lambdas,
            mus,
        )
        published_violation = self._projection_certificate(
            reference,
            x_o,
            z_o,
            y_o,
            system_score,
            target_lambdas,
            target_mus,
        )
        peer_lambdas = target_lambdas.copy()
        peer_mus = target_mus.copy()
        peer_lambdas[peer_lambdas <= self.peer_tolerance] = 0.0
        peer_mus[peer_mus <= self.peer_tolerance] = 0.0
        peer_violation = max(
            self._projection_certificate(
                reference,
                x_o,
                z_o,
                y_o,
                system_score,
                peer_lambdas,
                peer_mus,
            ),
            self._peer_reconstruction_violation(
                reference,
                target_lambdas,
                target_mus,
                peer_lambdas,
                peer_mus,
            ),
        )
        target_valid = bool(
            published_violation <= self.tolerance
            and np.all(target_lambdas >= 0.0)
            and np.all(target_mus >= 0.0)
        )
        peer_valid = bool(target_valid and peer_violation <= self.tolerance)
        return _Projection(
            target_valid=target_valid,
            target_status=(
                "defined"
                if target_valid
                else "unavailable_uncertified_projection_account"
            ),
            source="explicit_envelopment_fallback",
            target_lambdas=target_lambdas if target_valid else None,
            target_mus=target_mus if target_valid else None,
            peer_valid=peer_valid,
            peer_status=(
                "defined"
                if peer_valid
                else "unavailable_after_peer_reporting_threshold"
                if target_valid
                else "not_available_without_certified_target_account"
            ),
            peer_lambdas=peer_lambdas if peer_valid else None,
            peer_mus=peer_mus if peer_valid else None,
            message=primal.message,
            raw_account_certified=True,
            published_account_certified=target_valid,
            raw_account_violation=violation,
            published_account_violation=published_violation,
            peer_account_violation=peer_violation,
        )

    def _solve_secondary(
        self,
        *,
        priority: str,
        reference: CompiledAdditiveReference,
        x_o: np.ndarray,
        z_o: np.ndarray,
        y_o: np.ndarray,
        system_score: float,
        name: str,
        dmu_id: object,
        period: object | None,
        diagnostics: list[dict[str, Any]],
        self_in_reference: bool,
    ) -> _CertifiedAdditiveSolve:
        problem = secondary_problem(
            reference,
            x_o,
            z_o,
            y_o,
            system_score=system_score,
            priority=priority,
            returns_to_scale=self.returns_to_scale,
            minimum_stage_share=self.minimum_stage_share,
            name=f"{name}:maximize_{priority}",
        )
        solution = self.solver.solve(problem)
        task = self._certify_solve(
            problem=problem,
            solution=solution,
            reference=reference,
            x_o=x_o,
            z_o=z_o,
            y_o=y_o,
            phase=priority,
            fixed_system_score=system_score,
            self_in_reference=self_in_reference,
        )
        diagnostics.append(
            _diagnostic(
                dmu_id=dmu_id,
                period=period,
                phase=f"maximize_{priority}",
                task=task,
            )
        )
        return task

    def _append_multipliers(
        self,
        rows: list[dict[str, Any]],
        *,
        data: NetworkData,
        observation: int,
        reference: CompiledAdditiveReference,
        roles: TwoStageSeriesRoles,
        account: _Account,
        policy: str,
        x_o: np.ndarray,
        z_o: np.ndarray,
        y_o: np.ndarray,
    ) -> None:
        assert account.solution.primal is not None
        period = None if data.periods is None else data.periods[observation]
        dmu_id = data.dmu_ids[observation]
        m = len(roles.inputs)
        q = len(roles.intermediates)
        scaled = account.solution.primal
        groups = (
            (
                roles.stage_1,
                "external_input",
                roles.inputs,
                x_o,
                reference.input_scales,
                scaled[:m],
                None,
            ),
            (
                f"{roles.stage_1}|{roles.stage_2}",
                "intermediate",
                roles.intermediates,
                z_o,
                reference.intermediate_scales,
                scaled[m : m + q],
                f"{roles.stage_1}.output|{roles.stage_2}.input",
            ),
            (
                roles.stage_2,
                "final_output",
                roles.outputs,
                y_o,
                reference.output_scales,
                scaled[m + q : -2],
                None,
            ),
        )
        for process_id, role, names, observed, scales, values, shared in groups:
            for variable, value, scale, scaled_value in zip(
                names,
                observed,
                scales,
                values,
                strict=True,
            ):
                multiplier = float(scaled_value / scale)
                rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": "stage_selection",
                        "process_id": process_id,
                        "role": role,
                        "variable": variable,
                        "scaled_multiplier": float(scaled_value),
                        "multiplier": multiplier,
                        "observed": float(value),
                        "virtual_contribution": multiplier * float(value),
                        "shared_between": shared,
                        "selection_policy": policy,
                        "is_zero_for_display": bool(
                            abs(scaled_value) <= self.tolerance
                        ),
                        "account_valid": True,
                        "account_status": "defined",
                    }
                )
        for process_id, value in (
            (roles.stage_1, account.stage_1_intercept),
            (roles.stage_2, account.stage_2_intercept),
        ):
            rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": "stage_selection",
                    "process_id": process_id,
                    "role": "process_intercept",
                    "variable": None,
                    "scaled_multiplier": value,
                    "multiplier": value,
                    "observed": 1.0,
                    "virtual_contribution": value,
                    "shared_between": None,
                    "selection_policy": policy,
                    "is_zero_for_display": bool(abs(value) <= self.tolerance),
                    "account_valid": True,
                    "account_status": "defined",
                }
            )

    def fit(self, data: NetworkData) -> DEAResult:
        """Estimate additive system and process efficiency for every observation."""
        if not isinstance(data, NetworkData):
            raise TypeError("ChenCookLiZhuAdditiveDEA.fit expects NetworkData")
        data.ensure_nonnegative(model_name="Chen--Cook--Li--Zhu additive DEA")
        roles = basic_shared_multiplier_series_roles(
            data,
            model_name="Chen--Cook--Li--Zhu additive DEA",
        )
        inputs = data.matrix(roles.inputs)
        intermediates = data.matrix(roles.intermediates)
        outputs = data.matrix(roles.outputs)
        reference_plan = build_reference_plan(data, self.reference)
        compiled: dict[int, CompiledAdditiveReference] = {}

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
                reference = compile_additive_reference(
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
            undefined_domain = (
                "undefined_input_normalizer"
                if x_o.sum() <= 0
                else "undefined_intermediate_normalizer"
                if z_o.sum() <= 0
                else None
            )
            if undefined_domain is not None:
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        status=undefined_domain,
                    )
                )
                continue

            primary_lp = primary_problem(
                reference,
                x_o,
                z_o,
                y_o,
                returns_to_scale=self.returns_to_scale,
                minimum_stage_share=self.minimum_stage_share,
                name=f"{name}:system",
            )
            primary = self.solver.solve(primary_lp)
            primary_solver_calls += 1
            self_in_reference = bool(np.any(reference.rows == observation))
            primary_task = self._certify_solve(
                problem=primary_lp,
                solution=primary,
                reference=reference,
                x_o=x_o,
                z_o=z_o,
                y_o=y_o,
                phase="primary",
                fixed_system_score=None,
                self_in_reference=self_in_reference,
            )
            precomputed_projection: _Projection | None = None
            if (
                not primary_task.valid
                and self.projection == "source"
                and primary_task.certificate.reason
                == "missing_or_invalid_row_optimality_certificate"
                and primary.primal is not None
                and primary.objective is not None
            ):
                preliminary = self._audit_account(
                    solution=primary,
                    reference=reference,
                    x_o=x_o,
                    z_o=z_o,
                    y_o=y_o,
                    phase="primary",
                    fixed_system_score=None,
                    self_in_reference=self_in_reference,
                )
                if preliminary.max_violation <= self.tolerance:
                    precomputed_projection = self._recover_projection(
                        reference=reference,
                        x_o=x_o,
                        z_o=z_o,
                        y_o=y_o,
                        system_score=preliminary.account.reconstructed_system,
                        primary=primary,
                        name=name,
                        dmu_id=dmu_id,
                        period=period,
                        diagnostics=diagnostic_rows,
                    )
                    projection_fallback_solver_calls += 1
                    if precomputed_projection.target_valid:
                        witness_violation = max(
                            preliminary.max_violation,
                            precomputed_projection.raw_account_violation,
                            precomputed_projection.published_account_violation,
                        )
                        source_pair_certificate = replace(
                            primary_task.certificate,
                            certified=True,
                            reason="certified_by_source_primal_dual_pair",
                            duality_gap=witness_violation,
                            max_dual_violation=witness_violation,
                            complementarity_violation=witness_violation,
                        )
                        primary_task = self._certify_solve(
                            problem=primary_lp,
                            solution=primary,
                            reference=reference,
                            x_o=x_o,
                            z_o=z_o,
                            y_o=y_o,
                            phase="primary",
                            fixed_system_score=None,
                            self_in_reference=self_in_reference,
                            certificate_override=source_pair_certificate,
                        )
            diagnostic_rows.append(
                _diagnostic(
                    dmu_id=dmu_id,
                    period=period,
                    phase="system",
                    task=primary_task,
                )
            )
            if not primary_task.valid or primary_task.account is None:
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        status=primary_task.status,
                        solver_status=primary.status,
                    )
                )
                continue

            primary_account = primary_task.account
            system_score = primary_account.reconstructed_system

            stage_1_task: _CertifiedAdditiveSolve | None = None
            stage_2_task: _CertifiedAdditiveSolve | None = None
            if self.decomposition in {"maximize_stage_1", "both_priorities"}:
                stage_1_task = self._solve_secondary(
                    priority="stage_1",
                    reference=reference,
                    x_o=x_o,
                    z_o=z_o,
                    y_o=y_o,
                    system_score=system_score,
                    name=name,
                    dmu_id=dmu_id,
                    period=period,
                    diagnostics=diagnostic_rows,
                    self_in_reference=self_in_reference,
                )
                secondary_solver_calls += 1
            if self.decomposition in {"maximize_stage_2", "both_priorities"}:
                stage_2_task = self._solve_secondary(
                    priority="stage_2",
                    reference=reference,
                    x_o=x_o,
                    z_o=z_o,
                    y_o=y_o,
                    system_score=system_score,
                    name=name,
                    dmu_id=dmu_id,
                    period=period,
                    diagnostics=diagnostic_rows,
                    self_in_reference=self_in_reference,
                )
                secondary_solver_calls += 1

            account_1 = None if stage_1_task is None else stage_1_task.account
            account_2 = None if stage_2_task is None else stage_2_task.account

            if self.decomposition == "none":
                selected = primary_account
                selected_policy = "primary_optimum_not_attributed"
                decomposition_status = "not_requested"
                report_stage_scores = False
                process_account_valid = False
                process_account_status = "not_requested"
            elif self.decomposition in {"maximize_stage_1", "both_priorities"}:
                selected = account_1 or primary_account
                selected_policy = "maximize_stage_1"
                decomposition_status = (
                    "defined"
                    if account_1 is not None
                    else (
                        "secondary_solver_failed"
                        if stage_1_task is None
                        else stage_1_task.status
                    )
                )
                report_stage_scores = account_1 is not None
                process_account_valid = account_1 is not None
                process_account_status = decomposition_status
                if (
                    self.decomposition == "both_priorities"
                    and account_1 is not None
                    and account_2 is not None
                    and math.isfinite(account_2.stage_1_efficiency)
                    and abs(account_2.stage_1_efficiency - account_1.stage_1_efficiency)
                    <= 10.0 * self.tolerance
                    and (
                        not math.isfinite(account_1.stage_2_efficiency)
                        or account_2.stage_2_efficiency
                        > account_1.stage_2_efficiency + self.tolerance
                    )
                ):
                    selected = account_2
                    selected_policy = "maximize_stage_1_then_stage_2_tie_break"
            else:
                selected = account_2 or primary_account
                selected_policy = "maximize_stage_2"
                decomposition_status = (
                    "defined"
                    if account_2 is not None
                    else (
                        "secondary_solver_failed"
                        if stage_2_task is None
                        else stage_2_task.status
                    )
                )
                report_stage_scores = account_2 is not None
                process_account_valid = account_2 is not None
                process_account_status = decomposition_status

            stage_1 = selected.stage_1_efficiency if report_stage_scores else np.nan
            stage_2 = selected.stage_2_efficiency if report_stage_scores else np.nan
            weight_1 = selected.stage_1_weight if report_stage_scores else np.nan
            weight_2 = selected.stage_2_weight if report_stage_scores else np.nan
            reconstructed = (
                selected.reconstructed_system if report_stage_scores else np.nan
            )
            reconstruction_residual = (
                reconstructed - system_score if math.isfinite(reconstructed) else np.nan
            )
            decomposition_unique: bool | Any = pd.NA
            if account_1 is not None and account_2 is not None:
                decomposition_unique = bool(
                    abs(account_1.stage_1_efficiency - account_2.stage_1_efficiency)
                    <= 10.0 * self.tolerance
                    and abs(account_1.stage_2_efficiency - account_2.stage_2_efficiency)
                    <= 10.0 * self.tolerance
                )

            within_reference = bool(system_score <= 1.0 + self.tolerance)
            is_additively_efficient = bool(
                within_reference and abs(system_score - 1.0) <= self.tolerance
            )
            is_stage_1_efficient: bool | Any = (
                bool(abs(stage_1 - 1.0) <= self.tolerance)
                if math.isfinite(stage_1)
                else pd.NA
            )
            is_stage_2_efficient: bool | Any = (
                bool(abs(stage_2 - 1.0) <= self.tolerance)
                if math.isfinite(stage_2)
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
                    "aggregation_weight": 1.0,
                    "weight_origin": "system_identity",
                    "virtual_input": 1.0,
                    "virtual_output": system_score,
                    "intercept": 0.0,
                    "is_measure_efficient": is_additively_efficient,
                    "selection_policy": "maximize_system_efficiency",
                    "status": "defined",
                    "account_valid": True,
                    "account_status": "defined",
                }
            )
            if report_stage_scores:
                for (
                    component_id,
                    score,
                    weight,
                    virtual_input,
                    virtual_output,
                    intercept,
                    efficient,
                ) in (
                    (
                        roles.stage_1,
                        stage_1,
                        weight_1,
                        selected.input_virtual,
                        selected.stage_1_output,
                        selected.stage_1_intercept,
                        is_stage_1_efficient,
                    ),
                    (
                        roles.stage_2,
                        stage_2,
                        weight_2,
                        selected.intermediate_virtual,
                        selected.stage_2_output,
                        selected.stage_2_intercept,
                        is_stage_2_efficient,
                    ),
                ):
                    component_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "component_kind": "process",
                            "component_id": component_id,
                            "score": score,
                            "efficiency": score,
                            "aggregation_weight": weight,
                            "weight_origin": ("endogenous_virtual_input_share"),
                            "virtual_input": virtual_input,
                            "virtual_output": virtual_output,
                            "intercept": intercept,
                            "is_measure_efficient": efficient,
                            "selection_policy": selected_policy,
                            "status": decomposition_status,
                            "account_valid": True,
                            "account_status": process_account_status,
                        }
                    )
                self._append_multipliers(
                    multiplier_rows,
                    data=data,
                    observation=observation,
                    reference=reference,
                    roles=roles,
                    account=selected,
                    policy=selected_policy,
                    x_o=x_o,
                    z_o=z_o,
                    y_o=y_o,
                )

            projection = _Projection(
                target_valid=False,
                target_status="not_requested",
                source="none",
                target_lambdas=None,
                target_mus=None,
                peer_valid=False,
                peer_status="not_requested",
                peer_lambdas=None,
                peer_mus=None,
                message="projection was not requested",
                raw_account_certified=None,
                published_account_certified=None,
                raw_account_violation=math.nan,
                published_account_violation=math.nan,
                peer_account_violation=math.nan,
            )
            if self.projection == "source":
                if precomputed_projection is not None:
                    projection = precomputed_projection
                else:
                    projection = self._recover_projection(
                        reference=reference,
                        x_o=x_o,
                        z_o=z_o,
                        y_o=y_o,
                        system_score=system_score,
                        primary=primary,
                        name=name,
                        dmu_id=dmu_id,
                        period=period,
                        diagnostics=diagnostic_rows,
                    )
                    if projection.source == "explicit_envelopment_fallback":
                        projection_fallback_solver_calls += 1
            primary_diagnostic = next(
                row
                for row in reversed(diagnostic_rows)
                if row["dmu_id"] == dmu_id
                and row["period"] == period
                and row["phase"] == "system"
            )
            primary_diagnostic["published_target_account_certified"] = (
                projection.published_account_certified
            )
            primary_diagnostic["published_peer_account_certified"] = (
                projection.peer_valid if projection.target_valid else pd.NA
            )
            primary_diagnostic["max_raw_target_account_violation"] = (
                projection.raw_account_violation
            )
            primary_diagnostic["max_published_target_account_violation"] = (
                projection.published_account_violation
            )
            primary_diagnostic["max_published_peer_account_violation"] = (
                projection.peer_account_violation
            )
            if projection.target_valid:
                self._append_projection(
                    data=data,
                    observation=observation,
                    reference=reference,
                    roles=roles,
                    x_o=x_o,
                    z_o=z_o,
                    y_o=y_o,
                    system_score=system_score,
                    projection=projection,
                    intensity_rows=intensity_rows,
                    target_rows=target_rows,
                    link_rows=link_rows,
                )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": system_score,
                    "efficiency": system_score,
                    "score_valid": True,
                    "distance": np.nan,
                    "system_efficiency": system_score,
                    "stage_1_efficiency": stage_1,
                    "stage_2_efficiency": stage_2,
                    "stage_1_weight": weight_1,
                    "stage_2_weight": weight_2,
                    "stage_1_efficiency_when_stage_1_prioritized": (
                        np.nan if account_1 is None else account_1.stage_1_efficiency
                    ),
                    "stage_2_efficiency_when_stage_1_prioritized": (
                        np.nan if account_1 is None else account_1.stage_2_efficiency
                    ),
                    "stage_1_efficiency_when_stage_2_prioritized": (
                        np.nan if account_2 is None else account_2.stage_1_efficiency
                    ),
                    "stage_2_efficiency_when_stage_2_prioritized": (
                        np.nan if account_2 is None else account_2.stage_2_efficiency
                    ),
                    "stage_1_intercept": (
                        selected.stage_1_intercept if report_stage_scores else np.nan
                    ),
                    "stage_2_intercept": (
                        selected.stage_2_intercept if report_stage_scores else np.nan
                    ),
                    "weighted_stage_sum": reconstructed,
                    "reconstruction_residual": reconstruction_residual,
                    "is_additively_efficient": is_additively_efficient,
                    "is_stage_1_efficient": is_stage_1_efficient,
                    "is_stage_2_efficient": is_stage_2_efficient,
                    "is_efficient": pd.NA,
                    "is_within_reference_technology": within_reference,
                    "decomposition_status": decomposition_status,
                    "process_account_valid": process_account_valid,
                    "process_account_status": process_account_status,
                    "link_account_valid": projection.target_valid,
                    "link_account_status": (
                        "defined"
                        if projection.target_valid
                        else projection.target_status
                    ),
                    "decomposition_unique": decomposition_unique,
                    "target_valid": projection.target_valid,
                    "target_status": projection.target_status,
                    "peer_valid": projection.peer_valid,
                    "peer_status": projection.peer_status,
                    "solver_status": primary.status.value,
                    "backend_solver_status": primary.status.value,
                    "raw_solver_status": primary.status.value,
                    "score_status": "defined",
                    "model_family": "network_additive_stage_decomposition",
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": reference.size,
                }
            )

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            targets=pd.DataFrame(target_rows, columns=_TARGET_COLUMNS),
            intensities=pd.DataFrame(intensity_rows, columns=_INTENSITY_COLUMNS),
            components=pd.DataFrame(component_rows, columns=_COMPONENT_COLUMNS),
            multipliers=pd.DataFrame(multiplier_rows, columns=_MULTIPLIER_COLUMNS),
            links=pd.DataFrame(link_rows, columns=_LINK_COLUMNS),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": ("joint_system_and_process_accountability"),
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {
                            "kind": "series",
                            "processes": [roles.stage_1, roles.stage_2],
                            "link": {
                                "id": roles.link_id,
                                "quantity": "observed_once",
                                "multiplier_policy": "shared",
                                "projection_account": (
                                    "distinct_upstream_and_downstream_targets"
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
                            "family": "closed_two_stage_series",
                            "returns_to_scale": self.returns_to_scale.value,
                            "process_relationship": "series",
                            "intermediate_disposition": "source_defined",
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
                            "family": "chen_etal_weighted_additive",
                            "orientation": "input_system",
                            "system_identity": (
                                "virtual_resource_share_weighted_stage_sum"
                            ),
                            "decomposition": self.decomposition,
                        },
                        "valuation": {
                            "kind": "endogenous_multiplier",
                            "stage_weight_origin": ("endogenous_virtual_input_share"),
                            "minimum_stage_share": self.minimum_stage_share,
                            "weight_floor": ("explicit_policy_no_numeric_epsilon"),
                        },
                        "evaluation_protocol": {
                            "kind": "self_appraisal",
                            "stage_selection": self.decomposition,
                            "projection": self.projection,
                            "strong_slack_completion": False,
                        },
                        "analysis": {
                            "kind": ("system_process_additive_decomposition"),
                            "reconstruction_check": True,
                        },
                        "uncertainty": {
                            "sampling": {"kind": "none"},
                            "data": {"kind": "none"},
                        },
                    },
                ),
                "graph_fingerprint": data.graph_fingerprint,
                "decomposition_policy": self.decomposition,
                "projection_policy": self.projection,
                "minimum_stage_share": self.minimum_stage_share,
                "compiled_reference_sets": len(compiled),
                "primary_solver_calls": primary_solver_calls,
                "secondary_solver_calls": secondary_solver_calls,
                "projection_fallback_solver_calls": (projection_fallback_solver_calls),
                "solver_calls": (
                    primary_solver_calls
                    + secondary_solver_calls
                    + projection_fallback_solver_calls
                ),
                "additional_solver_calls": 0,
                "certificate_extra_solver_calls": 0,
                "validation_basis": {
                    "dataset": "two_stage_public_service",
                    "score_account": "project_case_system_process_reconstruction",
                    "projection_account": "project_case_split_link_certificate",
                },
                "postsolve_certificate": {
                    "lp": "solver_neutral_primal_dual_kkt_and_strong_duality",
                    "economic": (
                        "raw_and_published_original_quantity_system_process_"
                        "link_and_constraint_slack_accounts"
                    ),
                    "peer": "thresholded_projection_account_reconstruction",
                    "failure_policy": (
                        "headline_process_target_and_peer_accounts_publish_"
                        "through_independent_atomic_gates"
                    ),
                },
            },
        )

    def _append_projection(
        self,
        *,
        data: NetworkData,
        observation: int,
        reference: CompiledAdditiveReference,
        roles: TwoStageSeriesRoles,
        x_o: np.ndarray,
        z_o: np.ndarray,
        y_o: np.ndarray,
        system_score: float,
        projection: _Projection,
        intensity_rows: list[dict[str, Any]],
        target_rows: list[dict[str, Any]],
        link_rows: list[dict[str, Any]],
    ) -> None:
        assert projection.target_lambdas is not None
        assert projection.target_mus is not None
        lambdas = projection.target_lambdas
        mus = projection.target_mus
        dmu_id = data.dmu_ids[observation]
        period = None if data.periods is None else data.periods[observation]
        input_targets = reference.inputs.T @ lambdas
        upstream_targets = reference.intermediates.T @ lambdas
        downstream_targets = reference.intermediates.T @ mus
        output_targets = reference.outputs.T @ mus

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
                            "reference_dmu_id": data.dmu_ids[reference_position],
                            "reference_period": (
                                None
                                if data.periods is None
                                else data.periods[reference_position]
                            ),
                            "intensity": float(intensity),
                            "lambda": float(intensity),
                            "peer_valid": True,
                            "peer_status": projection.peer_status,
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
                    "projection_policy": "lim_zhu_additive_dual",
                    "target_valid": True,
                    "target_status": projection.target_status,
                }
            )
        for variable, observed, upstream, downstream in zip(
            roles.intermediates,
            z_o,
            upstream_targets,
            downstream_targets,
            strict=True,
        ):
            for process_id, role, target in (
                (roles.stage_1, "intermediate_output", upstream),
                (roles.stage_2, "intermediate_input", downstream),
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
                        "target_lower": float(target),
                        "target_upper": float(target),
                        "projection_policy": "lim_zhu_split_link",
                        "target_valid": True,
                        "target_status": projection.target_status,
                    }
                )
            required_disposition = (1.0 - system_score) * float(observed)
            actual_disposition = float(upstream - downstream)
            link_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "link_id": roles.link_id,
                    "source_process_id": roles.stage_1,
                    "target_process_id": roles.stage_2,
                    "variable": variable,
                    "observed_source": float(observed),
                    "observed_target": float(observed),
                    "source_target": float(upstream),
                    "target_target": float(downstream),
                    "upstream_supply": float(upstream),
                    "downstream_requirement": float(downstream),
                    "target_lower": float(downstream),
                    "target_upper": float(upstream),
                    "target": np.nan,
                    "required_disposition": required_disposition,
                    "disposed_quantity": actual_disposition,
                    "disposable_surplus": actual_disposition,
                    "balance_residual": actual_disposition - required_disposition,
                    "projection_policy": "lim_zhu_split_link",
                    "target_valid": True,
                    "target_status": projection.target_status,
                    "link_account_valid": True,
                    "link_account_status": "defined",
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
                    "projection_policy": "lim_zhu_additive_dual",
                    "target_valid": True,
                    "target_status": projection.target_status,
                }
            )

    def _undefined_summary(
        self,
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        status: str,
        score: float = np.nan,
        solver_status: SolverStatus = SolverStatus.FAILED,
    ) -> dict[str, Any]:
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": score,
            "efficiency": score,
            "score_valid": False,
            "distance": np.nan,
            "system_efficiency": score,
            "stage_1_efficiency": np.nan,
            "stage_2_efficiency": np.nan,
            "stage_1_weight": np.nan,
            "stage_2_weight": np.nan,
            "stage_1_efficiency_when_stage_1_prioritized": np.nan,
            "stage_2_efficiency_when_stage_1_prioritized": np.nan,
            "stage_1_efficiency_when_stage_2_prioritized": np.nan,
            "stage_2_efficiency_when_stage_2_prioritized": np.nan,
            "stage_1_intercept": np.nan,
            "stage_2_intercept": np.nan,
            "weighted_stage_sum": np.nan,
            "reconstruction_residual": np.nan,
            "is_additively_efficient": pd.NA,
            "is_stage_1_efficient": pd.NA,
            "is_stage_2_efficient": pd.NA,
            "is_efficient": pd.NA,
            "is_within_reference_technology": pd.NA,
            "decomposition_status": "not_available",
            "process_account_valid": False,
            "process_account_status": "not_available_without_certified_primary",
            "link_account_valid": False,
            "link_account_status": "not_available_without_certified_primary",
            "decomposition_unique": pd.NA,
            "target_valid": False,
            "target_status": "not_computed",
            "peer_valid": False,
            "peer_status": "not_available_without_certified_target_account",
            "solver_status": solver_status.value,
            "backend_solver_status": solver_status.value,
            "raw_solver_status": solver_status.value,
            "score_status": status,
            "model_family": "network_additive_stage_decomposition",
            "returns_to_scale": self.returns_to_scale.value,
            "reference_size": reference_size,
        }


TwoStageAdditiveDecompositionDEA = ChenCookLiZhuAdditiveDEA


__all__ = [
    "ChenCookLiZhuAdditiveDEA",
    "TwoStageAdditiveDecompositionDEA",
]
