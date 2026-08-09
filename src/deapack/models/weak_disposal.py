"""Activity-specific weak disposal for undesirable-output technologies."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, eye, hstack, vstack

from .._registry import data_role_schema, direction_spec, registry_metadata
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import SolverStatus
from ..exceptions import ModelSpecificationError
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
from ._common import CompiledReference, clean_small, compile_reference
from ._radial_lp import radial_row_scales
from .directional import DirectionInput, _resolve_direction


def _activity_specific_row_scales(
    reference: CompiledReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
    b_o: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return positive physical-account scales for both programme phases."""
    input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
    bad_output_scales = np.maximum(reference.bad_output_row_max, np.abs(b_o))
    bad_output_scales[bad_output_scales <= 0.0] = 1.0
    return input_scales, output_scales, bad_output_scales


def _scaled_maximum(residual: np.ndarray, scale: np.ndarray) -> float:
    """Return the largest finite absolute residual relative to its account."""
    values = np.asarray(residual, dtype=np.float64).reshape(-1)
    account_scale = np.asarray(scale, dtype=np.float64).reshape(-1)
    if (
        values.shape != account_scale.shape
        or not np.isfinite(values).all()
        or not np.isfinite(account_scale).all()
        or np.any(account_scale <= 0.0)
    ):
        return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        ratios = np.abs(values) / account_scale
    return float(ratios.max(initial=0.0)) if np.isfinite(ratios).all() else math.inf


def _scaled_nonnegative_violation(values: np.ndarray) -> float:
    """Return a scale-free violation of a declared nonnegative account."""
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if not np.isfinite(array).all():
        return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        violation = np.maximum(-array, 0.0) / np.maximum(1.0, np.abs(array))
    return (
        float(violation.max(initial=0.0)) if np.isfinite(violation).all() else math.inf
    )


def _certificate_diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    phase: int,
    solution: LPSolution,
    certificate: LPCertificate,
) -> dict[str, Any]:
    """Return one auditable solver and postsolve-certificate record."""
    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": phase,
        "solver_status": solution.status.value,
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


class ActivitySpecificWeakDisposalDDF:
    r"""Estimate a VRS environmental DDF with activity-specific abatement.

    This class implements the linear activity-specific weak-disposal
    technology introduced by Kuosmanen (2005).  For every observed reference
    activity, ``mu`` records the part that remains active in desirable and
    undesirable output production, while ``tau`` records the complementary
    weak-disposal part.  Inputs support both parts.  The VRS normalization is
    therefore imposed on ``mu + tau``, not on ``mu`` alone.

    For an evaluated observation :math:`(x_o,y_o,b_o)`, phase one maximizes
    :math:`\beta` subject to

    $$
    \begin{aligned}
    X(\mu+\tau)+\beta g_x &\leq x_o,\\
    -Y\mu+\beta g_y &\leq -y_o,\\
    B\mu+\beta g_b &= b_o,\\
    \mathbf{1}'(\mu+\tau)&=1.
    \end{aligned}
    $$

    with nonnegative ``mu`` and ``tau``.  Phase two fixes the certified
    directional distance and maximizes only permissible input and desirable
    output slacks.  Undesirable output remains an equality and has no slack.

    ``tau`` is a mathematical activity component.  It must not be interpreted
    as an observed monetary, energy, or physical abatement cost.
    """

    _registry_method_id = "environmental.ddf.weak_disposal.activity_specific"
    _technology_id = "environmental.weak_disposal.activity_specific.vrs.kuosmanen_2005"

    def __init__(
        self,
        *,
        input_direction: DirectionInput = "zeros",
        output_direction: DirectionInput = "observed",
        bad_output_direction: DirectionInput = "observed",
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        compute_slacks: bool = True,
        allow_negative_distance: bool = False,
        null_jointness: bool = False,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.input_direction = input_direction
        self.output_direction = output_direction
        self.bad_output_direction = bad_output_direction
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
        self.compute_slacks = bool(compute_slacks)
        self.allow_negative_distance = bool(allow_negative_distance)
        self.null_jointness = bool(null_jointness)
        if not math.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("tolerance must be positive and finite")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not math.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0.0:
            raise ValueError("peer_tolerance must be positive and finite")

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is None:
            raise ModelSpecificationError(
                "ActivitySpecificWeakDisposalDDF requires declared bad_outputs "
                "in DEAData"
            )
        if self.null_jointness:
            # Null jointness is a physical-data restriction, not a solver
            # postsolve decision.  Exact declared zeros must therefore not
            # change meaning when the numerical certificate tolerance changes.
            positive_good = data.outputs.sum(axis=1) > 0.0
            zero_bad = data.bad_outputs.sum(axis=1) == 0.0
            invalid = positive_good & zero_bad
            if invalid.any():
                positions = np.flatnonzero(invalid)[:5].tolist()
                raise ModelSpecificationError(
                    "null jointness requires zero bad output to imply zero "
                    "desirable output; invalid row positions include "
                    f"{positions}"
                )

    def _phase_one_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        name: str,
    ) -> LinearProgram:
        """Build a row-scaled VRS ``(mu, tau, beta)`` linearization."""
        if reference.bad_outputs is None:
            raise RuntimeError("compiled weak-disposal reference lacks bad outputs")

        n = reference.size
        n_variables = 2 * n + 1
        beta_column = -1
        input_scales, output_scales, bad_scales = _activity_specific_row_scales(
            reference,
            x_o,
            y_o,
            b_o,
        )
        input_scaling = diags(1.0 / input_scales, format="csc")
        output_scaling = diags(1.0 / output_scales, format="csc")
        bad_scaling = diags(1.0 / bad_scales, format="csc")
        input_rows = hstack(
            [
                input_scaling @ reference.inputs,
                input_scaling @ reference.inputs,
                csc_matrix((g_x / input_scales).reshape(-1, 1)),
            ],
            format="csc",
        )
        output_rows = hstack(
            [
                -(output_scaling @ reference.outputs),
                csc_matrix((y_o.size, n)),
                csc_matrix((g_y / output_scales).reshape(-1, 1)),
            ],
            format="csc",
        )
        a_ub = vstack([input_rows, output_rows], format="csc")
        b_ub = np.concatenate([x_o / input_scales, -y_o / output_scales])

        bad_rows = hstack(
            [
                bad_scaling @ reference.bad_outputs,
                csc_matrix((b_o.size, n)),
                csc_matrix((g_b / bad_scales).reshape(-1, 1)),
            ],
            format="csc",
        )
        convexity = np.zeros((1, n_variables), dtype=np.float64)
        convexity[0, : 2 * n] = 1.0
        a_eq = vstack([bad_rows, csc_matrix(convexity)], format="csc")
        b_eq = np.concatenate([b_o / bad_scales, np.asarray([1.0])])

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[beta_column] = -1.0
        beta_bounds = (None, None) if self.allow_negative_distance else (0.0, None)
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=a_eq,
            b_eq=b_eq,
            bounds=((0.0, None),) * (2 * n) + (beta_bounds,),
            name=f"{name}:activity_specific_weak_disposal",
        )

    @staticmethod
    def _reference_membership_problem(
        phase_one_problem: LinearProgram,
    ) -> LinearProgram:
        """Fix beta at zero to test the assessed plan itself.

        A positive activity-specific DDF can be supported by a feasible
        positive-beta interval even when beta zero violates the bad-output
        equality and total-activity convexity.  The scaled primary rows are
        therefore reused in one explicit external-reference feasibility LP.
        """
        if not phase_one_problem.bounds:
            raise RuntimeError("activity-specific membership requires beta bounds")
        return LinearProgram(
            c=np.zeros_like(phase_one_problem.c),
            a_ub=phase_one_problem.a_ub,
            b_ub=phase_one_problem.b_ub,
            a_eq=phase_one_problem.a_eq,
            b_eq=phase_one_problem.b_eq,
            bounds=(*phase_one_problem.bounds[:-1], (0.0, 0.0)),
            name=f"{phase_one_problem.name}:reference_membership",
        )

    def _phase_two_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        beta: float,
        name: str,
    ) -> LinearProgram:
        """Fix ``beta`` and maximize row-scaled permissible slacks."""
        if reference.bad_outputs is None:
            raise RuntimeError("compiled weak-disposal reference lacks bad outputs")

        n = reference.size
        m = x_o.size
        s = y_o.size
        q = b_o.size
        n_variables = 2 * n + m + s
        input_scales, output_scales, bad_scales = _activity_specific_row_scales(
            reference,
            x_o,
            y_o,
            b_o,
        )

        input_rows = hstack(
            [
                diags(1.0 / input_scales, format="csc") @ reference.inputs,
                diags(1.0 / input_scales, format="csc") @ reference.inputs,
                eye(m, format="csc"),
                csc_matrix((m, s)),
            ],
            format="csc",
        )
        output_rows = hstack(
            [
                diags(1.0 / output_scales, format="csc") @ reference.outputs,
                csc_matrix((s, n + m)),
                -eye(s, format="csc"),
            ],
            format="csc",
        )
        bad_rows = hstack(
            [
                diags(1.0 / bad_scales, format="csc") @ reference.bad_outputs,
                csc_matrix((q, n + m + s)),
            ],
            format="csc",
        )
        convexity = np.zeros((1, n_variables), dtype=np.float64)
        convexity[0, : 2 * n] = 1.0
        a_eq = vstack(
            [input_rows, output_rows, bad_rows, csc_matrix(convexity)],
            format="csc",
        )
        b_eq = np.concatenate(
            [
                (x_o - beta * g_x) / input_scales,
                (y_o + beta * g_y) / output_scales,
                (b_o - beta * g_b) / bad_scales,
                np.asarray([1.0]),
            ]
        )

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[2 * n :] = -1.0
        return LinearProgram(
            c=objective,
            a_ub=None,
            b_ub=None,
            a_eq=a_eq,
            b_eq=b_eq,
            bounds=((0.0, None),) * n_variables,
            name=f"{name}:activity_specific_weak_disposal_slacks",
        )

    def _primary_economic_violation(
        self,
        *,
        reference: CompiledReference,
        solution: LPSolution,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        primal_override: np.ndarray | None = None,
    ) -> float:
        """Reconstruct the physical phase-one production account."""
        primal_source = solution.primal if primal_override is None else primal_override
        if (
            primal_source is None
            or solution.objective is None
            or not math.isfinite(solution.objective)
            or reference.bad_outputs is None
        ):
            return math.inf
        primal = np.asarray(primal_source, dtype=np.float64).reshape(-1)
        n = reference.size
        if primal.shape != (2 * n + 1,) or not np.isfinite(primal).all():
            return math.inf
        mu = primal[:n]
        tau = primal[n : 2 * n]
        beta = float(primal[-1])
        if not math.isfinite(beta):
            return math.inf

        with np.errstate(over="ignore", invalid="ignore"):
            total = mu + tau
            represented_inputs = np.asarray(reference.inputs @ total).reshape(-1)
            represented_outputs = np.asarray(reference.outputs @ mu).reshape(-1)
            represented_bad = np.asarray(reference.bad_outputs @ mu).reshape(-1)
            declared_inputs = np.asarray(x_o, dtype=np.float64) - beta * np.asarray(
                g_x,
                dtype=np.float64,
            )
            declared_outputs = np.asarray(y_o, dtype=np.float64) + beta * np.asarray(
                g_y,
                dtype=np.float64,
            )
            declared_bad = np.asarray(b_o, dtype=np.float64) - beta * np.asarray(
                g_b,
                dtype=np.float64,
            )
        if not all(
            np.isfinite(values).all()
            for values in (
                total,
                represented_inputs,
                represented_outputs,
                represented_bad,
                declared_inputs,
                declared_outputs,
                declared_bad,
            )
        ):
            return math.inf
        input_scales, output_scales, bad_scales = _activity_specific_row_scales(
            reference,
            x_o,
            y_o,
            b_o,
        )
        total_sum = float(total.sum())
        violations = [
            _scaled_nonnegative_violation(mu),
            _scaled_nonnegative_violation(tau),
            _scaled_maximum(
                np.maximum(represented_inputs - declared_inputs, 0.0),
                input_scales,
            ),
            _scaled_maximum(
                np.maximum(declared_outputs - represented_outputs, 0.0),
                output_scales,
            ),
            _scaled_maximum(represented_bad - declared_bad, bad_scales),
            abs(total_sum - 1.0) / max(1.0, abs(total_sum)),
            abs(float(solution.objective) + beta)
            / max(1.0, abs(float(solution.objective)), abs(beta)),
        ]
        if not self.allow_negative_distance:
            violations.append(max(-beta, 0.0) / max(1.0, abs(beta)))
        return (
            float(max(violations))
            if all(math.isfinite(value) for value in violations)
            else math.inf
        )

    def _completion_economic_violation(
        self,
        *,
        reference: CompiledReference,
        solution: LPSolution,
        beta: float,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        primal_override: np.ndarray | None = None,
    ) -> float:
        """Reconstruct phase two in physical units from scaled slack variables."""
        primal_source = solution.primal if primal_override is None else primal_override
        if (
            primal_source is None
            or solution.objective is None
            or not math.isfinite(solution.objective)
            or not math.isfinite(beta)
            or reference.bad_outputs is None
        ):
            return math.inf
        primal = np.asarray(primal_source, dtype=np.float64).reshape(-1)
        n = reference.size
        expected_size = 2 * n + x_o.size + y_o.size
        if primal.shape != (expected_size,) or not np.isfinite(primal).all():
            return math.inf
        offset = 0
        mu = primal[offset : offset + n]
        offset += n
        tau = primal[offset : offset + n]
        offset += n
        scaled_input_slacks = primal[offset : offset + x_o.size]
        offset += x_o.size
        scaled_output_slacks = primal[offset : offset + y_o.size]

        input_scales, output_scales, bad_scales = _activity_specific_row_scales(
            reference,
            x_o,
            y_o,
            b_o,
        )
        input_slacks = scaled_input_slacks * input_scales
        output_slacks = scaled_output_slacks * output_scales
        with np.errstate(over="ignore", invalid="ignore"):
            total = mu + tau
            represented_inputs = np.asarray(reference.inputs @ total).reshape(-1)
            represented_outputs = np.asarray(reference.outputs @ mu).reshape(-1)
            represented_bad = np.asarray(reference.bad_outputs @ mu).reshape(-1)
            declared_inputs = x_o - beta * g_x
            declared_outputs = y_o + beta * g_y
            declared_bad = b_o - beta * g_b
        arrays = (
            total,
            input_slacks,
            output_slacks,
            represented_inputs,
            represented_outputs,
            represented_bad,
            declared_inputs,
            declared_outputs,
            declared_bad,
        )
        if not all(np.isfinite(values).all() for values in arrays):
            return math.inf
        total_sum = float(total.sum())
        reconstructed_objective = -float(
            scaled_input_slacks.sum() + scaled_output_slacks.sum()
        )
        violations = [
            _scaled_nonnegative_violation(mu),
            _scaled_nonnegative_violation(tau),
            _scaled_nonnegative_violation(scaled_input_slacks),
            _scaled_nonnegative_violation(scaled_output_slacks),
            _scaled_maximum(
                represented_inputs + input_slacks - declared_inputs,
                input_scales,
            ),
            _scaled_maximum(
                represented_outputs - output_slacks - declared_outputs,
                output_scales,
            ),
            _scaled_maximum(represented_bad - declared_bad, bad_scales),
            abs(total_sum - 1.0) / max(1.0, abs(total_sum)),
            abs(reconstructed_objective - float(solution.objective))
            / max(
                1.0,
                abs(reconstructed_objective),
                abs(float(solution.objective)),
            ),
        ]
        return (
            float(max(violations))
            if all(math.isfinite(value) for value in violations)
            else math.inf
        )

    def _clean_primary_primal(
        self,
        primal: np.ndarray,
        n: int,
    ) -> np.ndarray:
        """Create the only phase-one vector eligible for publication."""
        published = clean_small(np.asarray(primal, dtype=np.float64), self.tolerance)
        published[: 2 * n] = np.maximum(published[: 2 * n], 0.0)
        if not self.allow_negative_distance:
            published[-1] = max(float(published[-1]), 0.0)
        return published

    def _threshold_activity_primal(
        self,
        primal: np.ndarray,
        n: int,
    ) -> np.ndarray:
        """Threshold whole reference activities before peer publication."""
        peer_primal = np.asarray(primal, dtype=np.float64).copy()
        totals = peer_primal[:n] + peer_primal[n : 2 * n]
        inactive = totals <= self.peer_tolerance
        peer_primal[:n][inactive] = 0.0
        peer_primal[n : 2 * n][inactive] = 0.0
        return peer_primal

    def _undefined_summary(
        self,
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        solver_status: SolverStatus,
        score_status: str,
        self_in_reference: bool,
    ) -> dict[str, Any]:
        """Return a fail-closed row for an uncertified primary programme."""
        within_reference: bool | Any = (
            True
            if self_in_reference
            else False
            if solver_status is SolverStatus.INFEASIBLE
            else pd.NA
        )
        membership_status = (
            "certified_by_self_inclusion"
            if self_in_reference
            else "outside_reference_technology"
            if solver_status is SolverStatus.INFEASIBLE
            else "not_available_without_certified_primary"
        )
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "score_valid": False,
            "score_status": score_status,
            "distance": np.nan,
            "is_efficient": pd.NA,
            "is_directionally_efficient": pd.NA,
            "is_within_reference_technology": within_reference,
            "self_in_reference": self_in_reference,
            "membership_status": membership_status,
            "solver_status": solver_status.value,
            "completion_solver_status": pd.NA,
            "completion_valid": False,
            "completion_status": "not_available_without_certified_primary",
            "target_valid": False,
            "target_status": "not_available_without_certified_primary",
            "peer_valid": False,
            "peer_status": "not_available_without_certified_primary",
            "dual_valid": False,
            "dual_status": "not_available_without_certified_primary",
            "model_family": "activity_specific_weak_disposal_ddf",
            "orientation": "environmental_directional",
            "returns_to_scale": "vrs",
            "bad_output_disposability": "weak_activity_specific",
            "compatibility_alias": None,
            "null_jointness": self.null_jointness,
            "reference_size": reference_size,
            "max_slack": np.nan,
            "max_scaled_slack": np.nan,
            "efficiency_denominator_valid": (
                within_reference if isinstance(within_reference, bool) else pd.NA
            ),
        }

    def _dual_rows(
        self,
        data: DEAData,
        observation: int,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        solution: LPSolution,
    ) -> list[dict[str, Any]]:
        """Return a complete finite phase-one dual account in original units."""
        expected_inequalities = data.n_inputs + data.n_outputs
        expected_equalities = data.n_bad_outputs + 1
        if solution.inequality_marginals is None:
            return []
        inequality_marginals = np.asarray(
            solution.inequality_marginals,
            dtype=np.float64,
        )
        equality_marginals = (
            None
            if solution.equality_marginals is None
            else np.asarray(solution.equality_marginals, dtype=np.float64)
        )
        if (
            inequality_marginals.shape != (expected_inequalities,)
            or not np.isfinite(inequality_marginals).all()
            or equality_marginals is None
            or equality_marginals.shape != (expected_equalities,)
            or not np.isfinite(equality_marginals).all()
        ):
            return []

        period = None if data.periods is None else data.periods[observation]
        common = {"dmu_id": data.dmu_ids[observation], "period": period, "phase": 1}
        rows: list[dict[str, Any]] = []
        input_scales, output_scales, bad_scales = _activity_specific_row_scales(
            reference,
            x_o,
            y_o,
            b_o,
        )

        def original_unit_marginal(value: float, scale: float) -> float:
            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                return float(value / scale)

        inequality_offset = 0
        for role, names, scales in (
            ("input", data.input_names, input_scales),
            ("output", data.output_names, output_scales),
        ):
            for variable, scale in zip(names, scales, strict=True):
                rows.append(
                    {
                        **common,
                        "constraint_role": role,
                        "variable": variable,
                        "marginal": original_unit_marginal(
                            inequality_marginals[inequality_offset],
                            scale,
                        ),
                    }
                )
                inequality_offset += 1
        equality_offset = 0
        for variable, scale in zip(
            data.bad_output_names,
            bad_scales,
            strict=True,
        ):
            rows.append(
                {
                    **common,
                    "constraint_role": "bad_output_equality",
                    "variable": variable,
                    "marginal": original_unit_marginal(
                        equality_marginals[equality_offset],
                        scale,
                    ),
                }
            )
            equality_offset += 1
        rows.append(
            {
                **common,
                "constraint_role": "vrs_convexity",
                "variable": "sum_mu_plus_tau",
                "marginal": float(equality_marginals[equality_offset]),
            }
        )
        return (
            rows if all(math.isfinite(float(row["marginal"])) for row in rows) else []
        )

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate activity-specific weak-disposal distances."""
        self._validate_data(data)
        if data.bad_outputs is None:
            raise RuntimeError("validated weak-disposal data lost bad outputs")

        input_directions, input_direction_kind = _resolve_direction(
            self.input_direction,
            data.inputs,
            data.input_names,
            "input",
        )
        output_directions, output_direction_kind = _resolve_direction(
            self.output_direction,
            data.outputs,
            data.output_names,
            "output",
        )
        bad_directions, bad_direction_kind = _resolve_direction(
            self.bad_output_direction,
            data.bad_outputs,
            data.bad_output_names,
            "bad_output",
        )
        zero_direction = (
            input_directions.sum(axis=1)
            + output_directions.sum(axis=1)
            + bad_directions.sum(axis=1)
        ) <= 0
        if zero_direction.any():
            positions = np.flatnonzero(zero_direction)[:5].tolist()
            raise ModelSpecificationError(
                "each evaluated observation needs at least one positive direction "
                f"component; zero-direction row positions include {positions}"
            )

        reference_plan = build_reference_plan(data, self.reference)
        self_membership = reference_plan.self_membership_mask()
        if all(self_membership):
            appraisal_kind = "self_appraisal"
        elif any(self_membership):
            appraisal_kind = "mixed_self_and_external_reference_appraisal"
        else:
            appraisal_kind = "external_reference_appraisal"
        compiled: dict[int, CompiledReference] = {}
        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        dual_rows: list[dict[str, Any]] = []
        phase_one_solver_calls = 0
        phase_two_solver_calls = 0
        membership_solver_calls = 0

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
            g_x = input_directions[observation]
            g_y = output_directions[observation]
            g_b = bad_directions[observation]

            phase_one_problem = self._phase_one_problem(
                reference,
                x_o,
                y_o,
                b_o,
                g_x,
                g_y,
                g_b,
                name,
            )
            phase_one = self.solver.solve(phase_one_problem)
            phase_one_solver_calls += 1
            primary_certificate = certify_lp_solution(
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
                    certificate=primary_certificate,
                )
            )
            primary_published_primal: np.ndarray | None = None
            primary_score_valid = False
            primary_raw_violation = math.nan
            primary_published_violation = math.nan
            economic_reason = "not_checked_uncertified_source_program"
            if primary_certificate.certified and phase_one.primal is not None:
                primary_raw_violation = self._primary_economic_violation(
                    reference=reference,
                    solution=phase_one,
                    x_o=x_o,
                    y_o=y_o,
                    b_o=b_o,
                    g_x=g_x,
                    g_y=g_y,
                    g_b=g_b,
                )
                raw_economic_certified = bool(
                    math.isfinite(primary_raw_violation)
                    and primary_raw_violation <= 10.0 * self.tolerance
                )
                diagnostic_rows[-1]["raw_economic_postsolve_certified"] = (
                    raw_economic_certified
                )
                diagnostic_rows[-1]["max_raw_economic_violation"] = (
                    primary_raw_violation
                )
                if raw_economic_certified:
                    primary_published_primal = self._clean_primary_primal(
                        phase_one.primal,
                        reference.size,
                    )
                    primary_published_violation = self._primary_economic_violation(
                        reference=reference,
                        solution=phase_one,
                        x_o=x_o,
                        y_o=y_o,
                        b_o=b_o,
                        g_x=g_x,
                        g_y=g_y,
                        g_b=g_b,
                        primal_override=primary_published_primal,
                    )
                    primary_score_valid = bool(
                        math.isfinite(primary_published_violation)
                        and primary_published_violation <= 10.0 * self.tolerance
                    )
                    economic_reason = (
                        "certified"
                        if primary_score_valid
                        else "published_activity_specific_account_reconstruction_failed"
                    )
                else:
                    economic_reason = "activity_specific_program_reconstruction_failed"
                diagnostic_rows[-1]["published_output_account_certified"] = (
                    primary_score_valid
                )
                diagnostic_rows[-1]["max_published_account_violation"] = (
                    primary_published_violation
                )
                diagnostic_rows[-1]["economic_postsolve_certified"] = (
                    primary_score_valid
                )
                diagnostic_rows[-1]["economic_certification_reason"] = economic_reason
                diagnostic_rows[-1]["max_economic_violation"] = (
                    primary_published_violation
                    if raw_economic_certified
                    else primary_raw_violation
                )
                diagnostic_rows[-1]["postsolve_certified"] = primary_score_valid
                diagnostic_rows[-1]["certification_reason"] = economic_reason

            if not primary_score_valid or primary_published_primal is None:
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        solver_status=phase_one.status,
                        score_status=(
                            "solver_failed"
                            if phase_one.status is not SolverStatus.OPTIMAL
                            else "unavailable_uncertified_primary_program"
                        ),
                        self_in_reference=bool(self_membership[observation]),
                    )
                )
                continue

            n = reference.size
            beta = float(primary_published_primal[-1])
            diagnostic_rows[-1]["certification_reason"] = "certified"

            primary_peer_primal = self._threshold_activity_primal(
                primary_published_primal,
                n,
            )
            primary_peer_violation = self._primary_economic_violation(
                reference=reference,
                solution=phase_one,
                x_o=x_o,
                y_o=y_o,
                b_o=b_o,
                g_x=g_x,
                g_y=g_y,
                g_b=g_b,
                primal_override=primary_peer_primal,
            )
            primary_peer_valid = bool(
                math.isfinite(primary_peer_violation)
                and primary_peer_violation <= 10.0 * self.tolerance
            )
            primary_peer_status = (
                "certified_primary_program"
                if primary_peer_valid
                else "unavailable_after_peer_reporting_threshold"
            )
            diagnostic_rows[-1]["published_peer_account_certified"] = primary_peer_valid
            diagnostic_rows[-1]["max_published_peer_account_violation"] = (
                primary_peer_violation
            )

            primary_dual_rows = self._dual_rows(
                data,
                observation,
                reference,
                x_o,
                y_o,
                b_o,
                phase_one,
            )
            expected_dual_rows = data.n_inputs + data.n_outputs + data.n_bad_outputs + 1
            primary_dual_valid = len(primary_dual_rows) == expected_dual_rows
            primary_dual_status = (
                "certified_primary_program"
                if primary_dual_valid
                else "unavailable_incomplete_primary_dual_account"
            )
            diagnostic_rows[-1]["published_dual_account_certified"] = primary_dual_valid
            diagnostic_rows[-1]["published_dual_row_count"] = len(primary_dual_rows)
            if primary_dual_valid:
                dual_rows.extend(primary_dual_rows)

            self_in_reference = bool(self_membership[observation])
            within_reference: bool | Any
            membership_status: str
            if self_in_reference:
                within_reference = True
                membership_status = "certified_by_self_inclusion"
            elif beta < 0.0:
                within_reference = False
                membership_status = "outside_reference_technology"
            else:
                membership_problem = self._reference_membership_problem(
                    phase_one_problem
                )
                membership_solution = self.solver.solve(membership_problem)
                membership_solver_calls += 1
                membership_certificate = certify_lp_solution(
                    membership_problem,
                    membership_solution,
                    tolerance=self.tolerance,
                )
                membership_diagnostic = _certificate_diagnostic(
                    dmu_id=dmu_id,
                    period=period,
                    phase=0,
                    solution=membership_solution,
                    certificate=membership_certificate,
                )
                membership_diagnostic["diagnostic_kind"] = "reference_membership"
                membership_raw_violation = math.nan
                membership_published_violation = math.nan
                membership_raw_certified: bool | None = None
                if membership_solution.status is SolverStatus.INFEASIBLE:
                    within_reference = False
                    membership_status = "outside_reference_technology"
                    membership_diagnostic["certification_reason"] = (
                        "infeasible_reference_membership_program"
                    )
                elif (
                    membership_certificate.certified
                    and membership_solution.primal is not None
                ):
                    membership_raw_violation = self._primary_economic_violation(
                        reference=reference,
                        solution=membership_solution,
                        x_o=x_o,
                        y_o=y_o,
                        b_o=b_o,
                        g_x=g_x,
                        g_y=g_y,
                        g_b=g_b,
                    )
                    membership_raw_certified = bool(
                        math.isfinite(membership_raw_violation)
                        and membership_raw_violation <= 10.0 * self.tolerance
                    )
                    membership_diagnostic["raw_economic_postsolve_certified"] = (
                        membership_raw_certified
                    )
                    membership_diagnostic["max_raw_economic_violation"] = (
                        membership_raw_violation
                    )
                    if membership_raw_certified:
                        membership_primal = self._clean_primary_primal(
                            membership_solution.primal,
                            reference.size,
                        )
                        membership_primal[-1] = 0.0
                        membership_published_violation = (
                            self._primary_economic_violation(
                                reference=reference,
                                solution=membership_solution,
                                x_o=x_o,
                                y_o=y_o,
                                b_o=b_o,
                                g_x=g_x,
                                g_y=g_y,
                                g_b=g_b,
                                primal_override=membership_primal,
                            )
                        )
                    else:
                        membership_published_violation = math.inf
                    membership_certified = bool(
                        math.isfinite(membership_published_violation)
                        and membership_published_violation <= 10.0 * self.tolerance
                    )
                    within_reference = True if membership_certified else pd.NA
                    membership_status = (
                        "certified_by_reference_membership_program"
                        if membership_certified
                        else "unavailable_uncertified_reference_membership"
                    )
                    membership_diagnostic["published_output_account_certified"] = (
                        membership_certified
                    )
                    membership_diagnostic["max_published_account_violation"] = (
                        membership_published_violation
                    )
                    membership_diagnostic["economic_postsolve_certified"] = (
                        membership_certified
                    )
                    membership_diagnostic["postsolve_certified"] = membership_certified
                    membership_diagnostic["economic_certification_reason"] = (
                        "certified"
                        if membership_certified
                        else (
                            "published_reference_membership_account_"
                            "reconstruction_failed"
                            if membership_raw_certified
                            else "reference_membership_account_reconstruction_failed"
                        )
                    )
                    membership_diagnostic["certification_reason"] = (
                        membership_diagnostic["economic_certification_reason"]
                    )
                else:
                    within_reference = pd.NA
                    membership_status = "unavailable_uncertified_reference_membership"
                membership_diagnostic["max_economic_violation"] = (
                    membership_published_violation
                    if membership_raw_certified is True
                    else membership_raw_violation
                )
                diagnostic_rows.append(membership_diagnostic)

            efficiency_denominator_valid: bool | Any = (
                within_reference if isinstance(within_reference, bool) else pd.NA
            )
            efficiency = 1.0 / (1.0 + beta) if within_reference is True else np.nan
            is_directionally_efficient: bool | Any = (
                bool(beta == 0.0) if within_reference is True else pd.NA
            )

            phase_two: LPSolution | None = None
            completion_solver_status: object = pd.NA
            completion_valid: bool | Any = pd.NA
            completion_status = "not_requested"
            target_valid: bool | Any = pd.NA
            target_status = "not_requested"
            peer_valid = primary_peer_valid
            peer_status = primary_peer_status
            dual_valid = primary_dual_valid
            dual_status = primary_dual_status
            activity_primal = primary_peer_primal if primary_peer_valid else None
            phase_two_published_primal: np.ndarray | None = None
            if self.compute_slacks:
                phase_two_problem = self._phase_two_problem(
                    reference,
                    x_o,
                    y_o,
                    b_o,
                    g_x,
                    g_y,
                    g_b,
                    beta,
                    name,
                )
                phase_two = self.solver.solve(phase_two_problem)
                phase_two_solver_calls += 1
                completion_certificate = certify_lp_solution(
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
                        certificate=completion_certificate,
                    )
                )
                completion_solver_status = phase_two.status.value
                completion_valid = False
                target_valid = False
                peer_valid = False
                activity_primal = None
                completion_status = (
                    "completion_solver_failed"
                    if phase_two.status is not SolverStatus.OPTIMAL
                    else "unavailable_uncertified_slack_completion"
                )
                target_status = completion_status
                peer_status = completion_status
                if completion_certificate.certified and phase_two.primal is not None:
                    raw_completion_violation = self._completion_economic_violation(
                        reference=reference,
                        solution=phase_two,
                        beta=beta,
                        x_o=x_o,
                        y_o=y_o,
                        b_o=b_o,
                        g_x=g_x,
                        g_y=g_y,
                        g_b=g_b,
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
                    if raw_completion_certified:
                        phase_two_published_primal = clean_small(
                            np.asarray(phase_two.primal, dtype=np.float64),
                            self.tolerance,
                        )
                        phase_two_published_primal = np.maximum(
                            phase_two_published_primal,
                            0.0,
                        )
                        published_completion_violation = (
                            self._completion_economic_violation(
                                reference=reference,
                                solution=phase_two,
                                beta=beta,
                                x_o=x_o,
                                y_o=y_o,
                                b_o=b_o,
                                g_x=g_x,
                                g_y=g_y,
                                g_b=g_b,
                                primal_override=phase_two_published_primal,
                            )
                        )
                    else:
                        published_completion_violation = math.inf
                    completion_valid = bool(
                        math.isfinite(published_completion_violation)
                        and published_completion_violation <= 10.0 * self.tolerance
                    )
                    diagnostic_rows[-1]["published_output_account_certified"] = (
                        completion_valid
                    )
                    diagnostic_rows[-1]["max_published_account_violation"] = (
                        published_completion_violation
                    )
                    diagnostic_rows[-1]["economic_postsolve_certified"] = (
                        completion_valid
                    )
                    completion_reason = (
                        "certified"
                        if completion_valid
                        else (
                            "published_activity_specific_completion_reconstruction_failed"
                            if raw_completion_certified
                            else "activity_specific_completion_reconstruction_failed"
                        )
                    )
                    diagnostic_rows[-1]["economic_certification_reason"] = (
                        completion_reason
                    )
                    diagnostic_rows[-1]["max_economic_violation"] = (
                        published_completion_violation
                        if raw_completion_certified
                        else raw_completion_violation
                    )
                    diagnostic_rows[-1]["postsolve_certified"] = completion_valid
                    diagnostic_rows[-1]["certification_reason"] = completion_reason
                    if completion_valid:
                        target_valid = True
                        completion_status = "certified"
                        target_status = "certified_slack_completion"
                        assert phase_two_published_primal is not None
                        phase_two_peer_primal = self._threshold_activity_primal(
                            phase_two_published_primal,
                            n,
                        )
                        phase_two_peer_violation = self._completion_economic_violation(
                            reference=reference,
                            solution=phase_two,
                            beta=beta,
                            x_o=x_o,
                            y_o=y_o,
                            b_o=b_o,
                            g_x=g_x,
                            g_y=g_y,
                            g_b=g_b,
                            primal_override=phase_two_peer_primal,
                        )
                        peer_valid = bool(
                            math.isfinite(phase_two_peer_violation)
                            and phase_two_peer_violation <= 10.0 * self.tolerance
                        )
                        peer_status = (
                            "certified_slack_completion"
                            if peer_valid
                            else "unavailable_after_peer_reporting_threshold"
                        )
                        activity_primal = phase_two_peer_primal if peer_valid else None
                        diagnostic_rows[-1]["published_peer_account_certified"] = (
                            peer_valid
                        )
                        diagnostic_rows[-1]["max_published_peer_account_violation"] = (
                            phase_two_peer_violation
                        )

            has_slack_solution = bool(completion_valid is True)
            if has_slack_solution:
                assert phase_two_published_primal is not None
                input_scales, output_scales, _ = _activity_specific_row_scales(
                    reference,
                    x_o,
                    y_o,
                    b_o,
                )
                offset = 2 * n
                scaled_input_slacks = phase_two_published_primal[
                    offset : offset + data.n_inputs
                ]
                offset += data.n_inputs
                scaled_output_slacks = phase_two_published_primal[
                    offset : offset + data.n_outputs
                ]
                input_slacks = scaled_input_slacks * input_scales
                output_slacks = scaled_output_slacks * output_scales
                input_targets = x_o - beta * g_x - input_slacks
                output_targets = y_o + beta * g_y + output_slacks
                bad_targets = b_o - beta * g_b
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
                if within_reference is not True:
                    is_efficient: bool | Any = pd.NA
                elif beta != 0.0 or max_scaled_slack > self.tolerance:
                    is_efficient = False
                else:
                    # The slack phase does not introduce coordinate-wise bad
                    # output improvements. A zero selected-direction distance
                    # is therefore not a full Pareto--Koopmans certificate.
                    is_efficient = pd.NA
            else:
                input_targets = np.full(data.n_inputs, np.nan)
                output_targets = np.full(data.n_outputs, np.nan)
                bad_targets = np.full(data.n_bad_outputs, np.nan)
                input_slacks = np.full(data.n_inputs, np.nan)
                output_slacks = np.full(data.n_outputs, np.nan)
                max_slack = np.nan
                max_scaled_slack = np.nan
                is_efficient = pd.NA

            if peer_valid and activity_primal is not None:
                peer_mu = activity_primal[:n]
                peer_tau = activity_primal[n : 2 * n]
                total = peer_mu + peer_tau
                for local_position, total_intensity in enumerate(total):
                    if total_intensity > self.peer_tolerance:
                        reference_position = reference.rows[local_position]
                        retention_rate = float(
                            np.clip(
                                peer_mu[local_position] / total_intensity,
                                0.0,
                                1.0,
                            )
                        )
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
                                "active_mu": float(peer_mu[local_position]),
                                "abatement_tau": float(peer_tau[local_position]),
                                "total_intensity": float(total_intensity),
                                "retention_rate_theta": retention_rate,
                                "curtailment_share_one_minus_theta": (
                                    1.0 - retention_rate
                                ),
                            }
                        )

            if target_valid is True:
                input_scales, output_scales, bad_scales = _activity_specific_row_scales(
                    reference, x_o, y_o, b_o
                )
                role_blocks = (
                    (
                        "input",
                        data.input_names,
                        x_o,
                        input_targets,
                        g_x,
                        input_slacks,
                        input_scales,
                        True,
                    ),
                    (
                        "output",
                        data.output_names,
                        y_o,
                        output_targets,
                        g_y,
                        output_slacks,
                        output_scales,
                        True,
                    ),
                    (
                        "bad_output",
                        data.bad_output_names,
                        b_o,
                        bad_targets,
                        g_b,
                        None,
                        bad_scales,
                        False,
                    ),
                )
                for (
                    role,
                    names,
                    observed,
                    targets,
                    directions,
                    slacks,
                    scales,
                    slack_allowed,
                ) in role_blocks:
                    for position, (
                        variable,
                        value,
                        target,
                        direction,
                        scale,
                    ) in enumerate(
                        zip(
                            names,
                            observed,
                            targets,
                            directions,
                            scales,
                            strict=True,
                        )
                    ):
                        target_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "observed": float(value),
                                "target": float(target),
                                "direction": float(direction),
                                "directional_change": float(beta * direction),
                                "slack_allowed": slack_allowed,
                            }
                        )
                        if slacks is not None:
                            slack_rows.append(
                                {
                                    "dmu_id": dmu_id,
                                    "period": period,
                                    "role": role,
                                    "variable": variable,
                                    "slack": float(slacks[position]),
                                    "scaled_slack": float(slacks[position] / scale),
                                }
                            )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": beta,
                    "efficiency": efficiency,
                    "score_valid": True,
                    "score_status": "defined",
                    "distance": beta,
                    "is_efficient": is_efficient,
                    "is_directionally_efficient": is_directionally_efficient,
                    "is_within_reference_technology": within_reference,
                    "self_in_reference": self_in_reference,
                    "membership_status": membership_status,
                    "solver_status": phase_one.status.value,
                    "completion_solver_status": completion_solver_status,
                    "completion_valid": completion_valid,
                    "completion_status": completion_status,
                    "target_valid": target_valid,
                    "target_status": target_status,
                    "peer_valid": peer_valid,
                    "peer_status": peer_status,
                    "dual_valid": dual_valid,
                    "dual_status": dual_status,
                    "model_family": "activity_specific_weak_disposal_ddf",
                    "orientation": "environmental_directional",
                    "returns_to_scale": "vrs",
                    "bad_output_disposability": "weak_activity_specific",
                    "compatibility_alias": None,
                    "null_jointness": self.null_jointness,
                    "reference_size": reference.size,
                    "max_slack": max_slack,
                    "max_scaled_slack": max_scaled_slack,
                    "efficiency_denominator_valid": (efficiency_denominator_valid),
                }
            )

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=pd.DataFrame(slack_rows),
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
                                "joint_operating_and_environmental_improvement"
                            ),
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box_joint_production"},
                        "data_roles": {
                            "inputs": "resources_to_contract",
                            "outputs": "desirable_services_to_expand",
                            "bad_outputs": "undesirable_residuals_to_contract",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "technology_id": self._technology_id,
                            "family": "activity_specific_weak_disposal",
                            "returns_to_scale": "vrs",
                            "source_identity": "kuosmanen_2005",
                            "linearization_variables": {
                                "active": "mu",
                                "weak_disposal_complement": "tau",
                                "convexity": "sum_mu_plus_tau_equals_one",
                            },
                            "bad_output_constraint": "equality_without_slack",
                            "null_jointness": self.null_jointness,
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                        ),
                        "performance": {
                            "family": "environmental_directional_distance",
                            "input_direction": direction_spec(
                                input_direction_kind,
                                input_directions,
                                data.input_names,
                            ),
                            "output_direction": direction_spec(
                                output_direction_kind,
                                output_directions,
                                data.output_names,
                            ),
                            "bad_output_direction": direction_spec(
                                bad_direction_kind,
                                bad_directions,
                                data.bad_output_names,
                            ),
                            "negative_distance": self.allow_negative_distance,
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": appraisal_kind,
                            "secondary_objective": (
                                "maximize_row_scaled_input_and_good_output_slacks"
                                if self.compute_slacks
                                else "none"
                            ),
                        },
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "activity_specific_weak_disposal_ddf",
                "orientation": "input_and_bad_contraction_good_expansion",
                "returns_to_scale": "vrs",
                "reference_kind": reference_plan.kind.value,
                "technology_id": self._technology_id,
                "source_identity": "kuosmanen_2005",
                "bad_output_disposability": "weak_activity_specific",
                "compatibility_alias": None,
                "bad_output_constraint": "equality",
                "null_jointness": self.null_jointness,
                "activity_components": {
                    "active_mu": (
                        "reference activity producing desirable and undesirable outputs"
                    ),
                    "abatement_tau": (
                        "complementary weak-disposal activity component; "
                        "not an observed monetary, energy, or physical cost"
                    ),
                    "total_intensity": "active_mu_plus_abatement_tau",
                    "retention_rate_theta": ("active_mu_divided_by_total_intensity"),
                    "curtailment_share_one_minus_theta": (
                        "abatement_tau_divided_by_total_intensity"
                    ),
                },
                "native_score": "beta",
                "score_direction": (
                    "signed_zero_frontier"
                    if self.allow_negative_distance
                    else "higher_is_farther"
                ),
                "efficiency_transform": (
                    "one_over_one_plus_beta_when_reference_membership_is_certified"
                ),
                "classification_domain": ("evaluated_plan_within_reference_technology"),
                "membership_policy": (
                    "structural_self_inclusion_or_negative_beta_exclusion_or_"
                    "beta_zero_feasibility_program"
                ),
                "input_direction": input_direction_kind,
                "output_direction": output_direction_kind,
                "bad_output_direction": bad_direction_kind,
                "direction_sign_convention": {
                    "input": "contract",
                    "output": "expand",
                    "bad_output": "contract",
                },
                "compute_slacks": self.compute_slacks,
                "slack_phase": "maximize_row_scaled_input_and_good_output_slacks",
                "slack_target_unit_invariant": True,
                "bad_output_slack": "not_allowed",
                "allow_negative_distance": self.allow_negative_distance,
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "planned_reference_sets": reference_plan.unique_reference_sets,
                "compiled_reference_sets": len(compiled),
                "phase_one_solver_calls": phase_one_solver_calls,
                "phase_two_solver_calls": phase_two_solver_calls,
                "membership_solver_calls": membership_solver_calls,
                "solver_calls": (
                    phase_one_solver_calls
                    + phase_two_solver_calls
                    + membership_solver_calls
                ),
                "additional_solver_calls": 0,
                "certificate_extra_solver_calls": 0,
                "postsolve_certificate": {
                    "primary_lp": ("solver_neutral_primal_dual_kkt_and_strong_duality"),
                    "primary_economic": (
                        "raw_and_published_activity_specific_direction_"
                        "objective_quantity_and_vrs_accounts"
                    ),
                    "primary_row_scaling": (
                        "input_output_and_bad_output_quantity_accounts"
                    ),
                    "peer_release": ("independent_thresholded_mu_tau_activity_account"),
                    "dual_release": ("complete_finite_original_unit_row_marginals"),
                    "slack_completion_lp": (
                        "solver_neutral_primal_dual_kkt_and_strong_duality"
                    ),
                    "slack_completion_economic": (
                        "row_scaled_slack_objective_and_physical_target_balances"
                    ),
                    "reference_membership_lp": (
                        "solver_neutral_beta_zero_feasibility_certificate_when_needed"
                    ),
                    "reference_membership_economic": (
                        "raw_and_published_original_quantity_activity_specific_"
                        "account_reconstruction"
                    ),
                    "membership_solver_calls": membership_solver_calls,
                    "classification_release": (
                        "efficiency_transform_and_efficiency_flags_require_"
                        "certified_reference_membership"
                    ),
                    "failure_policy": (
                        "withhold_uncertified_score_target_peer_or_dual_claims"
                    ),
                    "additional_solver_calls": 0,
                    "certificate_extra_solver_calls": 0,
                },
            },
        )


KuosmanenWeakDisposalDDF = ActivitySpecificWeakDisposalDDF
"""Source-name alias for :class:`ActivitySpecificWeakDisposalDDF`."""
