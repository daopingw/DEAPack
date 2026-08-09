"""Classical radial DEA on the shared DEAPack 2.0 kernel."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from .._registry import (
    data_role_schema,
    registry_metadata,
)
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import Orientation, ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
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
from ..technology import PeerEligibility, build_reference_plan
from ._common import (
    CompiledReference,
    compile_reference,
    get_or_compile_reference,
)
from ._radial_lp import (
    CompiledRadialPhaseOneTemplate,
    compile_radial_phase_one_template,
    radial_phase_one_problem,
    radial_row_scales,
)
from ._target_completion import (
    PARETO_KOOPMANS_TARGET_COMPLETION_ID,
    pareto_koopmans_target_completion_problem,
)


def _semantic_solver_status(
    backend_status: SolverStatus,
    *,
    certified: bool,
) -> SolverStatus:
    """Separate backend termination from the status of a published claim."""

    if backend_status is not SolverStatus.OPTIMAL:
        return backend_status
    return SolverStatus.OPTIMAL if certified else SolverStatus.NUMERICAL_ERROR


def _certificate_diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    phase: int,
    solution: LPSolution,
    certificate: LPCertificate,
) -> dict[str, Any]:
    """Return raw backend evidence and the solver-neutral LP certificate."""

    semantic_status = _semantic_solver_status(
        solution.status,
        certified=certificate.certified,
    )
    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": phase,
        "solver_status": semantic_status.value,
        "backend_solver_status": solution.status.value,
        "raw_solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
        "lp_postsolve_certified": certificate.certified,
        "postsolve_certified": certificate.certified,
        "certification_reason": certificate.reason,
        "max_constraint_violation": certificate.max_constraint_violation,
        "equality_violation": certificate.equality_violation,
        "max_bound_violation": certificate.max_bound_violation,
        "objective_residual": certificate.objective_residual,
        "duality_gap": certificate.duality_gap,
        "max_dual_violation": certificate.max_dual_violation,
        "complementarity_violation": certificate.complementarity_violation,
        "bound_marginals_used": certificate.bound_marginals_used,
        "economic_postsolve_certified": pd.NA,
        "economic_certification_reason": "not_checked",
        "max_economic_violation": np.nan,
        "raw_economic_postsolve_certified": pd.NA,
        "max_raw_economic_violation": np.nan,
        "published_output_account_certified": pd.NA,
        "max_published_account_violation": np.nan,
        "published_peer_account_certified": pd.NA,
        "max_published_peer_account_violation": np.nan,
        "published_dual_account_certified": pd.NA,
        "published_dual_row_count": np.nan,
    }


def _scaled_equality_violation(
    actual: np.ndarray,
    required: np.ndarray,
    account_scale: np.ndarray,
) -> float:
    """Return an equality residual in the LP account's row-scaled units."""

    left = np.asarray(actual, dtype=np.float64).reshape(-1)
    right = np.asarray(required, dtype=np.float64).reshape(-1)
    scale = np.asarray(account_scale, dtype=np.float64).reshape(-1)
    if (
        left.shape != right.shape
        or left.shape != scale.shape
        or not np.isfinite(left).all()
        or not np.isfinite(right).all()
        or not np.isfinite(scale).all()
        or np.any(scale <= 0.0)
    ):
        return math.inf
    return float((np.abs(left - right) / scale).max(initial=0.0))


def _scaled_upper_violation(
    actual: np.ndarray,
    upper: np.ndarray,
    account_scale: np.ndarray,
) -> float:
    """Return ``actual <= upper`` violation in row-scaled LP units."""

    left = np.asarray(actual, dtype=np.float64).reshape(-1)
    right = np.asarray(upper, dtype=np.float64).reshape(-1)
    scale = np.asarray(account_scale, dtype=np.float64).reshape(-1)
    if (
        left.shape != right.shape
        or left.shape != scale.shape
        or not np.isfinite(left).all()
        or not np.isfinite(right).all()
        or not np.isfinite(scale).all()
        or np.any(scale <= 0.0)
    ):
        return math.inf
    return float((np.maximum(left - right, 0.0) / scale).max(initial=0.0))


def _scaled_nonnegative_violation(
    values: np.ndarray,
    account_scale: np.ndarray | None = None,
) -> float:
    """Return the largest scale-free violation of nonnegativity."""

    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if not np.isfinite(array).all():
        return math.inf
    if account_scale is None:
        scale = np.maximum(1.0, np.abs(array))
    else:
        scale = np.asarray(account_scale, dtype=np.float64).reshape(-1)
        if (
            scale.shape != array.shape
            or not np.isfinite(scale).all()
            or np.any(scale <= 0.0)
        ):
            return math.inf
    return float((np.maximum(-array, 0.0) / scale).max(initial=0.0))


def _rts_violation(
    lambdas: np.ndarray,
    returns_to_scale: ReturnsToScale,
) -> float:
    """Return the scale-free intensity-sum violation for one RTS regime."""

    total = float(np.sum(np.asarray(lambdas, dtype=np.float64)))
    if not math.isfinite(total):
        return math.inf
    scale = max(1.0, abs(total))
    if returns_to_scale is ReturnsToScale.VRS:
        return abs(total - 1.0) / scale
    if returns_to_scale is ReturnsToScale.NIRS:
        return max(total - 1.0, 0.0) / scale
    if returns_to_scale is ReturnsToScale.NDRS:
        return max(1.0 - total, 0.0) / scale
    return 0.0


class RadialDEA:
    """Input- or output-oriented radial DEA.

    `CCR` and `BCC` specialize this model to CRS and VRS while leaving
    orientation configurable. The solve is lexicographic: phase one estimates
    the radial factor and phase two fixes that factor while maximizing
    remaining input/output slacks.
    """

    _registry_method_id = "static.radial"
    _registry_preset_id: str | None = None
    _registry_specialization_id: str | None = None
    _registry_fixed_orientation: Orientation | None = None
    _registry_fixed_returns_to_scale: ReturnsToScale | None = None
    _registry_fixed_compute_slacks: bool | None = None

    def __init__(
        self,
        *,
        orientation: Orientation | str = Orientation.INPUT,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        reference: ReferenceSpec | str | None = None,
        peer_eligibility: PeerEligibility | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        compute_slacks: bool = True,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.orientation = parse_enum(orientation, Orientation, "orientation")
        self.returns_to_scale = parse_enum(
            returns_to_scale, ReturnsToScale, "returns_to_scale"
        )
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        if peer_eligibility is not None and not isinstance(
            peer_eligibility, PeerEligibility
        ):
            raise TypeError("peer_eligibility must be a PeerEligibility")
        self.peer_eligibility = peer_eligibility
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.compute_slacks = bool(compute_slacks)
        if not math.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be positive and finite")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not math.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive and finite")

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "RadialDEA does not infer how undesirable outputs are disposed. "
                "Use an explicit environmental technology/measure."
            )
        if np.any(data.inputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive output"
            )

    def _validate_registry_identity_contract(self) -> None:
        model_type = type(self)
        fixed = {
            "orientation": model_type._registry_fixed_orientation,
            "returns_to_scale": model_type._registry_fixed_returns_to_scale,
            "compute_slacks": model_type._registry_fixed_compute_slacks,
        }
        actual = {
            "orientation": self.orientation,
            "returns_to_scale": self.returns_to_scale,
            "compute_slacks": self.compute_slacks,
        }
        mismatches = {
            name: (expected, actual[name])
            for name, expected in fixed.items()
            if expected is not None and actual[name] is not expected
        }
        if mismatches:
            details = ", ".join(
                f"{name}={observed!r} (expected {expected!r})"
                for name, (expected, observed) in mismatches.items()
            )
            raise ModelSpecificationError(
                f"{model_type.__name__} has a fixed registry identity and cannot "
                f"fit after identity-defining attributes were changed: {details}. "
                "Construct CCR, BCC, or RadialDEA for a configurable recipe."
            )

    def _phase_one_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> LinearProgram:
        return radial_phase_one_problem(
            reference,
            x_o,
            y_o,
            self.orientation,
            self.returns_to_scale,
            name,
        )

    def _phase_two_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        factor: float,
        name: str,
    ) -> LinearProgram:
        if self.orientation is Orientation.INPUT:
            path_inputs = factor * x_o
            path_outputs = y_o
        else:
            path_inputs = x_o
            path_outputs = factor * y_o
        return pareto_koopmans_target_completion_problem(
            reference,
            path_inputs,
            path_outputs,
            self.returns_to_scale,
            name=f"{name}:slacks",
            input_scale_anchor=x_o,
            output_scale_anchor=y_o,
        )

    def _dual_rows(
        self,
        data: DEAData,
        observation: int,
        reference: CompiledReference,
        solution: LPSolution,
    ) -> list[dict[str, Any]]:
        if solution.inequality_marginals is None:
            return []
        expected_inequalities = (
            data.n_inputs
            + data.n_outputs
            + int(self.returns_to_scale in {ReturnsToScale.NIRS, ReturnsToScale.NDRS})
        )
        inequality_marginals = np.asarray(
            solution.inequality_marginals,
            dtype=np.float64,
        )
        if (
            inequality_marginals.shape != (expected_inequalities,)
            or not np.isfinite(inequality_marginals).all()
        ):
            return []
        equality_marginals = (
            None
            if solution.equality_marginals is None
            else np.asarray(solution.equality_marginals, dtype=np.float64)
        )
        if self.returns_to_scale is ReturnsToScale.VRS and (
            equality_marginals is None
            or equality_marginals.shape != (1,)
            or not np.isfinite(equality_marginals).all()
        ):
            return []
        period = None if data.periods is None else data.periods[observation]
        common = {"dmu_id": data.dmu_ids[observation], "period": period, "phase": 1}
        rows: list[dict[str, Any]] = []
        input_scales, output_scales = radial_row_scales(
            reference,
            data.inputs[observation],
            data.outputs[observation],
        )
        offset = 0
        for variable, scale in zip(
            data.input_names,
            input_scales,
            strict=True,
        ):
            rows.append(
                {
                    **common,
                    "constraint_role": "input",
                    "variable": variable,
                    "marginal": (inequality_marginals[offset] / scale),
                }
            )
            offset += 1
        for variable, scale in zip(
            data.output_names,
            output_scales,
            strict=True,
        ):
            rows.append(
                {
                    **common,
                    "constraint_role": "output",
                    "variable": variable,
                    "marginal": (inequality_marginals[offset] / scale),
                }
            )
            offset += 1
        if self.returns_to_scale is ReturnsToScale.VRS:
            assert equality_marginals is not None
            rows.append(
                {
                    **common,
                    "constraint_role": "returns_to_scale",
                    "variable": self.returns_to_scale.value,
                    "marginal": float(equality_marginals[0]),
                }
            )
        elif self.returns_to_scale in {ReturnsToScale.NIRS, ReturnsToScale.NDRS}:
            rows.append(
                {
                    **common,
                    "constraint_role": "returns_to_scale",
                    "variable": self.returns_to_scale.value,
                    "marginal": inequality_marginals[offset],
                }
            )
        return rows

    def _primary_economic_violation(
        self,
        *,
        reference: CompiledReference,
        solution: LPSolution,
        x_o: np.ndarray,
        y_o: np.ndarray,
        primal_override: np.ndarray | None = None,
    ) -> float:
        """Reconstruct the radial score and production accounts in data units."""

        primal = solution.primal if primal_override is None else primal_override
        if (
            primal is None
            or solution.objective is None
            or not math.isfinite(solution.objective)
        ):
            return math.inf
        values = np.asarray(primal, dtype=np.float64).reshape(-1)
        if values.shape != (reference.size + 1,) or not np.isfinite(values).all():
            return math.inf

        lambdas = values[: reference.size]
        factor = float(values[-1])
        if self.orientation is Orientation.OUTPUT and factor <= self.tolerance:
            return math.inf
        input_scales, output_scales = radial_row_scales(
            reference,
            x_o,
            y_o,
        )
        represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
        represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
        if self.orientation is Orientation.INPUT:
            available_inputs = factor * np.asarray(x_o, dtype=np.float64)
            required_outputs = np.asarray(y_o, dtype=np.float64)
            reconstructed_objective = factor
        else:
            available_inputs = np.asarray(x_o, dtype=np.float64)
            required_outputs = factor * np.asarray(y_o, dtype=np.float64)
            reconstructed_objective = -factor

        objective_scale = max(
            1.0,
            abs(reconstructed_objective),
            abs(float(solution.objective)),
        )
        violations = [
            _scaled_nonnegative_violation(lambdas),
            max(-factor, 0.0) / max(1.0, abs(factor)),
            _scaled_nonnegative_violation(represented_inputs, input_scales),
            _scaled_nonnegative_violation(represented_outputs, output_scales),
            _scaled_upper_violation(
                represented_inputs,
                available_inputs,
                input_scales,
            ),
            _scaled_upper_violation(
                required_outputs,
                represented_outputs,
                output_scales,
            ),
            _rts_violation(lambdas, self.returns_to_scale),
            abs(reconstructed_objective - float(solution.objective)) / objective_scale,
        ]
        return max(violations) if all(map(math.isfinite, violations)) else math.inf

    def _completion_economic_violation(
        self,
        *,
        reference: CompiledReference,
        solution: LPSolution,
        x_o: np.ndarray,
        y_o: np.ndarray,
        factor: float,
        primal_override: np.ndarray | None = None,
    ) -> float:
        """Reconstruct phase-two targets, slacks, objective, and RTS account."""

        primal = solution.primal if primal_override is None else primal_override
        expected_size = reference.size + x_o.size + y_o.size
        if (
            primal is None
            or solution.objective is None
            or not math.isfinite(solution.objective)
        ):
            return math.inf
        values = np.asarray(primal, dtype=np.float64).reshape(-1)
        if values.shape != (expected_size,) or not np.isfinite(values).all():
            return math.inf

        n_lambda = reference.size
        input_scales, output_scales = radial_row_scales(
            reference,
            x_o,
            y_o,
        )
        lambdas = values[:n_lambda]
        scaled_input_slacks = values[n_lambda : n_lambda + x_o.size]
        scaled_output_slacks = values[n_lambda + x_o.size :]
        input_slacks = scaled_input_slacks * input_scales
        output_slacks = scaled_output_slacks * output_scales
        represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
        represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
        if self.orientation is Orientation.INPUT:
            path_inputs = factor * np.asarray(x_o, dtype=np.float64)
            path_outputs = np.asarray(y_o, dtype=np.float64)
        else:
            path_inputs = np.asarray(x_o, dtype=np.float64)
            path_outputs = factor * np.asarray(y_o, dtype=np.float64)

        reconstructed_objective = -float(
            scaled_input_slacks.sum() + scaled_output_slacks.sum()
        )
        objective_scale = max(
            1.0,
            abs(reconstructed_objective),
            abs(float(solution.objective)),
        )
        violations = [
            _scaled_nonnegative_violation(lambdas),
            _scaled_nonnegative_violation(scaled_input_slacks),
            _scaled_nonnegative_violation(scaled_output_slacks),
            _scaled_nonnegative_violation(represented_inputs, input_scales),
            _scaled_nonnegative_violation(represented_outputs, output_scales),
            _scaled_equality_violation(
                represented_inputs + input_slacks,
                path_inputs,
                input_scales,
            ),
            _scaled_equality_violation(
                represented_outputs - output_slacks,
                path_outputs,
                output_scales,
            ),
            _rts_violation(lambdas, self.returns_to_scale),
            abs(reconstructed_objective - float(solution.objective)) / objective_scale,
        ]
        return max(violations) if all(map(math.isfinite, violations)) else math.inf

    def _peer_account_violation(
        self,
        *,
        reference: CompiledReference,
        lambdas: np.ndarray,
        input_targets: np.ndarray,
        output_targets: np.ndarray,
        x_o: np.ndarray,
        y_o: np.ndarray,
    ) -> float:
        """Check that reported peer intensities reproduce published targets."""

        input_scales, output_scales = radial_row_scales(
            reference,
            x_o,
            y_o,
        )
        represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
        represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
        violations = [
            _scaled_nonnegative_violation(lambdas),
            _scaled_equality_violation(
                represented_inputs,
                input_targets,
                input_scales,
            ),
            _scaled_equality_violation(
                represented_outputs,
                output_targets,
                output_scales,
            ),
            _rts_violation(lambdas, self.returns_to_scale),
        ]
        return max(violations) if all(map(math.isfinite, violations)) else math.inf

    def _undefined_summary(
        self,
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        backend_solver_status: SolverStatus,
        score_status: str,
        self_in_reference: bool,
    ) -> dict[str, Any]:
        """Return one fail-closed summary row for an uncertified phase one."""

        unavailable = "not_available_without_certified_primary"
        semantic_status = _semantic_solver_status(
            backend_solver_status,
            certified=False,
        ).value
        raw_status = backend_solver_status.value
        if self_in_reference:
            within_reference: bool | Any = True
            membership_status = "certified_by_self_inclusion"
        elif backend_solver_status is SolverStatus.INFEASIBLE:
            within_reference = False
            membership_status = "outside_reference_technology"
        else:
            within_reference = pd.NA
            membership_status = "unavailable_uncertified_radial_account"
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "score_valid": False,
            "score_status": score_status,
            "distance": np.nan,
            "is_efficient": pd.NA,
            "is_radially_efficient": pd.NA,
            "is_within_reference_technology": within_reference,
            "self_in_reference": self_in_reference,
            "membership_status": membership_status,
            "solver_status": semantic_status,
            "backend_solver_status": raw_status,
            "raw_solver_status": raw_status,
            "primary_solver_status": raw_status,
            "primary_semantic_solver_status": semantic_status,
            "primary_backend_solver_status": raw_status,
            "primary_raw_solver_status": raw_status,
            "completion_solver_status": pd.NA,
            "completion_semantic_solver_status": pd.NA,
            "completion_backend_solver_status": pd.NA,
            "completion_raw_solver_status": pd.NA,
            "completion_valid": False,
            "completion_status": unavailable,
            "target_valid": False,
            "target_status": unavailable,
            "peer_valid": False,
            "peer_status": unavailable,
            "dual_valid": False,
            "dual_status": unavailable,
            "model_family": "radial",
            "orientation": self.orientation.value,
            "returns_to_scale": self.returns_to_scale.value,
            "reference_size": reference_size,
            "max_slack": np.nan,
            "max_scaled_slack": np.nan,
            "efficiency_denominator_valid": pd.NA,
        }

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate radial efficiency for all observations."""
        return self._fit(data)

    def _fit(
        self,
        data: DEAData,
        *,
        compiled_references: dict[int, CompiledReference] | None = None,
    ) -> DEAResult:
        """Private execution path that may share compiled references."""
        self._validate_registry_identity_contract()
        self._validate_data(data)
        reference_plan = build_reference_plan(
            data,
            self.reference,
            peer_eligibility=self.peer_eligibility,
        )
        self_membership = reference_plan.self_membership_mask()
        if bool(np.all(self_membership)):
            appraisal_kind = "self_appraisal"
        elif bool(np.any(self_membership)):
            appraisal_kind = "mixed_self_and_external_reference_appraisal"
        else:
            appraisal_kind = "external_reference_appraisal"
        compiled = {} if compiled_references is None else compiled_references
        phase_one_templates: dict[int, CompiledRadialPhaseOneTemplate] = {}

        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        dual_rows: list[dict[str, Any]] = []
        phase_one_solver_calls = 0
        phase_two_solver_calls = 0
        phase_one_task_bindings = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            reference = get_or_compile_reference(
                data,
                reference_rows,
                set_id,
                compiled,
                compiler=compile_reference,
            )
            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]

            phase_one_template = phase_one_templates.get(set_id)
            if phase_one_template is None:
                phase_one_template = compile_radial_phase_one_template(
                    reference,
                    self.orientation,
                    self.returns_to_scale,
                )
                phase_one_templates[set_id] = phase_one_template
            phase_one_problem = phase_one_template.bind(x_o, y_o, name)
            phase_one_task_bindings += 1
            phase_one = self.solver.solve(phase_one_problem)
            phase_one_solver_calls += 1
            phase_one_certificate = certify_lp_solution(
                phase_one_problem,
                phase_one,
                tolerance=self.tolerance,
            )
            diagnostic_rows.append(
                _certificate_diagnostic(
                    dmu_id=dmu_id,
                    period=period,
                    phase=1,
                    solution=phase_one,
                    certificate=phase_one_certificate,
                )
            )

            if not phase_one_certificate.certified or phase_one.primal is None:
                self_in_reference = bool(self_membership[observation])
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        backend_solver_status=phase_one.status,
                        score_status=(
                            "outside_reference_technology"
                            if (
                                phase_one.status is SolverStatus.INFEASIBLE
                                and not self_in_reference
                            )
                            else "solver_failed"
                            if phase_one.status is not SolverStatus.OPTIMAL
                            else "unavailable_uncertified_primary_program"
                        ),
                        self_in_reference=self_in_reference,
                    )
                )
                continue

            raw_primary_violation = self._primary_economic_violation(
                reference=reference,
                solution=phase_one,
                x_o=x_o,
                y_o=y_o,
            )
            raw_primary_certified = bool(
                math.isfinite(raw_primary_violation)
                and raw_primary_violation <= 10.0 * self.tolerance
            )
            diagnostic_rows[-1]["raw_economic_postsolve_certified"] = (
                raw_primary_certified
            )
            diagnostic_rows[-1]["max_raw_economic_violation"] = raw_primary_violation

            primary_publish_primal = np.maximum(
                np.asarray(phase_one.primal, dtype=np.float64),
                0.0,
            )
            published_primary_violation = (
                self._primary_economic_violation(
                    reference=reference,
                    solution=phase_one,
                    x_o=x_o,
                    y_o=y_o,
                    primal_override=primary_publish_primal,
                )
                if raw_primary_certified
                else math.inf
            )
            published_primary_certified = bool(
                math.isfinite(published_primary_violation)
                and published_primary_violation <= 10.0 * self.tolerance
            )
            diagnostic_rows[-1]["published_output_account_certified"] = (
                published_primary_certified
            )
            diagnostic_rows[-1]["max_published_account_violation"] = (
                published_primary_violation
            )
            diagnostic_rows[-1]["economic_postsolve_certified"] = (
                published_primary_certified
            )
            diagnostic_rows[-1]["max_economic_violation"] = published_primary_violation
            diagnostic_rows[-1]["postsolve_certified"] = published_primary_certified
            diagnostic_rows[-1]["economic_certification_reason"] = (
                "certified"
                if published_primary_certified
                else (
                    "published_radial_account_reconstruction_failed"
                    if raw_primary_certified
                    else "radial_program_reconstruction_failed"
                )
            )
            if not published_primary_certified:
                diagnostic_rows[-1]["solver_status"] = (
                    SolverStatus.NUMERICAL_ERROR.value
                )
                diagnostic_rows[-1]["certification_reason"] = diagnostic_rows[-1][
                    "economic_certification_reason"
                ]
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        backend_solver_status=phase_one.status,
                        score_status="unavailable_uncertified_primary_program",
                        self_in_reference=bool(self_membership[observation]),
                    )
                )
                continue

            diagnostic_rows[-1]["certification_reason"] = "certified"
            factor = float(primary_publish_primal[-1])
            primary_lambdas = primary_publish_primal[: reference.size]
            primary_peer_lambdas = primary_lambdas.copy()
            primary_peer_lambdas[primary_peer_lambdas <= self.peer_tolerance] = 0.0
            primary_peer_primal = primary_publish_primal.copy()
            primary_peer_primal[: reference.size] = primary_peer_lambdas
            primary_peer_violation = self._primary_economic_violation(
                reference=reference,
                solution=phase_one,
                x_o=x_o,
                y_o=y_o,
                primal_override=primary_peer_primal,
            )
            primary_peer_valid = bool(
                math.isfinite(primary_peer_violation)
                and primary_peer_violation <= 10.0 * self.tolerance
            )
            diagnostic_rows[-1]["published_peer_account_certified"] = primary_peer_valid
            diagnostic_rows[-1]["max_published_peer_account_violation"] = (
                primary_peer_violation
            )
            primary_dual_rows = self._dual_rows(
                data,
                observation,
                reference,
                phase_one,
            )
            expected_dual_rows = (
                data.n_inputs
                + data.n_outputs
                + int(self.returns_to_scale is not ReturnsToScale.CRS)
            )
            primary_dual_valid = len(primary_dual_rows) == expected_dual_rows
            primary_dual_status = (
                "certified_primary_program"
                if primary_dual_valid
                else "unavailable_incomplete_primary_dual_account"
            )
            diagnostic_rows[-1]["published_dual_account_certified"] = primary_dual_valid
            diagnostic_rows[-1]["published_dual_row_count"] = len(primary_dual_rows)

            reciprocal_denominator_valid = bool(
                self.orientation is Orientation.INPUT or factor > self.tolerance
            )
            if self.orientation is Orientation.INPUT:
                efficiency = factor
                within_reference = bool(factor <= 1.0 + self.tolerance)
            else:
                efficiency = 1.0 / factor
                within_reference = bool(factor >= 1.0 - self.tolerance)
            is_radially_efficient: bool | Any = (
                bool(abs(efficiency - 1.0) <= self.tolerance)
                if within_reference and reciprocal_denominator_valid
                else pd.NA
            )

            phase_two: LPSolution | None = None
            completion_solver_status: object = pd.NA
            completion_semantic_solver_status: object = pd.NA
            completion_backend_solver_status: object = pd.NA
            completion_raw_solver_status: object = pd.NA
            completion_valid: bool | Any = pd.NA
            completion_status = "not_requested"
            target_valid: bool | Any = pd.NA
            target_status = "not_requested"
            peer_valid = primary_peer_valid
            peer_status = (
                "certified_primary_program"
                if primary_peer_valid
                else "unavailable_after_peer_reporting_threshold"
            )
            dual_valid = primary_dual_valid
            dual_status = primary_dual_status
            publication_lambdas: np.ndarray | None = (
                primary_peer_lambdas if primary_peer_valid else None
            )
            input_targets: np.ndarray | None = None
            output_targets: np.ndarray | None = None
            input_slacks: np.ndarray | None = None
            output_slacks: np.ndarray | None = None
            max_slack = np.nan
            max_scaled_slack = np.nan
            is_efficient: bool | Any = pd.NA
            final_status = SolverStatus.OPTIMAL.value
            final_backend_status = phase_one.status.value
            if self.compute_slacks:
                phase_two_problem = self._phase_two_problem(
                    reference,
                    x_o,
                    y_o,
                    factor,
                    name,
                )
                phase_two = self.solver.solve(phase_two_problem)
                phase_two_solver_calls += 1
                phase_two_certificate = certify_lp_solution(
                    phase_two_problem,
                    phase_two,
                    tolerance=self.tolerance,
                )
                diagnostic_rows.append(
                    _certificate_diagnostic(
                        dmu_id=dmu_id,
                        period=period,
                        phase=2,
                        solution=phase_two,
                        certificate=phase_two_certificate,
                    )
                )
                completion_semantic_status = _semantic_solver_status(
                    phase_two.status,
                    certified=phase_two_certificate.certified,
                ).value
                completion_solver_status = phase_two.status.value
                completion_semantic_solver_status = completion_semantic_status
                completion_backend_solver_status = phase_two.status.value
                completion_raw_solver_status = phase_two.status.value
                completion_valid = False
                completion_status = (
                    "completion_solver_failed"
                    if phase_two.status is not SolverStatus.OPTIMAL
                    else "unavailable_uncertified_slack_completion"
                )
                target_valid = False
                target_status = completion_status
                peer_valid = False
                peer_status = completion_status
                dual_valid = False
                dual_status = completion_status
                publication_lambdas = None
                final_status = completion_semantic_status
                final_backend_status = phase_two.status.value
                diagnostic_rows[-1]["published_output_account_certified"] = False
                diagnostic_rows[-1]["published_peer_account_certified"] = False

                if phase_two_certificate.certified and phase_two.primal is not None:
                    raw_completion_violation = self._completion_economic_violation(
                        reference=reference,
                        solution=phase_two,
                        x_o=x_o,
                        y_o=y_o,
                        factor=factor,
                    )
                    raw_completion_certified = bool(
                        math.isfinite(raw_completion_violation)
                        and raw_completion_violation <= 10.0 * self.tolerance
                    )
                    diagnostic_rows[-1]["raw_economic_postsolve_certified"] = (
                        raw_completion_certified
                    )
                    diagnostic_rows[-1]["max_raw_economic_violation"] = (
                        raw_completion_violation
                    )
                    phase_two_publish_primal = np.maximum(
                        np.asarray(phase_two.primal, dtype=np.float64),
                        0.0,
                    )
                    published_completion_violation = (
                        self._completion_economic_violation(
                            reference=reference,
                            solution=phase_two,
                            x_o=x_o,
                            y_o=y_o,
                            factor=factor,
                            primal_override=phase_two_publish_primal,
                        )
                        if raw_completion_certified
                        else math.inf
                    )
                    published_completion_certified = bool(
                        math.isfinite(published_completion_violation)
                        and published_completion_violation <= 10.0 * self.tolerance
                    )
                    diagnostic_rows[-1]["published_output_account_certified"] = (
                        published_completion_certified
                    )
                    diagnostic_rows[-1]["max_published_account_violation"] = (
                        published_completion_violation
                    )
                    diagnostic_rows[-1]["economic_postsolve_certified"] = (
                        published_completion_certified
                    )
                    diagnostic_rows[-1]["max_economic_violation"] = (
                        published_completion_violation
                    )
                    diagnostic_rows[-1]["postsolve_certified"] = (
                        published_completion_certified
                    )
                    diagnostic_rows[-1]["economic_certification_reason"] = (
                        "certified"
                        if published_completion_certified
                        else (
                            "published_radial_slack_account_reconstruction_failed"
                            if raw_completion_certified
                            else "radial_slack_account_reconstruction_failed"
                        )
                    )
                    if published_completion_certified:
                        diagnostic_rows[-1]["certification_reason"] = "certified"
                        n_lambda = reference.size
                        input_scales, output_scales = radial_row_scales(
                            reference,
                            x_o,
                            y_o,
                        )
                        completion_lambdas = phase_two_publish_primal[:n_lambda]
                        scaled_input_slacks = phase_two_publish_primal[
                            n_lambda : n_lambda + data.n_inputs
                        ]
                        scaled_output_slacks = phase_two_publish_primal[
                            n_lambda + data.n_inputs :
                        ]
                        input_slacks = scaled_input_slacks * input_scales
                        output_slacks = scaled_output_slacks * output_scales
                        input_targets = np.asarray(
                            reference.inputs @ completion_lambdas
                        ).reshape(-1)
                        output_targets = np.asarray(
                            reference.outputs @ completion_lambdas
                        ).reshape(-1)
                        max_slack = float(
                            max(
                                input_slacks.max(initial=0.0),
                                output_slacks.max(initial=0.0),
                            )
                        )
                        max_scaled_slack = float(
                            max(
                                scaled_input_slacks.max(initial=0.0),
                                scaled_output_slacks.max(initial=0.0),
                            )
                        )
                        completion_valid = True
                        completion_status = "certified"
                        target_valid = True
                        target_status = "certified_slack_completion"
                        dual_valid = primary_dual_valid
                        dual_status = (
                            "certified_primary_program_after_completion"
                            if primary_dual_valid
                            else primary_dual_status
                        )
                        completion_peer_lambdas = completion_lambdas.copy()
                        completion_peer_lambdas[
                            completion_peer_lambdas <= self.peer_tolerance
                        ] = 0.0
                        peer_violation = self._peer_account_violation(
                            reference=reference,
                            lambdas=completion_peer_lambdas,
                            input_targets=input_targets,
                            output_targets=output_targets,
                            x_o=x_o,
                            y_o=y_o,
                        )
                        peer_valid = bool(
                            math.isfinite(peer_violation)
                            and peer_violation <= 10.0 * self.tolerance
                        )
                        peer_status = (
                            "certified_slack_completion"
                            if peer_valid
                            else "unavailable_after_peer_reporting_threshold"
                        )
                        publication_lambdas = (
                            completion_peer_lambdas if peer_valid else None
                        )
                        diagnostic_rows[-1]["published_peer_account_certified"] = (
                            peer_valid
                        )
                        diagnostic_rows[-1]["max_published_peer_account_violation"] = (
                            peer_violation
                        )
                        is_efficient = (
                            bool(
                                is_radially_efficient
                                and max_scaled_slack <= self.tolerance
                            )
                            if within_reference and reciprocal_denominator_valid
                            else pd.NA
                        )
                    else:
                        diagnostic_rows[-1]["solver_status"] = (
                            SolverStatus.NUMERICAL_ERROR.value
                        )
                        completion_semantic_solver_status = (
                            SolverStatus.NUMERICAL_ERROR.value
                        )
                        final_status = SolverStatus.NUMERICAL_ERROR.value
                        diagnostic_rows[-1]["certification_reason"] = diagnostic_rows[
                            -1
                        ]["economic_certification_reason"]

            if dual_valid:
                dual_rows.extend(primary_dual_rows)

            if peer_valid and publication_lambdas is not None:
                for local_position, intensity in enumerate(publication_lambdas):
                    if intensity <= 0.0:
                        continue
                    reference_position = reference.rows[local_position]
                    intensity_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "reference_dmu_id": data.dmu_ids[reference_position],
                            "reference_period": (
                                None
                                if data.periods is None
                                else data.periods[reference_position]
                            ),
                            "lambda": float(intensity),
                        }
                    )

            if target_valid is True:
                assert input_targets is not None
                assert output_targets is not None
                assert input_slacks is not None
                assert output_slacks is not None
                input_scales, output_scales = radial_row_scales(
                    reference,
                    x_o,
                    y_o,
                )
                for role, names, observed, targets, slacks, scales in (
                    (
                        "input",
                        data.input_names,
                        x_o,
                        input_targets,
                        input_slacks,
                        input_scales,
                    ),
                    (
                        "output",
                        data.output_names,
                        y_o,
                        output_targets,
                        output_slacks,
                        output_scales,
                    ),
                ):
                    for variable, value, target, slack, scale in zip(
                        names,
                        observed,
                        targets,
                        slacks,
                        scales,
                        strict=True,
                    ):
                        target_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "observed": float(value),
                                "target": float(target),
                            }
                        )
                        slack_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "slack": float(slack),
                                "scaled_slack": float(slack / scale),
                            }
                        )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": factor,
                    "efficiency": efficiency,
                    "score_valid": True,
                    "score_status": "defined",
                    "distance": np.nan,
                    "is_efficient": is_efficient,
                    "is_radially_efficient": is_radially_efficient,
                    "is_within_reference_technology": within_reference,
                    "self_in_reference": bool(self_membership[observation]),
                    "membership_status": (
                        "certified_by_self_inclusion"
                        if self_membership[observation]
                        else "certified_by_radial_factor"
                        if within_reference
                        else "outside_reference_technology"
                    ),
                    "solver_status": final_status,
                    "backend_solver_status": final_backend_status,
                    "raw_solver_status": final_backend_status,
                    "primary_solver_status": phase_one.status.value,
                    "primary_semantic_solver_status": SolverStatus.OPTIMAL.value,
                    "primary_backend_solver_status": phase_one.status.value,
                    "primary_raw_solver_status": phase_one.status.value,
                    "completion_solver_status": completion_solver_status,
                    "completion_semantic_solver_status": (
                        completion_semantic_solver_status
                    ),
                    "completion_backend_solver_status": (
                        completion_backend_solver_status
                    ),
                    "completion_raw_solver_status": completion_raw_solver_status,
                    "completion_valid": completion_valid,
                    "completion_status": completion_status,
                    "target_valid": target_valid,
                    "target_status": target_status,
                    "peer_valid": peer_valid,
                    "peer_status": peer_status,
                    "dual_valid": dual_valid,
                    "dual_status": dual_status,
                    "model_family": "radial",
                    "orientation": self.orientation.value,
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": reference.size,
                    "max_slack": max_slack,
                    "max_scaled_slack": max_scaled_slack,
                    "efficiency_denominator_valid": (reciprocal_denominator_valid),
                }
            )

        summary_frame = pd.DataFrame(summary_rows)
        summary_frame["base_reference_size"] = reference_plan.base_size_by_observation
        peer_eligibility_metadata = reference_plan.peer_eligibility_metadata()

        return DEAResult(
            summary_frame=summary_frame,
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            duals=pd.DataFrame(dual_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    type(self)._registry_method_id,
                    {
                        "context": {
                            "purpose": "operating_performance_benchmarking",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "controllable_resources",
                            "outputs": "desirable_services",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                            "disposal": "ordinary_free",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                            peer_eligibility=peer_eligibility_metadata,
                        ),
                        "performance": {
                            "family": "radial",
                            "orientation": self.orientation.value,
                            "slack_refinement": self.compute_slacks,
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": appraisal_kind,
                            "target_completion_id": (
                                PARETO_KOOPMANS_TARGET_COMPLETION_ID
                                if self.compute_slacks
                                else None
                            ),
                            "target_completion_scale_anchor": (
                                "evaluated_observation" if self.compute_slacks else None
                            ),
                            "target_uniqueness": (
                                "not_assessed"
                                if self.compute_slacks
                                else "not_applicable"
                            ),
                            "secondary_objective": (
                                "maximize_row_scaled_slacks"
                                if self.compute_slacks
                                else "none"
                            ),
                        },
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                    preset_id=type(self)._registry_preset_id,
                    specialization_id=type(self)._registry_specialization_id,
                ),
                "model_family": "radial",
                "orientation": self.orientation.value,
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                **(
                    {}
                    if peer_eligibility_metadata is None
                    else {"peer_eligibility": peer_eligibility_metadata}
                ),
                "native_score": (
                    "theta" if self.orientation is Orientation.INPUT else "phi"
                ),
                "efficiency_transform": (
                    "identity"
                    if self.orientation is Orientation.INPUT
                    else "reciprocal"
                ),
                "target_completion_id": (
                    PARETO_KOOPMANS_TARGET_COMPLETION_ID
                    if self.compute_slacks
                    else None
                ),
                "target_completion_scale_anchor": (
                    "evaluated_observation" if self.compute_slacks else None
                ),
                "slack_phase": "maximize_row_scaled_sum",
                "slack_target_unit_invariant": True,
                "compute_slacks": self.compute_slacks,
                "postsolve_certificate": {
                    "primary_lp": ("solver_neutral_primal_dual_kkt_and_strong_duality"),
                    "primary_economic": (
                        "radial_objective_production_balances_and_rts"
                    ),
                    "slack_completion_lp": (
                        "solver_neutral_primal_dual_kkt_and_strong_duality"
                    ),
                    "slack_completion_economic": (
                        "row_scaled_slack_objective_target_balances_and_rts"
                    ),
                    "publication_checks": (
                        "nonnegative_cleanup_account",
                        "reported_peer_target_reconstruction",
                        "complete_primary_dual_account",
                    ),
                    "score_release_policy": (
                        "requires_certified_primary_lp_and_economic_account"
                    ),
                    "completion_release_policy": (
                        "when_requested_targets_slacks_peers_and_duals_require_"
                        "certified_completion"
                    ),
                    "score_only_release_policy": (
                        "certified_primary_peers_and_duals_may_be_released"
                    ),
                    "completion_failure_policy": (
                        "retain_certified_primary_score_and_withhold_completion_claims"
                    ),
                    "target_peer_account": (
                        "targets_use_unthresholded_certified_intensities_and_reported_"
                        "peers_are_rechecked_after_thresholding"
                    ),
                    "semantic_tables": (
                        "slacks",
                        "targets",
                        "intensities",
                        "duals",
                    ),
                    "failure_scope": "per_observation",
                },
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
                "phase_one_template_compilations": len(phase_one_templates),
                "phase_one_task_bindings": phase_one_task_bindings,
                "phase_one_solver_calls": phase_one_solver_calls,
                "phase_two_solver_calls": phase_two_solver_calls,
                "solver_calls": phase_one_solver_calls + phase_two_solver_calls,
            },
        )


class CCR(RadialDEA):
    """Radial DEA constructor that fixes constant returns to scale."""

    _registry_specialization_id = "static.radial.crs"
    _registry_fixed_returns_to_scale = ReturnsToScale.CRS

    def __init__(
        self, *, orientation: Orientation | str = Orientation.INPUT, **kwargs: Any
    ) -> None:
        super().__init__(
            orientation=orientation,
            returns_to_scale=ReturnsToScale.CRS,
            **kwargs,
        )


class BCC(RadialDEA):
    """Radial DEA constructor that fixes variable returns to scale."""

    _registry_specialization_id = "static.radial.vrs"
    _registry_fixed_returns_to_scale = ReturnsToScale.VRS

    def __init__(
        self, *, orientation: Orientation | str = Orientation.INPUT, **kwargs: Any
    ) -> None:
        super().__init__(
            orientation=orientation,
            returns_to_scale=ReturnsToScale.VRS,
            **kwargs,
        )


class CCRInput(RadialDEA):
    """Complete input-oriented CCR recipe.

    The constructor fixes CRS, input orientation, and DEAPack's row-scaled
    lexicographic slack-completion policy.  Use :class:`CCR` or
    :class:`RadialDEA` when score-only execution or a different orientation is
    required.
    """

    _registry_preset_id = "static.radial.crs.input"
    _registry_fixed_orientation = Orientation.INPUT
    _registry_fixed_returns_to_scale = ReturnsToScale.CRS
    _registry_fixed_compute_slacks = True

    def __init__(
        self,
        *,
        reference: ReferenceSpec | str | None = None,
        peer_eligibility: PeerEligibility | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        super().__init__(
            orientation=Orientation.INPUT,
            returns_to_scale=ReturnsToScale.CRS,
            reference=reference,
            peer_eligibility=peer_eligibility,
            solver=solver,
            solver_options=solver_options,
            compute_slacks=True,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )


class CCROutput(RadialDEA):
    """Complete output-oriented CCR recipe with slack completion."""

    _registry_preset_id = "static.radial.crs.output"
    _registry_fixed_orientation = Orientation.OUTPUT
    _registry_fixed_returns_to_scale = ReturnsToScale.CRS
    _registry_fixed_compute_slacks = True

    def __init__(
        self,
        *,
        reference: ReferenceSpec | str | None = None,
        peer_eligibility: PeerEligibility | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        super().__init__(
            orientation=Orientation.OUTPUT,
            returns_to_scale=ReturnsToScale.CRS,
            reference=reference,
            peer_eligibility=peer_eligibility,
            solver=solver,
            solver_options=solver_options,
            compute_slacks=True,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )


class BCCInput(RadialDEA):
    """Complete input-oriented BCC recipe with slack completion."""

    _registry_preset_id = "static.radial.vrs.input"
    _registry_fixed_orientation = Orientation.INPUT
    _registry_fixed_returns_to_scale = ReturnsToScale.VRS
    _registry_fixed_compute_slacks = True

    def __init__(
        self,
        *,
        reference: ReferenceSpec | str | None = None,
        peer_eligibility: PeerEligibility | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        super().__init__(
            orientation=Orientation.INPUT,
            returns_to_scale=ReturnsToScale.VRS,
            reference=reference,
            peer_eligibility=peer_eligibility,
            solver=solver,
            solver_options=solver_options,
            compute_slacks=True,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )


class BCCOutput(RadialDEA):
    """Complete output-oriented BCC recipe with slack completion."""

    _registry_preset_id = "static.radial.vrs.output"
    _registry_fixed_orientation = Orientation.OUTPUT
    _registry_fixed_returns_to_scale = ReturnsToScale.VRS
    _registry_fixed_compute_slacks = True

    def __init__(
        self,
        *,
        reference: ReferenceSpec | str | None = None,
        peer_eligibility: PeerEligibility | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        super().__init__(
            orientation=Orientation.OUTPUT,
            returns_to_scale=ReturnsToScale.VRS,
            reference=reference,
            peer_eligibility=peer_eligibility,
            solver=solver,
            solver_options=solver_options,
            compute_slacks=True,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )
