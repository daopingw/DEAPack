"""Declared-calibration Tone--Tsutsui input-oriented CRS EBM."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from numbers import Real
from types import MappingProxyType
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, hstack, vstack

from .._registry import (
    data_role_schema,
    numeric_parameter_signature,
    registry_metadata,
)
from ..data import DEAData
from ..enums import SolverStatus
from ..exceptions import ModelSpecificationError
from ..results import DEAResult
from ..solvers import (
    LinearProgram,
    LPSolution,
    LPSolver,
    SciPyHiGHSSolver,
    certify_lp_solution,
)
from ..specs import SolverOptions
from ._common import CompiledReference, compile_reference

_METHOD_ID = "static.ebm.input.tone_tsutsui_2010.crs.declared"
_CALIBRATION_SCHEMA = "deapack.declared-ebm-calibration.v1"
_WEIGHT_SUM_TOLERANCE = 1.0e-12
_ENDPOINT_POLICY = "package_defined_minimum_feasible_theta_given_selected_lambda"
_PRIMARY_SELECTION = "solver_selected_primary_optimum"
_ENDPOINT_SELECTION = "solver_selected_primary_optimum_with_package_theta_completion"

_SLACK_COLUMNS = (
    "dmu_id",
    "period",
    "role",
    "variable",
    "slack",
    "normalizer",
    "normalized_slack",
    "weight",
    "weighted_normalized_slack",
    "included_in_objective",
    "selection_status",
)
_TARGET_COLUMNS = (
    "dmu_id",
    "period",
    "role",
    "variable",
    "observed",
    "target",
    "change",
    "selection_status",
)
_INTENSITY_COLUMNS = (
    "dmu_id",
    "period",
    "reference_dmu_id",
    "reference_period",
    "lambda",
    "selection_status",
)
_COMPONENT_COLUMNS = (
    "dmu_id",
    "period",
    "component",
    "value",
    "selection_status",
)
_DUAL_COLUMNS = (
    "dmu_id",
    "period",
    "phase",
    "constraint_role",
    "variable",
    "marginal",
)


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _finite_number(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return 0.0 if number == 0.0 else number


@dataclass(frozen=True, slots=True)
class DeclaredEBMCalibration:
    """Immutable, provenance-bound epsilon and input-importance declaration.

    ``input_weights`` must be keyed by the exact input names used by
    :class:`~deapack.DEAData`. Values must already be normalized; this object
    never turns arbitrary relative weights into a different declaration.
    """

    epsilon: float
    input_weights: Mapping[str, float]
    source: str
    decision_owner: str
    calibration_population: str
    validity_period: str
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        epsilon = _finite_number(self.epsilon, "epsilon")
        if not 0.0 <= epsilon <= 1.0:
            raise ValueError("epsilon must be in the closed interval [0, 1]")
        object.__setattr__(self, "epsilon", epsilon)

        if not isinstance(self.input_weights, Mapping):
            raise TypeError("input_weights must be a name-keyed mapping")
        if not self.input_weights:
            raise ValueError("input_weights cannot be empty")

        canonical: dict[str, float] = {}
        for name, supplied in self.input_weights.items():
            if not isinstance(name, str) or not name.strip():
                raise TypeError("input weight names must be non-empty strings")
            if name in canonical:
                raise ValueError(f"duplicate input weight name: {name!r}")
            weight = _finite_number(supplied, f"input weight {name!r}")
            if weight < 0.0:
                raise ValueError("input weights must be nonnegative")
            canonical[name] = weight

        ordered = dict(sorted(canonical.items()))
        weight_sum = math.fsum(ordered.values())
        if not math.isclose(
            weight_sum,
            1.0,
            rel_tol=0.0,
            abs_tol=_WEIGHT_SUM_TOLERANCE,
        ):
            raise ValueError(
                "input weights must already be normalized to sum to one; "
                f"received sum={weight_sum:.17g}"
            )
        if len(ordered) == 1 and epsilon != 0.0:
            raise ValueError("a one-input Tone--Tsutsui declaration requires epsilon=0")
        object.__setattr__(self, "input_weights", MappingProxyType(ordered))

        provenance: dict[str, str] = {}
        for field_name in (
            "source",
            "decision_owner",
            "calibration_population",
            "validity_period",
        ):
            text = _required_text(getattr(self, field_name), field_name)
            object.__setattr__(self, field_name, text)
            provenance[field_name] = text

        payload = {
            "schema": _CALIBRATION_SCHEMA,
            "epsilon_hex": epsilon.hex(),
            "input_weights": [[name, value.hex()] for name, value in ordered.items()],
            "provenance": provenance,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(
            b"deapack.declared-ebm-calibration.v1\0" + encoded
        ).hexdigest()
        object.__setattr__(self, "fingerprint", digest)

    def resolve(self, input_names: tuple[str, ...]) -> np.ndarray:
        """Return weights in exact data-column order or fail closed."""

        if not input_names or any(
            not isinstance(name, str) or not name.strip() for name in input_names
        ):
            raise ModelSpecificationError(
                "EBM input names must be non-empty strings for declared alignment"
            )
        if len(set(input_names)) != len(input_names):
            raise ModelSpecificationError("EBM input names must be unique")
        declared = set(self.input_weights)
        observed = set(input_names)
        missing = observed.difference(declared)
        extra = declared.difference(observed)
        if missing or extra:
            raise ModelSpecificationError(
                "declared EBM input weights do not exactly match data inputs; "
                f"missing={sorted(missing)!r}, extra={sorted(extra)!r}"
            )
        values = np.asarray(
            [self.input_weights[name] for name in input_names],
            dtype=np.float64,
        )
        values.setflags(write=False)
        return values

    def metadata(self) -> dict[str, Any]:
        """Return detached, JSON-safe declaration metadata."""

        return {
            "schema": _CALIBRATION_SCHEMA,
            "mode": "declared",
            "epsilon": self.epsilon,
            "input_weights": dict(self.input_weights),
            "source": self.source,
            "decision_owner": self.decision_owner,
            "calibration_population": self.calibration_population,
            "validity_period": self.validity_period,
            "fingerprint": self.fingerprint,
            "normalization": "already_normalized_no_renormalization",
            "weight_sum_tolerance": _WEIGHT_SUM_TOLERANCE,
        }


@dataclass(frozen=True, slots=True)
class _EbmAccount:
    score_certified: bool
    quantity_certified: bool
    score_reason: str
    quantity_reason: str
    score: float
    target_form_score: float
    radial_factor: float
    input_targets: np.ndarray
    output_targets: np.ndarray
    input_slacks: np.ndarray
    output_surplus: np.ndarray
    weighted_normalized_input_excess: float
    weighted_input_mix_ratio: float
    radial_component: float
    input_mix_component: float
    max_score_violation: float
    max_quantity_violation: float


@dataclass(frozen=True, slots=True)
class _EbmDualAccount:
    certified: bool
    reason: str
    input_multipliers: np.ndarray
    output_multipliers: np.ndarray
    max_violation: float
    dual_objective: float


def _scaled_equality(left: np.ndarray, right: np.ndarray) -> float:
    actual = np.asarray(left, dtype=np.float64).reshape(-1)
    required = np.asarray(right, dtype=np.float64).reshape(-1)
    if actual.shape != required.shape:
        return math.inf
    if not np.isfinite(actual).all() or not np.isfinite(required).all():
        return math.inf
    scale = np.maximum(1.0, np.maximum(np.abs(actual), np.abs(required)))
    return float((np.abs(actual - required) / scale).max(initial=0.0))


def _scaled_nonnegative(values: np.ndarray, scale: np.ndarray | None = None) -> float:
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if not np.isfinite(array).all():
        return math.inf
    denominator = (
        np.maximum(1.0, np.abs(array))
        if scale is None
        else np.maximum(1.0, np.asarray(scale, dtype=np.float64).reshape(-1))
    )
    if denominator.shape != array.shape or not np.isfinite(denominator).all():
        return math.inf
    return float((np.maximum(-array, 0.0) / denominator).max(initial=0.0))


def _ebm_account(
    *,
    reference: CompiledReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
    lambdas: np.ndarray,
    theta: float,
    epsilon: float,
    weights: np.ndarray,
    solver_objective: float,
    tolerance: float,
) -> _EbmAccount:
    n = reference.size
    m = x_o.size
    if (
        np.asarray(lambdas).shape != (n,)
        or np.asarray(weights).shape != (m,)
        or not math.isfinite(theta)
        or not math.isfinite(solver_objective)
    ):
        empty_input = np.full(m, np.nan)
        empty_output = np.full(y_o.size, np.nan)
        return _EbmAccount(
            False,
            False,
            "invalid_account_shape_or_scalar",
            "invalid_account_shape_or_scalar",
            math.nan,
            math.nan,
            theta,
            empty_input,
            empty_output,
            empty_input.copy(),
            empty_output.copy(),
            math.nan,
            math.nan,
            math.nan,
            math.nan,
            math.inf,
            math.inf,
        )

    arrays = (lambdas, x_o, y_o, weights)
    if not all(
        np.isfinite(np.asarray(array, dtype=np.float64)).all() for array in arrays
    ):
        empty_input = np.full(m, np.nan)
        empty_output = np.full(y_o.size, np.nan)
        return _EbmAccount(
            False,
            False,
            "nonfinite_account",
            "nonfinite_account",
            math.nan,
            math.nan,
            theta,
            empty_input,
            empty_output,
            empty_input.copy(),
            empty_output.copy(),
            math.nan,
            math.nan,
            math.nan,
            math.nan,
            math.inf,
            math.inf,
        )

    input_targets = np.asarray(reference.inputs @ lambdas).reshape(-1)
    output_targets = np.asarray(reference.outputs @ lambdas).reshape(-1)
    input_slacks = theta * x_o - input_targets
    output_surplus = output_targets - y_o
    normalized_input_slacks = input_slacks / x_o
    normalized_input_targets = input_targets / x_o
    weighted_excess = float(weights @ normalized_input_slacks)
    weighted_mix = float(weights @ normalized_input_targets)
    source_score = float(theta - epsilon * weighted_excess)
    radial_component = float((1.0 - epsilon) * theta)
    input_mix_component = float(epsilon * weighted_mix)
    target_form_score = radial_component + input_mix_component

    objective_scale = max(
        1.0,
        abs(source_score),
        abs(target_form_score),
        abs(solver_objective),
    )
    score_violations = (
        abs(source_score - solver_objective) / objective_scale,
        abs(source_score - target_form_score) / objective_scale,
        max(-source_score, source_score - 1.0, 0.0),
    )
    max_score_violation = max(score_violations)
    score_certified = bool(max_score_violation <= tolerance)

    quantity_violations = (
        _scaled_nonnegative(lambdas),
        _scaled_nonnegative(input_slacks, x_o),
        _scaled_nonnegative(output_surplus, y_o),
        _scaled_nonnegative(input_targets, x_o),
        _scaled_nonnegative(output_targets, y_o),
        _scaled_equality(theta * x_o - input_slacks, input_targets),
        _scaled_equality(output_targets - output_surplus, y_o),
    )
    max_quantity_violation = max(quantity_violations)
    quantity_certified = bool(max_quantity_violation <= tolerance)
    return _EbmAccount(
        score_certified=score_certified,
        quantity_certified=quantity_certified,
        score_reason="certified" if score_certified else "score_account_failed",
        quantity_reason=(
            "certified" if quantity_certified else "quantity_account_failed"
        ),
        score=source_score,
        target_form_score=target_form_score,
        radial_factor=theta,
        input_targets=input_targets,
        output_targets=output_targets,
        input_slacks=input_slacks,
        output_surplus=output_surplus,
        weighted_normalized_input_excess=weighted_excess,
        weighted_input_mix_ratio=weighted_mix,
        radial_component=radial_component,
        input_mix_component=input_mix_component,
        max_score_violation=max_score_violation,
        max_quantity_violation=max_quantity_violation,
    )


def _dual_account(
    *,
    reference: CompiledReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
    epsilon: float,
    weights: np.ndarray,
    solution: LPSolution,
    score: float,
    tolerance: float,
) -> _EbmDualAccount:
    marginals = solution.inequality_marginals
    expected = x_o.size + y_o.size
    if marginals is None:
        return _EbmDualAccount(
            False,
            "missing_inequality_marginals",
            np.full(x_o.size, np.nan),
            np.full(y_o.size, np.nan),
            math.inf,
            math.nan,
        )
    values = np.asarray(marginals, dtype=np.float64)
    if values.shape != (expected,) or not np.isfinite(values).all():
        return _EbmDualAccount(
            False,
            "invalid_inequality_marginals",
            np.full(x_o.size, np.nan),
            np.full(y_o.size, np.nan),
            math.inf,
            math.nan,
        )

    input_multipliers = (-values[: x_o.size] + epsilon * weights) / x_o
    output_multipliers = -values[x_o.size :] / y_o
    input_floor = epsilon * weights / x_o
    input_value = np.asarray(input_multipliers @ reference.inputs).reshape(-1)
    output_value = np.asarray(output_multipliers @ reference.outputs).reshape(-1)
    technology_residual = -input_value + output_value
    technology_scale = np.maximum(
        1.0,
        np.maximum(np.abs(input_value), np.abs(output_value)),
    )
    dual_objective = float(output_multipliers @ y_o)
    score_scale = max(1.0, abs(dual_objective), abs(score))
    violations = (
        abs(float(input_multipliers @ x_o) - 1.0),
        float(
            (
                np.maximum(input_floor - input_multipliers, 0.0)
                / np.maximum(
                    1.0,
                    np.maximum(np.abs(input_floor), np.abs(input_multipliers)),
                )
            ).max(initial=0.0)
        ),
        _scaled_nonnegative(output_multipliers),
        float(
            (np.maximum(technology_residual, 0.0) / technology_scale).max(initial=0.0)
        ),
        abs(dual_objective - score) / score_scale,
    )
    max_violation = max(violations)
    certified = bool(max_violation <= tolerance)
    return _EbmDualAccount(
        certified=certified,
        reason="certified" if certified else "source_dual_account_failed",
        input_multipliers=input_multipliers,
        output_multipliers=output_multipliers,
        max_violation=max_violation,
        dual_objective=dual_objective,
    )


def _peer_account_violation(
    *,
    reference: CompiledReference,
    reported_lambdas: np.ndarray,
    input_targets: np.ndarray,
    output_targets: np.ndarray,
) -> float:
    return max(
        _scaled_nonnegative(reported_lambdas),
        _scaled_equality(
            np.asarray(reference.inputs @ reported_lambdas).reshape(-1),
            input_targets,
        ),
        _scaled_equality(
            np.asarray(reference.outputs @ reported_lambdas).reshape(-1),
            output_targets,
        ),
    )


class InputOrientedEpsilonBasedDEA:
    """Estimate declared-calibration Tone--Tsutsui EBM-I-C.

    This is the input-oriented CRS equations-(6)--(8) evaluator only. It uses
    one full, self-inclusive static cross-section and requires strictly
    positive ordinary inputs and desirable outputs. It does not run the
    source's affinity/PCA calibration procedure.
    """

    def __init__(
        self,
        *,
        calibration: DeclaredEBMCalibration,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1.0e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        if not isinstance(calibration, DeclaredEBMCalibration):
            raise TypeError("calibration must be a DeclaredEBMCalibration")
        self.calibration = calibration
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        if not math.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("tolerance must be finite and positive")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not math.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0.0:
            raise ValueError("peer_tolerance must be finite and positive")

    def _validate_data(self, data: DEAData) -> None:
        if data.is_panel:
            raise ModelSpecificationError(
                "declared EBM-I-C requires one static cross-section"
            )
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "declared EBM-I-C does not define undesirable-output disposal"
            )
        if data.polluting_input_names:
            raise ModelSpecificationError(
                "declared EBM-I-C accepts ordinary inputs only"
            )
        data.ensure_nonnegative(allow_zero=False)

    def _problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        weights: np.ndarray,
        name: str,
    ) -> LinearProgram:
        n = reference.size
        m = x_o.size
        s = y_o.size
        input_rows = hstack(
            [
                diags(1.0 / x_o, format="csc") @ reference.inputs,
                csc_matrix(-np.ones((m, 1), dtype=np.float64)),
            ],
            format="csc",
        )
        output_rows = hstack(
            [
                -diags(1.0 / y_o, format="csc") @ reference.outputs,
                csc_matrix((s, 1)),
            ],
            format="csc",
        )
        a_ub = vstack([input_rows, output_rows], format="csc")
        b_ub = np.concatenate([np.zeros(m), -np.ones(s)])
        lambda_cost = np.asarray(
            reference.inputs.T @ (self.calibration.epsilon * weights / x_o)
        ).reshape(-1)
        objective = np.concatenate(
            [lambda_cost, np.asarray([1.0 - self.calibration.epsilon])]
        )
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            bounds=((0.0, None),) * n + ((None, None),),
            name=f"{name}:declared_ebm_i_c",
        )

    def _reports_peer(
        self,
        reference: CompiledReference,
        local_position: int,
        intensity: float,
        input_targets: np.ndarray,
        output_targets: np.ndarray,
    ) -> bool:
        if intensity <= 0.0:
            return False
        if intensity > self.peer_tolerance:
            return True
        input_contribution = (
            np.abs(reference.inputs.getcol(local_position).toarray()).reshape(-1)
            * intensity
        )
        output_contribution = (
            np.abs(reference.outputs.getcol(local_position).toarray()).reshape(-1)
            * intensity
        )
        for contribution, target in (
            (input_contribution, input_targets),
            (output_contribution, output_targets),
        ):
            magnitude = np.abs(target)
            positive = magnitude > 0.0
            if np.any((~positive) & (contribution > 0.0)):
                return True
            if np.any(
                contribution[positive] / magnitude[positive] > self.peer_tolerance
            ):
                return True
        return False

    def _undefined_summary(
        self,
        *,
        dmu_id: object,
        solver_status: SolverStatus,
        score_status: str,
    ) -> dict[str, Any]:
        unavailable = "not_available_without_certified_primary"
        return {
            "dmu_id": dmu_id,
            "period": None,
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "is_efficient": pd.NA,
            "is_ebm_input_efficient": pd.NA,
            "score_valid": False,
            "score_status": score_status,
            "target_valid": False,
            "target_status": unavailable,
            "peer_valid": False,
            "peer_status": unavailable,
            "dual_valid": False,
            "dual_status": unavailable,
            "solver_status": solver_status.value,
            "model_family": "epsilon_based",
            "orientation": "input",
            "returns_to_scale": "crs",
            "reference_size": 0,
            "base_reference_size": 0,
            "self_in_reference": True,
            "is_within_reference_technology": True,
            "membership_status": "certified_by_self_inclusion",
            "epsilon": self.calibration.epsilon,
            "radial_factor": np.nan,
            "radial_factor_selection_status": unavailable,
            "weighted_normalized_input_excess": np.nan,
            "weighted_input_mix_ratio": np.nan,
            "max_input_excess": np.nan,
            "max_output_surplus": np.nan,
        }

    def fit(self, data: DEAData) -> DEAResult:
        """Fit declared-calibration EBM-I-C to every DMU in the sample."""

        self._validate_data(data)
        weights = self.calibration.resolve(data.input_names)
        rows = np.arange(data.n_dmus, dtype=np.int64)
        rows.setflags(write=False)
        reference = compile_reference(data, rows)

        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        component_rows: list[dict[str, Any]] = []
        dual_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        primary_solver_calls = 0

        for observation in range(data.n_dmus):
            dmu_id = data.dmu_ids[observation]
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            problem = self._problem(reference, x_o, y_o, weights, str(dmu_id))
            primary_solver_calls += 1
            solution = self.solver.solve(problem)
            lp_certificate = certify_lp_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )

            diagnostic: dict[str, Any] = {
                "dmu_id": dmu_id,
                "period": None,
                "phase": 1,
                "solver_status": solution.status.value,
                "message": solution.message,
                "iterations": solution.iterations,
                "max_primal_violation": solution.max_primal_violation,
                "postsolve_certified": lp_certificate.certified,
                "certification_reason": lp_certificate.reason,
                "max_constraint_violation": lp_certificate.max_constraint_violation,
                "max_bound_violation": lp_certificate.max_bound_violation,
                "objective_residual": lp_certificate.objective_residual,
                "duality_gap": lp_certificate.duality_gap,
                "max_dual_violation": lp_certificate.max_dual_violation,
                "complementarity_violation": (lp_certificate.complementarity_violation),
                "economic_score_certified": False,
                "economic_score_reason": "not_checked",
                "economic_quantity_certified": False,
                "economic_quantity_reason": "not_checked",
                "max_economic_score_violation": np.nan,
                "max_economic_quantity_violation": np.nan,
                "source_dual_certified": False,
                "source_dual_reason": "not_checked",
                "max_source_dual_violation": np.nan,
                "published_peer_account_violation": np.nan,
                "score_valid": False,
                "target_valid": False,
                "peer_valid": False,
                "dual_valid": False,
            }

            expected_size = data.n_dmus + 1
            primal_valid = bool(
                solution.primal is not None
                and np.asarray(solution.primal).shape == (expected_size,)
                and np.isfinite(np.asarray(solution.primal)).all()
                and solution.objective is not None
                and math.isfinite(solution.objective)
            )
            if not primal_valid:
                score_status = (
                    "solver_failed"
                    if solution.status is not SolverStatus.OPTIMAL
                    else "unavailable_uncertified_source_program"
                )
                summary = self._undefined_summary(
                    dmu_id=dmu_id,
                    solver_status=solution.status,
                    score_status=score_status,
                )
                summary["reference_size"] = data.n_dmus
                summary["base_reference_size"] = data.n_dmus
                summary_rows.append(summary)
                diagnostic_rows.append(diagnostic)
                continue

            assert solution.primal is not None
            assert solution.objective is not None
            raw_primal = np.asarray(solution.primal, dtype=np.float64)
            raw_lambdas = raw_primal[:-1]
            raw_theta = float(raw_primal[-1])
            raw_account = _ebm_account(
                reference=reference,
                x_o=x_o,
                y_o=y_o,
                lambdas=raw_lambdas,
                theta=raw_theta,
                epsilon=self.calibration.epsilon,
                weights=weights,
                solver_objective=float(solution.objective),
                tolerance=self.tolerance,
            )

            published_lambdas = raw_lambdas.copy()
            small_negative = (published_lambdas < 0.0) & (
                published_lambdas >= -self.tolerance
            )
            published_lambdas[small_negative] = 0.0
            endpoint_completed = self.calibration.epsilon == 1.0
            if endpoint_completed:
                represented_inputs = np.asarray(
                    reference.inputs @ published_lambdas
                ).reshape(-1)
                published_theta = float(np.max(represented_inputs / x_o))
                theta_selection = _ENDPOINT_SELECTION
            else:
                published_theta = raw_theta
                theta_selection = _PRIMARY_SELECTION

            published_account = _ebm_account(
                reference=reference,
                x_o=x_o,
                y_o=y_o,
                lambdas=published_lambdas,
                theta=published_theta,
                epsilon=self.calibration.epsilon,
                weights=weights,
                solver_objective=float(solution.objective),
                tolerance=self.tolerance,
            )
            score_valid = bool(
                lp_certificate.certified
                and raw_account.score_certified
                and published_account.score_certified
            )
            target_valid = bool(
                lp_certificate.certified
                and raw_account.quantity_certified
                and published_account.quantity_certified
            )

            dual_account = _dual_account(
                reference=reference,
                x_o=x_o,
                y_o=y_o,
                epsilon=self.calibration.epsilon,
                weights=weights,
                solution=solution,
                score=published_account.score,
                tolerance=self.tolerance,
            )
            dual_valid = bool(lp_certificate.certified and dual_account.certified)

            reported_lambdas = np.zeros_like(published_lambdas)
            if target_valid:
                for local_position, intensity in enumerate(published_lambdas):
                    if self._reports_peer(
                        reference,
                        local_position,
                        float(intensity),
                        published_account.input_targets,
                        published_account.output_targets,
                    ):
                        reported_lambdas[local_position] = intensity
            peer_violation = (
                _peer_account_violation(
                    reference=reference,
                    reported_lambdas=reported_lambdas,
                    input_targets=published_account.input_targets,
                    output_targets=published_account.output_targets,
                )
                if target_valid
                else math.inf
            )
            peer_valid = bool(target_valid and peer_violation <= self.tolerance)

            diagnostic.update(
                {
                    "economic_score_certified": published_account.score_certified,
                    "economic_score_reason": published_account.score_reason,
                    "economic_quantity_certified": (
                        published_account.quantity_certified
                    ),
                    "economic_quantity_reason": published_account.quantity_reason,
                    "max_economic_score_violation": (
                        published_account.max_score_violation
                    ),
                    "max_economic_quantity_violation": (
                        published_account.max_quantity_violation
                    ),
                    "source_dual_certified": dual_account.certified,
                    "source_dual_reason": dual_account.reason,
                    "max_source_dual_violation": dual_account.max_violation,
                    "published_peer_account_violation": peer_violation,
                    "score_valid": score_valid,
                    "target_valid": target_valid,
                    "peer_valid": peer_valid,
                    "dual_valid": dual_valid,
                }
            )
            diagnostic_rows.append(diagnostic)

            score = published_account.score if score_valid else math.nan
            efficient: bool | Any = (
                bool(abs(score - 1.0) <= self.tolerance) if score_valid else pd.NA
            )
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": None,
                    "score": score,
                    "efficiency": score,
                    "distance": 1.0 - score if score_valid else np.nan,
                    "is_efficient": efficient,
                    "is_ebm_input_efficient": efficient,
                    "score_valid": score_valid,
                    "score_status": (
                        "defined"
                        if score_valid
                        else "unavailable_uncertified_source_program"
                    ),
                    "target_valid": target_valid,
                    "target_status": (
                        _PRIMARY_SELECTION
                        if target_valid
                        else "unavailable_uncertified_quantity_account"
                    ),
                    "peer_valid": peer_valid,
                    "peer_status": (
                        "thresholded_solver_selected_primary_optimum"
                        if peer_valid
                        else "unavailable_uncertified_peer_reconstruction"
                    ),
                    "dual_valid": dual_valid,
                    "dual_status": (
                        "complete_source_multiplier_account"
                        if dual_valid
                        else "unavailable_uncertified_source_dual"
                    ),
                    "solver_status": solution.status.value,
                    "model_family": "epsilon_based",
                    "orientation": "input",
                    "returns_to_scale": "crs",
                    "reference_size": data.n_dmus,
                    "base_reference_size": data.n_dmus,
                    "self_in_reference": True,
                    "is_within_reference_technology": True,
                    "membership_status": "certified_by_self_inclusion",
                    "epsilon": self.calibration.epsilon,
                    "radial_factor": (
                        published_account.radial_factor if target_valid else np.nan
                    ),
                    "radial_factor_selection_status": (
                        theta_selection
                        if target_valid
                        else "unavailable_uncertified_quantity_account"
                    ),
                    "weighted_normalized_input_excess": (
                        published_account.weighted_normalized_input_excess
                        if target_valid
                        else np.nan
                    ),
                    "weighted_input_mix_ratio": (
                        published_account.weighted_input_mix_ratio
                        if target_valid
                        else np.nan
                    ),
                    "max_input_excess": (
                        float(published_account.input_slacks.max(initial=0.0))
                        if target_valid
                        else np.nan
                    ),
                    "max_output_surplus": (
                        float(published_account.output_surplus.max(initial=0.0))
                        if target_valid
                        else np.nan
                    ),
                }
            )

            if score_valid:
                for component, value in (
                    ("radial_account", published_account.radial_component),
                    ("input_mix_account", published_account.input_mix_component),
                    (
                        "weighted_normalized_input_excess",
                        published_account.weighted_normalized_input_excess,
                    ),
                ):
                    component_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": None,
                            "component": component,
                            "value": value,
                            "selection_status": theta_selection,
                        }
                    )

            if target_valid:
                input_slack_selection = (
                    _ENDPOINT_SELECTION if endpoint_completed else _PRIMARY_SELECTION
                )
                for variable, observed, target, slack, weight in zip(
                    data.input_names,
                    x_o,
                    published_account.input_targets,
                    published_account.input_slacks,
                    weights,
                    strict=True,
                ):
                    normalized = float(slack / observed)
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": None,
                            "role": "input",
                            "variable": variable,
                            "observed": float(observed),
                            "target": float(target),
                            "change": float(target - observed),
                            "selection_status": _PRIMARY_SELECTION,
                        }
                    )
                    slack_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": None,
                            "role": "input",
                            "variable": variable,
                            "slack": float(slack),
                            "normalizer": float(observed),
                            "normalized_slack": normalized,
                            "weight": float(weight),
                            "weighted_normalized_slack": float(weight * normalized),
                            "included_in_objective": bool(
                                self.calibration.epsilon > 0.0 and weight > 0.0
                            ),
                            "selection_status": input_slack_selection,
                        }
                    )
                for variable, observed, target, surplus in zip(
                    data.output_names,
                    y_o,
                    published_account.output_targets,
                    published_account.output_surplus,
                    strict=True,
                ):
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": None,
                            "role": "output",
                            "variable": variable,
                            "observed": float(observed),
                            "target": float(target),
                            "change": float(target - observed),
                            "selection_status": _PRIMARY_SELECTION,
                        }
                    )
                    slack_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": None,
                            "role": "output",
                            "variable": variable,
                            "slack": float(surplus),
                            "normalizer": float(observed),
                            "normalized_slack": float(surplus / observed),
                            "weight": np.nan,
                            "weighted_normalized_slack": np.nan,
                            "included_in_objective": False,
                            "selection_status": _PRIMARY_SELECTION,
                        }
                    )

            if peer_valid:
                for local_position, intensity in enumerate(reported_lambdas):
                    if intensity > 0.0:
                        intensity_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": None,
                                "reference_dmu_id": data.dmu_ids[local_position],
                                "reference_period": None,
                                "lambda": float(intensity),
                                "selection_status": _PRIMARY_SELECTION,
                            }
                        )

            if dual_valid:
                for variable, marginal in zip(
                    data.input_names,
                    dual_account.input_multipliers,
                    strict=True,
                ):
                    dual_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": None,
                            "phase": 1,
                            "constraint_role": "input_multiplier",
                            "variable": variable,
                            "marginal": float(marginal),
                        }
                    )
                for variable, marginal in zip(
                    data.output_names,
                    dual_account.output_multipliers,
                    strict=True,
                ):
                    dual_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": None,
                            "phase": 1,
                            "constraint_role": "output_multiplier",
                            "variable": variable,
                            "marginal": float(marginal),
                        }
                    )

        calibration_metadata = self.calibration.metadata()
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=pd.DataFrame(slack_rows, columns=_SLACK_COLUMNS),
            targets=pd.DataFrame(target_rows, columns=_TARGET_COLUMNS),
            intensities=pd.DataFrame(intensity_rows, columns=_INTENSITY_COLUMNS),
            components=pd.DataFrame(component_rows, columns=_COMPONENT_COLUMNS),
            duals=pd.DataFrame(dual_rows, columns=_DUAL_COLUMNS),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    _METHOD_ID,
                    {
                        "context": {
                            "purpose": "resource_and_input_mix_benchmarking",
                            "managerial_plan": (
                                "joint_proportional_and_variable_specific_input_"
                                "adjustment"
                            ),
                            "sample": "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "controllable_resources",
                            "outputs": "maintained_desirable_services",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": "crs",
                            "disposal": "ordinary_free",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "conditional_full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": {
                            "kind": "global",
                            "comparison_population": "full_self_inclusive_sample",
                        },
                        "performance": {
                            "family": "epsilon_based_measure",
                            "orientation": "input",
                            "native_score": "gamma",
                            "source_programme": "tone_tsutsui_2010_equations_6_8",
                        },
                        "valuation": {
                            "kind": "declared_resource_importance_calibration",
                            "epsilon": self.calibration.epsilon,
                            "input_weights": numeric_parameter_signature(
                                weights,
                                labels=data.input_names,
                            ),
                            "calibration_fingerprint": self.calibration.fingerprint,
                        },
                        "evaluation_protocol": {
                            "kind": "self_appraisal",
                            "alternate_target_policy": "solver_selected",
                            "epsilon_one_theta_completion": _ENDPOINT_POLICY,
                        },
                        "analysis": {
                            "kind": "direct_model_fit",
                            "automatic_affinity_pca_run": False,
                        },
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "epsilon_based",
                "variant": "tone_tsutsui_2010_ebm_i_c_declared",
                "orientation": "input",
                "returns_to_scale": "crs",
                "reference_kind": "global",
                "reference_population": "full_self_inclusive_sample",
                "native_score": "gamma",
                "reported_efficiency": "gamma",
                "score_direction": "higher_is_better",
                "distance_transform": "one_minus_efficiency",
                "data_requirement": "strictly_positive_cross_section",
                "calibration_mode": "declared",
                "calibration": calibration_metadata,
                "automatic_affinity_pca_run": False,
                "automatic_calibration_validated": False,
                "automatic_full_identity": ("static.ebm.input.tone_tsutsui_2010.crs"),
                "automatic_full_identity_status": "deferred_to_next_version",
                "theta_bound": "free",
                "epsilon_one_theta_completion": _ENDPOINT_POLICY,
                "target_selection": _PRIMARY_SELECTION,
                "peer_release": (
                    "thresholded_positive_lambdas_with_independent_target_"
                    "reconstruction"
                ),
                "output_surplus": "derived_feasible_unscored",
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": 1,
                "primary_solver_calls": primary_solver_calls,
                "secondary_solver_calls": 0,
                "solver_calls": primary_solver_calls,
                "additional_solver_calls": 0,
                "sparse_formulation": "lambda_theta_eliminated_input_slacks",
                "decision_variables_per_dmu": data.n_dmus + 1,
                "constraint_rows_per_dmu": data.n_inputs + data.n_outputs,
                "dense_observation_by_observation_allocation": False,
                "postsolve_certificate": {
                    "lp": "solver_neutral_primal_dual_kkt_and_strong_duality",
                    "score": "original_quantity_two_form_score_identity",
                    "targets": "original_quantity_input_output_accounts",
                    "peers": "independent_thresholded_target_reconstruction",
                    "duals": "tone_tsutsui_equations_9_12",
                },
            },
        )


__all__ = ["DeclaredEBMCalibration", "InputOrientedEpsilonBasedDEA"]
