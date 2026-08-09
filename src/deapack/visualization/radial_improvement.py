"""Prepared data for one certified classical radial improvement plan.

This module is deliberately backend- and solver-free.  It reads only a fitted
ordinary radial result and reconstructs two distinct operating claims: the
phase-one common proportional adjustment and the phase-two variable-specific
Pareto--Koopmans completion.  Peer and dual publication are not prerequisites
for this original-unit target ledger.
"""

from __future__ import annotations

import math
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from ._types import PlotNotAvailableError

_METHOD_ID = "static.radial"
_TARGET_COMPLETION_ID = "evaluation.target_completion.pareto_koopmans"
_SUPPORTED_ORIENTATIONS = frozenset({"input", "output"})
_SUPPORTED_RTS = frozenset({"crs", "vrs", "nirs", "ndrs"})
_LABEL_LIMIT = 48
_DMU_LABEL_LIMIT = 36
_PERIOD_LABEL_LIMIT = 24
_VARIABLE_LABEL_LIMIT = 32
_MISSING_PERIOD_KEY = object()

_SUMMARY_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "score",
        "efficiency",
        "score_valid",
        "score_status",
        "is_efficient",
        "is_radially_efficient",
        "is_within_reference_technology",
        "solver_status",
        "primary_solver_status",
        "completion_solver_status",
        "completion_valid",
        "completion_status",
        "target_valid",
        "target_status",
        "model_family",
        "orientation",
        "returns_to_scale",
        "max_slack",
        "max_scaled_slack",
        "efficiency_denominator_valid",
    }
)
_TARGET_COLUMNS = frozenset(
    {"dmu_id", "period", "role", "variable", "observed", "target"}
)
_SLACK_COLUMNS = frozenset({"dmu_id", "period", "role", "variable", "slack"})
_DIAGNOSTIC_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "phase",
        "solver_status",
        "certification_reason",
        "economic_certification_reason",
        "lp_postsolve_certified",
        "postsolve_certified",
        "economic_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
    }
)


@dataclass(frozen=True, slots=True)
class RadialImprovementPlotData:
    """Detached original-unit account for one classical radial operating plan."""

    dmu_id: object
    period: object | None
    dmu_label: str
    period_label: str | None
    native_score: float
    efficiency: float
    orientation: str
    returns_to_scale: str
    reference_kind: str
    is_radially_efficient: bool
    is_efficient: bool
    variables: pd.DataFrame
    target_status: str
    max_reconstruction_residual: float
    provenance: tuple[tuple[str, str], ...]

    @property
    def variable_count(self) -> int:
        """Number of resource and desirable-service rows in the plan."""
        return len(self.variables)

    @property
    def slack_completed_variable_count(self) -> int:
        """Number of variables receiving a positive completion adjustment."""
        return int((self.variables["slack_completion"] > 0.0).sum())


@dataclass(frozen=True, slots=True)
class _RadialContract:
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    orientation: str
    returns_to_scale: str
    reference_kind: str


def _missing_scalar(value: object) -> bool:
    try:
        marker = pd.isna(value)
    except (TypeError, ValueError) as error:
        raise PlotNotAvailableError(
            "radial improvement identifiers must be scalar values"
        ) from error
    if isinstance(marker, (bool, np.bool_)):
        return bool(marker)
    raise PlotNotAvailableError("radial improvement identifiers must be scalar values")


def _finite(value: object) -> bool:
    if _missing_scalar(value):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _true(value: object) -> bool:
    if _missing_scalar(value):
        return False
    return isinstance(value, (bool, np.bool_)) and bool(value)


def _explicit_boolean(value: object, *, field: str) -> bool:
    if _missing_scalar(value) or not isinstance(value, (bool, np.bool_)):
        raise PlotNotAvailableError(
            f"radial improvement plotting requires a Boolean {field}"
        )
    return bool(value)


def _display(value: object) -> str | None:
    if value is None or _missing_scalar(value):
        return None
    text = str(getattr(value, "value", value)).strip()
    return text or None


def _bounded_display_text(
    value: object,
    *,
    fallback: str,
    limit: int = _LABEL_LIMIT,
) -> str:
    """Return compact control-free text before it reaches a renderer."""
    if _missing_scalar(value):
        return fallback
    text = str(getattr(value, "value", value))
    text = "".join(
        " " if unicodedata.category(character).startswith("C") else character
        for character in text
    )
    text = " ".join(text.split()).strip()
    if not text:
        return fallback
    if len(text) > limit:
        return f"{text[: limit - 1]}\N{HORIZONTAL ELLIPSIS}"
    return text


def _variable_label(variable: str) -> str:
    text = _bounded_display_text(
        variable.replace("_", " "),
        fallback="Variable",
        limit=_VARIABLE_LABEL_LIMIT,
    )
    words = text.split()
    if words and all(word.isalpha() and word.islower() for word in words):
        return " ".join(word.capitalize() for word in words)
    return text


def _metadata(result: Any) -> Mapping[str, Any]:
    metadata = getattr(result, "metadata", None)
    if not isinstance(metadata, Mapping):
        raise PlotNotAvailableError(
            "radial improvement plotting requires fitted result metadata"
        )
    return metadata


def radial_improvement_route(result: Any) -> bool:
    """Whether improvement dispatch should apply the exact radial contract."""
    try:
        metadata = _metadata(result)
        method_id = metadata.get("method_id")
        return isinstance(method_id, str) and method_id == _METHOD_ID
    except (PlotNotAvailableError, TypeError, ValueError):
        return False


def _require_columns(
    frame: pd.DataFrame,
    required: frozenset[str],
    *,
    table: str,
) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise PlotNotAvailableError(
            "radial improvement plotting requires "
            f"{table} columns: {', '.join(sorted(missing))}"
        )


def _tolerances(metadata: Mapping[str, Any]) -> tuple[float, float]:
    value = metadata.get("tolerance")
    if not _finite(value) or float(value) <= 0.0:
        raise PlotNotAvailableError(
            "radial improvement plotting requires the fitted numerical tolerance"
        )
    model_tolerance = float(value)
    return model_tolerance, 10.0 * model_tolerance


def _named_sequence(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)) or not value:
        raise PlotNotAvailableError(
            f"radial improvement plotting requires declared {field}"
        )
    resolved = tuple(value)
    if not all(isinstance(item, str) and item.strip() for item in resolved):
        raise PlotNotAvailableError(
            f"radial improvement plotting requires named {field}"
        )
    if len(set(resolved)) != len(resolved):
        raise PlotNotAvailableError(
            f"radial improvement plotting requires unique {field}"
        )
    return resolved


def _semantic_contract(metadata: Mapping[str, Any]) -> _RadialContract:
    if metadata.get("method_id") != _METHOD_ID:
        raise PlotNotAvailableError(
            "radial improvement plotting is defined only for exact "
            "method_id='static.radial'"
        )
    orientation = _display(metadata.get("orientation"))
    returns_to_scale = _display(metadata.get("returns_to_scale"))
    if orientation not in _SUPPORTED_ORIENTATIONS:
        raise PlotNotAvailableError(
            "radial improvement plotting requires input or output orientation"
        )
    if returns_to_scale not in _SUPPORTED_RTS:
        raise PlotNotAvailableError(
            "radial improvement plotting requires CRS, VRS, NIRS, or NDRS"
        )
    expected_score = "theta" if orientation == "input" else "phi"
    expected_transform = "identity" if orientation == "input" else "reciprocal"
    expected_metadata = {
        "model_family": "radial",
        "native_score": expected_score,
        "efficiency_transform": expected_transform,
        "target_completion_id": _TARGET_COMPLETION_ID,
        "target_completion_scale_anchor": "evaluated_observation",
        "slack_phase": "maximize_row_scaled_sum",
    }
    if not _true(metadata.get("compute_slacks")) or not _true(
        metadata.get("slack_target_unit_invariant")
    ):
        raise PlotNotAvailableError(
            "radial improvement plotting requires unit-stable slack completion"
        )
    if any(
        _display(metadata.get(field)) != expected
        for field, expected in expected_metadata.items()
    ):
        raise PlotNotAvailableError(
            "radial improvement metadata does not declare the fitted proportional "
            "and Pareto--Koopmans completion account"
        )

    certificate = metadata.get("postsolve_certificate")
    expected_certificate = {
        "primary_lp": "solver_neutral_primal_dual_kkt_and_strong_duality",
        "primary_economic": "radial_objective_production_balances_and_rts",
        "slack_completion_lp": "solver_neutral_primal_dual_kkt_and_strong_duality",
        "slack_completion_economic": (
            "row_scaled_slack_objective_target_balances_and_rts"
        ),
    }
    if not isinstance(certificate, Mapping) or any(
        _display(certificate.get(field)) != expected
        for field, expected in expected_certificate.items()
    ):
        raise PlotNotAvailableError(
            "radial improvement plotting requires declared primary and completion "
            "postsolve certificates"
        )

    expanded = metadata.get("expanded_spec")
    if not isinstance(expanded, Mapping):
        raise PlotNotAvailableError(
            "radial improvement plotting requires expanded fitted semantics"
        )
    context = expanded.get("context")
    graph = expanded.get("graph")
    technology = expanded.get("technology")
    estimator = expanded.get("estimator")
    performance = expanded.get("performance")
    valuation = expanded.get("valuation")
    analysis = expanded.get("analysis")
    uncertainty = expanded.get("uncertainty")
    if (
        not isinstance(context, Mapping)
        or _display(context.get("purpose")) != "operating_performance_benchmarking"
        or _display(context.get("sample")) not in {"cross_section", "panel"}
        or not isinstance(graph, Mapping)
        or _display(graph.get("kind")) != "black_box"
        or not isinstance(technology, Mapping)
        or _display(technology.get("family")) != "convex_envelopment"
        or _display(technology.get("returns_to_scale")) != returns_to_scale
        or _display(technology.get("disposal")) != "ordinary_free"
        or not isinstance(estimator, Mapping)
        or _display(estimator.get("estimator_id")) != "estimator.full.dea"
        or _display(estimator.get("kind")) != "full_frontier"
        or _display(estimator.get("family")) != "dea_envelopment"
        or not isinstance(performance, Mapping)
        or _display(performance.get("family")) != "radial"
        or _display(performance.get("orientation")) != orientation
        or not _true(performance.get("slack_refinement"))
        or not isinstance(valuation, Mapping)
        or _display(valuation.get("kind")) != "none"
        or not isinstance(analysis, Mapping)
        or _display(analysis.get("kind")) != "direct_model_fit"
        or not isinstance(uncertainty, Mapping)
        or _display(uncertainty.get("kind")) != "deterministic"
    ):
        raise PlotNotAvailableError(
            "radial improvement expanded semantics do not preserve the ordinary "
            "black-box radial account"
        )

    reference = expanded.get("reference")
    reference_kind = (
        _display(reference.get("kind")) if isinstance(reference, Mapping) else None
    )
    if reference_kind is None or reference_kind != _display(
        metadata.get("reference_kind")
    ):
        raise PlotNotAvailableError(
            "radial improvement reference declarations disagree"
        )

    evaluation = expanded.get("evaluation_protocol")
    if (
        not isinstance(evaluation, Mapping)
        or _display(evaluation.get("kind")) != "self_appraisal"
        or _display(evaluation.get("target_completion_id")) != _TARGET_COMPLETION_ID
        or _display(evaluation.get("target_completion_scale_anchor"))
        != "evaluated_observation"
        or _display(evaluation.get("target_uniqueness")) != "not_assessed"
        or _display(evaluation.get("secondary_objective"))
        != "maximize_row_scaled_slacks"
    ):
        raise PlotNotAvailableError(
            "radial improvement plotting requires the fitted primary-and-completion "
            "evaluation protocol"
        )

    data_roles = expanded.get("data_roles")
    variables = data_roles.get("variables") if isinstance(data_roles, Mapping) else None
    if (
        not isinstance(data_roles, Mapping)
        or _display(data_roles.get("inputs")) != "controllable_resources"
        or _display(data_roles.get("outputs")) != "desirable_services"
        or _display(data_roles.get("bad_outputs")) != "excluded"
        or not isinstance(variables, Mapping)
    ):
        raise PlotNotAvailableError(
            "radial improvement plotting requires ordinary resource and desirable-"
            "service roles"
        )
    inputs = _named_sequence(variables.get("inputs"), field="inputs")
    outputs = _named_sequence(variables.get("outputs"), field="outputs")
    if variables.get("bad_outputs") not in ((), []) or variables.get(
        "polluting_inputs"
    ) not in ((), []):
        raise PlotNotAvailableError(
            "radial improvement plotting does not reinterpret environmental roles"
        )
    if set(inputs).intersection(outputs):
        raise PlotNotAvailableError(
            "radial improvement variable identities must be distinct across roles"
        )
    counts = data_roles.get("counts")
    expected_counts = {
        "inputs": len(inputs),
        "outputs": len(outputs),
        "bad_outputs": 0,
        "polluting_inputs": 0,
    }
    if not isinstance(counts, Mapping) or any(
        isinstance(counts.get(role), (bool, np.bool_))
        or not isinstance(counts.get(role), (int, np.integer))
        or int(counts[role]) != count
        for role, count in expected_counts.items()
    ):
        raise PlotNotAvailableError(
            "radial improvement declared role counts do not match its variables"
        )
    panel = data_roles.get("panel")
    if not isinstance(panel, (bool, np.bool_)) or bool(panel) != (
        _display(context.get("sample")) == "panel"
    ):
        raise PlotNotAvailableError("radial improvement panel declarations disagree")
    return _RadialContract(
        inputs=inputs,
        outputs=outputs,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        reference_kind=reference_kind,
    )


def _period_mask(frame: pd.DataFrame, period: object | None) -> pd.Series:
    if period is None:
        return frame["period"].isna()
    return frame["period"].eq(period).fillna(False)


def _selected_rows(
    frame: pd.DataFrame,
    *,
    dmu_id: object,
    period: object | None,
) -> pd.DataFrame:
    return frame.loc[
        frame["dmu_id"].eq(dmu_id).fillna(False) & _period_mask(frame, period)
    ].copy(deep=True)


def _observation_key(dmu_id: object, period: object) -> tuple[object, object]:
    if _missing_scalar(dmu_id):
        raise PlotNotAvailableError(
            "radial improvement observation identifiers must be nonmissing"
        )
    resolved_period = _MISSING_PERIOD_KEY if _missing_scalar(period) else period
    key = (dmu_id, resolved_period)
    try:
        hash(key)
    except TypeError as error:
        raise PlotNotAvailableError(
            "radial improvement observation identifiers must be hashable"
        ) from error
    return key


def _group_positions_by_observation(
    frame: pd.DataFrame,
) -> dict[tuple[object, object], list[int]]:
    groups: dict[tuple[object, object], list[int]] = {}
    for position, row in enumerate(frame[["dmu_id", "period"]].itertuples(index=False)):
        key = _observation_key(row.dmu_id, row.period)
        groups.setdefault(key, []).append(position)
    return groups


def _available_observations(summary: pd.DataFrame) -> str:
    labels: list[str] = []
    for row in summary[["dmu_id", "period"]].drop_duplicates().itertuples(index=False):
        label = repr(row.dmu_id)
        if not _missing_scalar(row.period):
            label = f"{label}@{row.period!r}"
        labels.append(label)
    return ", ".join(labels)


def _scaled_residual(actual: float, expected: float, *context: float) -> float:
    scale = max(1.0, abs(actual), abs(expected), *(abs(value) for value in context))
    return abs(actual - expected) / scale


def _validate_summary_values(
    row: pd.Series,
    *,
    contract: _RadialContract,
    model_tolerance: float,
    tolerance: float,
) -> tuple[bool, bool]:
    if any(
        _display(row[field]) != "optimal"
        for field in (
            "solver_status",
            "primary_solver_status",
            "completion_solver_status",
        )
    ):
        raise PlotNotAvailableError(
            "radial improvement plotting requires optimal primary and completion "
            "programmes"
        )
    if not _true(row["score_valid"]) or _display(row["score_status"]) != "defined":
        raise PlotNotAvailableError(
            "radial improvement plotting requires a defined valid radial score"
        )
    if (
        not _true(row["completion_valid"])
        or _display(row["completion_status"]) != "certified"
    ):
        raise PlotNotAvailableError(
            "radial improvement plotting requires certified slack completion"
        )
    if not _true(row["target_valid"]) or _display(row["target_status"]) != (
        "certified_slack_completion"
    ):
        raise PlotNotAvailableError(
            "radial improvement plotting requires certified completed targets"
        )
    if not _true(row["efficiency_denominator_valid"]):
        raise PlotNotAvailableError(
            "radial improvement plotting requires a valid efficiency transform"
        )
    if not _true(row["is_within_reference_technology"]):
        raise PlotNotAvailableError(
            "radial improvement plotting requires the selected operation to be "
            "within the fitted reference technology"
        )
    expected_summary = {
        "model_family": "radial",
        "orientation": contract.orientation,
        "returns_to_scale": contract.returns_to_scale,
    }
    if any(_display(row[field]) != value for field, value in expected_summary.items()):
        raise PlotNotAvailableError(
            "radial improvement summary disagrees with its fitted technology"
        )
    if not all(
        _finite(row[field])
        for field in ("score", "efficiency", "max_slack", "max_scaled_slack")
    ):
        raise PlotNotAvailableError(
            "radial improvement summary quantities must be finite"
        )
    score = float(row["score"])
    efficiency = float(row["efficiency"])
    max_slack = float(row["max_slack"])
    max_scaled_slack = float(row["max_scaled_slack"])
    if score < 0.0 or max_slack < 0.0 or max_scaled_slack < 0.0:
        raise PlotNotAvailableError(
            "radial improvement score and slack accounts must be nonnegative"
        )
    if contract.orientation == "input":
        expected_efficiency = score
        within_numerically = score <= 1.0 + model_tolerance
    else:
        if score <= model_tolerance:
            raise PlotNotAvailableError(
                "output radial improvement requires a positive expansion factor"
            )
        expected_efficiency = 1.0 / score
        within_numerically = score >= 1.0 - model_tolerance
    if not within_numerically:
        raise PlotNotAvailableError(
            "radial improvement within-technology status contradicts its score"
        )
    if _scaled_residual(efficiency, expected_efficiency, score) > tolerance:
        raise PlotNotAvailableError(
            "radial improvement efficiency does not reconstruct its native score"
        )
    is_radially_efficient = _explicit_boolean(
        row["is_radially_efficient"], field="radial-efficiency classification"
    )
    is_efficient = _explicit_boolean(
        row["is_efficient"], field="strong-efficiency classification"
    )
    expected_radial_classification = abs(efficiency - 1.0) <= model_tolerance
    expected_strong_classification = bool(
        expected_radial_classification and max_scaled_slack <= model_tolerance
    )
    if is_radially_efficient != expected_radial_classification:
        raise PlotNotAvailableError(
            "radial improvement radial-efficiency classification does not "
            "reconstruct the fitted score"
        )
    if is_efficient != expected_strong_classification:
        raise PlotNotAvailableError(
            "radial improvement strong-efficiency classification does not "
            "reconstruct the completion account"
        )
    return is_radially_efficient, is_efficient


def _summary_row(
    result: Any,
    *,
    dmu_id: object,
    period: object | None,
    contract: _RadialContract,
    model_tolerance: float,
    tolerance: float,
    summary: pd.DataFrame | None = None,
) -> tuple[pd.Series, object | None, bool, bool]:
    summary = result.summary(copy=True) if summary is None else summary
    if not isinstance(summary, pd.DataFrame):
        raise PlotNotAvailableError(
            "radial improvement plotting requires a summary table"
        )
    _require_columns(summary, _SUMMARY_COLUMNS, table="summary")
    selected = summary.loc[summary["dmu_id"].eq(dmu_id).fillna(False)]
    if period is not None:
        selected = selected.loc[_period_mask(selected, period)]
    elif len(selected) > 1:
        available_periods = ", ".join(repr(value) for value in selected["period"])
        raise PlotNotAvailableError(
            f"radial improvement plotting requires period for {dmu_id!r}; "
            f"available periods: {available_periods}"
        )
    if len(selected) != 1:
        if selected.empty:
            raise PlotNotAvailableError(
                f"unknown radial observation {dmu_id!r}; available observations: "
                f"{_available_observations(summary)}"
            )
        raise PlotNotAvailableError(
            "radial improvement plotting requires one summary row per observation"
        )
    row = selected.iloc[0].copy(deep=True)
    resolved_period = None if _missing_scalar(row["period"]) else row["period"]
    radial, strong = _validate_summary_values(
        row,
        contract=contract,
        model_tolerance=model_tolerance,
        tolerance=tolerance,
    )
    return row, resolved_period, radial, strong


def _validate_diagnostic_rows(selected: pd.DataFrame) -> None:
    if len(selected) != 2 or set(selected["phase"]) != {1, 2}:
        raise PlotNotAvailableError(
            "radial improvement plotting requires one phase-one and one phase-two "
            "certificate"
        )
    certificate_fields = (
        "lp_postsolve_certified",
        "postsolve_certified",
        "economic_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
    )
    for phase in (1, 2):
        row = selected.loc[selected["phase"].eq(phase)].iloc[0]
        if (
            _display(row["solver_status"]) != "optimal"
            or _display(row["certification_reason"]) != "certified"
            or _display(row["economic_certification_reason"]) != "certified"
            or not all(_true(row[field]) for field in certificate_fields)
        ):
            raise PlotNotAvailableError(
                "radial improvement plotting requires certified LP, raw, economic, "
                "and published-output accounts in both phases"
            )


def _certified_diagnostics(
    result: Any,
    *,
    dmu_id: object,
    period: object | None,
) -> None:
    diagnostics = getattr(result, "diagnostics", None)
    if not isinstance(diagnostics, pd.DataFrame):
        raise PlotNotAvailableError(
            "radial improvement plotting requires postsolve diagnostics"
        )
    _require_columns(diagnostics, _DIAGNOSTIC_COLUMNS, table="diagnostic")
    selected = _selected_rows(diagnostics, dmu_id=dmu_id, period=period)
    _validate_diagnostic_rows(selected)


def _reconstruct_plan(
    *,
    summary: pd.Series,
    selected_targets: pd.DataFrame,
    selected_slacks: pd.DataFrame,
    contract: _RadialContract,
    tolerance: float,
) -> tuple[pd.DataFrame, float]:
    expected = [
        *(("input", variable) for variable in contract.inputs),
        *(("output", variable) for variable in contract.outputs),
    ]
    target_keys = list(
        zip(selected_targets["role"], selected_targets["variable"], strict=True)
    )
    slack_keys = list(
        zip(selected_slacks["role"], selected_slacks["variable"], strict=True)
    )
    if len(target_keys) != len(set(target_keys)) or set(target_keys) != set(expected):
        raise PlotNotAvailableError(
            "radial improvement targets do not match every declared resource and "
            "service"
        )
    if len(slack_keys) != len(set(slack_keys)) or set(slack_keys) != set(expected):
        raise PlotNotAvailableError(
            "radial improvement slacks do not match every declared resource and service"
        )
    target_index = selected_targets.set_index(["role", "variable"])
    slack_index = selected_slacks.set_index(["role", "variable"])
    factor = float(summary["score"])
    rows: list[dict[str, Any]] = []
    residuals: list[float] = []
    for order, (role, variable) in enumerate(expected):
        target_row = target_index.loc[(role, variable)]
        slack_row = slack_index.loc[(role, variable)]
        numeric = (
            target_row["observed"],
            target_row["target"],
            slack_row["slack"],
        )
        if not all(_finite(value) for value in numeric):
            raise PlotNotAvailableError(
                "radial improvement target and slack quantities must be finite"
            )
        observed, target, slack = map(float, numeric)
        quantity_scale = max(1.0, abs(observed), abs(target), abs(slack))
        if observed < -tolerance * quantity_scale or target < (
            -tolerance * quantity_scale
        ):
            raise PlotNotAvailableError(
                "radial improvement observed and target quantities must be nonnegative"
            )
        if slack < -tolerance * quantity_scale:
            raise PlotNotAvailableError(
                "radial improvement slack completion must be nonnegative"
            )
        observed = max(0.0, observed)
        target = max(0.0, target)
        slack = max(0.0, slack)

        adjusted_role = (contract.orientation == "input" and role == "input") or (
            contract.orientation == "output" and role == "output"
        )
        raw_radial_target = factor * observed if adjusted_role else observed
        raw_radial_change = (
            observed - raw_radial_target
            if role == "input"
            else raw_radial_target - observed
        )
        if raw_radial_target < -tolerance * quantity_scale or raw_radial_change < (
            -tolerance * quantity_scale
        ):
            raise PlotNotAvailableError(
                "radial improvement score implies movement away from its declared "
                "within-technology orientation"
            )
        radial_change = max(0.0, raw_radial_change)
        radial_target = (
            observed - radial_change if role == "input" else observed + radial_change
        )
        expected_target = (
            radial_target - slack if role == "input" else radial_target + slack
        )
        if expected_target < -tolerance * quantity_scale:
            raise PlotNotAvailableError(
                "radial improvement slack completion implies a negative target"
            )
        residuals.extend(
            [
                _scaled_residual(
                    radial_target,
                    raw_radial_target,
                    observed,
                    factor,
                ),
                _scaled_residual(
                    target,
                    expected_target,
                    observed,
                    radial_target,
                    slack,
                ),
            ]
        )
        rows.append(
            {
                "role": role,
                "variable": variable,
                "variable_label": _variable_label(variable),
                "order": order,
                "observed": observed,
                "radial_change": radial_change,
                "radial_target": radial_target,
                "slack_completion": slack,
                "target": target,
            }
        )

    max_slack = max((float(row["slack_completion"]) for row in rows), default=0.0)
    aggregate_residuals = (_scaled_residual(float(summary["max_slack"]), max_slack),)
    residuals.extend(aggregate_residuals)
    max_residual = max(residuals, default=0.0)
    if not math.isfinite(max_residual) or max_residual > tolerance:
        raise PlotNotAvailableError(
            "radial improvement plan does not reconstruct its proportional, slack, "
            "and completed-target accounts"
        )
    return pd.DataFrame.from_records(rows).copy(deep=True), max_residual


def prepare_radial_improvement_data(
    result: Any,
    *,
    dmu_id: object,
    period: object | None = None,
) -> RadialImprovementPlotData:
    """Prepare one certified radial plan without importing a backend or solver."""
    metadata = _metadata(result)
    contract = _semantic_contract(metadata)
    model_tolerance, tolerance = _tolerances(metadata)
    full_summary = result.summary(copy=True)
    summary, resolved_period, radial, strong = _summary_row(
        result,
        dmu_id=dmu_id,
        period=period,
        contract=contract,
        model_tolerance=model_tolerance,
        tolerance=tolerance,
        summary=full_summary,
    )
    _certified_diagnostics(result, dmu_id=dmu_id, period=resolved_period)

    targets = getattr(result, "targets", None)
    slacks = getattr(result, "slacks", None)
    if not isinstance(targets, pd.DataFrame) or not isinstance(slacks, pd.DataFrame):
        raise PlotNotAvailableError(
            "radial improvement plotting requires public target and slack tables"
        )
    _require_columns(targets, _TARGET_COLUMNS, table="target")
    _require_columns(slacks, _SLACK_COLUMNS, table="slack")
    selected_targets = _selected_rows(targets, dmu_id=dmu_id, period=resolved_period)
    selected_slacks = _selected_rows(slacks, dmu_id=dmu_id, period=resolved_period)
    variables, max_residual = _reconstruct_plan(
        summary=summary,
        selected_targets=selected_targets,
        selected_slacks=selected_slacks,
        contract=contract,
        tolerance=tolerance,
    )
    reference_label = _bounded_display_text(
        contract.reference_kind,
        fallback="Unspecified",
    )
    return RadialImprovementPlotData(
        dmu_id=dmu_id,
        period=resolved_period,
        dmu_label=_bounded_display_text(
            dmu_id,
            fallback="Organization",
            limit=_DMU_LABEL_LIMIT,
        ),
        period_label=(
            None
            if resolved_period is None
            else _bounded_display_text(
                resolved_period,
                fallback="Period not reported",
                limit=_PERIOD_LABEL_LIMIT,
            )
        ),
        native_score=float(summary["score"]),
        efficiency=float(summary["efficiency"]),
        orientation=contract.orientation,
        returns_to_scale=contract.returns_to_scale,
        reference_kind=contract.reference_kind,
        is_radially_efficient=radial,
        is_efficient=strong,
        variables=variables,
        target_status="certified_slack_completion",
        max_reconstruction_residual=max_residual,
        provenance=(
            ("Method", _METHOD_ID),
            ("Orientation", contract.orientation),
            ("RTS", contract.returns_to_scale.upper()),
            ("Reference", reference_label),
        ),
    )


def radial_improvement_plot_applicable(result: Any) -> bool:
    """Whether at least one certified radial operating plan is reconstructable."""
    try:
        if not radial_improvement_route(result):
            return False
        summary = result.summary(copy=True)
        if not isinstance(summary, pd.DataFrame):
            return False
        _require_columns(summary, _SUMMARY_COLUMNS, table="summary")
        score = pd.to_numeric(summary["score"], errors="coerce")
        efficiency = pd.to_numeric(summary["efficiency"], errors="coerce")
        max_slack = pd.to_numeric(summary["max_slack"], errors="coerce")
        max_scaled_slack = pd.to_numeric(summary["max_scaled_slack"], errors="coerce")
        candidate_mask = (
            summary["solver_status"].map(_display).eq("optimal")
            & summary["primary_solver_status"].map(_display).eq("optimal")
            & summary["completion_solver_status"].map(_display).eq("optimal")
            & summary["score_valid"].map(_true)
            & summary["score_status"].map(_display).eq("defined")
            & summary["completion_valid"].map(_true)
            & summary["completion_status"].map(_display).eq("certified")
            & summary["target_valid"].map(_true)
            & summary["target_status"].map(_display).eq("certified_slack_completion")
            & summary["is_within_reference_technology"].map(_true)
            & summary["efficiency_denominator_valid"].map(_true)
            & summary["model_family"].map(_display).eq("radial")
            & summary["orientation"].map(_display).isin(_SUPPORTED_ORIENTATIONS)
            & summary["returns_to_scale"].map(_display).isin(_SUPPORTED_RTS)
            & np.isfinite(score)
            & np.isfinite(efficiency)
            & np.isfinite(max_slack)
            & np.isfinite(max_scaled_slack)
            & score.ge(0.0)
            & max_slack.ge(0.0)
            & max_scaled_slack.ge(0.0)
        )
        candidates = summary.loc[candidate_mask, ["dmu_id", "period"]]
        if candidates.empty:
            return False

        metadata = _metadata(result)
        contract = _semantic_contract(metadata)
        model_tolerance, tolerance = _tolerances(metadata)
        targets = getattr(result, "targets", None)
        slacks = getattr(result, "slacks", None)
        diagnostics = getattr(result, "diagnostics", None)
        if not all(
            isinstance(frame, pd.DataFrame) for frame in (targets, slacks, diagnostics)
        ):
            return False
        _require_columns(targets, _TARGET_COLUMNS, table="target")
        _require_columns(slacks, _SLACK_COLUMNS, table="slack")
        _require_columns(diagnostics, _DIAGNOSTIC_COLUMNS, table="diagnostic")
        summary_groups = _group_positions_by_observation(summary)
        target_groups = _group_positions_by_observation(targets)
        slack_groups = _group_positions_by_observation(slacks)
        diagnostic_groups = _group_positions_by_observation(diagnostics)
        candidate_positions = np.flatnonzero(candidate_mask.to_numpy(dtype=bool))
        for position in candidate_positions:
            row = summary.iloc[position].copy(deep=True)
            key = _observation_key(row["dmu_id"], row["period"])
            if len(summary_groups.get(key, ())) != 1:
                continue
            try:
                _validate_summary_values(
                    row,
                    contract=contract,
                    model_tolerance=model_tolerance,
                    tolerance=tolerance,
                )
                diagnostic_positions = diagnostic_groups.get(key, ())
                target_positions = target_groups.get(key, ())
                slack_positions = slack_groups.get(key, ())
                _validate_diagnostic_rows(diagnostics.iloc[list(diagnostic_positions)])
                _reconstruct_plan(
                    summary=row,
                    selected_targets=targets.iloc[list(target_positions)],
                    selected_slacks=slacks.iloc[list(slack_positions)],
                    contract=contract,
                    tolerance=tolerance,
                )
            except PlotNotAvailableError:
                continue
            return True
    except (AttributeError, KeyError, PlotNotAvailableError, TypeError, ValueError):
        return False
    return False


__all__ = [
    "RadialImprovementPlotData",
    "prepare_radial_improvement_data",
    "radial_improvement_plot_applicable",
    "radial_improvement_route",
]
