"""By-production directional distance with separate production relations."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, hstack, vstack

from .._registry import (
    data_role_schema,
    direction_spec,
    registry_metadata,
)
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import ReferenceKind, ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import ModelSpecificationError
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._common import (
    CompiledReference,
    compile_reference,
    join_optional_rows,
    join_optional_values,
    rts_matrices,
)
from ._radial_lp import radial_row_scales
from .directional import DirectionInput, _resolve_direction
from .environmental import (
    _certificate_diagnostic,
    _certify_environmental_distance_task,
    _rts_violation,
    _scaled_maximum,
    _scaled_nonnegative_violation,
)


class ByProductionDirectionalDistanceDEA:
    """Apply an output directional distance to a by-production technology.

    Intended production and residual generation use separate intensity
    vectors. The intended subtechnology freely disposes inputs and good
    outputs, while the residual subtechnology imposes costly disposability on
    pollution-generating inputs and bad outputs. The reported joint distance
    is the smaller of the two component distances.

    Murty, Russell, and Levkoff (2012) study this conventional DDF on their
    by-production technology but criticize it for understating inefficiency
    and for its sensitivity to the fixed direction. Their proposed
    by-production performance index is the distinct FGL measure. BP-DDF's
    joint projection can be weakly efficient even when one component retains
    improvement potential, so this result reports directional and
    componentwise efficiency separately.
    """

    _registry_method_id = "environmental.by_production.ddf"

    def __init__(
        self,
        *,
        output_direction: DirectionInput = "ones",
        bad_output_direction: DirectionInput = "ones",
        intended_returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        residual_returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.output_direction = output_direction
        self.bad_output_direction = bad_output_direction
        self.intended_returns_to_scale = parse_enum(
            intended_returns_to_scale,
            ReturnsToScale,
            "intended_returns_to_scale",
        )
        self.residual_returns_to_scale = parse_enum(
            residual_returns_to_scale,
            ReturnsToScale,
            "residual_returns_to_scale",
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
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
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
        if data.bad_outputs is None:
            raise ModelSpecificationError(
                "ByProductionDirectionalDistanceDEA requires declared "
                "bad_outputs in DEAData"
            )
        if not data.polluting_input_names:
            raise ModelSpecificationError(
                "ByProductionDirectionalDistanceDEA requires at least one "
                "polluting_inputs column in DEAData"
            )

    def _unscaled_intended_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        g_y: np.ndarray,
        name: str,
    ) -> LinearProgram:
        n_lambda = reference.size
        n_variables = n_lambda + 1
        input_rows = hstack([reference.inputs, csc_matrix((x_o.size, 1))], format="csc")
        output_rows = hstack(
            [-reference.outputs, csc_matrix(g_y.reshape(-1, 1))], format="csc"
        )
        a_ub = vstack([input_rows, output_rows], format="csc")
        b_ub = np.concatenate([x_o, -y_o])
        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_variables, n_lambda, self.intended_returns_to_scale
        )
        a_ub = join_optional_rows(a_ub, rts_ub)
        b_ub = join_optional_values(b_ub, rts_b_ub)

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[-1] = -1.0
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=rts_eq,
            b_eq=rts_b_eq,
            bounds=((0.0, None),) * n_variables,
            name=f"{name}:by_production:intended",
        )

    def _intended_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        g_y: np.ndarray,
        name: str,
    ) -> LinearProgram:
        """Build the intended-production programme in stable quantity units."""
        problem = self._unscaled_intended_problem(
            reference,
            x_o,
            y_o,
            g_y,
            name,
        )
        input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
        quantity_scales = np.concatenate([input_scales, output_scales])
        extra_rows = problem.a_ub.shape[0] - quantity_scales.size
        if extra_rows < 0:
            raise RuntimeError("by-production intended row layout is invalid")
        row_scales = (
            quantity_scales
            if extra_rows == 0
            else np.concatenate(
                [quantity_scales, np.ones(extra_rows, dtype=np.float64)]
            )
        )
        return LinearProgram(
            c=problem.c,
            a_ub=diags(1.0 / row_scales, format="csc") @ problem.a_ub,
            b_ub=np.asarray(problem.b_ub, dtype=np.float64) / row_scales,
            a_eq=problem.a_eq,
            b_eq=problem.b_eq,
            bounds=problem.bounds,
            name=problem.name,
        )

    def _unscaled_residual_problem(
        self,
        reference: CompiledReference,
        polluting_indices: tuple[int, ...],
        x_polluting_o: np.ndarray,
        b_o: np.ndarray,
        g_b: np.ndarray,
        name: str,
    ) -> LinearProgram:
        if reference.bad_outputs is None:
            raise RuntimeError("compiled by-production reference lacks bad outputs")
        n_mu = reference.size
        n_variables = n_mu + 1
        polluting_reference = reference.inputs[np.asarray(polluting_indices), :]
        polluting_rows = hstack(
            [-polluting_reference, csc_matrix((x_polluting_o.size, 1))],
            format="csc",
        )
        bad_rows = hstack(
            [reference.bad_outputs, csc_matrix(g_b.reshape(-1, 1))],
            format="csc",
        )
        a_ub = vstack([polluting_rows, bad_rows], format="csc")
        b_ub = np.concatenate([-x_polluting_o, b_o])
        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_variables, n_mu, self.residual_returns_to_scale
        )
        a_ub = join_optional_rows(a_ub, rts_ub)
        b_ub = join_optional_values(b_ub, rts_b_ub)

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[-1] = -1.0
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=rts_eq,
            b_eq=rts_b_eq,
            bounds=((0.0, None),) * n_variables,
            name=f"{name}:by_production:residual",
        )

    def _residual_problem(
        self,
        reference: CompiledReference,
        polluting_indices: tuple[int, ...],
        x_polluting_o: np.ndarray,
        b_o: np.ndarray,
        g_b: np.ndarray,
        name: str,
    ) -> LinearProgram:
        """Build the residual-generation programme in stable quantity units."""
        problem = self._unscaled_residual_problem(
            reference,
            polluting_indices,
            x_polluting_o,
            b_o,
            g_b,
            name,
        )
        if reference.bad_outputs is None:
            raise RuntimeError("compiled by-production reference lacks bad outputs")
        polluting_scales = np.maximum(
            reference.input_row_max[np.asarray(polluting_indices)],
            np.abs(x_polluting_o),
        )
        polluting_scales[polluting_scales <= 0.0] = 1.0
        bad_scales = np.maximum(reference.bad_output_row_max, np.abs(b_o))
        bad_scales[bad_scales <= 0.0] = 1.0
        quantity_scales = np.concatenate([polluting_scales, bad_scales])
        extra_rows = problem.a_ub.shape[0] - quantity_scales.size
        if extra_rows < 0:
            raise RuntimeError("by-production residual row layout is invalid")
        row_scales = (
            quantity_scales
            if extra_rows == 0
            else np.concatenate(
                [quantity_scales, np.ones(extra_rows, dtype=np.float64)]
            )
        )
        return LinearProgram(
            c=problem.c,
            a_ub=diags(1.0 / row_scales, format="csc") @ problem.a_ub,
            b_ub=np.asarray(problem.b_ub, dtype=np.float64) / row_scales,
            a_eq=problem.a_eq,
            b_eq=problem.b_eq,
            bounds=problem.bounds,
            name=problem.name,
        )

    def _intended_economic_violation(
        self,
        *,
        reference: CompiledReference,
        solution: LPSolution,
        x_o: np.ndarray,
        y_o: np.ndarray,
        g_y: np.ndarray,
        primal_override: np.ndarray | None = None,
    ) -> float:
        """Rebuild the intended-production account from one solver vector."""
        primal_source = solution.primal if primal_override is None else primal_override
        if (
            primal_source is None
            or solution.objective is None
            or not math.isfinite(solution.objective)
        ):
            return math.inf
        primal = np.asarray(primal_source, dtype=np.float64).reshape(-1)
        if primal.shape != (reference.size + 1,) or not np.isfinite(primal).all():
            return math.inf
        lambdas = primal[: reference.size]
        beta = float(primal[-1])
        with np.errstate(over="ignore", invalid="ignore"):
            represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
            represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
            declared_outputs = np.asarray(y_o, dtype=np.float64) + beta * np.asarray(
                g_y,
                dtype=np.float64,
            )
        if not all(
            np.isfinite(values).all()
            for values in (
                represented_inputs,
                represented_outputs,
                declared_outputs,
            )
        ):
            return math.inf
        input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
        objective_violation = abs(float(solution.objective) + beta) / max(
            1.0,
            abs(float(solution.objective)),
            abs(beta),
        )
        violations = [
            _scaled_nonnegative_violation(lambdas),
            max(-beta, 0.0) / max(1.0, abs(beta)),
            _scaled_nonnegative_violation(represented_inputs),
            _scaled_nonnegative_violation(represented_outputs),
            _scaled_maximum(
                np.maximum(represented_inputs - x_o, 0.0),
                input_scales,
            ),
            _scaled_maximum(
                np.maximum(declared_outputs - represented_outputs, 0.0),
                output_scales,
            ),
            _rts_violation(lambdas, self.intended_returns_to_scale),
            objective_violation,
        ]
        return (
            float(max(violations)) if all(map(math.isfinite, violations)) else math.inf
        )

    def _residual_economic_violation(
        self,
        *,
        reference: CompiledReference,
        polluting_indices: tuple[int, ...],
        solution: LPSolution,
        x_polluting_o: np.ndarray,
        b_o: np.ndarray,
        g_b: np.ndarray,
        primal_override: np.ndarray | None = None,
    ) -> float:
        """Rebuild nature's residual-generation account from one solver vector."""
        primal_source = solution.primal if primal_override is None else primal_override
        if (
            primal_source is None
            or solution.objective is None
            or not math.isfinite(solution.objective)
            or reference.bad_outputs is None
        ):
            return math.inf
        primal = np.asarray(primal_source, dtype=np.float64).reshape(-1)
        if primal.shape != (reference.size + 1,) or not np.isfinite(primal).all():
            return math.inf
        intensities = primal[: reference.size]
        beta = float(primal[-1])
        polluting_reference = reference.inputs[np.asarray(polluting_indices), :]
        with np.errstate(over="ignore", invalid="ignore"):
            represented_polluting_inputs = np.asarray(
                polluting_reference @ intensities
            ).reshape(-1)
            represented_bad_outputs = np.asarray(
                reference.bad_outputs @ intensities
            ).reshape(-1)
            declared_bad_outputs = np.asarray(
                b_o, dtype=np.float64
            ) - beta * np.asarray(g_b, dtype=np.float64)
        if not all(
            np.isfinite(values).all()
            for values in (
                represented_polluting_inputs,
                represented_bad_outputs,
                declared_bad_outputs,
            )
        ):
            return math.inf
        polluting_scales = np.maximum(
            reference.input_row_max[np.asarray(polluting_indices)],
            np.abs(x_polluting_o),
        )
        polluting_scales[polluting_scales <= 0.0] = 1.0
        bad_scales = np.maximum(reference.bad_output_row_max, np.abs(b_o))
        bad_scales[bad_scales <= 0.0] = 1.0
        objective_violation = abs(float(solution.objective) + beta) / max(
            1.0,
            abs(float(solution.objective)),
            abs(beta),
        )
        violations = [
            _scaled_nonnegative_violation(intensities),
            max(-beta, 0.0) / max(1.0, abs(beta)),
            _scaled_nonnegative_violation(represented_polluting_inputs),
            _scaled_nonnegative_violation(represented_bad_outputs),
            _scaled_nonnegative_violation(declared_bad_outputs),
            _scaled_maximum(
                np.maximum(x_polluting_o - represented_polluting_inputs, 0.0),
                polluting_scales,
            ),
            _scaled_maximum(
                np.maximum(represented_bad_outputs - declared_bad_outputs, 0.0),
                bad_scales,
            ),
            _rts_violation(intensities, self.residual_returns_to_scale),
            objective_violation,
        ]
        return (
            float(max(violations)) if all(map(math.isfinite, violations)) else math.inf
        )

    def _dual_rows(
        self,
        data: DEAData,
        observation: int,
        subtechnology: str,
        solution: LPSolution,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        polluting_indices: tuple[int, ...],
    ) -> list[dict[str, Any]]:
        period = None if data.periods is None else data.periods[observation]
        common = {
            "dmu_id": data.dmu_ids[observation],
            "period": period,
            "phase": 1,
            "subtechnology": subtechnology,
        }
        if subtechnology == "intended_production":
            variables = [
                *(("input_upper", name) for name in data.input_names),
                *(("desirable_output_lower", name) for name in data.output_names),
            ]
            input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
            quantity_scales = np.concatenate([input_scales, output_scales])
            rts = self.intended_returns_to_scale
        else:
            variables = [
                *(
                    ("polluting_input_lower", name)
                    for name in data.polluting_input_names
                ),
                *(("bad_output_upper", name) for name in data.bad_output_names),
            ]
            polluting_scales = np.maximum(
                reference.input_row_max[np.asarray(polluting_indices)],
                np.abs(x_o[np.asarray(polluting_indices)]),
            )
            polluting_scales[polluting_scales <= 0.0] = 1.0
            bad_scales = np.maximum(reference.bad_output_row_max, np.abs(b_o))
            bad_scales[bad_scales <= 0.0] = 1.0
            quantity_scales = np.concatenate([polluting_scales, bad_scales])
            rts = self.residual_returns_to_scale

        expected_inequalities = len(variables) + int(
            rts in {ReturnsToScale.NIRS, ReturnsToScale.NDRS}
        )
        marginals = (
            None
            if solution.inequality_marginals is None
            else np.asarray(solution.inequality_marginals, dtype=np.float64)
        )
        if (
            marginals is None
            or marginals.shape != (expected_inequalities,)
            or not np.isfinite(marginals).all()
        ):
            return []
        if rts is ReturnsToScale.VRS:
            equality_marginals = (
                None
                if solution.equality_marginals is None
                else np.asarray(solution.equality_marginals, dtype=np.float64)
            )
            if (
                equality_marginals is None
                or equality_marginals.shape != (1,)
                or not np.isfinite(equality_marginals).all()
            ):
                return []

        rows: list[dict[str, Any]] = []
        for offset, (role, variable) in enumerate(variables):
            rows.append(
                {
                    **common,
                    "constraint_role": role,
                    "variable": variable,
                    "marginal": float(marginals[offset] / quantity_scales[offset]),
                }
            )
        if rts in {ReturnsToScale.NIRS, ReturnsToScale.NDRS}:
            rows.append(
                {
                    **common,
                    "constraint_role": "returns_to_scale",
                    "variable": rts.value,
                    "marginal": float(marginals[len(variables)]),
                }
            )
        if rts is ReturnsToScale.VRS and solution.equality_marginals is not None:
            rows.append(
                {
                    **common,
                    "constraint_role": "returns_to_scale",
                    "variable": rts.value,
                    "marginal": float(solution.equality_marginals[0]),
                }
            )
        return rows

    @staticmethod
    def _task_diagnostic(
        *,
        dmu_id: object,
        period: object | None,
        subtechnology: str,
        task: Any,
    ) -> dict[str, Any]:
        """Expose one component solve without overstating its release status."""
        row = _certificate_diagnostic(
            dmu_id=dmu_id,
            period=period,
            phase=1,
            solution=task.solution,
            certificate=task.certificate,
        )
        row["subtechnology"] = subtechnology
        if task.raw_economic_certified is not None:
            row["raw_economic_postsolve_certified"] = task.raw_economic_certified
            row["max_raw_economic_violation"] = task.raw_economic_violation
            row["economic_postsolve_certified"] = task.score_valid
            row["economic_certification_reason"] = task.economic_certification_reason
            row["max_economic_violation"] = (
                task.published_economic_violation
                if task.published_economic_certified is not None
                else task.raw_economic_violation
            )
            row["postsolve_certified"] = task.score_valid
        if task.published_economic_certified is not None:
            row["published_output_account_certified"] = (
                task.published_economic_certified
            )
            row["max_published_account_violation"] = task.published_economic_violation
        if task.score_valid:
            row["published_peer_account_certified"] = task.peer_valid
            row["max_published_peer_account_violation"] = task.peer_economic_violation
            row["certification_reason"] = "certified"
        elif task.certificate.certified:
            row["certification_reason"] = task.economic_certification_reason
        return row

    @staticmethod
    def _undefined_summary(
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        intended_task: Any,
        residual_task: Any,
        self_in_reference: bool,
    ) -> dict[str, Any]:
        """Return one fail-closed joint row while retaining component status."""
        tasks = (
            ("intended_production", intended_task),
            ("residual_generation", residual_task),
        )
        invalid_subtechnologies = tuple(
            subtechnology for subtechnology, task in tasks if not task.score_valid
        )
        _, failed_task = next(
            (
                (subtechnology, task)
                for subtechnology, task in tasks
                if task.solution.status is not SolverStatus.OPTIMAL
            ),
            next(
                (item for item in tasks if not item[1].score_valid),
                ("unknown", intended_task),
            ),
        )
        failed_subtechnology = (
            invalid_subtechnologies[0] if len(invalid_subtechnologies) == 1 else "both"
        )
        component_infeasible = any(
            task.solution.status is SolverStatus.INFEASIBLE for _, task in tasks
        )
        within_reference: bool | Any = (
            True if self_in_reference else False if component_infeasible else pd.NA
        )
        membership_status = (
            "certified_by_self_inclusion"
            if self_in_reference
            else "outside_reference_technology"
            if component_infeasible
            else "unavailable_uncertified_reference_membership"
        )
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "score_valid": False,
            "score_status": failed_task.score_status,
            "distance": np.nan,
            "is_efficient": pd.NA,
            "is_directionally_efficient": pd.NA,
            "self_in_reference": self_in_reference,
            "is_within_reference_technology": within_reference,
            "membership_status": membership_status,
            "solver_status": failed_task.solution.status.value,
            "target_valid": False,
            "target_status": "not_available_without_both_certified_components",
            "peer_valid": False,
            "peer_status": "not_available_without_both_certified_components",
            "dual_valid": False,
            "dual_status": "not_available_without_both_certified_components",
            "model_family": "by_production_directional",
            "orientation": "output",
            "intended_distance": np.nan,
            "environmental_distance": np.nan,
            "intended_score_valid": intended_task.score_valid,
            "intended_score_status": intended_task.score_status,
            "environmental_score_valid": residual_task.score_valid,
            "environmental_score_status": residual_task.score_status,
            "limiting_subtechnology": None,
            "failed_subtechnology": failed_subtechnology,
            "reference_size": reference_size,
        }

    @staticmethod
    def _direction_scope(
        output_directions: np.ndarray,
        bad_directions: np.ndarray,
    ) -> str:
        """Classify whether one direction vector is held fixed for all DMUs."""
        output_is_fixed = np.array_equal(
            output_directions,
            np.broadcast_to(output_directions[0], output_directions.shape),
        )
        bad_is_fixed = np.array_equal(
            bad_directions,
            np.broadcast_to(bad_directions[0], bad_directions.shape),
        )
        return (
            "fixed_across_observations"
            if output_is_fixed and bad_is_fixed
            else "varies_by_observation"
        )

    def _source_profile(
        self,
        data: DEAData,
        reference_kind: ReferenceKind,
        direction_scope: str,
    ) -> tuple[str, tuple[str, ...]]:
        """Identify the equation-level Murty--Russell--Levkoff profile."""
        mismatches: list[str] = []
        if self.intended_returns_to_scale is not ReturnsToScale.CRS:
            mismatches.append("intended_returns_to_scale_is_not_crs")
        if self.residual_returns_to_scale is not ReturnsToScale.CRS:
            mismatches.append("residual_returns_to_scale_is_not_crs")
        if direction_scope != "fixed_across_observations":
            mismatches.append("direction_is_not_fixed_across_observations")
        if data.is_panel:
            mismatches.append("data_are_not_one_cross_section")
        if reference_kind is not ReferenceKind.GLOBAL:
            mismatches.append("reference_is_not_the_full_self_inclusive_sample")
        profile = (
            "murty_russell_levkoff_2012_eq_4_6_4_8_5_4"
            if not mismatches
            else "deapack_configurable_by_production_ddf_extension"
        )
        return profile, tuple(mismatches)

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate BP-DDF distances and their two subtechnology components."""
        self._validate_data(data)
        if data.bad_outputs is None:
            raise RuntimeError("validated by-production data lost bad outputs")
        output_directions, output_kind = _resolve_direction(
            self.output_direction, data.outputs, data.output_names, "output"
        )
        bad_directions, bad_kind = _resolve_direction(
            self.bad_output_direction,
            data.bad_outputs,
            data.bad_output_names,
            "bad_output",
        )
        direction_scope = self._direction_scope(
            output_directions,
            bad_directions,
        )
        zero_good = np.all(output_directions <= 0.0, axis=1)
        zero_bad = np.all(bad_directions <= 0.0, axis=1)
        if zero_good.any() or zero_bad.any():
            raise ModelSpecificationError(
                "BP-DDF requires at least one positive good-output and bad-output "
                "direction for every observation; zero-direction row positions "
                f"include good={np.flatnonzero(zero_good)[:5].tolist()}, "
                f"bad={np.flatnonzero(zero_bad)[:5].tolist()}"
            )

        reference_plan = build_reference_plan(data, self.reference)
        self_membership = reference_plan.self_membership_mask()
        if all(self_membership):
            appraisal_kind = "componentwise_self_appraisal"
        elif any(self_membership):
            appraisal_kind = "componentwise_mixed_self_and_external_reference_appraisal"
        else:
            appraisal_kind = "componentwise_external_reference_appraisal"
        compiled: dict[int, CompiledReference] = {}
        polluting_indices = data.polluting_input_indices

        summary_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        dual_rows: list[dict[str, Any]] = []
        intended_solver_calls = 0
        residual_solver_calls = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                reference = compile_reference(data, reference_rows)
                compiled[set_id] = reference

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            b_o = data.bad_outputs[observation]
            x_polluting_o = x_o[np.asarray(polluting_indices)]
            g_y = output_directions[observation]
            g_b = bad_directions[observation]

            intended_problem = self._intended_problem(
                reference,
                x_o,
                y_o,
                g_y,
                name,
            )
            intended = self.solver.solve(intended_problem)
            intended_solver_calls += 1
            residual_problem = self._residual_problem(
                reference,
                polluting_indices,
                x_polluting_o,
                b_o,
                g_b,
                name,
            )
            residual = self.solver.solve(residual_problem)
            residual_solver_calls += 1

            def intended_account(
                primal_override: np.ndarray | None,
                reference_account: CompiledReference = reference,
                solution_account: LPSolution = intended,
                input_account: np.ndarray = x_o,
                output_account: np.ndarray = y_o,
                direction_account: np.ndarray = g_y,
            ) -> float:
                return self._intended_economic_violation(
                    reference=reference_account,
                    solution=solution_account,
                    x_o=input_account,
                    y_o=output_account,
                    g_y=direction_account,
                    primal_override=primal_override,
                )

            def residual_account(
                primal_override: np.ndarray | None,
                reference_account: CompiledReference = reference,
                solution_account: LPSolution = residual,
                polluting_input_account: np.ndarray = x_polluting_o,
                bad_account: np.ndarray = b_o,
                direction_account: np.ndarray = g_b,
            ) -> float:
                return self._residual_economic_violation(
                    reference=reference_account,
                    polluting_indices=polluting_indices,
                    solution=solution_account,
                    x_polluting_o=polluting_input_account,
                    b_o=bad_account,
                    g_b=direction_account,
                    primal_override=primal_override,
                )

            intended_task = _certify_environmental_distance_task(
                problem=intended_problem,
                solution=intended,
                n_lambdas=reference.size,
                account_violation=intended_account,
                tolerance=self.tolerance,
                peer_tolerance=self.peer_tolerance,
                beta_nonnegative=True,
            )
            residual_task = _certify_environmental_distance_task(
                problem=residual_problem,
                solution=residual,
                n_lambdas=reference.size,
                account_violation=residual_account,
                tolerance=self.tolerance,
                peer_tolerance=self.peer_tolerance,
                beta_nonnegative=True,
            )
            intended_diagnostic = self._task_diagnostic(
                dmu_id=dmu_id,
                period=period,
                subtechnology="intended_production",
                task=intended_task,
            )
            residual_diagnostic = self._task_diagnostic(
                dmu_id=dmu_id,
                period=period,
                subtechnology="residual_generation",
                task=residual_task,
            )
            diagnostic_rows.extend([intended_diagnostic, residual_diagnostic])

            if not intended_task.score_valid or not residual_task.score_valid:
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        intended_task=intended_task,
                        residual_task=residual_task,
                        self_in_reference=self_membership[observation],
                    )
                )
                continue

            assert intended_task.distance is not None
            assert residual_task.distance is not None
            intended_distance = intended_task.distance
            environmental_distance = residual_task.distance
            joint_distance = min(intended_distance, environmental_distance)
            efficiency = 1.0 / (1.0 + joint_distance)
            limiting = (
                "both"
                if np.isclose(
                    intended_distance,
                    environmental_distance,
                    atol=self.tolerance,
                    rtol=0.0,
                )
                else "intended_production"
                if intended_distance < environmental_distance
                else "residual_generation"
            )

            intended_dual_rows = self._dual_rows(
                data,
                observation,
                "intended_production",
                intended,
                reference,
                x_o,
                y_o,
                b_o,
                polluting_indices,
            )
            residual_dual_rows = self._dual_rows(
                data,
                observation,
                "residual_generation",
                residual,
                reference,
                x_o,
                y_o,
                b_o,
                polluting_indices,
            )
            expected_intended_duals = (
                data.n_inputs
                + data.n_outputs
                + int(self.intended_returns_to_scale is not ReturnsToScale.CRS)
            )
            expected_residual_duals = (
                len(polluting_indices)
                + data.n_bad_outputs
                + int(self.residual_returns_to_scale is not ReturnsToScale.CRS)
            )
            intended_dual_valid = len(intended_dual_rows) == expected_intended_duals
            residual_dual_valid = len(residual_dual_rows) == expected_residual_duals
            intended_diagnostic["published_dual_account_certified"] = (
                intended_dual_valid
            )
            intended_diagnostic["published_dual_row_count"] = len(intended_dual_rows)
            residual_diagnostic["published_dual_account_certified"] = (
                residual_dual_valid
            )
            residual_diagnostic["published_dual_row_count"] = len(residual_dual_rows)
            dual_valid = intended_dual_valid and residual_dual_valid
            dual_status = (
                "certified_both_subtechnologies"
                if dual_valid
                else "unavailable_incomplete_component_dual_account"
            )
            if dual_valid:
                dual_rows.extend(intended_dual_rows)
                dual_rows.extend(residual_dual_rows)

            peer_valid = intended_task.peer_valid and residual_task.peer_valid
            peer_status = (
                "certified_both_subtechnologies"
                if peer_valid
                else "unavailable_after_component_peer_reporting_threshold"
            )
            if peer_valid:
                assert intended_task.peer_lambdas is not None
                assert residual_task.peer_lambdas is not None
            for subtechnology, intensities in (
                ("intended_production", intended_task.peer_lambdas),
                ("residual_generation", residual_task.peer_lambdas),
            ):
                if not peer_valid or intensities is None:
                    continue
                for local_position, intensity in enumerate(intensities):
                    if intensity > self.peer_tolerance:
                        reference_position = reference.rows[local_position]
                        intensity_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "subtechnology": subtechnology,
                                "reference_dmu_id": data.dmu_ids[reference_position],
                                "reference_period": (
                                    None
                                    if data.periods is None
                                    else data.periods[reference_position]
                                ),
                                "lambda": float(intensity),
                            }
                        )

            for role, names, observed, direction, sign, component_distance in (
                (
                    "input",
                    data.input_names,
                    x_o,
                    np.zeros_like(x_o),
                    0.0,
                    0.0,
                ),
                (
                    "output",
                    data.output_names,
                    y_o,
                    g_y,
                    1.0,
                    intended_distance,
                ),
                (
                    "bad_output",
                    data.bad_output_names,
                    b_o,
                    g_b,
                    -1.0,
                    environmental_distance,
                ),
            ):
                for variable, value, direction_value in zip(
                    names, observed, direction, strict=True
                ):
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "observed": float(value),
                            "direction": float(direction_value),
                            "directional_change": float(
                                joint_distance * direction_value
                            ),
                            "target": float(
                                value + sign * joint_distance * direction_value
                            ),
                            "component_distance": component_distance,
                            "component_target": float(
                                value + sign * component_distance * direction_value
                            ),
                            "is_polluting_input": bool(
                                role == "input"
                                and variable in data.polluting_input_names
                            ),
                        }
                    )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": joint_distance,
                    "efficiency": efficiency,
                    "score_valid": True,
                    "score_status": "defined",
                    "distance": joint_distance,
                    "is_efficient": pd.NA,
                    "is_directionally_efficient": bool(joint_distance == 0.0),
                    "self_in_reference": self_membership[observation],
                    "is_within_reference_technology": True,
                    "membership_status": (
                        "certified_by_self_inclusion"
                        if self_membership[observation]
                        else "certified_by_componentwise_directional_accounts"
                    ),
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "target_valid": True,
                    "target_status": "certified_both_subtechnologies",
                    "peer_valid": peer_valid,
                    "peer_status": peer_status,
                    "dual_valid": dual_valid,
                    "dual_status": dual_status,
                    "model_family": "by_production_directional",
                    "orientation": "output",
                    "intended_distance": intended_distance,
                    "environmental_distance": environmental_distance,
                    "intended_score_valid": True,
                    "intended_score_status": intended_task.score_status,
                    "environmental_score_valid": True,
                    "environmental_score_status": residual_task.score_status,
                    "limiting_subtechnology": limiting,
                    "failed_subtechnology": None,
                    "reference_size": reference.size,
                }
            )

        source_profile, source_profile_mismatches = self._source_profile(
            data,
            reference_plan.kind,
            direction_scope,
        )
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            duals=pd.DataFrame(dual_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": (
                                "joint_production_and_residual_generation_appraisal"
                            ),
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {
                            "kind": "by_production",
                            "subtechnologies": "intended_and_residual",
                        },
                        "data_roles": {
                            "inputs": "productive_resources",
                            "polluting_inputs": "residual_generating_resources",
                            "outputs": "desirable_services_to_expand",
                            "bad_outputs": "undesirable_residuals_to_contract",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "intersection_of_subtechnologies",
                            "intended_returns_to_scale": (
                                self.intended_returns_to_scale.value
                            ),
                            "residual_returns_to_scale": (
                                self.residual_returns_to_scale.value
                            ),
                            "residual_disposal": "costly",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference, reference_plan.kind
                        ),
                        "performance": {
                            "family": "directional_distance",
                            "joint_aggregation": "minimum_component_distance",
                            "source_profile": source_profile,
                            "output_direction": direction_spec(
                                output_kind,
                                output_directions,
                                data.output_names,
                            ),
                            "bad_output_direction": direction_spec(
                                bad_kind,
                                bad_directions,
                                data.bad_output_names,
                            ),
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {"kind": appraisal_kind},
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "by_production_directional",
                "variant": "bp_ddf",
                "orientation": "output",
                "technology": "intersection_of_subtechnologies",
                "intended_subtechnology": "X lambda <= x; Y lambda >= y",
                "residual_subtechnology": "X_p mu >= x_p; B mu <= b",
                "intended_returns_to_scale": (self.intended_returns_to_scale.value),
                "residual_returns_to_scale": (self.residual_returns_to_scale.value),
                "reference_kind": reference_plan.kind.value,
                "polluting_inputs": data.polluting_input_names,
                "output_direction_kind": output_kind,
                "bad_output_direction_kind": bad_kind,
                "direction_scope": direction_scope,
                "native_score": "joint_beta",
                "score_direction": "higher_is_farther",
                "score_ordering": "lower_is_better",
                "joint_aggregation": "minimum_of_component_distances",
                "efficiency_transform": "one_over_one_plus_distance",
                "efficiency_transform_source": "deapack_display_only",
                "classification_domain": (
                    "evaluated_plan_within_both_reference_subtechnologies"
                ),
                "source_profile": source_profile,
                "source_profile_matches": not source_profile_mismatches,
                "source_profile_mismatches": source_profile_mismatches,
                "source_interpretive_caveat": (
                    "the_defining_source_uses_bp_ddf_as_a_criticized_"
                    "conventional_index_not_as_its_proposed_preferred_measure"
                ),
                "strong_efficiency_rule": (
                    "not_certified_without_joint_slack_completion"
                ),
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "planned_reference_sets": reference_plan.unique_reference_sets,
                "compiled_reference_sets": len(compiled),
                "intended_solver_calls": intended_solver_calls,
                "residual_solver_calls": residual_solver_calls,
                "solver_calls": intended_solver_calls + residual_solver_calls,
                "additional_solver_calls": 0,
                "postsolve_certificate": {
                    "component_lp": (
                        "solver_neutral_primal_dual_kkt_and_strong_duality"
                    ),
                    "component_economic": (
                        "raw_and_published_intended_and_residual_production_"
                        "accounts_objectives_and_rts"
                    ),
                    "component_row_scaling": (
                        "input_output_polluting_input_and_bad_output_accounts"
                    ),
                    "joint_release": (
                        "both_component_scores_required_before_minimum_aggregation"
                    ),
                    "target_release": "both_component_accounts_certified",
                    "peer_release": ("both_thresholded_component_accounts_certified"),
                    "dual_release": (
                        "both_complete_finite_original_unit_component_accounts"
                    ),
                    "failure_policy": (
                        "withhold_joint_score_targets_peers_and_duals_when_a_"
                        "required_component_fails"
                    ),
                    "additional_solver_calls": 0,
                },
            },
        )


ByProductionDDF = ByProductionDirectionalDistanceDEA
"""Discoverability alias for :class:`ByProductionDirectionalDistanceDEA`."""
