"""Charnes--Cooper--Seiford--Stutz multiplicative DEA.

The two source variants share one sparse log-space compiler:

* the 1982 model uses a conic envelope of log quantities and fixes every
  output/input exponent below by one; and
* the 1983 model adds a free log intercept, which is dual to a convexity
  equation and produces a unit-invariant piecewise Cobb--Douglas envelope.

Neither variant is obtained by fitting ordinary radial DEA and logging its
score.  The logarithm changes the maintained empirical technology.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, eye, hstack, vstack

from .._registry import data_role_schema, registry_metadata
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import (
    MultiplicativeVariant,
    ReferenceKind,
    SolverStatus,
    parse_enum,
)
from ..exceptions import DataValidationError, ModelSpecificationError
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan


def _positive_finite(value: Real, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a finite positive real number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return normalized


def _freeze_sparse(matrix: csc_matrix) -> csc_matrix:
    """Canonicalize one CSC matrix and freeze all structural storage."""

    matrix.sum_duplicates()
    matrix.sort_indices()
    for values in (matrix.data, matrix.indices, matrix.indptr):
        values.setflags(write=False)
    return matrix


def _safe_original_unit_value(log_value: float) -> tuple[float, bool, str]:
    """Transform one finite log quantity without hiding float range loss."""

    upper = math.log(np.finfo(np.float64).max)
    lower = math.log(np.nextafter(0.0, 1.0))
    if log_value > upper:
        return math.nan, False, "overflow"
    if log_value < lower:
        return math.nan, False, "underflow"
    return math.exp(log_value), True, "available"


def _scale_log_inefficiency(
    base_log_inefficiency: float,
    exponent_floor: float,
) -> tuple[float, str]:
    """Scale a normalized log gap without publishing range-loss artifacts."""

    if not math.isfinite(base_log_inefficiency) or base_log_inefficiency < 0.0:
        return math.nan, "nonfinite_or_negative_base_log_inefficiency"
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        scaled = float(np.multiply(base_log_inefficiency, exponent_floor))
    if not math.isfinite(scaled):
        return math.nan, "scaled_log_inefficiency_overflow"
    if base_log_inefficiency > 0.0 and scaled == 0.0:
        return math.nan, "scaled_log_inefficiency_underflow"
    return scaled, "available"


@dataclass(frozen=True, slots=True)
class _MultiplicativeCertificate:
    certified: bool
    reason: str
    max_constraint_violation: float = math.inf
    max_bound_violation: float = math.inf
    objective_residual: float = math.inf
    backend_violation: float = math.inf


@dataclass(frozen=True, slots=True)
class _MultiplicativeDualCertificate:
    certified: bool
    reason: str
    input_exponents: np.ndarray | None = None
    output_exponents: np.ndarray | None = None
    intercept: float = 0.0
    max_bound_violation: float = math.inf
    max_reference_violation: float = math.inf
    objective_residual: float = math.inf


def _uncertified(reason: str) -> _MultiplicativeCertificate:
    return _MultiplicativeCertificate(certified=False, reason=reason)


def _certify_multipliers(
    marginals: np.ndarray | None,
    *,
    variant: MultiplicativeVariant,
    exponent_floor: float,
    reference_log_inputs: np.ndarray,
    reference_log_outputs: np.ndarray,
    input_anchor: np.ndarray,
    output_anchor: np.ndarray,
    focal_log_inputs: np.ndarray,
    focal_log_outputs: np.ndarray,
    log_efficiency: float,
    tolerance: float,
) -> _MultiplicativeDualCertificate:
    """Restore and validate source multiplier values in raw log coordinates."""

    if marginals is None:
        return _MultiplicativeDualCertificate(False, "missing_equality_marginals")
    raw = np.asarray(marginals, dtype=np.float64).reshape(-1)
    m = int(focal_log_inputs.size)
    s = int(focal_log_outputs.size)
    expected = m + s + (1 if variant is MultiplicativeVariant.INVARIANT_1983 else 0)
    if raw.size != expected:
        return _MultiplicativeDualCertificate(False, "wrong_marginal_length")
    if not np.isfinite(raw).all():
        return _MultiplicativeDualCertificate(False, "nonfinite_marginals")

    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        scaled = np.multiply(exponent_floor, raw)
    if not np.isfinite(scaled).all():
        return _MultiplicativeDualCertificate(False, "nonfinite_scaled_marginals")

    input_exponents = -scaled[:m]
    output_exponents = scaled[m : m + s]
    intercept = 0.0
    if variant is MultiplicativeVariant.INVARIANT_1983:
        centered_intercept = float(scaled[-1])
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            intercept = float(
                centered_intercept
                - output_exponents @ output_anchor
                + input_exponents @ input_anchor
            )
        if not math.isfinite(intercept):
            return _MultiplicativeDualCertificate(False, "nonfinite_restored_intercept")

    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        input_bound_gaps = np.maximum(exponent_floor - input_exponents, 0.0)
        output_bound_gaps = np.maximum(exponent_floor - output_exponents, 0.0)
    if not (
        np.isfinite(input_bound_gaps).all() and np.isfinite(output_bound_gaps).all()
    ):
        return _MultiplicativeDualCertificate(False, "nonfinite_multiplier_bound_check")
    bound_violation = float(
        max(
            input_bound_gaps.max(initial=0.0),
            output_bound_gaps.max(initial=0.0),
        )
    )

    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        reference_values = (
            reference_log_outputs @ output_exponents
            - reference_log_inputs @ input_exponents
            + intercept
        )
        reference_scales = np.maximum(
            1.0,
            np.abs(reference_log_outputs) @ np.abs(output_exponents)
            + np.abs(reference_log_inputs) @ np.abs(input_exponents)
            + abs(intercept),
        )
    if not (
        np.isfinite(reference_values).all() and np.isfinite(reference_scales).all()
    ):
        return _MultiplicativeDualCertificate(
            False, "nonfinite_multiplier_reference_check"
        )
    reference_violation = float(
        (np.maximum(reference_values, 0.0) / reference_scales).max(initial=0.0)
    )
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        focal_value = float(
            focal_log_outputs @ output_exponents
            - focal_log_inputs @ input_exponents
            + intercept
        )
        objective_difference = float(np.subtract(focal_value, log_efficiency))
    if not math.isfinite(focal_value) or not math.isfinite(objective_difference):
        return _MultiplicativeDualCertificate(
            False, "nonfinite_multiplier_objective_check"
        )
    objective_residual = abs(objective_difference) / max(
        1.0, abs(focal_value), abs(log_efficiency)
    )
    certified = bool(
        bound_violation <= tolerance
        and reference_violation <= tolerance
        and objective_residual <= tolerance
    )
    return _MultiplicativeDualCertificate(
        certified=certified,
        reason=(
            "certified"
            if certified
            else "multiplier_bound_reference_or_objective_check_failed"
        ),
        input_exponents=input_exponents,
        output_exponents=output_exponents,
        intercept=intercept,
        max_bound_violation=bound_violation,
        max_reference_violation=reference_violation,
        objective_residual=objective_residual,
    )


def _certify_solution(
    problem: LinearProgram,
    solution: LPSolution,
    *,
    tolerance: float,
) -> _MultiplicativeCertificate:
    """Independently check the backend incumbent before publishing results."""

    if solution.status is not SolverStatus.OPTIMAL:
        return _uncertified(f"solver_status_{solution.status.value}")
    if solution.primal is None:
        return _uncertified("missing_primal")
    primal = np.asarray(solution.primal, dtype=np.float64)
    if primal.shape != problem.c.shape:
        return _uncertified("wrong_primal_length")
    if not np.isfinite(primal).all():
        return _uncertified("nonfinite_primal")
    if solution.objective is None or not math.isfinite(solution.objective):
        return _uncertified("nonfinite_objective")

    constraint_violation = 0.0
    if problem.a_eq is not None and problem.b_eq is not None:
        residual = np.asarray(
            problem.a_eq @ primal - problem.b_eq,
            dtype=np.float64,
        ).reshape(-1)
        scales = np.maximum(1.0, np.abs(problem.b_eq))
        constraint_violation = float((np.abs(residual) / scales).max(initial=0.0))
    if problem.a_ub is not None and problem.b_ub is not None:
        residual = np.asarray(
            problem.a_ub @ primal - problem.b_ub,
            dtype=np.float64,
        ).reshape(-1)
        scales = np.maximum(1.0, np.abs(problem.b_ub))
        constraint_violation = max(
            constraint_violation,
            float((np.maximum(residual, 0.0) / scales).max(initial=0.0)),
        )

    bound_violation = 0.0
    for value, (lower, upper) in zip(primal, problem.bounds, strict=True):
        if lower is not None:
            bound_violation = max(bound_violation, max(lower - value, 0.0))
        if upper is not None:
            bound_violation = max(bound_violation, max(value - upper, 0.0))

    recomputed = float(problem.c @ primal)
    objective_scale = max(1.0, abs(recomputed), abs(float(solution.objective)))
    objective_residual = abs(recomputed - float(solution.objective)) / objective_scale
    backend = solution.max_primal_violation
    backend_violation = (
        0.0
        if backend is None
        else float(backend)
        if math.isfinite(backend) and backend >= 0.0
        else math.inf
    )
    certified = bool(
        constraint_violation <= tolerance
        and bound_violation <= tolerance
        and objective_residual <= tolerance
        and backend_violation <= tolerance
    )
    return _MultiplicativeCertificate(
        certified=certified,
        reason=(
            "certified"
            if certified
            else "primal_bound_constraint_or_objective_check_failed"
        ),
        max_constraint_violation=constraint_violation,
        max_bound_violation=bound_violation,
        objective_residual=objective_residual,
        backend_violation=backend_violation,
    )


@dataclass(frozen=True, slots=True)
class _CompiledMultiplicativeReference:
    """One immutable sparse log-space reference template."""

    rows: np.ndarray
    log_inputs: csc_matrix
    log_outputs: csc_matrix
    input_anchor: np.ndarray
    output_anchor: np.ndarray
    a_eq: csc_matrix
    bounds: tuple[tuple[float | None, float | None], ...]
    variant: MultiplicativeVariant

    @property
    def size(self) -> int:
        return int(self.rows.size)

    @classmethod
    def compile(
        cls,
        log_inputs_by_observation: np.ndarray,
        log_outputs_by_observation: np.ndarray,
        rows: np.ndarray,
        variant: MultiplicativeVariant,
    ) -> _CompiledMultiplicativeReference:
        selected_inputs = log_inputs_by_observation[rows]
        selected_outputs = log_outputs_by_observation[rows]
        if variant is MultiplicativeVariant.INVARIANT_1983:
            # Translation of each log coordinate is an exact representation
            # under sum(lambda)=1 and greatly improves numerical conditioning.
            input_anchor = selected_inputs[0].copy()
            output_anchor = selected_outputs[0].copy()
        else:
            input_anchor = np.zeros(selected_inputs.shape[1], dtype=np.float64)
            output_anchor = np.zeros(selected_outputs.shape[1], dtype=np.float64)

        reference_inputs = _freeze_sparse(
            csc_matrix((selected_inputs - input_anchor).T)
        )
        reference_outputs = _freeze_sparse(
            csc_matrix((selected_outputs - output_anchor).T)
        )
        n_lambda = int(rows.size)
        m = reference_inputs.shape[0]
        s = reference_outputs.shape[0]
        input_rows = hstack(
            [
                reference_inputs,
                eye(m, format="csc"),
                csc_matrix((m, s)),
            ],
            format="csc",
        )
        output_rows = hstack(
            [
                reference_outputs,
                csc_matrix((s, m)),
                -eye(s, format="csc"),
            ],
            format="csc",
        )
        blocks = [input_rows, output_rows]
        if variant is MultiplicativeVariant.INVARIANT_1983:
            blocks.append(
                hstack(
                    [
                        csc_matrix(np.ones((1, n_lambda), dtype=np.float64)),
                        csc_matrix((1, m + s)),
                    ],
                    format="csc",
                )
            )
        a_eq = _freeze_sparse(vstack(blocks, format="csc"))
        immutable_rows = np.asarray(rows, dtype=np.int64).copy()
        immutable_rows.setflags(write=False)
        input_anchor.setflags(write=False)
        output_anchor.setflags(write=False)
        return cls(
            rows=immutable_rows,
            log_inputs=reference_inputs,
            log_outputs=reference_outputs,
            input_anchor=input_anchor,
            output_anchor=output_anchor,
            a_eq=a_eq,
            bounds=((0.0, None),) * (n_lambda + m + s),
            variant=variant,
        )

    def problem(
        self,
        log_x_o: np.ndarray,
        log_y_o: np.ndarray,
        name: str,
    ) -> LinearProgram:
        x_rhs = log_x_o - self.input_anchor
        y_rhs = log_y_o - self.output_anchor
        b_parts = [x_rhs, y_rhs]
        if self.variant is MultiplicativeVariant.INVARIANT_1983:
            b_parts.append(np.asarray([1.0], dtype=np.float64))
        objective = np.zeros(len(self.bounds), dtype=np.float64)
        # Solve the homogeneous delta=1 task for stable scaling.  The public
        # score and dual exponents are rescaled by exponent_floor after solve.
        objective[self.size :] = -1.0
        return LinearProgram(
            c=objective,
            a_eq=self.a_eq,
            b_eq=np.concatenate(b_parts),
            bounds=self.bounds,
            name=f"{name}:multiplicative:{self.variant.value}",
        )


class MultiplicativeDEA:
    """Estimate source-frozen multiplicative DEA efficiency.

    Parameters
    ----------
    variant:
        ``"invariant_1983"`` (default) fits the unit-invariant convex
        log-space/Cobb--Douglas technology of Charnes et al. (1983).
        ``"original_1982"`` reproduces the earlier log-conic model, whose
        source domain requires every input and output to exceed one and whose
        score changes when measurement units change.
    exponent_floor:
        Strictly positive lower bound on the output and input exponents.  The
        1982 source fixes it at one.  In the 1983 homogeneous formulation a
        different positive value is an explicit score-power convention: it
        scales log inefficiency while leaving the feasible peer plans and
        ranking unchanged.
    reference:
        Reference population.  The source profile is a self-inclusive global
        cross-section; other supported reference rules are labelled as
        package extensions in result metadata.

    Notes
    -----
    ``score`` and ``efficiency`` contain multiplicative efficiency
    ``exp(log_efficiency)``.  ``distance`` is nonnegative log inefficiency.
    Targets are reconstructed in the original quantity units.  The 1983
    target is a weighted geometric mean of peer observations.
    """

    model_family = "multiplicative"
    _registry_method_id = "static.multiplicative"
    _registry_preset_id: str | None = None

    def __init__(
        self,
        *,
        variant: MultiplicativeVariant | str = (MultiplicativeVariant.INVARIANT_1983),
        exponent_floor: Real = 1.0,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: Real = 1e-7,
        peer_tolerance: Real | None = None,
    ) -> None:
        self.variant = parse_enum(variant, MultiplicativeVariant, "variant")
        self.exponent_floor = _positive_finite(exponent_floor, "exponent_floor")
        if (
            self.variant is MultiplicativeVariant.ORIGINAL_1982
            and self.exponent_floor != 1.0
        ):
            raise ModelSpecificationError(
                "the original_1982 source fixes every exponent lower bound at "
                "one; use exponent_floor=1 or select invariant_1983"
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
        self.tolerance = _positive_finite(tolerance, "tolerance")
        self.peer_tolerance = (
            self.tolerance
            if peer_tolerance is None
            else _positive_finite(peer_tolerance, "peer_tolerance")
        )

    @property
    def unit_invariant(self) -> bool:
        return self.variant is MultiplicativeVariant.INVARIANT_1983

    def _validate_data(self, data: DEAData) -> None:
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "MultiplicativeDEA models ordinary desirable outputs only; "
                "undesirable-output multiplicative technologies require a "
                "separate source-qualified method"
            )
        data.ensure_nonnegative(allow_zero=False)
        if self.variant is MultiplicativeVariant.ORIGINAL_1982 and (
            np.any(data.inputs <= 1.0) or np.any(data.outputs <= 1.0)
        ):
            raise DataValidationError(
                "the original_1982 multiplicative source requires every input "
                "and output value to be strictly greater than one"
            )

    def _source_profile(
        self,
        data: DEAData,
        reference_kind: ReferenceKind,
    ) -> tuple[str, tuple[str, ...]]:
        mismatches: list[str] = []
        if data.is_panel:
            mismatches.append("data_are_not_one_cross_section")
        if reference_kind is not ReferenceKind.GLOBAL:
            mismatches.append("reference_is_not_the_global_sample")
        profile = (
            "charnes_cooper_seiford_stutz_1983_invariant"
            if self.unit_invariant
            else "charnes_cooper_seiford_stutz_1982_original"
        )
        if mismatches:
            profile = f"deapack_{self.variant.value}_reference_extension"
        return profile, tuple(mismatches)

    def _failure_summary(
        self,
        *,
        dmu_id: object,
        period: object | None,
        status: SolverStatus,
        reason: str,
        reference_size: int,
    ) -> dict[str, Any]:
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "log_efficiency": np.nan,
            "log_inefficiency": np.nan,
            "multiplicative_efficiency": np.nan,
            "is_efficient": pd.NA,
            "solver_status": status.value,
            "failure_reason": reason,
            "model_family": self.model_family,
            "orientation": "non-oriented",
            "technology_variant": self.variant.value,
            "returns_to_scale": ("log_convex" if self.unit_invariant else "log_conic"),
            "reference_size": reference_size,
            "max_log_slack": np.nan,
        }

    def fit(self, data: DEAData) -> DEAResult:
        """Fit one multiplicative efficiency programme per observation."""

        self._validate_data(data)
        log_inputs = np.log(data.inputs)
        log_outputs = np.log(data.outputs)
        if not np.isfinite(log_inputs).all() or not np.isfinite(log_outputs).all():
            raise DataValidationError(
                "positive quantities must have finite logarithms in float64"
            )

        reference_plan = build_reference_plan(data, self.reference)
        compiled: dict[int, _CompiledMultiplicativeReference] = {}
        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        multiplier_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                reference = _CompiledMultiplicativeReference.compile(
                    log_inputs,
                    log_outputs,
                    reference_plan.rows_for(observation),
                    self.variant,
                )
                compiled[set_id] = reference

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            problem = reference.problem(
                log_inputs[observation],
                log_outputs[observation],
                name,
            )
            solution = self.solver.solve(problem)
            certificate = _certify_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )
            common_diagnostic = {
                "dmu_id": dmu_id,
                "period": period,
                "phase": 1,
                "reference_set_id": set_id,
                "reference_size": reference.size,
                "technology_variant": self.variant.value,
                "solver_status": solution.status.value,
                "message": solution.message,
                "iterations": solution.iterations,
                "max_primal_violation": solution.max_primal_violation,
                "max_constraint_violation": certificate.max_constraint_violation,
                "max_bound_violation": certificate.max_bound_violation,
                "objective_residual": certificate.objective_residual,
                "backend_violation": certificate.backend_violation,
            }
            if not certificate.certified or solution.primal is None:
                diagnostic_rows.append(
                    {
                        **common_diagnostic,
                        "postsolve_certified": False,
                        "certification_reason": certificate.reason,
                        "economic_account_violation": np.nan,
                        "target_reconstruction_violation": np.nan,
                        "efficiency_underflowed": pd.NA,
                        "reported_intensity_mass": np.nan,
                        "omitted_intensity_mass": np.nan,
                    }
                )
                reported_status = (
                    solution.status
                    if solution.status is not SolverStatus.OPTIMAL
                    else SolverStatus.FAILED
                )
                summary_rows.append(
                    self._failure_summary(
                        dmu_id=dmu_id,
                        period=period,
                        status=reported_status,
                        reason=certificate.reason,
                        reference_size=reference.size,
                    )
                )
                continue

            primal = np.asarray(solution.primal, dtype=np.float64)
            n_lambda = reference.size
            m = data.n_inputs
            lambdas = np.maximum(primal[:n_lambda], 0.0)
            input_log_slacks = np.maximum(primal[n_lambda : n_lambda + m], 0.0)
            output_log_slacks = np.maximum(primal[n_lambda + m :], 0.0)
            log_x_target = log_inputs[observation] - input_log_slacks
            log_y_target = log_outputs[observation] + output_log_slacks
            peer_log_x_target = (
                np.asarray(reference.log_inputs @ lambdas).reshape(-1)
                + reference.input_anchor
            )
            peer_log_y_target = (
                np.asarray(reference.log_outputs @ lambdas).reshape(-1)
                + reference.output_anchor
            )
            balance_scales = np.concatenate(
                [
                    np.maximum.reduce(
                        [
                            np.ones_like(log_x_target),
                            np.abs(log_x_target),
                            np.abs(peer_log_x_target),
                        ]
                    ),
                    np.maximum.reduce(
                        [
                            np.ones_like(log_y_target),
                            np.abs(log_y_target),
                            np.abs(peer_log_y_target),
                        ]
                    ),
                ]
            )
            target_residuals = np.concatenate(
                [
                    peer_log_x_target - log_x_target,
                    peer_log_y_target - log_y_target,
                ]
            )
            target_reconstruction_violation = float(
                (np.abs(target_residuals) / balance_scales).max(initial=0.0)
            )
            intensity_violation = (
                abs(float(lambdas.sum()) - 1.0) if self.unit_invariant else 0.0
            )
            base_log_inefficiency = float(
                input_log_slacks.sum() + output_log_slacks.sum()
            )
            log_inefficiency, score_scaling_reason = _scale_log_inefficiency(
                base_log_inefficiency,
                self.exponent_floor,
            )
            assert solution.objective is not None
            objective_account_violation = abs(
                base_log_inefficiency + float(solution.objective)
            ) / max(
                1.0,
                base_log_inefficiency,
                abs(float(solution.objective)),
            )
            economic_account_violation = max(
                target_reconstruction_violation,
                intensity_violation,
                objective_account_violation,
            )

            input_target_transforms = [
                _safe_original_unit_value(float(value)) for value in log_x_target
            ]
            output_target_transforms = [
                _safe_original_unit_value(float(value)) for value in log_y_target
            ]
            input_targets = np.asarray(
                [item[0] for item in input_target_transforms], dtype=np.float64
            )
            output_targets = np.asarray(
                [item[0] for item in output_target_transforms], dtype=np.float64
            )
            target_transforms = input_target_transforms + output_target_transforms
            original_unit_targets_available = all(item[1] for item in target_transforms)
            target_transform_reasons = tuple(
                sorted({item[2] for item in target_transforms if not item[1]})
            )
            if economic_account_violation > self.tolerance:
                reason = "postprocessed_log_account_check_failed"
                diagnostic_rows.append(
                    {
                        **common_diagnostic,
                        "postsolve_certified": False,
                        "certification_reason": reason,
                        "economic_account_violation": economic_account_violation,
                        "target_reconstruction_violation": (
                            target_reconstruction_violation
                        ),
                        "efficiency_underflowed": pd.NA,
                        "original_unit_targets_available": (
                            original_unit_targets_available
                        ),
                        "target_transform_reasons": target_transform_reasons,
                        "reported_intensity_mass": np.nan,
                        "omitted_intensity_mass": np.nan,
                    }
                )
                summary_rows.append(
                    self._failure_summary(
                        dmu_id=dmu_id,
                        period=period,
                        status=SolverStatus.FAILED,
                        reason=reason,
                        reference_size=reference.size,
                    )
                )
                continue

            if score_scaling_reason != "available":
                diagnostic_rows.append(
                    {
                        **common_diagnostic,
                        "postsolve_certified": False,
                        "certification_reason": score_scaling_reason,
                        "economic_account_violation": economic_account_violation,
                        "target_reconstruction_violation": (
                            target_reconstruction_violation
                        ),
                        "efficiency_underflowed": pd.NA,
                        "original_unit_targets_available": (
                            original_unit_targets_available
                        ),
                        "target_transform_reasons": target_transform_reasons,
                        "reported_intensity_mass": np.nan,
                        "omitted_intensity_mass": np.nan,
                    }
                )
                summary_rows.append(
                    self._failure_summary(
                        dmu_id=dmu_id,
                        period=period,
                        status=SolverStatus.FAILED,
                        reason=score_scaling_reason,
                        reference_size=reference.size,
                    )
                )
                continue

            log_efficiency = -log_inefficiency
            efficiency = (
                0.0
                if log_inefficiency > -math.log(np.nextafter(0.0, 1.0))
                else math.exp(log_efficiency)
            )
            efficiency_underflowed = bool(efficiency == 0.0)
            max_log_slack = float(
                max(
                    input_log_slacks.max(initial=0.0),
                    output_log_slacks.max(initial=0.0),
                )
            )

            report_mask = lambdas > self.peer_tolerance
            reported_mass = float(lambdas[report_mask].sum())
            omitted_mass = float(lambdas[~report_mask].sum())
            for local_position in np.flatnonzero(report_mask):
                reference_position = int(reference.rows[local_position])
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
                        "lambda": float(lambdas[local_position]),
                        "target_aggregation": (
                            "weighted_geometric_mean"
                            if self.unit_invariant
                            else "log_conic_product"
                        ),
                    }
                )

            for (
                role,
                names,
                observed,
                targets,
                log_observed,
                log_targets,
                log_slacks,
                transform_records,
            ) in (
                (
                    "input",
                    data.input_names,
                    data.inputs[observation],
                    input_targets,
                    log_inputs[observation],
                    log_x_target,
                    input_log_slacks,
                    input_target_transforms,
                ),
                (
                    "output",
                    data.output_names,
                    data.outputs[observation],
                    output_targets,
                    log_outputs[observation],
                    log_y_target,
                    output_log_slacks,
                    output_target_transforms,
                ),
            ):
                for (
                    variable,
                    observed_value,
                    target,
                    observed_log_value,
                    target_log_value,
                    log_slack,
                    target_transform,
                ) in zip(
                    names,
                    observed,
                    targets,
                    log_observed,
                    log_targets,
                    log_slacks,
                    transform_records,
                    strict=True,
                ):
                    log_factor = (
                        -float(log_slack) if role == "input" else float(log_slack)
                    )
                    factor, factor_available, factor_reason = _safe_original_unit_value(
                        log_factor
                    )
                    _, target_available, target_transform_reason = target_transform
                    absolute_change = (
                        float(observed_value - target)
                        if role == "input" and target_available
                        else float(target - observed_value)
                        if target_available
                        else math.nan
                    )
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "observed": float(observed_value),
                            "target": float(target),
                            "log_observed": float(observed_log_value),
                            "log_target": float(target_log_value),
                            "target_factor": float(factor),
                            "original_unit_available": target_available,
                            "factor_available": factor_available,
                            "transform_reason": (
                                "available"
                                if target_available and factor_available
                                else target_transform_reason
                                if not target_available
                                else factor_reason
                            ),
                        }
                    )
                    slack_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "slack": float(absolute_change),
                            "scaled_slack": float(log_slack),
                            "log_slack": float(log_slack),
                            "exponent_weight": self.exponent_floor,
                            "weighted_log_slack": (
                                self.exponent_floor * float(log_slack)
                            ),
                            "improvement_factor": float(factor),
                            "absolute_change": float(absolute_change),
                        }
                    )

            dual_certificate = _certify_multipliers(
                solution.equality_marginals,
                variant=self.variant,
                exponent_floor=self.exponent_floor,
                reference_log_inputs=log_inputs[reference.rows],
                reference_log_outputs=log_outputs[reference.rows],
                input_anchor=reference.input_anchor,
                output_anchor=reference.output_anchor,
                focal_log_inputs=log_inputs[observation],
                focal_log_outputs=log_outputs[observation],
                log_efficiency=log_efficiency,
                tolerance=self.tolerance,
            )
            if (
                dual_certificate.certified
                and dual_certificate.input_exponents is not None
                and dual_certificate.output_exponents is not None
            ):
                for role, names, values in (
                    (
                        "input_exponent",
                        data.input_names,
                        dual_certificate.input_exponents,
                    ),
                    (
                        "output_exponent",
                        data.output_names,
                        dual_certificate.output_exponents,
                    ),
                ):
                    for variable, value in zip(names, values, strict=True):
                        multiplier_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "phase": 1,
                                "role": role,
                                "variable": variable,
                                "multiplier": float(value),
                                "lower_bound": self.exponent_floor,
                                "selection": "solver_selected_optimum",
                            }
                        )
                if self.unit_invariant:
                    multiplier_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "phase": 1,
                            "role": "log_intercept",
                            "variable": "omega",
                            "multiplier": dual_certificate.intercept,
                            "lower_bound": np.nan,
                            "selection": "solver_selected_optimum",
                        }
                    )

            diagnostic_rows.append(
                {
                    **common_diagnostic,
                    "postsolve_certified": True,
                    "certification_reason": "certified",
                    "economic_account_violation": economic_account_violation,
                    "target_reconstruction_violation": (
                        target_reconstruction_violation
                    ),
                    "efficiency_underflowed": efficiency_underflowed,
                    "original_unit_targets_available": (
                        original_unit_targets_available
                    ),
                    "target_transform_reasons": target_transform_reasons,
                    "multiplier_certified": dual_certificate.certified,
                    "multiplier_certification_reason": dual_certificate.reason,
                    "multiplier_max_bound_violation": (
                        dual_certificate.max_bound_violation
                    ),
                    "multiplier_max_reference_violation": (
                        dual_certificate.max_reference_violation
                    ),
                    "multiplier_objective_residual": (
                        dual_certificate.objective_residual
                    ),
                    "reported_intensity_mass": reported_mass,
                    "omitted_intensity_mass": omitted_mass,
                }
            )
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": efficiency,
                    "efficiency": efficiency,
                    "distance": log_inefficiency,
                    "log_efficiency": log_efficiency,
                    "log_inefficiency": log_inefficiency,
                    "multiplicative_efficiency": efficiency,
                    "is_efficient": bool(max_log_slack <= self.tolerance),
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": self.model_family,
                    "orientation": "non-oriented",
                    "technology_variant": self.variant.value,
                    "returns_to_scale": (
                        "log_convex" if self.unit_invariant else "log_conic"
                    ),
                    "reference_size": reference.size,
                    "max_log_slack": max_log_slack,
                }
            )

        source_profile, source_profile_mismatches = self._source_profile(
            data,
            reference_plan.kind,
        )
        source = (
            {
                "authors": "Charnes, Cooper, Seiford, and Stutz",
                "year": 1983,
                "doi": "10.1016/0167-6377(83)90014-7",
                "equations": "1, 3-I/3-II, 4, and 6-I/6-II",
            }
            if self.unit_invariant
            else {
                "authors": "Charnes, Cooper, Seiford, and Stutz",
                "year": 1982,
                "doi": "10.1016/0038-0121(82)90029-5",
                "equations": "1--6",
            }
        )
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            multipliers=pd.DataFrame(multiplier_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
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
                            "family": (
                                "multiplicative_log_convex"
                                if self.unit_invariant
                                else "multiplicative_log_conic"
                            ),
                            "returns_to_scale": (
                                "convex_in_log_quantities"
                                if self.unit_invariant
                                else "conic_in_log_quantities"
                            ),
                            "disposal": "source_log_slack_envelopment",
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
                            "family": "multiplicative_efficiency",
                            "orientation": "non_oriented",
                            "source_profile": source_profile,
                            "exponent_floor": self.exponent_floor,
                        },
                        "valuation": {
                            "kind": "multiplicative_virtual_weights",
                            "source": "source_exponent_lower_bound",
                        },
                        "evaluation_protocol": {"kind": "self_appraisal"},
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                    preset_id=type(self)._registry_preset_id,
                ),
                "model_family": self.model_family,
                "native_score": "multiplicative_efficiency",
                "score_direction": "higher_is_better",
                "distance_field": "log_inefficiency",
                "efficiency_transform": "exp(-log_inefficiency)",
                "variant": self.variant.value,
                "unit_invariant": self.unit_invariant,
                "exponent_floor": self.exponent_floor,
                "orientation": "non-oriented",
                "returns_to_scale": (
                    "log_convex" if self.unit_invariant else "log_conic"
                ),
                "reference_kind": reference_plan.kind.value,
                "target_aggregation": (
                    "weighted_geometric_mean"
                    if self.unit_invariant
                    else "log_conic_product"
                ),
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
                "source": source,
                "source_profile": source_profile,
                "source_profile_matches": not source_profile_mismatches,
                "source_profile_mismatches": source_profile_mismatches,
                "peer_reporting_policy": "lambda_above_peer_tolerance",
                "causal_interpretation": "not_identified",
                "target_uniqueness": "not_guaranteed",
            },
        )


class InvariantMultiplicativeDEA(MultiplicativeDEA):
    """Source-exact 1983 invariant multiplicative-model constructor."""

    _registry_preset_id = "static.multiplicative.invariant.charnes_etal_1983"

    def __init__(
        self,
        *,
        exponent_floor: Real = 1.0,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: Real = 1e-7,
        peer_tolerance: Real | None = None,
    ) -> None:
        super().__init__(
            variant=MultiplicativeVariant.INVARIANT_1983,
            exponent_floor=exponent_floor,
            reference=reference,
            solver=solver,
            solver_options=solver_options,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )


class C2S2MultiplicativeDEA(MultiplicativeDEA):
    """Historical 1982 C2S2 multiplicative-model constructor.

    The C2S2 name belongs to the original non-unit-invariant log-conic
    model.  This constructor fixes ``variant="original_1982"`` so that the
    historical name can never silently select the 1983 modification.
    """

    _registry_preset_id = "static.multiplicative.original.charnes_etal_1982"

    def __init__(
        self,
        *,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: Real = 1e-7,
        peer_tolerance: Real | None = None,
    ) -> None:
        super().__init__(
            variant=MultiplicativeVariant.ORIGINAL_1982,
            exponent_floor=1.0,
            reference=reference,
            solver=solver,
            solver_options=solver_options,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )


__all__ = [
    "C2S2MultiplicativeDEA",
    "InvariantMultiplicativeDEA",
    "MultiplicativeDEA",
]
