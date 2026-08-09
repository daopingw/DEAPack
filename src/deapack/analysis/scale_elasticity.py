"""One-sided radial scale elasticity at selected VRS targets."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .._registry import data_role_schema, registry_metadata
from ..data import DEAData
from ..enums import Orientation, parse_enum
from ..results import DEAResult
from ..solvers import LPSolver
from ..specs import ReferenceSpec, SolverOptions
from .local_rts import local_returns_to_scale

_METHOD_ID = "analysis.scale_elasticity.local.radial_vrs"


@dataclass(frozen=True, slots=True)
class _ElasticityPair:
    """Resolved one-sided elasticities and their operating interpretation."""

    right: float
    left: float
    right_exists: bool | None
    left_exists: bool | None
    right_extended: bool | None
    left_extended: bool | None
    right_response: str
    left_response: str
    status: str
    valid: bool
    domain_valid: bool
    economic_certified: bool
    right_valid: bool
    left_valid: bool
    right_status: str
    left_status: str
    max_transform_violation: float
    failure_kind: str


@dataclass(frozen=True, slots=True)
class _TransformedEndpoint:
    """One independently checked support-to-elasticity transformation."""

    value: float
    valid: bool
    perturbation_exists: bool | None
    extended: bool | None
    status: str
    identity_violation: float


def _endpoint_value(
    delta: float,
    orientation: Orientation,
    *,
    side: str,
    tolerance: float,
) -> _TransformedEndpoint:
    """Transform one support endpoint and validate the radial VRS domain."""

    if math.isnan(delta):
        return _TransformedEndpoint(
            value=math.nan,
            valid=False,
            perturbation_exists=None,
            extended=None,
            status="missing_support_endpoint",
            identity_violation=math.inf,
        )

    asymptotic_boundary = False
    if orientation is Orientation.OUTPUT:
        if delta == -math.inf:
            value = math.inf
            identity_violation = 0.0
        elif delta == math.inf:
            return _TransformedEndpoint(
                value=math.nan,
                valid=False,
                perturbation_exists=None,
                extended=None,
                status="undefined_radial_domain",
                identity_violation=math.inf,
            )
        else:
            value = 1.0 - delta
            identity_violation = abs(value + delta - 1.0)
    elif math.isinf(delta):
        if delta > 0:
            value = 0.0
            identity_violation = 0.0
            asymptotic_boundary = True
        else:
            return _TransformedEndpoint(
                value=math.nan,
                valid=False,
                perturbation_exists=None,
                extended=None,
                status="undefined_radial_domain",
                identity_violation=math.inf,
            )
    else:
        denominator = 1.0 + delta
        if denominator < -tolerance:
            return _TransformedEndpoint(
                value=math.nan,
                valid=False,
                perturbation_exists=None,
                extended=None,
                status="undefined_radial_domain",
                identity_violation=abs(min(denominator, 0.0)),
            )
        value = math.inf if abs(denominator) <= tolerance else 1.0 / denominator
        identity_violation = (
            0.0 if math.isinf(value) else abs(value * denominator - 1.0)
        )

    if value == -math.inf or value < -tolerance:
        return _TransformedEndpoint(
            value=math.nan,
            valid=False,
            perturbation_exists=None,
            extended=None,
            status="undefined_radial_domain",
            identity_violation=math.inf,
        )
    if -tolerance <= value < 0:
        value = 0.0

    # Ordinary free-disposal VRS always permits a small input expansion.
    # A positive-infinite right response therefore signals an inconsistent
    # support transformation rather than a usable scale-up elasticity.
    if side == "right" and value == math.inf:
        return _TransformedEndpoint(
            value=math.nan,
            valid=False,
            perturbation_exists=None,
            extended=None,
            status="undefined_right_expansion_boundary",
            identity_violation=math.inf,
        )
    extended = not math.isfinite(value)
    return _TransformedEndpoint(
        value=float(value),
        valid=bool(
            math.isfinite(identity_violation) and identity_violation <= tolerance
        ),
        perturbation_exists=not extended,
        extended=extended,
        status=(
            "identified_extended_boundary"
            if extended
            else (
                "identified_asymptotic_boundary"
                if asymptotic_boundary
                else "identified"
            )
        ),
        identity_violation=identity_violation,
    )


def _response_label(
    delta: float,
    *,
    perturbation_exists: bool,
    tolerance: float,
) -> str:
    """Translate a support sign into a proportional operating response."""

    if not perturbation_exists:
        return "not_locally_feasible"
    if delta < -tolerance:
        return "more_than_proportional"
    if delta > tolerance:
        return "less_than_proportional"
    return "proportional"


def _transform_pair(
    row: pd.Series,
    orientation: Orientation,
    *,
    tolerance: float,
) -> _ElasticityPair:
    """Transform the shared Banker--Thrall support interval."""

    source_valid = all(
        isinstance(row.get(column), (bool, np.bool_)) and bool(row.get(column))
        for column in (
            "analysis_valid",
            "support_interval_valid",
            "economic_classification_certified",
            "support_intercept_lower_valid",
            "support_intercept_upper_valid",
        )
    )
    if row["solver_status"] != "optimal" or not source_valid:
        source_status = str(row.get("support_interval_status", "component_failure"))
        backend_status = str(row.get("backend_solver_status", "unknown"))
        if source_status == "projection_failure":
            failure_kind = "projection_failure"
        elif source_status.startswith("mathematically_undefined"):
            failure_kind = "mathematically_undefined_domain"
        elif source_status == "unverified_unbounded_ray":
            failure_kind = "unverified_unbounded_ray"
        elif backend_status not in {"optimal", "unbounded"}:
            failure_kind = "backend_or_numerical_failure"
        else:
            failure_kind = "uncertified_component"
        return _ElasticityPair(
            right=math.nan,
            left=math.nan,
            right_exists=None,
            left_exists=None,
            right_extended=None,
            left_extended=None,
            right_response="indeterminate",
            left_response="indeterminate",
            status=source_status,
            valid=False,
            domain_valid=False,
            economic_certified=False,
            right_valid=False,
            left_valid=False,
            right_status="not_available_without_certified_support_interval",
            left_status="not_available_without_certified_support_interval",
            max_transform_violation=math.inf,
            failure_kind=failure_kind,
        )

    lower = float(row["support_intercept_lower"])
    upper = float(row["support_intercept_upper"])
    right_endpoint = _endpoint_value(
        upper,
        orientation,
        side="right",
        tolerance=tolerance,
    )
    left_endpoint = _endpoint_value(
        lower,
        orientation,
        side="left",
        tolerance=tolerance,
    )
    right = right_endpoint.value
    left = left_endpoint.value
    ordered = (
        right_endpoint.valid
        and left_endpoint.valid
        and (
            left == math.inf
            or right <= left + tolerance * max(1.0, abs(right), abs(left))
        )
    )
    if not ordered:
        domain_valid = bool(right_endpoint.valid and left_endpoint.valid)
        return _ElasticityPair(
            right=math.nan,
            left=math.nan,
            right_exists=None,
            left_exists=None,
            right_extended=None,
            left_extended=None,
            right_response="indeterminate",
            left_response="indeterminate",
            status=(
                "inconsistent_support_transform"
                if domain_valid
                else "mathematically_undefined"
            ),
            valid=False,
            domain_valid=domain_valid,
            economic_certified=False,
            right_valid=right_endpoint.valid,
            left_valid=left_endpoint.valid,
            right_status=right_endpoint.status,
            left_status=left_endpoint.status,
            max_transform_violation=max(
                right_endpoint.identity_violation,
                left_endpoint.identity_violation,
            ),
            failure_kind=(
                "inconsistent_economic_transform"
                if domain_valid
                else "mathematically_undefined_domain"
            ),
        )

    right_extended = bool(right_endpoint.extended)
    left_extended = bool(left_endpoint.extended)
    right_exists = bool(right_endpoint.perturbation_exists)
    left_exists = bool(left_endpoint.perturbation_exists)
    classification = str(row["rts_classification"])
    scale = max(
        1.0,
        abs(right) if math.isfinite(right) else 1.0,
        abs(left) if math.isfinite(left) else 1.0,
    )
    economic_identity = (
        (classification == "increasing" and right > 1.0 + tolerance / scale)
        or (classification == "decreasing" and left < 1.0 - tolerance / scale)
        or (
            classification == "constant"
            and right <= 1.0 + tolerance * scale
            and left >= 1.0 - tolerance * scale
        )
    )
    max_transform_violation = max(
        right_endpoint.identity_violation,
        left_endpoint.identity_violation,
        max(right - left, 0.0) / scale,
    )
    economic_certified = bool(
        economic_identity
        and math.isfinite(max_transform_violation)
        and max_transform_violation <= tolerance
    )
    if not economic_certified:
        return _ElasticityPair(
            right=math.nan,
            left=math.nan,
            right_exists=None,
            left_exists=None,
            right_extended=None,
            left_extended=None,
            right_response="indeterminate",
            left_response="indeterminate",
            status="inconsistent_economic_classification",
            valid=False,
            domain_valid=True,
            economic_certified=False,
            right_valid=True,
            left_valid=True,
            right_status=right_endpoint.status,
            left_status=left_endpoint.status,
            max_transform_violation=max_transform_violation,
            failure_kind="inconsistent_economic_classification",
        )
    return _ElasticityPair(
        right=right,
        left=left,
        right_exists=right_exists,
        left_exists=left_exists,
        right_extended=right_extended,
        left_extended=left_extended,
        right_response=_response_label(
            upper,
            perturbation_exists=right_exists,
            tolerance=tolerance,
        ),
        left_response=_response_label(
            lower,
            perturbation_exists=left_exists,
            tolerance=tolerance,
        ),
        status=(
            "identified_extended_boundary"
            if right_extended or left_extended
            else (
                "identified_asymptotic_boundary"
                if "identified_asymptotic_boundary"
                in {right_endpoint.status, left_endpoint.status}
                else "identified"
            )
        ),
        valid=True,
        domain_valid=True,
        economic_certified=True,
        right_valid=True,
        left_valid=True,
        right_status=right_endpoint.status,
        left_status=left_endpoint.status,
        max_transform_violation=max_transform_violation,
        failure_kind="none",
    )


def scale_elasticity(
    data: DEAData,
    *,
    orientation: Orientation | str = Orientation.INPUT,
    reference: ReferenceSpec | str | None = None,
    solver: LPSolver | None = None,
    solver_options: SolverOptions | None = None,
    tolerance: float = 1e-7,
    rts_tolerance: float | None = None,
) -> DEAResult:
    """Estimate left and right radial scale elasticity at selected VRS targets.

    The right endpoint quantifies the local output response to a proportional
    increase in all resources. The left endpoint quantifies the output loss
    associated with a proportional resource contraction. At a frontier kink
    the two responses can differ.

    This operator reuses the fixed Pareto-efficient projection and complete
    supporting-intercept interval returned by :func:`local_returns_to_scale`.
    It does not solve a second projection or silently choose one supporting
    hyperplane. For an inefficient observation, every elasticity therefore
    belongs to the same explicitly retained selected target as the local
    returns-to-scale result.

    An infinite mathematical endpoint is reported as an extended value, while
    the corresponding perturbation-existence flag is false. This distinction
    prevents a boundary with no local contraction from being presented as an
    actionable increasing-returns recommendation.
    """

    normalized_orientation = parse_enum(orientation, Orientation, "orientation")
    local_result = local_returns_to_scale(
        data,
        orientation=normalized_orientation,
        reference=reference,
        solver=solver,
        solver_options=solver_options,
        tolerance=tolerance,
        rts_tolerance=rts_tolerance,
    )
    interval_tolerance = float(local_result.metadata["rts_tolerance"])
    summary = local_result.summary()
    pairs = [
        _transform_pair(
            row,
            normalized_orientation,
            tolerance=interval_tolerance,
        )
        for _, row in summary.iterrows()
    ]

    summary["scale_elasticity_right"] = [pair.right for pair in pairs]
    summary["scale_elasticity_left"] = [pair.left for pair in pairs]
    summary["scale_up_perturbation_exists"] = pd.array(
        [pd.NA if pair.right_exists is None else pair.right_exists for pair in pairs],
        dtype="boolean",
    )
    summary["scale_down_perturbation_exists"] = pd.array(
        [pd.NA if pair.left_exists is None else pair.left_exists for pair in pairs],
        dtype="boolean",
    )
    summary["scale_elasticity_right_is_extended"] = pd.array(
        [
            pd.NA if pair.right_extended is None else pair.right_extended
            for pair in pairs
        ],
        dtype="boolean",
    )
    summary["scale_elasticity_left_is_extended"] = pd.array(
        [pd.NA if pair.left_extended is None else pair.left_extended for pair in pairs],
        dtype="boolean",
    )
    summary["scale_up_response"] = [pair.right_response for pair in pairs]
    summary["scale_down_response"] = [pair.left_response for pair in pairs]
    summary["scale_elasticity_status"] = [pair.status for pair in pairs]
    summary["scale_elasticity_valid"] = pd.array(
        [pair.valid for pair in pairs],
        dtype="boolean",
    )
    summary["scale_elasticity_domain_valid"] = pd.array(
        [pair.domain_valid for pair in pairs],
        dtype="boolean",
    )
    summary["scale_elasticity_economic_postsolve_certified"] = pd.array(
        [pair.economic_certified for pair in pairs],
        dtype="boolean",
    )
    summary["scale_elasticity_right_valid"] = pd.array(
        [pair.right_valid for pair in pairs],
        dtype="boolean",
    )
    summary["scale_elasticity_left_valid"] = pd.array(
        [pair.left_valid for pair in pairs],
        dtype="boolean",
    )
    summary["scale_elasticity_right_status"] = [pair.right_status for pair in pairs]
    summary["scale_elasticity_left_status"] = [pair.left_status for pair in pairs]
    summary["scale_elasticity_max_transform_violation"] = [
        pair.max_transform_violation for pair in pairs
    ]
    summary["scale_elasticity_failure_kind"] = [pair.failure_kind for pair in pairs]
    summary["scale_elasticity_is_unique"] = pd.array(
        [
            (
                pd.NA
                if pair.right_exists is None
                else bool(row["support_intercept_is_unique"])
            )
            for pair, (_, row) in zip(pairs, summary.iterrows(), strict=True)
        ],
        dtype="boolean",
    )
    summary["aggregate_rts_classification"] = summary["rts_classification"]
    summary["model_family"] = "scale_elasticity"
    summary["analysis_valid"] = summary["scale_elasticity_valid"]
    summary["analysis_status"] = summary["scale_elasticity_status"]

    local_spec = local_result.metadata["expanded_spec"]
    formula = (
        "epsilon_right=1/(1+delta_upper);epsilon_left=1/(1+delta_lower)"
        if normalized_orientation is Orientation.INPUT
        else "epsilon_right=1-delta_upper;epsilon_left=1-delta_lower"
    )
    return DEAResult(
        summary_frame=summary,
        slacks=local_result.slacks.copy(),
        targets=local_result.targets.copy(),
        intensities=local_result.intensities.copy(),
        diagnostics=local_result.diagnostics.copy(),
        metadata={
            **registry_metadata(
                _METHOD_ID,
                {
                    "context": {
                        "purpose": "quantify_local_scale_response",
                        "sample": "panel" if data.is_panel else "cross_section",
                    },
                    "graph": {"kind": "black_box"},
                    "data_roles": {
                        "inputs": "productive_resources",
                        "outputs": "desirable_services",
                        "bad_outputs": "excluded",
                        **data_role_schema(data),
                    },
                    "technology": {
                        "family": "convex_envelopment",
                        "returns_to_scale": "vrs",
                        "disposal": "ordinary_free",
                    },
                    "estimator": {
                        "estimator_id": "estimator.full.dea",
                        "kind": "full_frontier",
                        "family": "dea_envelopment",
                    },
                    "reference": {
                        **dict(local_spec["reference"]),
                        "matched_across_projection_support_and_elasticity": True,
                    },
                    "performance": {
                        "family": "radial_scale_elasticity",
                        "orientation": normalized_orientation.value,
                        "native_result": "left_and_right_elasticity",
                    },
                    "valuation": {"kind": "none"},
                    "evaluation_protocol": {
                        "kind": "selected_projection_support_transform",
                        "projection_completion": "maximize_row_scaled_slacks",
                        "projection_selection": local_result.metadata[
                            "projection_policy"
                        ],
                        "support_extrema": "all_normalized_supports_at_target",
                    },
                    "analysis": {
                        "kind": "one_sided_scale_elasticity",
                        "scope": "selected_projection",
                        "formula": formula,
                        "aggregate_rts_rule": "banker_thrall_support_interval",
                        "projection_invariance_claimed": False,
                    },
                    "uncertainty": {"kind": "deterministic"},
                },
            ),
            "model_family": "scale_elasticity",
            "orientation": normalized_orientation.value,
            "reference_kind": local_result.metadata["reference_kind"],
            "projection_scope": "selected_projection",
            "projection_policy": local_result.metadata["projection_policy"],
            "projection_invariance_claimed": False,
            "support_intercept_sign_convention": local_result.metadata[
                "support_intercept_sign_convention"
            ],
            "endpoint_formula": formula,
            "endpoint_order": "epsilon_right <= epsilon_left",
            "response_labels": {
                "more_than_proportional": "elasticity > 1",
                "proportional": "elasticity = 1 within rts_tolerance",
                "less_than_proportional": "elasticity < 1",
                "not_locally_feasible": "one_sided perturbation does not exist",
            },
            "aggregate_rts_identity": {
                "increasing": "1 < epsilon_right <= epsilon_left",
                "decreasing": "epsilon_right <= epsilon_left < 1",
                "constant": "epsilon_right <= 1 <= epsilon_left",
            },
            "tolerance": float(tolerance),
            "rts_tolerance": interval_tolerance,
            "solver": local_result.metadata["solver"],
            "compiled_reference_sets": local_result.metadata["compiled_reference_sets"],
            "projection_solver_calls": local_result.metadata["projection_solver_calls"],
            "support_endpoint_solver_calls": local_result.metadata[
                "support_endpoint_solver_calls"
            ],
            "solver_calls": local_result.metadata["solver_calls"],
            "additional_solver_calls": 0,
            "postsolve_certificate": {
                "source_support_interval": (
                    "requires_both_endpoint_and_economic_classification_certificates"
                ),
                "endpoint_domain": (
                    "orientation_specific_radial_vrs_domain_and_extended_boundary"
                ),
                "transform_identity": (
                    "support_endpoint_formula_order_and_aggregate_rts_identity"
                ),
                "undefined_domain_policy": (
                    "separate_from_backend_or_numerical_failure"
                ),
                "additional_solver_calls": 0,
            },
            "components": {
                "local_returns_to_scale": local_result.metadata,
            },
        },
    )


__all__ = ["scale_elasticity"]
