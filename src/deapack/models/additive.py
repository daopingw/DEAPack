"""Direct additive DEA and its configurable slack-weight extension."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Any, TypeAlias

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, eye, hstack, vstack

from .._registry import (
    data_role_schema,
    numeric_parameter_signature,
    registry_metadata,
)
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import ReferenceKind, ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..results import DEAResult
from ..solvers import (
    LinearProgram,
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
    join_optional_rows,
    join_optional_values,
    rts_matrices,
)

WeightInput: TypeAlias = Mapping[str, float] | Sequence[float] | None

_SLACK_COLUMNS = (
    "dmu_id",
    "period",
    "role",
    "variable",
    "slack",
    "weight",
    "scale",
    "scaled_slack",
    "solver_scale",
    "solver_scaled_slack",
)
_TARGET_COLUMNS = ("dmu_id", "period", "role", "variable", "observed", "target")
_INTENSITY_COLUMNS = (
    "dmu_id",
    "period",
    "reference_dmu_id",
    "reference_period",
    "lambda",
)
_DUAL_COLUMNS = (
    "dmu_id",
    "period",
    "phase",
    "constraint_role",
    "variable",
    "marginal",
)


@dataclass(frozen=True, slots=True)
class _AdditiveAccountCertificate:
    """Original-quantity resource, service, RTS, and score accounts."""

    quantity_certified: bool
    weighted_slack_certified: bool
    reason: str
    resource_violation: float = math.inf
    service_violation: float = math.inf
    rts_violation: float = math.inf
    nonnegativity_violation: float = math.inf
    weighted_slack_residual: float = math.inf
    weighted_slack_value: float = math.nan

    @property
    def certified(self) -> bool:
        return self.quantity_certified and self.weighted_slack_certified

    @property
    def max_quantity_violation(self) -> float:
        return max(
            self.resource_violation,
            self.service_violation,
            self.rts_violation,
            self.nonnegativity_violation,
        )

    @property
    def max_economic_violation(self) -> float:
        return max(self.max_quantity_violation, self.weighted_slack_residual)


@dataclass(frozen=True, slots=True)
class _AdditivePeerCertificate:
    """Reconstruction of one target from the intensities actually published."""

    certified: bool
    reason: str
    resource_violation: float = math.inf
    service_violation: float = math.inf
    rts_violation: float = math.inf
    nonnegativity_violation: float = math.inf

    @property
    def max_violation(self) -> float:
        return max(
            self.resource_violation,
            self.service_violation,
            self.rts_violation,
            self.nonnegativity_violation,
        )


@dataclass(frozen=True, slots=True)
class _AdditiveDualCertificate:
    """Completeness and original-unit objective closure of published dual rows."""

    certified: bool
    reason: str
    expected_row_count: int
    published_row_count: int
    original_unit_dual_objective: float = math.nan
    objective_residual: float = math.inf

    @property
    def max_violation(self) -> float:
        return self.objective_residual


def _scaled_maximum(residual: np.ndarray, scale: np.ndarray) -> float:
    values = np.asarray(residual, dtype=np.float64).reshape(-1)
    account_scale = np.asarray(scale, dtype=np.float64).reshape(-1)
    if (
        values.shape != account_scale.shape
        or not np.isfinite(values).all()
        or not np.isfinite(account_scale).all()
        or np.any(account_scale <= 0.0)
    ):
        return math.inf
    ratios = np.abs(values) / account_scale
    return float(ratios.max(initial=0.0)) if np.isfinite(ratios).all() else math.inf


def _rts_account_violation(
    lambdas: np.ndarray,
    returns_to_scale: ReturnsToScale,
) -> float:
    total = float(np.sum(lambdas))
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


def _certify_additive_account(
    *,
    reference: CompiledReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
    lambdas: np.ndarray,
    input_slacks: np.ndarray,
    output_slacks: np.ndarray,
    input_scales: np.ndarray,
    output_scales: np.ndarray,
    input_weights: np.ndarray,
    output_weights: np.ndarray,
    source_distance: float,
    returns_to_scale: ReturnsToScale,
    tolerance: float,
) -> _AdditiveAccountCertificate:
    """Certify one raw or publication-form additive account in user units."""

    expected_shapes = (
        (lambdas, (reference.size,)),
        (input_slacks, x_o.shape),
        (output_slacks, y_o.shape),
    )
    if any(np.asarray(values).shape != shape for values, shape in expected_shapes):
        return _AdditiveAccountCertificate(
            quantity_certified=False,
            weighted_slack_certified=False,
            reason="invalid_account_shape",
        )
    arrays = (
        lambdas,
        input_slacks,
        output_slacks,
        input_scales,
        output_scales,
        input_weights,
        output_weights,
    )
    if not all(
        np.isfinite(np.asarray(values, dtype=np.float64)).all() for values in arrays
    ):
        return _AdditiveAccountCertificate(
            quantity_certified=False,
            weighted_slack_certified=False,
            reason="nonfinite_account",
        )

    resource_residual = np.asarray(
        reference.inputs @ lambdas + input_slacks - x_o,
        dtype=np.float64,
    ).reshape(-1)
    service_residual = np.asarray(
        reference.outputs @ lambdas - output_slacks - y_o,
        dtype=np.float64,
    ).reshape(-1)
    resource_violation = _scaled_maximum(resource_residual, input_scales)
    service_violation = _scaled_maximum(service_residual, output_scales)
    rts_violation = _rts_account_violation(lambdas, returns_to_scale)
    nonnegativity_violation = max(
        float(np.maximum(-lambdas, 0.0).max(initial=0.0)),
        _scaled_maximum(np.minimum(input_slacks, 0.0), input_scales),
        _scaled_maximum(np.minimum(output_slacks, 0.0), output_scales),
    )
    weighted_slack_value = float(
        input_weights @ input_slacks + output_weights @ output_slacks
    )
    distance_scale = max(1.0, abs(weighted_slack_value), abs(source_distance))
    weighted_slack_residual = (
        abs(weighted_slack_value - source_distance) / distance_scale
        if math.isfinite(weighted_slack_value) and math.isfinite(source_distance)
        else math.inf
    )
    quantity_certified = bool(
        max(
            resource_violation,
            service_violation,
            rts_violation,
            nonnegativity_violation,
        )
        <= tolerance
    )
    weighted_slack_certified = bool(weighted_slack_residual <= tolerance)
    reason = (
        "certified"
        if quantity_certified and weighted_slack_certified
        else "quantity_account_failed"
        if not quantity_certified
        else "weighted_slack_account_failed"
    )
    return _AdditiveAccountCertificate(
        quantity_certified=quantity_certified,
        weighted_slack_certified=weighted_slack_certified,
        reason=reason,
        resource_violation=resource_violation,
        service_violation=service_violation,
        rts_violation=rts_violation,
        nonnegativity_violation=nonnegativity_violation,
        weighted_slack_residual=weighted_slack_residual,
        weighted_slack_value=weighted_slack_value,
    )


def _certify_thresholded_peer_account(
    *,
    reference: CompiledReference,
    peer_lambdas: np.ndarray,
    input_targets: np.ndarray,
    output_targets: np.ndarray,
    input_scales: np.ndarray,
    output_scales: np.ndarray,
    returns_to_scale: ReturnsToScale,
    tolerance: float,
) -> _AdditivePeerCertificate:
    """Check the target and RTS account represented by published peer rows."""

    if peer_lambdas.shape != (reference.size,) or not all(
        np.isfinite(values).all()
        for values in (peer_lambdas, input_targets, output_targets)
    ):
        return _AdditivePeerCertificate(False, "invalid_peer_account")
    resource_violation = _scaled_maximum(
        np.asarray(reference.inputs @ peer_lambdas).reshape(-1) - input_targets,
        input_scales,
    )
    service_violation = _scaled_maximum(
        np.asarray(reference.outputs @ peer_lambdas).reshape(-1) - output_targets,
        output_scales,
    )
    rts_violation = _rts_account_violation(peer_lambdas, returns_to_scale)
    nonnegativity_violation = float(np.maximum(-peer_lambdas, 0.0).max(initial=0.0))
    certified = bool(
        max(
            resource_violation,
            service_violation,
            rts_violation,
            nonnegativity_violation,
        )
        <= tolerance
    )
    return _AdditivePeerCertificate(
        certified=certified,
        reason="certified" if certified else "thresholded_peer_account_failed",
        resource_violation=resource_violation,
        service_violation=service_violation,
        rts_violation=rts_violation,
        nonnegativity_violation=nonnegativity_violation,
    )


def _certify_original_unit_duals(
    *,
    rows: list[dict[str, Any]],
    input_names: tuple[str, ...],
    output_names: tuple[str, ...],
    x_o: np.ndarray,
    y_o: np.ndarray,
    returns_to_scale: ReturnsToScale,
    source_objective: float,
    tolerance: float,
) -> _AdditiveDualCertificate:
    """Certify completeness and the original-unit dual objective account."""

    expected_count = (
        len(input_names)
        + len(output_names)
        + int(returns_to_scale is not ReturnsToScale.CRS)
    )
    if len(rows) != expected_count:
        return _AdditiveDualCertificate(
            False,
            "incomplete_published_dual_rows",
            expected_count,
            len(rows),
        )

    keyed: dict[tuple[object, object], float] = {}
    for row in rows:
        key = (row.get("constraint_role"), row.get("variable"))
        marginal = row.get("marginal")
        if (
            key in keyed
            or not isinstance(marginal, Real)
            or not math.isfinite(marginal)
        ):
            return _AdditiveDualCertificate(
                False,
                "duplicate_or_nonfinite_published_dual_row",
                expected_count,
                len(rows),
            )
        keyed[key] = float(marginal)

    expected_keys = {
        *(("input_balance", name) for name in input_names),
        *(("output_balance", name) for name in output_names),
    }
    if returns_to_scale is not ReturnsToScale.CRS:
        expected_keys.add(("returns_to_scale", returns_to_scale.value))
    if set(keyed) != expected_keys:
        return _AdditiveDualCertificate(
            False,
            "incomplete_published_dual_rows",
            expected_count,
            len(rows),
        )

    dual_objective = sum(
        float(value) * keyed[("input_balance", name)]
        for name, value in zip(input_names, x_o, strict=True)
    ) + sum(
        float(value) * keyed[("output_balance", name)]
        for name, value in zip(output_names, y_o, strict=True)
    )
    if returns_to_scale in {ReturnsToScale.VRS, ReturnsToScale.NIRS}:
        dual_objective += keyed[("returns_to_scale", returns_to_scale.value)]
    elif returns_to_scale is ReturnsToScale.NDRS:
        dual_objective -= keyed[("returns_to_scale", returns_to_scale.value)]

    scale = max(1.0, abs(dual_objective), abs(source_objective))
    objective_residual = (
        abs(dual_objective - source_objective) / scale
        if math.isfinite(dual_objective) and math.isfinite(source_objective)
        else math.inf
    )
    certified = bool(objective_residual <= tolerance)
    return _AdditiveDualCertificate(
        certified=certified,
        reason=(
            "certified" if certified else "original_unit_dual_objective_account_failed"
        ),
        expected_row_count=expected_count,
        published_row_count=len(rows),
        original_unit_dual_objective=dual_objective,
        objective_residual=objective_residual,
    )


def _resolve_weights(
    specification: WeightInput,
    names: tuple[str, ...],
    role: str,
) -> np.ndarray:
    if specification is None:
        weights = np.ones(len(names), dtype=np.float64)
    elif isinstance(specification, Mapping):
        missing = set(names).difference(specification)
        extra = set(specification).difference(names)
        if missing or extra:
            raise ModelSpecificationError(
                f"{role}_weights must name every {role} exactly once; "
                f"missing={sorted(missing, key=repr)!r}, "
                f"extra={sorted(extra, key=repr)!r}"
            )
        try:
            weights = np.asarray(
                [specification[name] for name in names], dtype=np.float64
            )
        except (TypeError, ValueError) as error:
            raise ModelSpecificationError(
                f"{role}_weights must contain numeric values"
            ) from error
    else:
        if isinstance(specification, (str, bytes)):
            raise ModelSpecificationError(
                f"{role}_weights must be a numeric sequence or name-to-weight mapping"
            )
        try:
            weights = np.asarray(tuple(specification), dtype=np.float64)
        except (TypeError, ValueError) as error:
            raise ModelSpecificationError(
                f"{role}_weights must contain numeric values"
            ) from error
        if weights.ndim != 1 or weights.size != len(names):
            raise ModelSpecificationError(
                f"{role}_weights needs {len(names)} values in data-column order"
            )

    if not np.isfinite(weights).all() or np.any(weights <= 0):
        raise ModelSpecificationError(
            f"{role}_weights must be finite and strictly positive"
        )
    weights.setflags(write=False)
    return weights


def _additive_row_scales(
    reference: CompiledReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return positive evaluated-account scales for a unit-stable LP."""
    input_scales = np.abs(x_o).copy()
    output_scales = np.abs(y_o).copy()
    zero_inputs = input_scales <= 0.0
    zero_outputs = output_scales <= 0.0
    if np.any(zero_inputs):
        input_scales[zero_inputs] = reference.input_abs_row_max[zero_inputs]
    if np.any(zero_outputs):
        output_scales[zero_outputs] = reference.output_abs_row_max[zero_outputs]
    input_scales[input_scales <= 0.0] = 1.0
    output_scales[output_scales <= 0.0] = 1.0
    return input_scales, output_scales


def _additive_strong_status_scales(
    x_o: np.ndarray,
    y_o: np.ndarray,
    input_lower: np.ndarray,
    input_upper: np.ndarray,
    output_lower: np.ndarray,
    output_upper: np.ndarray,
    solver_input_scales: np.ndarray,
    solver_output_scales: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return unit- and translation-stable scales for strong status."""
    input_scales = np.maximum(
        np.abs(x_o - input_lower),
        np.abs(input_upper - x_o),
    )
    output_scales = np.maximum(
        np.abs(y_o - output_lower),
        np.abs(output_upper - y_o),
    )
    input_scales[input_scales <= 0.0] = solver_input_scales[input_scales <= 0.0]
    output_scales[output_scales <= 0.0] = solver_output_scales[output_scales <= 0.0]
    return input_scales, output_scales


class AdditiveDEA:
    """Estimate additive Pareto--Koopmans inefficiency.

    The source-qualified Charnes et al. (1985) profile uses VRS, unit
    input/output slack weights, and one self-inclusive cross-section. The
    configurable weights, other returns-to-scale restrictions, and temporal
    reference policies exposed by this class are transparent DEAPack
    extensions; they do not inherit that narrow historical certificate.

    The native score is the maximized weighted sum of input excesses and
    output shortfalls. Zero means efficient and larger values mean farther
    from the frontier. Because this quantity depends on units unless the user
    supplies defensible normalizing weights, the model does not invent a
    bounded ``efficiency`` value.

    Parameters
    ----------
    returns_to_scale:
        ``"crs"``, ``"vrs"``, ``"nirs"``, or ``"ndrs"``.
    input_weights, output_weights:
        Strictly positive weights supplied either in data-column order or by
        variable name. Omitting them yields the classical unweighted additive
        objective.
    reference:
        Reference-set rule shared with the other DEA measures.
    """

    model_family = "additive"
    _registry_method_id = "static.additive"

    def __init__(
        self,
        *,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        input_weights: WeightInput = None,
        output_weights: WeightInput = None,
        reference: ReferenceSpec | str | None = None,
        peer_eligibility: PeerEligibility | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.returns_to_scale = parse_enum(
            returns_to_scale, ReturnsToScale, "returns_to_scale"
        )
        self.input_weights = input_weights
        self.output_weights = output_weights
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
        if not np.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be finite and positive")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not np.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be finite and positive")

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "AdditiveDEA does not infer how undesirable outputs are disposed. "
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

    def _weight_vectors(self, data: DEAData) -> tuple[np.ndarray, np.ndarray]:
        return (
            _resolve_weights(self.input_weights, data.input_names, "input"),
            _resolve_weights(self.output_weights, data.output_names, "output"),
        )

    def _summary_values(
        self,
        distance: float,
        max_scaled_slack: float,
    ) -> dict[str, Any]:
        return {
            "score": distance,
            "efficiency": np.nan,
            "distance": distance,
            "is_efficient": bool(max_scaled_slack <= self.tolerance),
        }

    def _measure_metadata(
        self,
        data: DEAData,
        input_weights: np.ndarray,
        output_weights: np.ndarray,
    ) -> dict[str, Any]:
        weighting = (
            "unit"
            if np.array_equal(input_weights, np.ones_like(input_weights))
            and np.array_equal(output_weights, np.ones_like(output_weights))
            else "user"
        )
        return {
            "model_family": self.model_family,
            "native_score": "weighted_slack_sum",
            "score_direction": "higher_is_farther",
            "efficiency_transform": None,
            "weighting": weighting,
            "weight_source": (
                "implicit_defaults"
                if self.input_weights is None and self.output_weights is None
                else "user_declared"
            ),
            "input_weights": tuple(
                (name, float(weight))
                for name, weight in zip(data.input_names, input_weights, strict=True)
            ),
            "output_weights": tuple(
                (name, float(weight))
                for name, weight in zip(data.output_names, output_weights, strict=True)
            ),
        }

    def _problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        input_scales: np.ndarray,
        output_scales: np.ndarray,
        solver_input_weights: np.ndarray,
        solver_output_weights: np.ndarray,
        name: str,
        *,
        input_activity: csc_matrix | None = None,
        output_activity: csc_matrix | None = None,
        input_anchor: np.ndarray | None = None,
        output_anchor: np.ndarray | None = None,
    ) -> LinearProgram:
        n_lambda = reference.size
        m = x_o.size
        s = y_o.size
        n_variables = n_lambda + m + s

        input_activity = reference.inputs if input_activity is None else input_activity
        output_activity = (
            reference.outputs if output_activity is None else output_activity
        )
        input_rhs = (
            x_o
            if input_anchor is None
            else x_o - np.asarray(input_anchor, dtype=np.float64)
        ) / input_scales
        output_rhs = (
            y_o
            if output_anchor is None
            else y_o - np.asarray(output_anchor, dtype=np.float64)
        ) / output_scales

        input_rows = hstack(
            [
                diags(1.0 / input_scales, format="csc") @ input_activity,
                eye(m, format="csc"),
                csc_matrix((m, s)),
            ],
            format="csc",
        )
        output_rows = hstack(
            [
                diags(1.0 / output_scales, format="csc") @ output_activity,
                csc_matrix((s, m)),
                -eye(s, format="csc"),
            ],
            format="csc",
        )
        a_eq = vstack([input_rows, output_rows], format="csc")
        b_eq = np.concatenate([input_rhs, output_rhs])

        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_variables, n_lambda, self.returns_to_scale
        )
        a_eq = join_optional_rows(a_eq, rts_eq)
        b_eq = join_optional_values(b_eq, rts_b_eq)

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[n_lambda : n_lambda + m] = -solver_input_weights
        objective[n_lambda + m :] = -solver_output_weights
        return LinearProgram(
            c=objective,
            a_ub=rts_ub,
            b_ub=rts_b_ub,
            a_eq=a_eq,
            b_eq=b_eq,
            bounds=((0.0, None),) * n_variables,
            name=f"{name}:additive",
        )

    def _dual_rows(
        self,
        data: DEAData,
        observation: int,
        solution: LPSolution,
        *,
        input_scales: np.ndarray | None = None,
        output_scales: np.ndarray | None = None,
        objective_scale: float = 1.0,
        vrs_input_anchor: np.ndarray | None = None,
        vrs_output_anchor: np.ndarray | None = None,
    ) -> list[dict[str, Any]]:
        period = None if data.periods is None else data.periods[observation]
        common = {"dmu_id": data.dmu_ids[observation], "period": period, "phase": 1}
        rows: list[dict[str, Any]] = []

        if solution.equality_marginals is not None:
            offset = 0
            for local_index, variable in enumerate(data.input_names):
                scale = (
                    1.0 if input_scales is None else float(input_scales[local_index])
                )
                rows.append(
                    {
                        **common,
                        "constraint_role": "input_balance",
                        "variable": variable,
                        "marginal": (
                            solution.equality_marginals[offset]
                            * objective_scale
                            / scale
                        ),
                    }
                )
                offset += 1
            for local_index, variable in enumerate(data.output_names):
                scale = (
                    1.0 if output_scales is None else float(output_scales[local_index])
                )
                rows.append(
                    {
                        **common,
                        "constraint_role": "output_balance",
                        "variable": variable,
                        "marginal": (
                            solution.equality_marginals[offset]
                            * objective_scale
                            / scale
                        ),
                    }
                )
                offset += 1
            if self.returns_to_scale is ReturnsToScale.VRS:
                marginal = float(solution.equality_marginals[offset])
                if vrs_input_anchor is not None or vrs_output_anchor is not None:
                    assert input_scales is not None
                    assert output_scales is not None
                    assert vrs_input_anchor is not None
                    assert vrs_output_anchor is not None
                    marginal -= float(
                        np.dot(
                            solution.equality_marginals[: data.n_inputs],
                            vrs_input_anchor / input_scales,
                        )
                        + np.dot(
                            solution.equality_marginals[
                                data.n_inputs : data.n_inputs + data.n_outputs
                            ],
                            vrs_output_anchor / output_scales,
                        )
                    )
                rows.append(
                    {
                        **common,
                        "constraint_role": "returns_to_scale",
                        "variable": self.returns_to_scale.value,
                        "marginal": marginal * objective_scale,
                    }
                )

        if (
            self.returns_to_scale in {ReturnsToScale.NIRS, ReturnsToScale.NDRS}
            and solution.inequality_marginals is not None
        ):
            rows.append(
                {
                    **common,
                    "constraint_role": "returns_to_scale",
                    "variable": self.returns_to_scale.value,
                    "marginal": (solution.inequality_marginals[0] * objective_scale),
                }
            )
        return rows

    def _solver_weight_scaling(
        self,
        input_weights: np.ndarray,
        output_weights: np.ndarray,
        input_scales: np.ndarray,
        output_scales: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, float]:
        """Map physical slack weights to stable normalized-slack coefficients."""
        effective_input = input_weights * input_scales
        effective_output = output_weights * output_scales
        effective = np.concatenate([effective_input, effective_output])
        if not np.isfinite(effective).all():
            raise ModelSpecificationError(
                "weight-by-unit scale products must be finite; rescale the "
                "declared quantities and reciprocal weights"
            )

        objective_scale = float(effective.max(initial=0.0))
        if objective_scale <= 0.0:
            return effective_input, effective_output, 1.0

        normalized_input = effective_input / objective_scale
        normalized_output = effective_output / objective_scale
        objective_guard = self._objective_weight_guard_tolerance()
        active = np.concatenate([normalized_input, normalized_output])
        active = active[active > 0.0]
        if np.any(active <= objective_guard):
            raise ModelSpecificationError(
                "the declared weights and quantity units create effective "
                "positive slack weights at or below the effective solver dual "
                "feasibility tolerance after numerical scaling; rescale "
                "the units/weights or configure a smaller solver dual "
                "tolerance together with a suitable model tolerance"
            )
        return normalized_input, normalized_output, objective_scale

    def _solver_feasibility_tolerance(self, kind: str) -> float | None:
        """Return a backend-declared effective feasibility tolerance."""
        value = getattr(
            self.solver,
            f"effective_{kind}_feasibility_tolerance",
            None,
        )
        if value is None:
            return None
        tolerance = float(value)
        return tolerance if np.isfinite(tolerance) and tolerance > 0.0 else None

    def _objective_weight_guard_tolerance(self) -> float:
        """Return the safest available floor for objective coefficients."""
        solver_tolerance = self._solver_feasibility_tolerance("dual")
        return self.tolerance if solver_tolerance is None else solver_tolerance

    def _reports_peer(
        self,
        reference: CompiledReference,
        local_position: int,
        intensity: float,
        input_targets: np.ndarray,
        output_targets: np.ndarray,
    ) -> bool:
        """Keep a small intensity when it materially explains a target."""
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
            target_magnitude = np.abs(target)
            if np.any((target_magnitude <= 0.0) & (contribution > 0.0)):
                return True
            positive = target_magnitude > 0.0
            if np.any(
                contribution[positive] / target_magnitude[positive]
                > self.peer_tolerance
            ):
                return True
        return False

    def _source_profile(
        self,
        data: DEAData,
        reference_kind: ReferenceKind,
        reference_is_full_self_inclusive: bool,
        input_weights: np.ndarray,
        output_weights: np.ndarray,
    ) -> tuple[str, tuple[str, ...]]:
        """Identify whether a fit matches the narrow 1985 source profile."""
        mismatches: list[str] = []
        if self.model_family != "additive":
            mismatches.append("model_family_is_not_direct_additive")
        if self.returns_to_scale is not ReturnsToScale.VRS:
            mismatches.append("returns_to_scale_is_not_vrs")
        if not np.array_equal(input_weights, np.ones_like(input_weights)) or not (
            np.array_equal(output_weights, np.ones_like(output_weights))
        ):
            mismatches.append("slack_weights_are_not_unit_weights")
        if data.is_panel:
            mismatches.append("data_are_not_one_cross_section")
        if (
            reference_kind is not ReferenceKind.GLOBAL
            or not reference_is_full_self_inclusive
        ):
            mismatches.append("reference_is_not_the_full_self_inclusive_sample")
        profile = (
            "charnes_etal_1985_eq_4_6"
            if not mismatches
            else "deapack_configurable_additive_extension"
        )
        return profile, tuple(mismatches)

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate direct additive inefficiency for all observations."""
        self._validate_data(data)
        input_weights, output_weights = self._weight_vectors(data)
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
        compiled: dict[int, CompiledReference] = {}
        reference_bounds: dict[
            int,
            tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
        ] = {}
        vrs_activities: dict[
            int,
            tuple[csc_matrix, csc_matrix, np.ndarray, np.ndarray],
        ] = {}

        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        dual_rows: list[dict[str, Any]] = []
        primary_solver_calls = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                reference = compile_reference(data, reference_rows)
                compiled[set_id] = reference
                selected_inputs = data.inputs[reference_rows]
                selected_outputs = data.outputs[reference_rows]
                bounds = (
                    np.min(selected_inputs, axis=0),
                    np.max(selected_inputs, axis=0),
                    np.min(selected_outputs, axis=0),
                    np.max(selected_outputs, axis=0),
                )
                reference_bounds[set_id] = bounds
                if self.returns_to_scale is ReturnsToScale.VRS:
                    input_anchor = bounds[0]
                    output_anchor = bounds[2]
                    vrs_activities[set_id] = (
                        reference.inputs
                        - csc_matrix(
                            np.broadcast_to(
                                input_anchor[:, None],
                                reference.inputs.shape,
                            )
                        ),
                        reference.outputs
                        - csc_matrix(
                            np.broadcast_to(
                                output_anchor[:, None],
                                reference.outputs.shape,
                            )
                        ),
                        input_anchor,
                        output_anchor,
                    )
            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            self_in_reference = bool(self_membership[observation])
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            input_scales, output_scales = _additive_row_scales(reference, x_o, y_o)
            (
                input_lower,
                input_upper,
                output_lower,
                output_upper,
            ) = reference_bounds[set_id]
            strong_input_scales, strong_output_scales = _additive_strong_status_scales(
                x_o,
                y_o,
                input_lower,
                input_upper,
                output_lower,
                output_upper,
                input_scales,
                output_scales,
            )
            if self.returns_to_scale is ReturnsToScale.VRS:
                input_scales = strong_input_scales
                output_scales = strong_output_scales
                (
                    problem_input_activity,
                    problem_output_activity,
                    input_anchor,
                    output_anchor,
                ) = vrs_activities[set_id]
            else:
                problem_input_activity = None
                problem_output_activity = None
                input_anchor = None
                output_anchor = None
            (
                solver_input_weights,
                solver_output_weights,
                objective_scale,
            ) = self._solver_weight_scaling(
                input_weights,
                output_weights,
                input_scales,
                output_scales,
            )
            problem = self._problem(
                reference,
                x_o,
                y_o,
                input_scales,
                output_scales,
                solver_input_weights,
                solver_output_weights,
                name,
                input_activity=problem_input_activity,
                output_activity=problem_output_activity,
                input_anchor=input_anchor,
                output_anchor=output_anchor,
            )
            primary_solver_calls += 1
            solution = self.solver.solve(problem)
            lp_certificate = certify_lp_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )

            n_lambda = reference.size
            expected_primal_size = n_lambda + data.n_inputs + data.n_outputs
            primal_available = bool(
                solution.primal is not None
                and np.asarray(solution.primal).shape == (expected_primal_size,)
                and np.isfinite(np.asarray(solution.primal)).all()
                and solution.objective is not None
                and math.isfinite(solution.objective)
            )
            if primal_available:
                assert solution.primal is not None
                raw_primal = np.asarray(solution.primal, dtype=np.float64)
                published_primal = np.maximum(raw_primal, 0.0)
            else:
                raw_primal = np.full(expected_primal_size, np.nan)
                published_primal = raw_primal.copy()

            raw_lambdas = raw_primal[:n_lambda]
            raw_solver_scaled_input_slacks = raw_primal[
                n_lambda : n_lambda + data.n_inputs
            ]
            raw_solver_scaled_output_slacks = raw_primal[n_lambda + data.n_inputs :]
            raw_input_slacks = raw_solver_scaled_input_slacks * input_scales
            raw_output_slacks = raw_solver_scaled_output_slacks * output_scales
            source_distance = (
                -float(solution.objective) * objective_scale
                if solution.objective is not None and math.isfinite(solution.objective)
                else math.nan
            )
            raw_account = _certify_additive_account(
                reference=reference,
                x_o=x_o,
                y_o=y_o,
                lambdas=raw_lambdas,
                input_slacks=raw_input_slacks,
                output_slacks=raw_output_slacks,
                input_scales=input_scales,
                output_scales=output_scales,
                input_weights=input_weights,
                output_weights=output_weights,
                source_distance=source_distance,
                returns_to_scale=self.returns_to_scale,
                tolerance=self.tolerance,
            )

            lambdas = published_primal[:n_lambda]
            solver_scaled_input_slacks = published_primal[
                n_lambda : n_lambda + data.n_inputs
            ]
            solver_scaled_output_slacks = published_primal[n_lambda + data.n_inputs :]
            input_slacks = solver_scaled_input_slacks * input_scales
            output_slacks = solver_scaled_output_slacks * output_scales
            published_account = _certify_additive_account(
                reference=reference,
                x_o=x_o,
                y_o=y_o,
                lambdas=lambdas,
                input_slacks=input_slacks,
                output_slacks=output_slacks,
                input_scales=input_scales,
                output_scales=output_scales,
                input_weights=input_weights,
                output_weights=output_weights,
                source_distance=source_distance,
                returns_to_scale=self.returns_to_scale,
                tolerance=self.tolerance,
            )
            strong_scaled_input_slacks = input_slacks / strong_input_scales
            strong_scaled_output_slacks = output_slacks / strong_output_scales
            input_targets = x_o - input_slacks
            output_targets = y_o + output_slacks
            distance = published_account.weighted_slack_value
            max_slack = (
                float(
                    max(
                        input_slacks.max(initial=0.0),
                        output_slacks.max(initial=0.0),
                    )
                )
                if primal_available
                else math.nan
            )
            max_scaled_slack = (
                float(
                    max(
                        strong_scaled_input_slacks.max(initial=0.0),
                        strong_scaled_output_slacks.max(initial=0.0),
                    )
                )
                if primal_available
                else math.nan
            )

            source_claim_valid = bool(
                lp_certificate.certified and raw_account.certified
            )
            score_valid = bool(
                source_claim_valid and published_account.weighted_slack_certified
            )
            target_valid = bool(
                source_claim_valid and published_account.quantity_certified
            )

            score_values: dict[str, Any] = {
                "score": np.nan,
                "efficiency": np.nan,
                "distance": np.nan,
                "is_efficient": pd.NA,
            }
            score_range_valid = True
            if score_valid:
                try:
                    score_values = self._summary_values(distance, max_scaled_slack)
                except RuntimeError:
                    score_valid = False
                    score_range_valid = False

            candidate_intensity_rows: list[dict[str, Any]] = []
            peer_lambdas = np.zeros(reference.size, dtype=np.float64)
            if target_valid:
                for local_position, intensity in enumerate(lambdas):
                    if self._reports_peer(
                        reference,
                        local_position,
                        float(intensity),
                        input_targets,
                        output_targets,
                    ):
                        peer_lambdas[local_position] = float(intensity)
                        reference_position = reference.rows[local_position]
                        candidate_intensity_rows.append(
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
                peer_certificate = _certify_thresholded_peer_account(
                    reference=reference,
                    peer_lambdas=peer_lambdas,
                    input_targets=input_targets,
                    output_targets=output_targets,
                    input_scales=input_scales,
                    output_scales=output_scales,
                    returns_to_scale=self.returns_to_scale,
                    tolerance=self.tolerance,
                )
            else:
                peer_certificate = _AdditivePeerCertificate(
                    False,
                    "not_checked_without_certified_target",
                )
            peer_valid = bool(target_valid and peer_certificate.certified)

            candidate_dual_rows: list[dict[str, Any]] = []
            expected_dual_rows = (
                data.n_inputs
                + data.n_outputs
                + int(self.returns_to_scale is not ReturnsToScale.CRS)
            )
            dual_certificate = _AdditiveDualCertificate(
                False,
                "not_checked_without_certified_primary",
                expected_dual_rows,
                0,
            )
            if source_claim_valid:
                candidate_dual_rows = self._dual_rows(
                    data,
                    observation,
                    solution,
                    input_scales=input_scales,
                    output_scales=output_scales,
                    objective_scale=objective_scale,
                    vrs_input_anchor=input_anchor,
                    vrs_output_anchor=output_anchor,
                )
                dual_certificate = _certify_original_unit_duals(
                    rows=candidate_dual_rows,
                    input_names=data.input_names,
                    output_names=data.output_names,
                    x_o=x_o,
                    y_o=y_o,
                    returns_to_scale=self.returns_to_scale,
                    source_objective=(
                        float(solution.objective) * objective_scale
                        if solution.objective is not None
                        else math.nan
                    ),
                    tolerance=self.tolerance,
                )
            dual_valid = bool(source_claim_valid and dual_certificate.certified)

            if solution.status is SolverStatus.INFEASIBLE and not self_in_reference:
                score_status = "outside_reference_technology"
            elif solution.status is not SolverStatus.OPTIMAL:
                score_status = "solver_failed"
            elif not lp_certificate.certified:
                score_status = "unavailable_uncertified_primary_lp"
            elif not raw_account.certified:
                score_status = "unavailable_uncertified_raw_account"
            elif not published_account.weighted_slack_certified:
                score_status = "unavailable_uncertified_published_score_account"
            elif not score_range_valid:
                score_status = "unavailable_invalid_score_range"
            else:
                score_status = "defined"

            if not source_claim_valid:
                target_status = "not_available_without_certified_primary"
            elif not published_account.quantity_certified:
                target_status = "unavailable_uncertified_published_quantity_account"
            else:
                target_status = "certified_published_quantity_account"
            if not target_valid:
                peer_status = "not_available_without_certified_target"
            elif not peer_certificate.certified:
                peer_status = "unavailable_after_peer_reporting_threshold"
            else:
                peer_status = "certified_thresholded_peer_account"
            if not source_claim_valid:
                dual_status = "not_available_without_certified_primary"
            elif not dual_certificate.certified:
                dual_status = "unavailable_uncertified_published_dual_account"
            else:
                dual_status = "certified_original_unit_dual_account"

            if self_in_reference:
                is_within_reference_technology: bool | Any = True
                membership_status = "certified_by_self_inclusion"
            elif source_claim_valid:
                is_within_reference_technology = True
                membership_status = "certified_by_raw_additive_balance"
            elif solution.status is SolverStatus.INFEASIBLE:
                is_within_reference_technology = False
                membership_status = "outside_reference_technology"
            else:
                is_within_reference_technology = pd.NA
                membership_status = "unavailable_uncertified_additive_account"

            certification_reason = (
                "certified"
                if score_valid
                else lp_certificate.reason
                if not lp_certificate.certified
                else raw_account.reason
                if not raw_account.certified
                else published_account.reason
                if not published_account.weighted_slack_certified
                else "invalid_score_range"
            )
            reported_backend_violation = solution.max_primal_violation
            backend_violation = (
                0.0
                if reported_backend_violation is None
                else float(reported_backend_violation)
                if math.isfinite(reported_backend_violation)
                and reported_backend_violation >= 0.0
                else math.inf
            )
            diagnostic_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": 1,
                    "solver_status": solution.status.value,
                    "backend_solver_status": solution.status.value,
                    "raw_solver_status": solution.status.value,
                    "message": solution.message,
                    "iterations": solution.iterations,
                    "max_primal_violation": solution.max_primal_violation,
                    "objective_scale": objective_scale,
                    "lp_postsolve_certified": lp_certificate.certified,
                    "postsolve_certified": score_valid,
                    "certification_reason": certification_reason,
                    "max_constraint_violation": (
                        lp_certificate.max_constraint_violation
                    ),
                    "equality_violation": lp_certificate.equality_violation,
                    "max_bound_violation": lp_certificate.max_bound_violation,
                    "objective_residual": lp_certificate.objective_residual,
                    "duality_gap": lp_certificate.duality_gap,
                    "max_dual_violation": lp_certificate.max_dual_violation,
                    "complementarity_violation": (
                        lp_certificate.complementarity_violation
                    ),
                    "bound_marginals_used": lp_certificate.bound_marginals_used,
                    "backend_violation": backend_violation,
                    "raw_account_certified": raw_account.certified,
                    "raw_account_reason": raw_account.reason,
                    "raw_resource_account_violation": (raw_account.resource_violation),
                    "raw_service_account_violation": raw_account.service_violation,
                    "raw_rts_account_violation": raw_account.rts_violation,
                    "raw_nonnegativity_violation": (
                        raw_account.nonnegativity_violation
                    ),
                    "raw_weighted_slack_residual": (
                        raw_account.weighted_slack_residual
                    ),
                    "max_raw_economic_violation": (raw_account.max_economic_violation),
                    "published_account_certified": published_account.certified,
                    "published_account_reason": published_account.reason,
                    "published_quantity_account_certified": (
                        published_account.quantity_certified
                    ),
                    "published_weighted_slack_account_certified": (
                        published_account.weighted_slack_certified
                    ),
                    "published_resource_account_violation": (
                        published_account.resource_violation
                    ),
                    "published_service_account_violation": (
                        published_account.service_violation
                    ),
                    "published_rts_account_violation": (
                        published_account.rts_violation
                    ),
                    "published_nonnegativity_violation": (
                        published_account.nonnegativity_violation
                    ),
                    "published_weighted_slack_residual": (
                        published_account.weighted_slack_residual
                    ),
                    "max_published_economic_violation": (
                        published_account.max_economic_violation
                    ),
                    "economic_postsolve_certified": (
                        raw_account.certified and published_account.certified
                    ),
                    "economic_account_violation": max(
                        raw_account.max_economic_violation,
                        published_account.max_economic_violation,
                    ),
                    "published_peer_account_certified": peer_valid,
                    "published_peer_account_reason": peer_certificate.reason,
                    "peer_resource_account_violation": (
                        peer_certificate.resource_violation
                    ),
                    "peer_service_account_violation": (
                        peer_certificate.service_violation
                    ),
                    "peer_rts_account_violation": peer_certificate.rts_violation,
                    "max_published_peer_account_violation": (
                        peer_certificate.max_violation
                    ),
                    "published_dual_account_certified": dual_valid,
                    "published_dual_account_reason": dual_certificate.reason,
                    "published_dual_row_count": (dual_certificate.published_row_count),
                    "expected_dual_row_count": dual_certificate.expected_row_count,
                    "original_unit_dual_objective": (
                        dual_certificate.original_unit_dual_objective
                    ),
                    "original_unit_dual_objective_residual": (
                        dual_certificate.objective_residual
                    ),
                    "max_published_dual_account_violation": (
                        dual_certificate.max_violation
                    ),
                    "score_valid": score_valid,
                    "score_status": score_status,
                    "target_valid": target_valid,
                    "target_status": target_status,
                    "peer_valid": peer_valid,
                    "peer_status": peer_status,
                    "dual_valid": dual_valid,
                    "dual_status": dual_status,
                }
            )
            if peer_valid:
                intensity_rows.extend(candidate_intensity_rows)
            if dual_valid:
                dual_rows.extend(candidate_dual_rows)

            for (
                role,
                names,
                observed,
                targets,
                slacks,
                weights,
                strong_scales,
                strong_scaled_slacks,
                solver_scales,
                solver_scaled_slacks,
            ) in (
                (
                    "input",
                    data.input_names,
                    x_o,
                    input_targets,
                    input_slacks,
                    input_weights,
                    strong_input_scales,
                    strong_scaled_input_slacks,
                    input_scales,
                    solver_scaled_input_slacks,
                ),
                (
                    "output",
                    data.output_names,
                    y_o,
                    output_targets,
                    output_slacks,
                    output_weights,
                    strong_output_scales,
                    strong_scaled_output_slacks,
                    output_scales,
                    solver_scaled_output_slacks,
                ),
            ):
                for (
                    variable,
                    value,
                    target,
                    slack,
                    weight,
                    strong_scale,
                    strong_scaled_slack,
                    solver_scale,
                    solver_scaled_slack,
                ) in zip(
                    names,
                    observed,
                    targets,
                    slacks,
                    weights,
                    strong_scales,
                    strong_scaled_slacks,
                    solver_scales,
                    solver_scaled_slacks,
                    strict=True,
                ):
                    if target_valid:
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
                    if score_valid:
                        slack_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "slack": float(slack),
                                "weight": float(weight),
                                "scale": float(strong_scale),
                                "scaled_slack": float(strong_scaled_slack),
                                "solver_scale": float(solver_scale),
                                "solver_scaled_slack": float(solver_scaled_slack),
                            }
                        )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    **score_values,
                    "score_valid": score_valid,
                    "score_status": score_status,
                    "target_valid": target_valid,
                    "target_status": target_status,
                    "peer_valid": peer_valid,
                    "peer_status": peer_status,
                    "dual_valid": dual_valid,
                    "dual_status": dual_status,
                    "solver_status": solution.status.value,
                    "backend_solver_status": solution.status.value,
                    "raw_solver_status": solution.status.value,
                    "failure_reason": (pd.NA if score_valid else certification_reason),
                    "is_within_reference_technology": (is_within_reference_technology),
                    "self_in_reference": self_in_reference,
                    "membership_status": membership_status,
                    "model_family": self.model_family,
                    "orientation": "non-oriented",
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": reference.size,
                    "max_slack": max_slack if score_valid else np.nan,
                    "max_scaled_slack": max_scaled_slack if score_valid else np.nan,
                }
            )

        measure_metadata = self._measure_metadata(data, input_weights, output_weights)
        full_self_inclusive_reference = bool(
            reference_plan.kind is ReferenceKind.GLOBAL
            and reference_plan.unique_reference_sets == 1
            and np.array_equal(
                reference_plan.unique_rows[0],
                np.arange(data.n_dmus, dtype=np.int64),
            )
        )
        source_profile, source_profile_mismatches = self._source_profile(
            data,
            reference_plan.kind,
            full_self_inclusive_reference,
            input_weights,
            output_weights,
        )
        solver_primal_tolerance = self._solver_feasibility_tolerance("primal")
        solver_dual_tolerance = self._solver_feasibility_tolerance("dual")
        summary_frame = pd.DataFrame(summary_rows)
        summary_frame["base_reference_size"] = reference_plan.base_size_by_observation
        peer_eligibility_metadata = reference_plan.peer_eligibility_metadata()
        return DEAResult(
            summary_frame=summary_frame,
            slacks=pd.DataFrame(slack_rows, columns=_SLACK_COLUMNS),
            targets=pd.DataFrame(target_rows, columns=_TARGET_COLUMNS),
            intensities=pd.DataFrame(intensity_rows, columns=_INTENSITY_COLUMNS),
            duals=pd.DataFrame(dual_rows, columns=_DUAL_COLUMNS),
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
                            "family": self.model_family,
                            "orientation": "non_oriented",
                            "slack_aggregation": measure_metadata["weighting"],
                            "source_profile": source_profile,
                        },
                        "valuation": {
                            "kind": "slack_weights",
                            "source": measure_metadata["weighting"],
                            "input_weights": numeric_parameter_signature(
                                input_weights,
                                labels=data.input_names,
                            ),
                            "output_weights": numeric_parameter_signature(
                                output_weights,
                                labels=data.output_names,
                            ),
                        },
                        "evaluation_protocol": {"kind": appraisal_kind},
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                **measure_metadata,
                "orientation": "non-oriented",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                **(
                    {}
                    if peer_eligibility_metadata is None
                    else {"peer_eligibility": peer_eligibility_metadata}
                ),
                "solver": self.solver.name,
                "solver_primal_feasibility_tolerance": solver_primal_tolerance,
                "solver_dual_feasibility_tolerance": solver_dual_tolerance,
                "objective_weight_guard_tolerance": (
                    self._objective_weight_guard_tolerance()
                ),
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": len(compiled),
                "primary_solver_calls": primary_solver_calls,
                "secondary_solver_calls": 0,
                "solver_calls": primary_solver_calls,
                "additional_solver_calls": 0,
                "certificate_extra_solver_calls": 0,
                "postsolve_certificate": {
                    "kind": (
                        "solver_neutral_lp_and_original_quantity_additive_accounts"
                    ),
                    "lp_checks": (
                        "primal_rows",
                        "variable_bounds",
                        "objective_reconstruction",
                        "dual_feasibility",
                        "complementarity",
                        "strong_duality",
                    ),
                    "economic_checks": (
                        "raw_resource_service_rts_and_weighted_slack_account",
                        "published_resource_service_rts_account",
                        "published_weighted_slack_account",
                        "thresholded_peer_target_and_rts_reconstruction",
                        "published_original_unit_dual_objective_closure",
                    ),
                    "failure_scope": "per_observation_and_per_claim",
                    "additional_solver_calls": 0,
                },
                "source_profile": source_profile,
                "source_profile_matches": not source_profile_mismatches,
                "source_profile_mismatches": source_profile_mismatches,
                "numerical_formulation": (
                    "anchored_vrs_or_level_scaled_rts_balances_with_common_"
                    "objective_scaling"
                ),
                "strong_status_basis": ("maximum_reference_deviation_scaled_slack"),
                "reported_scaled_slack_policy": (
                    "maximum_reference_deviation_from_evaluated_account"
                ),
                "peer_reporting_policy": ("intensity_or_material_target_contribution"),
            },
        )


class RangeAdjustedDEA(AdditiveDEA):
    """Range-adjusted measure (RAM) on a VRS additive technology.

    RAM uses one common data range per input and output. Its normalized
    inefficiency is bounded in ``[0, 1]`` and its native efficiency is one
    minus that distance. Cooper--Park--Pastor (1999) direct analysts to omit
    a zero-range coordinate and set its associated slack to zero. DEAPack
    retains the corresponding balance with zero objective weight; when the
    range and VRS reference populations coincide, that balance forces the
    same zero slack and is source-equivalent.

    A panel must request ``reference="global"`` explicitly. This prevents an
    automatic contemporaneous reference rule from being combined silently
    with data-wide ranges that include other periods.
    """

    model_family = "range_adjusted"
    _registry_method_id = "static.ram"

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
            returns_to_scale=ReturnsToScale.VRS,
            reference=reference,
            peer_eligibility=peer_eligibility,
            solver=solver,
            solver_options=solver_options,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )

    def _validate_data(self, data: DEAData) -> None:
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "RangeAdjustedDEA does not infer how undesirable outputs are "
                "disposed. Use an explicit environmental technology/measure."
            )
        if self.reference.kind not in {ReferenceKind.AUTO, ReferenceKind.GLOBAL}:
            raise ModelSpecificationError(
                "canonical RAM currently requires one global range and global "
                "reference technology"
            )
        if data.is_panel and self.reference.kind is ReferenceKind.AUTO:
            raise ModelSpecificationError(
                "panel RAM requires reference='global' explicitly; this confirms "
                "that ranges and the frontier may use all periods"
            )

    def _weight_vectors(self, data: DEAData) -> tuple[np.ndarray, np.ndarray]:
        dimensions = data.n_inputs + data.n_outputs
        input_ranges = np.ptp(data.inputs, axis=0)
        output_ranges = np.ptp(data.outputs, axis=0)
        input_weights = np.divide(
            1.0,
            dimensions * input_ranges,
            out=np.zeros_like(input_ranges),
            where=input_ranges > 0,
        )
        output_weights = np.divide(
            1.0,
            dimensions * output_ranges,
            out=np.zeros_like(output_ranges),
            where=output_ranges > 0,
        )
        input_weights.setflags(write=False)
        output_weights.setflags(write=False)
        return input_weights, output_weights

    def _source_profile(
        self,
        data: DEAData,
        reference_kind: ReferenceKind,
        reference_is_full_self_inclusive: bool,
        input_weights: np.ndarray,
        output_weights: np.ndarray,
    ) -> tuple[str, tuple[str, ...]]:
        """Identify the exact Cooper--Park--Pastor (1999) RAM profile."""

        mismatches: list[str] = []
        input_ranges = np.ptp(data.inputs, axis=0)
        output_ranges = np.ptp(data.outputs, axis=0)
        if self.returns_to_scale is not ReturnsToScale.VRS:
            mismatches.append("returns_to_scale_is_not_vrs")
        if data.is_panel:
            mismatches.append("data_are_not_one_cross_section")
        if (
            reference_kind is not ReferenceKind.GLOBAL
            or not reference_is_full_self_inclusive
        ):
            mismatches.append("reference_is_not_the_full_self_inclusive_sample")
        dimensions = data.n_inputs + data.n_outputs
        expected_input = np.divide(
            1.0,
            dimensions * input_ranges,
            out=np.zeros_like(input_ranges),
            where=input_ranges > 0.0,
        )
        expected_output = np.divide(
            1.0,
            dimensions * output_ranges,
            out=np.zeros_like(output_ranges),
            where=output_ranges > 0.0,
        )
        if not np.array_equal(input_weights, expected_input) or not np.array_equal(
            output_weights,
            expected_output,
        ):
            mismatches.append("slack_weights_are_not_source_range_weights")

        profile = (
            "cooper_park_pastor_1999_eq_17_18_20_23"
            if not mismatches
            else "deapack_ram_extension"
        )
        return profile, tuple(mismatches)

    def _summary_values(
        self,
        distance: float,
        max_slack: float,
    ) -> dict[str, Any]:
        if not -self.tolerance <= distance <= 1.0 + self.tolerance:
            raise RuntimeError(
                "RAM distance fell outside its theoretical [0, 1] bounds; "
                "inspect solver diagnostics and data scaling"
            )
        bounded_distance = float(np.clip(distance, 0.0, 1.0))
        efficiency = 1.0 - bounded_distance
        return {
            "score": efficiency,
            "efficiency": efficiency,
            "distance": bounded_distance,
            "is_efficient": bool(max_slack <= self.tolerance),
        }

    def _measure_metadata(
        self,
        data: DEAData,
        input_weights: np.ndarray,
        output_weights: np.ndarray,
    ) -> dict[str, Any]:
        return {
            "model_family": self.model_family,
            "native_score": "ram_efficiency",
            "native_distance": "ram_inefficiency",
            "score_direction": "higher_is_better",
            "efficiency_transform": "one_minus_distance",
            "weighting": "range",
            "normalization": "sample_range",
            "range_scope": "data",
            "range_population": (
                "base_global_data_before_peer_eligibility"
                if self.peer_eligibility is not None
                else "identical_to_global_reference_population"
            ),
            "input_ranges": tuple(
                (name, float(value))
                for name, value in zip(
                    data.input_names, np.ptp(data.inputs, axis=0), strict=True
                )
            ),
            "output_ranges": tuple(
                (name, float(value))
                for name, value in zip(
                    data.output_names, np.ptp(data.outputs, axis=0), strict=True
                )
            ),
            "input_weights": tuple(
                (name, float(weight))
                for name, weight in zip(data.input_names, input_weights, strict=True)
            ),
            "output_weights": tuple(
                (name, float(weight))
                for name, weight in zip(data.output_names, output_weights, strict=True)
            ),
            "zero_range_policy": (
                "zero_objective_weight_with_vrs_balance_forced_zero_slack"
            ),
            "zero_range_policy_source": "cooper_park_pastor_1999_section_8",
        }


RAM = RangeAdjustedDEA
"""Historical discoverability alias for :class:`RangeAdjustedDEA`."""

WeightedAdditiveDEA = AdditiveDEA
"""Discoverability alias; weights are parameters of :class:`AdditiveDEA`."""
