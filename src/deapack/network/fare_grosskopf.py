"""Färe--Grosskopf radial efficiency for a two-stage series network."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
import pandas as pd

from .._registry import reference_spec as registry_reference_spec
from .._registry import registry_metadata
from ..enums import Orientation, ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError
from ..models._common import clean_small
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
    CompiledTwoStageQuantities,
    compile_two_stage_quantities,
    envelopment_problem,
)
from ._series import basic_two_stage_series_roles
from .data import NetworkData

_LPCertificate = LPCertificate
"""Backward-compatible private name for established internal imports."""


@dataclass(frozen=True, slots=True)
class _CertifiedNetworkRadialTask:
    """One solved system programme and its independent release decisions."""

    solution: LPSolution
    certificate: LPCertificate
    score_valid: bool
    score_status: str
    factor: float | None
    published_primal: np.ndarray | None
    peer_lambdas: np.ndarray | None
    peer_mus: np.ndarray | None
    peer_valid: bool
    peer_status: str
    raw_economic_certified: bool | None
    published_economic_certified: bool | None
    raw_economic_violation: float
    published_economic_violation: float
    peer_economic_violation: float
    economic_certification_reason: str


def _certify_lp_solution(
    problem: LinearProgram,
    solution: LPSolution,
    *,
    tolerance: float,
) -> LPCertificate:
    """Compatibility entry point backed by the shared solver-neutral gate."""

    certificate = certify_lp_solution(problem, solution, tolerance=tolerance)
    if certificate.reason == "missing_or_invalid_row_optimality_certificate":
        return replace(certificate, reason="missing_optimality_certificate")
    return certificate


def _diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    solution: LPSolution,
    certificate: LPCertificate,
    economic_violation: float,
    accepted: bool,
) -> dict[str, Any]:
    """Compatibility diagnostic used by established network kernels."""

    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": "system",
        "solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
        "certification_status": "certified" if accepted else "failed",
        "certificate_reason": (
            "postprocessed_quantity_certificate_failed"
            if certificate.certified and not accepted
            else certificate.reason
        ),
        "max_recomputed_constraint_violation": certificate.max_constraint_violation,
        "equality_violation": certificate.equality_violation,
        "max_bound_violation": certificate.max_bound_violation,
        "objective_residual": certificate.objective_residual,
        "duality_gap": certificate.duality_gap,
        "max_dual_violation": certificate.max_dual_violation,
        "max_economic_constraint_violation": economic_violation,
    }


def _network_radial_diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    task: _CertifiedNetworkRadialTask,
) -> dict[str, Any]:
    solution = task.solution
    certificate = task.certificate
    certificate_reason = (
        certificate.reason
        if not certificate.certified
        else task.economic_certification_reason
    )
    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": "system",
        "solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
        "lp_postsolve_certified": certificate.certified,
        "raw_economic_postsolve_certified": task.raw_economic_certified,
        "published_economic_postsolve_certified": (task.published_economic_certified),
        "economic_postsolve_certified": task.score_valid,
        "published_target_account_certified": (task.published_economic_certified),
        "published_peer_account_certified": (
            task.peer_valid if task.score_valid else pd.NA
        ),
        "postsolve_certified": task.score_valid,
        "certification_status": "certified" if task.score_valid else "failed",
        "certificate_reason": certificate_reason,
        "economic_certification_reason": task.economic_certification_reason,
        "max_recomputed_constraint_violation": (certificate.max_constraint_violation),
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
        "max_published_peer_account_violation": task.peer_economic_violation,
        "max_economic_constraint_violation": (
            task.published_economic_violation
            if task.published_economic_certified is not None
            else task.raw_economic_violation
        ),
    }


class FareGrosskopfNetworkRadialDEA:
    """Input- or output-radial efficiency for a two-stage series network.

    The system uses separate upstream and downstream reference intensities.
    Intermediate supply may exceed downstream use and the difference is
    reported as disposable link surplus. The programme defines one system
    score; it does not define stage efficiencies.

    The CRS output orientation evaluates the reciprocal output distance by
    applying one expansion factor to final outputs. Under VRS, the same
    standard output-distance measure is combined with the separately sourced
    two-process technology that imposes one convexity row per process.

    The evaluated organization's observed intermediate vector does not
    condition its score. Intermediate quantities are chosen endogenously in
    the coordinated benchmark; an observation's intermediates enter the
    reference technology only when that observation belongs to the comparison
    population. This is distinct from conditional network models that hold
    the evaluated handoff fixed.
    """

    _registry_method_id = "network.radial.fare_grosskopf_2000"

    def __init__(
        self,
        *,
        orientation: Orientation | str = Orientation.INPUT,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.orientation = parse_enum(orientation, Orientation, "orientation")
        self.returns_to_scale = parse_enum(
            returns_to_scale,
            ReturnsToScale,
            "returns_to_scale",
        )
        if self.returns_to_scale not in {
            ReturnsToScale.CRS,
            ReturnsToScale.VRS,
        }:
            raise ValueError("FareGrosskopfNetworkRadialDEA supports only CRS or VRS")
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
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

        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.tolerance = float(tolerance)
        self.peer_tolerance = float(resolved_peer_tolerance)

    def _validate_data(
        self,
        data: NetworkData,
        inputs: np.ndarray,
        outputs: np.ndarray,
    ) -> None:
        data.ensure_nonnegative(model_name="Färe--Grosskopf network radial DEA")
        if np.any(inputs.sum(axis=1) <= 0.0):
            raise DataValidationError(
                "every organization needs positive aggregate external input"
            )
        if np.any(outputs.sum(axis=1) <= 0.0):
            raise DataValidationError(
                "every organization needs positive aggregate final output"
            )

    def _economic_violation(
        self,
        *,
        reference: CompiledTwoStageQuantities,
        x_o: np.ndarray,
        y_o: np.ndarray,
        primal: np.ndarray,
        reported_objective: float,
        self_in_reference: bool,
    ) -> float:
        """Rebuild one complete two-process account in scaled quantity units."""

        values = np.asarray(primal, dtype=np.float64).reshape(-1)
        expected_size = 2 * reference.size + 1
        if (
            values.shape != (expected_size,)
            or not np.isfinite(values).all()
            or not math.isfinite(reported_objective)
        ):
            return math.inf
        n = reference.size
        lambdas = values[:n]
        mus = values[n : 2 * n]
        factor = float(values[-1])
        nonnegative_violation = float(np.maximum(-values, 0.0).max(initial=0.0))
        if self.orientation is Orientation.INPUT:
            input_violation = np.maximum(
                reference.scaled_inputs.T @ lambdas
                - factor * (x_o / reference.input_scales),
                0.0,
            )
            output_violation = np.maximum(
                y_o / reference.output_scales - reference.scaled_outputs.T @ mus,
                0.0,
            )
            expected_objective = factor
            self_reference_violation = (
                max(factor - 1.0, 0.0) if self_in_reference else 0.0
            )
        else:
            input_violation = np.maximum(
                reference.scaled_inputs.T @ lambdas - x_o / reference.input_scales,
                0.0,
            )
            output_violation = np.maximum(
                factor * (y_o / reference.output_scales)
                - reference.scaled_outputs.T @ mus,
                0.0,
            )
            expected_objective = -factor
            self_reference_violation = (
                max(1.0 - factor, 0.0) if self_in_reference else 0.0
            )
        link_violation = np.maximum(
            reference.scaled_intermediates.T @ mus
            - reference.scaled_intermediates.T @ lambdas,
            0.0,
        )
        convexity_violation = 0.0
        if self.returns_to_scale is ReturnsToScale.VRS:
            convexity_violation = max(
                abs(float(lambdas.sum()) - 1.0),
                abs(float(mus.sum()) - 1.0),
            )
        objective_violation = abs(reported_objective - expected_objective) / max(
            1.0,
            abs(reported_objective),
            abs(expected_objective),
        )
        return float(
            max(
                nonnegative_violation,
                input_violation.max(initial=0.0),
                link_violation.max(initial=0.0),
                output_violation.max(initial=0.0),
                convexity_violation,
                objective_violation,
                self_reference_violation,
            )
        )

    @staticmethod
    def _peer_reconstruction_violation(
        reference: CompiledTwoStageQuantities,
        published_primal: np.ndarray,
        peer_primal: np.ndarray,
    ) -> float:
        """Check that displayed peers reconstruct the published operating plan."""

        n = reference.size
        published_lambdas = published_primal[:n]
        published_mus = published_primal[n : 2 * n]
        peer_lambdas = peer_primal[:n]
        peer_mus = peer_primal[n : 2 * n]
        differences = (
            reference.scaled_inputs.T @ (published_lambdas - peer_lambdas),
            reference.scaled_intermediates.T @ (published_lambdas - peer_lambdas),
            reference.scaled_intermediates.T @ (published_mus - peer_mus),
            reference.scaled_outputs.T @ (published_mus - peer_mus),
        )
        if not all(np.isfinite(values).all() for values in differences):
            return math.inf
        return float(
            max(
                *(np.abs(values).max(initial=0.0) for values in differences),
                abs(float(published_primal[-1] - peer_primal[-1])),
            )
        )

    def _certify_task(
        self,
        *,
        problem: LinearProgram,
        solution: LPSolution,
        reference: CompiledTwoStageQuantities,
        x_o: np.ndarray,
        y_o: np.ndarray,
        self_in_reference: bool,
    ) -> _CertifiedNetworkRadialTask:
        """Certify one already-solved programme without another optimization."""

        certificate = certify_lp_solution(
            problem,
            solution,
            tolerance=self.tolerance,
        )
        unavailable = "not_available_without_certified_primary"
        if not certificate.certified or solution.primal is None:
            return _CertifiedNetworkRadialTask(
                solution=solution,
                certificate=certificate,
                score_valid=False,
                score_status=(
                    "solver_failed"
                    if solution.status is not SolverStatus.OPTIMAL
                    else "unavailable_uncertified_primary_program"
                ),
                factor=None,
                published_primal=None,
                peer_lambdas=None,
                peer_mus=None,
                peer_valid=False,
                peer_status=unavailable,
                raw_economic_certified=None,
                published_economic_certified=None,
                raw_economic_violation=math.nan,
                published_economic_violation=math.nan,
                peer_economic_violation=math.nan,
                economic_certification_reason=(
                    "not_checked_uncertified_source_program"
                ),
            )

        raw_primal = np.asarray(solution.primal, dtype=np.float64)
        reported_objective = float(solution.objective)
        raw_violation = self._economic_violation(
            reference=reference,
            x_o=x_o,
            y_o=y_o,
            primal=raw_primal,
            reported_objective=reported_objective,
            self_in_reference=self_in_reference,
        )
        raw_certified = bool(
            math.isfinite(raw_violation) and raw_violation <= self.tolerance
        )
        if not raw_certified:
            return _CertifiedNetworkRadialTask(
                solution=solution,
                certificate=certificate,
                score_valid=False,
                score_status="unavailable_uncertified_primary_program",
                factor=None,
                published_primal=None,
                peer_lambdas=None,
                peer_mus=None,
                peer_valid=False,
                peer_status=unavailable,
                raw_economic_certified=False,
                published_economic_certified=None,
                raw_economic_violation=raw_violation,
                published_economic_violation=math.nan,
                peer_economic_violation=math.nan,
                economic_certification_reason=(
                    "raw_network_account_reconstruction_failed"
                ),
            )

        published_primal = raw_primal.copy()
        published_primal[:-1] = clean_small(
            published_primal[:-1],
            self.tolerance,
        )
        published_primal[:-1] = np.maximum(published_primal[:-1], 0.0)
        if (
            self.orientation is Orientation.INPUT
            and -self.tolerance <= published_primal[-1] < 0.0
        ):
            published_primal[-1] = 0.0
        factor = float(published_primal[-1])
        reciprocal = math.nan
        if self.orientation is Orientation.OUTPUT and factor > 0.0:
            with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
                reciprocal = float(np.float64(1.0) / np.float64(factor))
        factor_valid = bool(
            factor >= 0.0
            if self.orientation is Orientation.INPUT
            else factor > 0.0 and math.isfinite(reciprocal)
        )
        published_violation = self._economic_violation(
            reference=reference,
            x_o=x_o,
            y_o=y_o,
            primal=published_primal,
            reported_objective=reported_objective,
            self_in_reference=self_in_reference,
        )
        published_certified = bool(
            factor_valid
            and math.isfinite(published_violation)
            and published_violation <= self.tolerance
        )
        if not published_certified:
            return _CertifiedNetworkRadialTask(
                solution=solution,
                certificate=certificate,
                score_valid=False,
                score_status="unavailable_uncertified_primary_program",
                factor=None,
                published_primal=None,
                peer_lambdas=None,
                peer_mus=None,
                peer_valid=False,
                peer_status=unavailable,
                raw_economic_certified=True,
                published_economic_certified=False,
                raw_economic_violation=raw_violation,
                published_economic_violation=published_violation,
                peer_economic_violation=math.nan,
                economic_certification_reason=(
                    "published_network_account_reconstruction_failed"
                ),
            )

        n = reference.size
        peer_primal = published_primal.copy()
        peer_primal[: 2 * n][peer_primal[: 2 * n] <= self.peer_tolerance] = 0.0
        peer_economic_violation = self._economic_violation(
            reference=reference,
            x_o=x_o,
            y_o=y_o,
            primal=peer_primal,
            reported_objective=reported_objective,
            self_in_reference=self_in_reference,
        )
        peer_reconstruction_violation = self._peer_reconstruction_violation(
            reference,
            published_primal,
            peer_primal,
        )
        peer_violation = max(
            peer_economic_violation,
            peer_reconstruction_violation,
        )
        peer_valid = bool(
            math.isfinite(peer_violation) and peer_violation <= self.tolerance
        )
        return _CertifiedNetworkRadialTask(
            solution=solution,
            certificate=certificate,
            score_valid=True,
            score_status="defined",
            factor=factor,
            published_primal=published_primal,
            peer_lambdas=(peer_primal[:n].copy() if peer_valid else None),
            peer_mus=(peer_primal[n : 2 * n].copy() if peer_valid else None),
            peer_valid=peer_valid,
            peer_status=(
                "certified_primary_program"
                if peer_valid
                else "unavailable_after_peer_reporting_threshold"
            ),
            raw_economic_certified=True,
            published_economic_certified=True,
            raw_economic_violation=raw_violation,
            published_economic_violation=published_violation,
            peer_economic_violation=peer_violation,
            economic_certification_reason="certified",
        )

    def _failure_row(
        self,
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        task: _CertifiedNetworkRadialTask,
    ) -> dict[str, Any]:
        solution = task.solution
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "system_score": np.nan,
            "system_efficiency": np.nan,
            "score_valid": False,
            "efficiency_denominator_valid": pd.NA,
            "is_efficient": pd.NA,
            "is_system_radially_efficient": pd.NA,
            "is_within_reference_technology": (
                False if solution.status is SolverStatus.INFEASIBLE else pd.NA
            ),
            "solver_status": solution.status.value,
            "score_status": task.score_status,
            "target_valid": False,
            "target_status": "not_available_without_certified_primary",
            "peer_valid": False,
            "peer_status": "not_available_without_certified_primary",
            "model_family": "network_radial",
            "orientation": self.orientation.value,
            "returns_to_scale": self.returns_to_scale.value,
            "reference_size": reference_size,
            "stage_efficiencies_defined": False,
            "conditions_on_observed_intermediate": False,
            "has_link_disposal": pd.NA,
            "max_scaled_link_disposal_surplus": np.nan,
            "max_scaled_external_residual": np.nan,
            "upstream_omitted_intensity_sum": np.nan,
            "downstream_omitted_intensity_sum": np.nan,
        }

    def fit(self, data: NetworkData) -> DEAResult:
        """Estimate one system radial factor per observation."""

        if not isinstance(data, NetworkData):
            raise TypeError("FareGrosskopfNetworkRadialDEA.fit expects NetworkData")
        roles = basic_two_stage_series_roles(
            data,
            model_name="Färe--Grosskopf network radial DEA",
        )
        inputs = data.matrix(roles.inputs)
        intermediates = data.matrix(roles.intermediates)
        outputs = data.matrix(roles.outputs)
        self._validate_data(data, inputs, outputs)

        reference_plan = build_reference_plan(data, self.reference)
        compiled: dict[int, CompiledTwoStageQuantities] = {}
        summary_rows: list[dict[str, Any]] = []
        component_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        link_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        primary_solver_calls = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                reference = compile_two_stage_quantities(
                    inputs,
                    intermediates,
                    outputs,
                    reference_plan.rows_for(observation),
                )
                compiled[set_id] = reference

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = inputs[observation]
            z_o = intermediates[observation]
            y_o = outputs[observation]
            problem = envelopment_problem(
                reference,
                x_o,
                y_o,
                orientation=self.orientation,
                returns_to_scale=self.returns_to_scale,
                name=f"{name}:system",
            )
            solution = self.solver.solve(problem)
            primary_solver_calls += 1
            task = self._certify_task(
                problem=problem,
                solution=solution,
                reference=reference,
                x_o=x_o,
                y_o=y_o,
                self_in_reference=bool(np.any(reference.rows == observation)),
            )

            diagnostic_rows.append(
                _network_radial_diagnostic(
                    dmu_id=dmu_id,
                    period=period,
                    task=task,
                )
            )
            if not task.score_valid or task.published_primal is None:
                summary_rows.append(
                    self._failure_row(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        task=task,
                    )
                )
                continue

            n = reference.size
            factor = float(task.published_primal[-1])
            lambdas = task.published_primal[:n]
            mus = task.published_primal[n : 2 * n]

            input_targets = np.asarray(
                reference.inputs.T @ lambdas,
                dtype=np.float64,
            )
            upstream_supply = np.asarray(
                reference.intermediates.T @ lambdas,
                dtype=np.float64,
            )
            downstream_requirement = np.asarray(
                reference.intermediates.T @ mus,
                dtype=np.float64,
            )
            output_targets = np.asarray(
                reference.outputs.T @ mus,
                dtype=np.float64,
            )

            if (
                task.peer_valid
                and task.peer_lambdas is not None
                and task.peer_mus is not None
            ):
                for process_id, intensity_kind, values in (
                    (roles.stage_1, "upstream_lambda", task.peer_lambdas),
                    (roles.stage_2, "downstream_mu", task.peer_mus),
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
                                "intensity_kind": intensity_kind,
                                "reference_dmu_id": data.dmu_ids[reference_position],
                                "reference_period": (
                                    None
                                    if data.periods is None
                                    else data.periods[reference_position]
                                ),
                                "intensity": float(intensity),
                                "lambda": (
                                    float(intensity)
                                    if intensity_kind == "upstream_lambda"
                                    else np.nan
                                ),
                                "mu": (
                                    float(intensity)
                                    if intensity_kind == "downstream_mu"
                                    else np.nan
                                ),
                            }
                        )
                upstream_omitted_intensity_sum = float(
                    lambdas[lambdas <= self.peer_tolerance].sum()
                )
                downstream_omitted_intensity_sum = float(
                    mus[mus <= self.peer_tolerance].sum()
                )
            else:
                upstream_omitted_intensity_sum = float(lambdas.sum())
                downstream_omitted_intensity_sum = float(mus.sum())

            scaled_external_residuals: list[float] = []
            for variable, observed, target, scale in zip(
                roles.inputs,
                x_o,
                input_targets,
                reference.input_scales,
                strict=True,
            ):
                bound = (
                    factor * float(observed)
                    if self.orientation is Orientation.INPUT
                    else float(observed)
                )
                residual = bound - float(target)
                scaled_residual = residual / float(scale)
                if abs(scaled_residual) <= self.tolerance:
                    residual = 0.0
                    scaled_residual = 0.0
                scaled_external_residuals.append(max(scaled_residual, 0.0))
                target_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "process_id": roles.stage_1,
                        "role": "external_input",
                        "variable": variable,
                        "observed": float(observed),
                        "target": float(target),
                        "constraint_bound": bound,
                        "constraint_residual": residual,
                        "scaled_constraint_residual": scaled_residual,
                        "projection_policy": "primary_system_optimum",
                    }
                )
            for variable, observed, target, scale in zip(
                roles.outputs,
                y_o,
                output_targets,
                reference.output_scales,
                strict=True,
            ):
                bound = (
                    float(observed)
                    if self.orientation is Orientation.INPUT
                    else factor * float(observed)
                )
                residual = float(target) - bound
                scaled_residual = residual / float(scale)
                if abs(scaled_residual) <= self.tolerance:
                    residual = 0.0
                    scaled_residual = 0.0
                scaled_external_residuals.append(max(scaled_residual, 0.0))
                target_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "process_id": roles.stage_2,
                        "role": "final_output",
                        "variable": variable,
                        "observed": float(observed),
                        "target": float(target),
                        "constraint_bound": bound,
                        "constraint_residual": residual,
                        "scaled_constraint_residual": scaled_residual,
                        "projection_policy": "primary_system_optimum",
                    }
                )

            scaled_link_surpluses: list[float] = []
            for variable, observed, upstream, downstream, scale in zip(
                roles.intermediates,
                z_o,
                upstream_supply,
                downstream_requirement,
                reference.intermediate_scales,
                strict=True,
            ):
                surplus = float(upstream - downstream)
                scaled_surplus = surplus / float(scale)
                if abs(scaled_surplus) <= self.tolerance:
                    surplus = 0.0
                    scaled_surplus = 0.0
                scaled_link_surpluses.append(max(scaled_surplus, 0.0))
                link_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "link_id": roles.link_id,
                        "variable": variable,
                        "observed": float(observed),
                        "upstream_supply": float(upstream),
                        "downstream_requirement": float(downstream),
                        "disposable_surplus": surplus,
                        "scaled_disposable_surplus": scaled_surplus,
                        "balance_residual": surplus,
                        "common_link_target_defined": False,
                        "observed_is_conditioning_value": False,
                        "projection_policy": "primary_system_optimum",
                    }
                )

            efficiency_denominator_valid = bool(
                self.orientation is Orientation.INPUT
                or (
                    factor > 0.0
                    and math.isfinite(float(np.float64(1.0) / np.float64(factor)))
                )
            )
            efficiency = (
                factor
                if self.orientation is Orientation.INPUT
                else float(np.float64(1.0) / np.float64(factor))
            )
            within_reference = bool(
                factor <= 1.0 + self.tolerance
                if self.orientation is Orientation.INPUT
                else factor >= 1.0 - self.tolerance
            )
            is_radially_efficient: bool | Any = (
                bool(abs(efficiency - 1.0) <= self.tolerance)
                if within_reference
                else pd.NA
            )
            max_scaled_link_surplus = max(scaled_link_surpluses, default=0.0)
            max_scaled_external_residual = max(
                scaled_external_residuals,
                default=0.0,
            )
            component_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "component_kind": "system",
                    "component_id": "system",
                    "score": factor,
                    "efficiency": efficiency,
                    "is_measure_efficient": is_radially_efficient,
                    "status": "defined",
                }
            )
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": factor,
                    "efficiency": efficiency,
                    "score_valid": True,
                    "distance": np.nan,
                    "system_score": factor,
                    "system_efficiency": efficiency,
                    "efficiency_denominator_valid": (efficiency_denominator_valid),
                    "is_efficient": pd.NA,
                    "is_system_radially_efficient": is_radially_efficient,
                    "is_within_reference_technology": within_reference,
                    "solver_status": solution.status.value,
                    "score_status": task.score_status,
                    "target_valid": True,
                    "target_status": "certified_primary_program",
                    "peer_valid": task.peer_valid,
                    "peer_status": task.peer_status,
                    "model_family": "network_radial",
                    "orientation": self.orientation.value,
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": reference.size,
                    "stage_efficiencies_defined": False,
                    "conditions_on_observed_intermediate": False,
                    "has_link_disposal": bool(max_scaled_link_surplus > self.tolerance),
                    "max_scaled_link_disposal_surplus": (max_scaled_link_surplus),
                    "max_scaled_external_residual": (max_scaled_external_residual),
                    "upstream_omitted_intensity_sum": (upstream_omitted_intensity_sum),
                    "downstream_omitted_intensity_sum": (
                        downstream_omitted_intensity_sum
                    ),
                }
            )

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            components=pd.DataFrame(component_rows),
            links=pd.DataFrame(link_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": "system_performance_with_internal_flow",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {
                            "kind": "series",
                            "processes": [roles.stage_1, roles.stage_2],
                            "link": {
                                "id": roles.link_id,
                                "quantity": "observed_once",
                                "declared_multiplier_policy": (
                                    data.network_spec.links[0].multiplier_policy
                                ),
                                "multiplier_policy_used": "none",
                                "intensity_policy": "process_specific",
                                "envelopment_balance": (
                                    "upstream_supply_greater_than_or_equal_to_"
                                    "downstream_requirement"
                                ),
                                "evaluated_intermediate_policy": (
                                    "endogenous_not_conditioned_on_observed"
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
                            "family": "network_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                            "process_relationship": "series",
                            "link_disposal": "upstream_surplus_allowed",
                            "convexity": (
                                "separate_by_process"
                                if self.returns_to_scale is ReturnsToScale.VRS
                                else "not_imposed"
                            ),
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_network_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                        ),
                        "performance": {
                            "family": "fare_grosskopf_network_radial",
                            "orientation": self.orientation.value,
                            "system_score": (
                                "theta"
                                if self.orientation is Orientation.INPUT
                                else "phi"
                            ),
                            "stage_efficiencies": "not_defined",
                            "evaluated_intermediate": (
                                "endogenous_not_conditioned_on_observed"
                            ),
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": "self_appraisal",
                            "primary_programmes_per_observation": 1,
                            "secondary_objective": "none",
                        },
                        "analysis": {"kind": "direct_network_fit"},
                        "uncertainty": {
                            "sampling": {"kind": "none"},
                            "data": {"kind": "none"},
                        },
                    },
                ),
                "model_family": "network_radial",
                "orientation": self.orientation.value,
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                "native_score": (
                    "theta" if self.orientation is Orientation.INPUT else "phi"
                ),
                "efficiency_transform": (
                    "identity"
                    if self.orientation is Orientation.INPUT
                    else "reciprocal"
                ),
                "graph_fingerprint": data.graph_fingerprint,
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": len(compiled),
                "primary_solves": primary_solver_calls,
                "secondary_solves": 0,
                "solver_calls": primary_solver_calls,
                "additional_solver_calls": 0,
                "primary_programmes_per_observation": 1,
                "stage_efficiencies_defined": False,
                "conditions_on_observed_intermediate": False,
                "common_link_target_defined": False,
                "intensity_roles": ["upstream_lambda", "downstream_mu"],
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
                        "raw_and_published_two_process_account_reconstruction"
                    ),
                    "peer": ("thresholded_peer_account_and_target_reconstruction"),
                    "failure_policy": ("per_observation_fail_closed_semantic_release"),
                    "additional_solver_calls": 0,
                },
            },
        )


__all__ = ["FareGrosskopfNetworkRadialDEA"]
