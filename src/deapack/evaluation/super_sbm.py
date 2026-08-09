"""Tone's source-qualified slacks-based measure of super-efficiency."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, eye, hstack, vstack

from .._registry import (
    data_role_schema,
    registry_metadata,
)
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import ModelSpecificationError
from ..models._common import CompiledReference, compile_reference
from ..models.sbm import SlacksBasedDEA
from ..results import DEAResult
from ..solvers import (
    LinearProgram,
    LPSolution,
    LPSolver,
    SciPyHiGHSSolver,
)
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._crs_multiplier import _CertifiedLPSolution, _certify_lp_solution

_METHOD_ID = "evaluation.super.sbm.tone_2002"
_SOURCE_DOI = "https://doi.org/10.1016/S0377-2217(01)00324-1"
_ORIENTATIONS = frozenset({"non-oriented", "input", "output"})


@dataclass(frozen=True, slots=True)
class _ScreenAuditRecord:
    """One ordinary-SBM screening solve and its independent certificate."""

    problem: LinearProgram
    solution: LPSolution
    certificate: _CertifiedLPSolution


class _ScreenAuditSolver:
    """Certify screening LPs before ``SlacksBasedDEA`` postprocesses them."""

    def __init__(self, delegate: LPSolver, tolerance: float) -> None:
        self.delegate = delegate
        self.tolerance = tolerance
        self.name = delegate.name
        self.records: list[_ScreenAuditRecord] = []

    def solve(self, problem: LinearProgram) -> LPSolution:
        solution = self.delegate.solve(problem)
        certificate = _certify_lp_solution(
            problem,
            solution,
            tolerance=self.tolerance,
        )
        if (
            certificate.certified
            and solution.primal is not None
            and float(solution.primal[-1]) <= self.tolerance
        ):
            certificate = replace(
                certificate,
                certified=False,
                reason="nonpositive_sbm_transform_scale",
            )
        self.records.append(
            _ScreenAuditRecord(
                problem=problem,
                solution=solution,
                certificate=certificate,
            )
        )
        if solution.status is SolverStatus.OPTIMAL and not certificate.certified:
            return replace(
                solution,
                status=SolverStatus.FAILED,
                objective=None,
                primal=None,
                message=(
                    f"{solution.message}; ordinary SBM postsolve certificate "
                    f"failed: {certificate.reason}"
                ),
            )
        return solution


@dataclass(frozen=True, slots=True)
class _RecoveredSuperSolution:
    """A source-coordinate solution recovered from one certified LP."""

    score: float
    input_replacement_factor: float
    output_retention_factor: float
    transform_scale: float
    lambdas: np.ndarray
    input_replacement_plan: np.ndarray
    output_replacement_plan: np.ndarray
    peer_inputs: np.ndarray
    peer_outputs: np.ndarray
    certified: bool
    certification_reason: str
    max_economic_violation: float
    score_reconstruction_residual: float
    source_normalization_violation: float


def _normalize_orientation(value: object) -> str:
    raw = getattr(value, "value", value)
    normalized = str(raw).strip().lower().replace("_", "-")
    if normalized == "nonoriented":
        normalized = "non-oriented"
    if normalized not in _ORIENTATIONS:
        choices = ", ".join(sorted(_ORIENTATIONS))
        raise ValueError(f"orientation must be one of: {choices}; got {value!r}")
    return normalized


def _readonly_rows(rows: np.ndarray) -> np.ndarray:
    copied = np.asarray(rows, dtype=np.int64).copy()
    copied.setflags(write=False)
    return copied


def _clean_nonnegative_gap(
    values: np.ndarray,
    normalizers: np.ndarray,
    tolerance: float,
) -> np.ndarray:
    cleaned = np.maximum(np.asarray(values, dtype=np.float64), 0.0)
    cleaned[cleaned / normalizers <= tolerance] = 0.0
    return cleaned


class ToneSuperSBM:
    """Evaluate Tone's (2002) non-radial super-efficiency measure.

    The source measure is defined only for observations that are strongly
    efficient under the ordinary non-oriented SBM.  This implementation first
    performs that matched-RTS screen once for the full sample and then solves a
    leave-one-out super-SBM only for eligible observations.  Ordinary SBM
    scores are never substituted for unavailable super-SBM scores.

    Strictly positive inputs and desirable outputs are required.  CRS supports
    the source non-oriented, input-oriented, and output-oriented programmes.
    VRS is available only for the non-oriented programme explicitly stated by
    Tone.  Signed-data, automatic zero-data, NIRS/NDRS, and VRS-oriented
    extensions are different formulations and are rejected.
    """

    _registry_method_id = _METHOD_ID

    def __init__(
        self,
        *,
        orientation: str = "non-oriented",
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.orientation = _normalize_orientation(orientation)
        self.returns_to_scale = parse_enum(
            returns_to_scale,
            ReturnsToScale,
            "returns_to_scale",
        )
        if self.returns_to_scale not in {
            ReturnsToScale.CRS,
            ReturnsToScale.VRS,
        }:
            raise ModelSpecificationError(
                "ToneSuperSBM implements only the CRS and VRS formulations "
                "explicitly stated by Tone (2002)"
            )
        if (
            self.returns_to_scale is ReturnsToScale.VRS
            and self.orientation != "non-oriented"
        ):
            raise ModelSpecificationError(
                "Tone (2002) states the VRS super-SBM for the non-oriented "
                "programme; VRS input/output-oriented variants are outside "
                "this source-qualified implementation"
            )
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        if not math.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("tolerance must be positive and finite")
        normalized_peer_tolerance = (
            float(tolerance) if peer_tolerance is None else float(peer_tolerance)
        )
        if (
            not math.isfinite(normalized_peer_tolerance)
            or normalized_peer_tolerance <= 0.0
        ):
            raise ValueError("peer_tolerance must be positive and finite")

        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.tolerance = float(tolerance)
        self.peer_tolerance = normalized_peer_tolerance

    def _validate_data(self, data: DEAData) -> None:
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "ToneSuperSBM does not infer undesirable-output disposal; use "
                "a separately sourced environmental super-efficiency model"
            )
        data.ensure_nonnegative(allow_zero=False)
        if data.n_dmus < 2:
            raise ModelSpecificationError(
                "ToneSuperSBM requires at least two observations so one peer "
                "remains after self-exclusion"
            )

    def _validate_reference_sets(self, data: DEAData, reference_plan: Any) -> None:
        missing_self: list[object] = []
        empty_after_exclusion: list[object] = []
        for observation in range(data.n_dmus):
            rows = reference_plan.rows_for(observation)
            self_count = int(np.count_nonzero(rows == observation))
            if self_count != 1:
                missing_self.append(data.dmu_ids[observation])
                continue
            if int(rows.size) - 1 == 0:
                empty_after_exclusion.append(data.dmu_ids[observation])
        if missing_self:
            raise ModelSpecificationError(
                "every ordinary-SBM reference set must contain its evaluated "
                "observation exactly once before Tone's self-exclusion; "
                f"examples={missing_self[:5]!r}"
            )
        if empty_after_exclusion:
            raise ModelSpecificationError(
                "ToneSuperSBM self-exclusion leaves no eligible peer for some "
                f"observations; examples={empty_after_exclusion[:5]!r}"
            )

    def _nonoriented_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> LinearProgram:
        n_lambda = reference.size
        m = x_o.size
        s = y_o.size
        n_variables = n_lambda + m + s + 1

        input_technology = hstack(
            [
                reference.inputs,
                -eye(m, format="csc"),
                csc_matrix((m, s + 1)),
            ],
            format="csc",
        )
        output_technology = hstack(
            [
                -reference.outputs,
                csc_matrix((s, m)),
                eye(s, format="csc"),
                csc_matrix((s, 1)),
            ],
            format="csc",
        )
        input_floor = hstack(
            [
                csc_matrix((m, n_lambda)),
                -eye(m, format="csc"),
                csc_matrix((m, s)),
                csc_matrix(x_o.reshape(-1, 1)),
            ],
            format="csc",
        )
        output_ceiling = hstack(
            [
                csc_matrix((s, n_lambda + m)),
                eye(s, format="csc"),
                csc_matrix((-y_o).reshape(-1, 1)),
            ],
            format="csc",
        )
        a_ub = vstack(
            [
                input_technology,
                output_technology,
                input_floor,
                output_ceiling,
            ],
            format="csc",
        )
        b_ub = np.zeros(2 * (m + s), dtype=np.float64)

        normalization = np.zeros(n_variables, dtype=np.float64)
        normalization[n_lambda + m : n_lambda + m + s] = 1.0 / (s * y_o)
        equality_rows = [csc_matrix(normalization.reshape(1, -1))]
        equality_values = [1.0]
        if self.returns_to_scale is ReturnsToScale.VRS:
            convexity = np.zeros(n_variables, dtype=np.float64)
            convexity[:n_lambda] = 1.0
            convexity[-1] = -1.0
            equality_rows.append(csc_matrix(convexity.reshape(1, -1)))
            equality_values.append(0.0)

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[n_lambda : n_lambda + m] = 1.0 / (m * x_o)
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=vstack(equality_rows, format="csc"),
            b_eq=np.asarray(equality_values, dtype=np.float64),
            bounds=((0.0, None),) * n_variables,
            name=f"super_sbm_peer_replacement:{name}:non_oriented",
        )

    def _input_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> LinearProgram:
        n_lambda = reference.size
        m = x_o.size
        s = y_o.size
        n_variables = n_lambda + m

        input_technology = hstack(
            [reference.inputs, -eye(m, format="csc")],
            format="csc",
        )
        output_support = hstack(
            [-reference.outputs, csc_matrix((s, m))],
            format="csc",
        )
        input_floor = hstack(
            [
                csc_matrix((m, n_lambda)),
                -eye(m, format="csc"),
            ],
            format="csc",
        )
        objective = np.zeros(n_variables, dtype=np.float64)
        objective[n_lambda:] = 1.0 / (m * x_o)
        return LinearProgram(
            c=objective,
            a_ub=vstack(
                [input_technology, output_support, input_floor],
                format="csc",
            ),
            b_ub=np.concatenate(
                [
                    np.zeros(m, dtype=np.float64),
                    -y_o,
                    -x_o,
                ]
            ),
            bounds=((0.0, None),) * n_variables,
            name=f"super_sbm_peer_replacement:{name}:input",
        )

    def _output_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> LinearProgram:
        n_lambda = reference.size
        m = x_o.size
        s = y_o.size
        n_variables = n_lambda + s

        input_ceiling = hstack(
            [reference.inputs, csc_matrix((m, s))],
            format="csc",
        )
        output_technology = hstack(
            [-reference.outputs, eye(s, format="csc")],
            format="csc",
        )
        output_ceiling = hstack(
            [
                csc_matrix((s, n_lambda)),
                eye(s, format="csc"),
            ],
            format="csc",
        )
        objective = np.zeros(n_variables, dtype=np.float64)
        objective[n_lambda:] = -1.0 / (s * y_o)
        return LinearProgram(
            c=objective,
            a_ub=vstack(
                [input_ceiling, output_technology, output_ceiling],
                format="csc",
            ),
            b_ub=np.concatenate(
                [
                    x_o,
                    np.zeros(s, dtype=np.float64),
                    y_o,
                ]
            ),
            bounds=((0.0, None),) * n_variables,
            name=f"super_sbm_peer_replacement:{name}:output",
        )

    def _problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> LinearProgram:
        if self.orientation == "non-oriented":
            return self._nonoriented_problem(reference, x_o, y_o, name)
        if self.orientation == "input":
            return self._input_problem(reference, x_o, y_o, name)
        return self._output_problem(reference, x_o, y_o, name)

    def _recover_and_certify(
        self,
        *,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        solution: LPSolution,
    ) -> _RecoveredSuperSolution:
        assert solution.primal is not None
        assert solution.objective is not None
        primal = np.asarray(solution.primal, dtype=np.float64)
        n_lambda = reference.size
        m = x_o.size
        s = y_o.size

        transform_scale = 1.0
        source_normalization_violation = 0.0
        if self.orientation == "non-oriented":
            transform_scale = float(primal[-1])
            if not math.isfinite(transform_scale) or transform_scale <= 0.0:
                return self._invalid_recovered(
                    reason="nonpositive_super_sbm_transform_scale"
                )
            lambdas = primal[:n_lambda] / transform_scale
            input_plan = primal[n_lambda : n_lambda + m] / transform_scale
            output_plan = primal[n_lambda + m : n_lambda + m + s] / transform_scale
            source_normalization_violation = abs(
                float(np.mean(primal[n_lambda + m : n_lambda + m + s] / y_o)) - 1.0
            )
        elif self.orientation == "input":
            lambdas = primal[:n_lambda]
            input_plan = primal[n_lambda:]
            output_plan = y_o.copy()
        else:
            lambdas = primal[:n_lambda]
            input_plan = x_o.copy()
            output_plan = primal[n_lambda:]

        peer_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
        peer_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
        values = (
            lambdas,
            input_plan,
            output_plan,
            peer_inputs,
            peer_outputs,
        )
        if any(not np.isfinite(value).all() for value in values):
            return self._invalid_recovered(reason="nonfinite_recovered_solution")

        input_factor = float(np.mean(input_plan / x_o))
        output_retention = float(np.mean(output_plan / y_o))
        if (
            not math.isfinite(input_factor)
            or not math.isfinite(output_retention)
            or output_retention <= 0.0
        ):
            return self._invalid_recovered(reason="invalid_replacement_factor")
        score = input_factor / output_retention

        violations = [
            float(np.maximum(-lambdas, 0.0).max(initial=0.0)),
            float(np.maximum((peer_inputs - input_plan) / x_o, 0.0).max(initial=0.0)),
            float(np.maximum((output_plan - peer_outputs) / y_o, 0.0).max(initial=0.0)),
            float(np.maximum((x_o - input_plan) / x_o, 0.0).max(initial=0.0)),
            float(np.maximum((output_plan - y_o) / y_o, 0.0).max(initial=0.0)),
            float(max(1.0 - score, 0.0)),
            source_normalization_violation,
        ]
        if self.returns_to_scale is ReturnsToScale.VRS:
            violations.append(abs(float(lambdas.sum()) - 1.0))

        if self.orientation == "output":
            source_objective = -float(solution.objective)
            reconstructed_objective = output_retention
        else:
            source_objective = float(solution.objective)
            reconstructed_objective = score
        objective_scale = max(
            1.0,
            abs(source_objective),
            abs(reconstructed_objective),
        )
        score_residual = (
            abs(source_objective - reconstructed_objective) / objective_scale
        )
        max_economic_violation = max([*violations, score_residual])
        certified = bool(max_economic_violation <= self.tolerance)
        return _RecoveredSuperSolution(
            score=score,
            input_replacement_factor=input_factor,
            output_retention_factor=output_retention,
            transform_scale=transform_scale,
            lambdas=lambdas,
            input_replacement_plan=input_plan,
            output_replacement_plan=output_plan,
            peer_inputs=peer_inputs,
            peer_outputs=peer_outputs,
            certified=certified,
            certification_reason=(
                "certified" if certified else "source_equation_reconstruction_failed"
            ),
            max_economic_violation=max_economic_violation,
            score_reconstruction_residual=score_residual,
            source_normalization_violation=source_normalization_violation,
        )

    @staticmethod
    def _invalid_recovered(*, reason: str) -> _RecoveredSuperSolution:
        empty = np.asarray([], dtype=np.float64)
        return _RecoveredSuperSolution(
            score=np.nan,
            input_replacement_factor=np.nan,
            output_retention_factor=np.nan,
            transform_scale=np.nan,
            lambdas=empty,
            input_replacement_plan=empty,
            output_replacement_plan=empty,
            peer_inputs=empty,
            peer_outputs=empty,
            certified=False,
            certification_reason=reason,
            max_economic_violation=math.inf,
            score_reconstruction_residual=math.inf,
            source_normalization_violation=math.inf,
        )

    def _base_summary(
        self,
        *,
        data: DEAData,
        observation: int,
        screen_score: float,
        is_sbm_eligible: bool | Any,
        reference_size_before_exclusion: int,
        reference_size: int,
        solver_status: str,
        screen_solver_status: str,
        super_solver_status: str | None,
        applicability_status: str,
        failure_reason: str | None,
    ) -> dict[str, Any]:
        return {
            "dmu_id": data.dmu_ids[observation],
            "period": (None if data.periods is None else data.periods[observation]),
            "score": np.nan,
            "super_sbm_score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "is_efficient": pd.NA,
            "sbm_screen_score": screen_score,
            "is_sbm_eligible": is_sbm_eligible,
            "is_super_efficient": pd.NA,
            "score_valid": False,
            "applicability_status": applicability_status,
            "solver_status": solver_status,
            "screen_solver_status": screen_solver_status,
            "super_solver_status": super_solver_status,
            "failure_reason": failure_reason,
            "model_family": "super_sbm_peer_replacement",
            "orientation": self.orientation,
            "returns_to_scale": self.returns_to_scale.value,
            "reference_size_before_exclusion": (reference_size_before_exclusion),
            "reference_size": reference_size,
            "self_excluded": True,
            "score_direction": "higher_is_more_exposed",
            "input_replacement_factor": np.nan,
            "output_retention_factor": np.nan,
            "transform_scale": np.nan,
            "reported_peer_count": 0,
            "omitted_intensity_sum": np.nan,
        }

    @staticmethod
    def _certificate_fields(
        certificate: _CertifiedLPSolution,
    ) -> dict[str, Any]:
        return {
            "postsolve_certified": certificate.certified,
            "certification_reason": certificate.reason,
            "max_constraint_violation": certificate.max_constraint_violation,
            "equality_violation": certificate.equality_violation,
            "max_bound_violation": certificate.max_bound_violation,
            "objective_residual": certificate.objective_residual,
            "duality_gap": certificate.duality_gap,
            "max_dual_violation": certificate.max_dual_violation,
        }

    def _screen_diagnostic(
        self,
        *,
        data: DEAData,
        observation: int,
        record: _ScreenAuditRecord,
        screen_score: float,
        is_sbm_eligible: bool | Any,
    ) -> dict[str, Any]:
        solution = record.solution
        return {
            "dmu_id": data.dmu_ids[observation],
            "period": (None if data.periods is None else data.periods[observation]),
            "phase": 1,
            "phase_name": "ordinary_sbm_screen",
            "phase_status": (
                "completed"
                if record.certificate.certified
                else "failed_postsolve_certificate"
                if solution.status is SolverStatus.OPTIMAL
                else "solver_failed"
            ),
            "solver_status": solution.status.value,
            "message": solution.message,
            "iterations": solution.iterations,
            "max_primal_violation": solution.max_primal_violation,
            "sbm_screen_score": screen_score,
            "is_sbm_eligible": is_sbm_eligible,
            **self._certificate_fields(record.certificate),
        }

    def _skipped_super_diagnostic(
        self,
        *,
        data: DEAData,
        observation: int,
        phase_status: str,
    ) -> dict[str, Any]:
        return {
            "dmu_id": data.dmu_ids[observation],
            "period": (None if data.periods is None else data.periods[observation]),
            "phase": 2,
            "phase_name": "super_sbm_peer_replacement",
            "phase_status": phase_status,
            "solver_status": None,
            "message": None,
            "iterations": None,
            "max_primal_violation": np.nan,
            "postsolve_certified": pd.NA,
            "certification_reason": phase_status,
            "max_constraint_violation": np.nan,
            "equality_violation": np.nan,
            "max_bound_violation": np.nan,
            "objective_residual": np.nan,
            "duality_gap": np.nan,
            "max_dual_violation": np.nan,
            "economic_postsolve_certified": pd.NA,
            "economic_certification_reason": phase_status,
            "max_economic_violation": np.nan,
            "score_reconstruction_residual": np.nan,
            "source_normalization_violation": np.nan,
        }

    def fit(self, data: DEAData) -> DEAResult:
        """Screen ordinary SBM efficiency and appraise eligible observations."""

        self._validate_data(data)
        reference_plan = build_reference_plan(data, self.reference)
        self._validate_reference_sets(data, reference_plan)

        screen_solver = _ScreenAuditSolver(self.solver, self.tolerance)
        screen_result = SlacksBasedDEA(
            returns_to_scale=self.returns_to_scale,
            reference=self.reference,
            solver=screen_solver,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
        ).fit(data)
        if len(screen_solver.records) != data.n_dmus:
            raise RuntimeError(
                "ordinary SBM screening did not return one solve per observation"
            )
        screen_summary = screen_result.summary(copy=False).reset_index(drop=True)

        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        eligible_observations = 0
        super_solves = 0

        for observation in range(data.n_dmus):
            base_rows = reference_plan.rows_for(observation)
            eligible_rows = _readonly_rows(base_rows[base_rows != observation])
            reference_size_before_exclusion = int(base_rows.size)
            reference_size = int(eligible_rows.size)
            screen_row = screen_summary.iloc[observation]
            screen_record = screen_solver.records[observation]
            screen_score = float(screen_row["score"])
            screen_certified = bool(screen_record.certificate.certified)
            raw_eligibility = screen_row["is_sbm_efficient"]
            is_sbm_eligible: bool | Any = (
                bool(raw_eligibility)
                if screen_certified and not pd.isna(raw_eligibility)
                else pd.NA
            )
            diagnostic_rows.append(
                self._screen_diagnostic(
                    data=data,
                    observation=observation,
                    record=screen_record,
                    screen_score=screen_score,
                    is_sbm_eligible=is_sbm_eligible,
                )
            )

            if not screen_certified:
                summary_rows.append(
                    self._base_summary(
                        data=data,
                        observation=observation,
                        screen_score=screen_score,
                        is_sbm_eligible=pd.NA,
                        reference_size_before_exclusion=(
                            reference_size_before_exclusion
                        ),
                        reference_size=reference_size,
                        solver_status=(
                            screen_record.solution.status.value
                            if screen_record.solution.status is not SolverStatus.OPTIMAL
                            else SolverStatus.FAILED.value
                        ),
                        screen_solver_status=(screen_record.solution.status.value),
                        super_solver_status=None,
                        applicability_status=("not_applicable_screening_failed"),
                        failure_reason=screen_record.certificate.reason,
                    )
                )
                diagnostic_rows.append(
                    self._skipped_super_diagnostic(
                        data=data,
                        observation=observation,
                        phase_status="not_run_screening_failed",
                    )
                )
                continue

            if not bool(is_sbm_eligible):
                summary_rows.append(
                    self._base_summary(
                        data=data,
                        observation=observation,
                        screen_score=screen_score,
                        is_sbm_eligible=False,
                        reference_size_before_exclusion=(
                            reference_size_before_exclusion
                        ),
                        reference_size=reference_size,
                        solver_status=SolverStatus.OPTIMAL.value,
                        screen_solver_status=SolverStatus.OPTIMAL.value,
                        super_solver_status=None,
                        applicability_status=("not_applicable_not_sbm_efficient"),
                        failure_reason=None,
                    )
                )
                diagnostic_rows.append(
                    self._skipped_super_diagnostic(
                        data=data,
                        observation=observation,
                        phase_status="not_run_not_sbm_efficient",
                    )
                )
                continue

            eligible_observations += 1
            reference = compile_reference(data, eligible_rows)
            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            problem = self._problem(reference, x_o, y_o, name)
            solution = self.solver.solve(problem)
            super_solves += 1
            certificate = _certify_lp_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )
            recovered = (
                self._recover_and_certify(
                    reference=reference,
                    x_o=x_o,
                    y_o=y_o,
                    solution=solution,
                )
                if certificate.certified
                else self._invalid_recovered(reason="super_lp_certificate_failed")
            )
            diagnostic_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": 2,
                    "phase_name": "super_sbm_peer_replacement",
                    "phase_status": (
                        "completed"
                        if certificate.certified and recovered.certified
                        else "failed_postsolve_certificate"
                        if solution.status is SolverStatus.OPTIMAL
                        else "solver_failed"
                    ),
                    "solver_status": solution.status.value,
                    "message": solution.message,
                    "iterations": solution.iterations,
                    "max_primal_violation": solution.max_primal_violation,
                    **self._certificate_fields(certificate),
                    "economic_postsolve_certified": recovered.certified,
                    "economic_certification_reason": (recovered.certification_reason),
                    "max_economic_violation": (recovered.max_economic_violation),
                    "score_reconstruction_residual": (
                        recovered.score_reconstruction_residual
                    ),
                    "source_normalization_violation": (
                        recovered.source_normalization_violation
                    ),
                    "super_sbm_score": recovered.score,
                    "input_replacement_factor": (recovered.input_replacement_factor),
                    "output_retention_factor": (recovered.output_retention_factor),
                    "transform_scale": recovered.transform_scale,
                    "reference_size": reference_size,
                    "self_excluded": True,
                }
            )
            if not certificate.certified or not recovered.certified:
                reason = (
                    certificate.reason
                    if not certificate.certified
                    else recovered.certification_reason
                )
                summary_rows.append(
                    self._base_summary(
                        data=data,
                        observation=observation,
                        screen_score=screen_score,
                        is_sbm_eligible=True,
                        reference_size_before_exclusion=(
                            reference_size_before_exclusion
                        ),
                        reference_size=reference_size,
                        solver_status=(
                            solution.status.value
                            if solution.status is not SolverStatus.OPTIMAL
                            else SolverStatus.FAILED.value
                        ),
                        screen_solver_status=SolverStatus.OPTIMAL.value,
                        super_solver_status=solution.status.value,
                        applicability_status=("applicable_super_solve_failed"),
                        failure_reason=reason,
                    )
                )
                continue

            # Preserve every certified intensity when reconstructing peer
            # activity.  ``peer_tolerance`` affects disclosure only; it never
            # changes targets, slacks, or the source score.
            lambdas = np.maximum(recovered.lambdas, 0.0)
            input_plan = recovered.input_replacement_plan
            output_plan = recovered.output_replacement_plan
            peer_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
            peer_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
            input_replacement_adjustment = _clean_nonnegative_gap(
                input_plan - x_o,
                x_o,
                self.tolerance,
            )
            output_replacement_adjustment = _clean_nonnegative_gap(
                y_o - output_plan,
                y_o,
                self.tolerance,
            )
            input_technology_slack = _clean_nonnegative_gap(
                input_plan - peer_inputs,
                x_o,
                self.tolerance,
            )
            output_technology_slack = _clean_nonnegative_gap(
                peer_outputs - output_plan,
                y_o,
                self.tolerance,
            )

            omitted_intensity_sum = float(lambdas[lambdas <= self.peer_tolerance].sum())
            reported_peer_count = int(np.count_nonzero(lambdas > self.peer_tolerance))
            for local_position, intensity in enumerate(lambdas):
                if intensity <= self.peer_tolerance:
                    continue
                reference_position = int(reference.rows[local_position])
                intensity_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "reference_dmu_id": (data.dmu_ids[reference_position]),
                        "reference_period": (
                            None
                            if data.periods is None
                            else data.periods[reference_position]
                        ),
                        "reference_row_position": reference_position,
                        "lambda": float(intensity),
                        "intensity": float(intensity),
                        "selection": ("solver_selected_source_primary_optimum"),
                    }
                )

            blocks = (
                (
                    "input",
                    data.input_names,
                    x_o,
                    input_plan,
                    peer_inputs,
                    input_replacement_adjustment,
                    input_technology_slack,
                    "additional_input_allowance",
                ),
                (
                    "output",
                    data.output_names,
                    y_o,
                    output_plan,
                    peer_outputs,
                    output_replacement_adjustment,
                    output_technology_slack,
                    "output_sacrifice",
                ),
            )
            for (
                role,
                names,
                observed,
                replacement_plan,
                peer_activity,
                replacement_adjustment,
                technology_slack,
                adjustment_meaning,
            ) in blocks:
                for (
                    variable,
                    value,
                    target,
                    peer_value,
                    replacement_gap,
                    technology_gap,
                ) in zip(
                    names,
                    observed,
                    replacement_plan,
                    peer_activity,
                    replacement_adjustment,
                    technology_slack,
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
                            "replacement_plan": float(target),
                            "peer_activity": float(peer_value),
                            "replacement_ratio": float(target / value),
                            "target_meaning": "peer_replacement_plan",
                            "target_selection": (
                                "solver_selected_source_primary_optimum"
                            ),
                        }
                    )
                    for gap_kind, gap, meaning in (
                        (
                            "replacement_adjustment",
                            replacement_gap,
                            adjustment_meaning,
                        ),
                        (
                            "technology_slack",
                            technology_gap,
                            "replacement_plan_minus_peer_input"
                            if role == "input"
                            else "peer_output_minus_replacement_plan",
                        ),
                    ):
                        slack_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "gap_kind": gap_kind,
                                "slack": float(gap),
                                "normalizer": float(value),
                                "normalized_slack": float(gap / value),
                                "economic_meaning": meaning,
                                "included_in_native_score": (
                                    gap_kind == "replacement_adjustment"
                                    and (
                                        self.orientation == "non-oriented"
                                        or self.orientation == role
                                    )
                                ),
                            }
                        )

            valid_summary = self._base_summary(
                data=data,
                observation=observation,
                screen_score=screen_score,
                is_sbm_eligible=True,
                reference_size_before_exclusion=(reference_size_before_exclusion),
                reference_size=reference_size,
                solver_status=SolverStatus.OPTIMAL.value,
                screen_solver_status=SolverStatus.OPTIMAL.value,
                super_solver_status=SolverStatus.OPTIMAL.value,
                applicability_status="applicable",
                failure_reason=None,
            )
            valid_summary.update(
                {
                    "score": recovered.score,
                    "super_sbm_score": recovered.score,
                    "is_super_efficient": bool(recovered.score > 1.0 + self.tolerance),
                    "score_valid": True,
                    "input_replacement_factor": (recovered.input_replacement_factor),
                    "output_retention_factor": (recovered.output_retention_factor),
                    "transform_scale": recovered.transform_scale,
                    "reported_peer_count": reported_peer_count,
                    "omitted_intensity_sum": omitted_intensity_sum,
                }
            )
            summary_rows.append(valid_summary)

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": (
                                "frontier_discrimination_and_replacement_exposure"
                            ),
                            "sample": ("panel" if data.is_panel else "cross_section"),
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
                            "returns_to_scale": (self.returns_to_scale.value),
                            "disposal": "ordinary_free",
                            "data_domain": "strictly_positive",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": {
                            **registry_reference_spec(
                                self.reference,
                                reference_plan.kind,
                            ),
                            "evaluated_observation": ("required_in_base_then_excluded"),
                        },
                        "performance": {
                            "family": "slacks_based_super_efficiency",
                            "orientation": self.orientation.replace("-", "_"),
                            "reported_score": "delta",
                            "score_direction": "higher_is_more_exposed",
                        },
                        "valuation": {"kind": "equal_dimension_weights"},
                        "evaluation_protocol": {
                            "kind": ("ordinary_sbm_screen_then_leave_one_out"),
                            "source": "tone_2002",
                            "source_doi": _SOURCE_DOI,
                        },
                        "analysis": {
                            "kind": ("frontier_ranking_and_replacement_appraisal"),
                            "target_selection": (
                                "solver_selected_source_primary_optimum"
                            ),
                        },
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "super_sbm_peer_replacement",
                "source": {
                    "author": "Kaoru Tone",
                    "year": 2002,
                    "title": (
                        "A slacks-based measure of super-efficiency in data "
                        "envelopment analysis"
                    ),
                    "doi": _SOURCE_DOI,
                },
                "orientation": self.orientation,
                "returns_to_scale": self.returns_to_scale.value,
                "returns_to_scale_scope": (
                    "crs_three_source_orientations"
                    if self.returns_to_scale is ReturnsToScale.CRS
                    else "vrs_nonoriented_source_equation_24"
                ),
                "reference_kind": reference_plan.kind.value,
                "base_reference_sets": (reference_plan.unique_reference_sets),
                "evaluation_protocol": ("ordinary_sbm_screen_then_leave_one_out"),
                "eligibility_policy": ("ordinary_nonoriented_sbm_strong_efficiency"),
                "ineligible_score_policy": ("missing_never_combined_with_ordinary_sbm"),
                "data_requirement": "strictly_positive",
                "zero_policy": "reject",
                "signed_data_policy": "reject",
                "bad_output_policy": "reject",
                "score_direction": "higher_is_more_exposed",
                "native_score": "super_sbm_score",
                "generic_efficiency_classification": "not_reported",
                "target_meaning": "peer_replacement_plan_not_improvement_target",
                "target_selection": ("solver_selected_source_primary_optimum"),
                "intensity_selection": ("solver_selected_source_primary_optimum"),
                "targets_use_unthresholded_intensities": True,
                "peer_threshold_scope": "reporting_only",
                "screening_solves": data.n_dmus,
                "eligible_observations": eligible_observations,
                "super_solves": super_solves,
                "solver_calls": data.n_dmus + super_solves,
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "failure_policy": ("fail_closed_without_score_target_or_intensity"),
            },
        )


SuperSBM = ToneSuperSBM
"""Exact public alias for :class:`ToneSuperSBM`."""


__all__ = ["SuperSBM", "ToneSuperSBM"]
