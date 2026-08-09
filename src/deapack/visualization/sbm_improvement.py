"""Prepared data for a certified mainstream SBM operating-plan plot.

The contract covers Tone's three classic static SBM orientations and the exact
strong-separable undesirable-output SBM.  It does not reinterpret additive,
RAM, weak-disposal, nonseparable, network, dynamic, or paper-specific variants
as though they shared one score account.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from ._types import PlotNotAvailableError

_ENVIRONMENTAL_METHOD_ID = "environmental.sbm.separable_strong"
_METHOD_ORIENTATIONS = {
    "static.sbm.input.tone2001": "input",
    "static.sbm.output.tone2001": "output",
    "static.sbm.nonoriented.tone2001": "non-oriented",
    _ENVIRONMENTAL_METHOD_ID: "non-oriented",
}
_SELECTION_STATUS = "solver_selected_primary_optimum"
_TARGET_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "role",
        "variable",
        "observed",
        "target",
        "selection_status",
    }
)
_SLACK_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "role",
        "variable",
        "slack",
        "normalizer",
        "normalized_slack",
        "average_weight",
        "included_in_objective",
    }
)
_DIAGNOSTIC_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "phase",
        "solver_status",
        "postsolve_certified",
        "economic_postsolve_certified",
    }
)


@dataclass(frozen=True, slots=True)
class SBMImprovementPlotData:
    """Detached payload for one certified variable-specific SBM plan."""

    dmu_id: object
    period: object | None
    orientation: str
    returns_to_scale: str
    efficiency: float
    input_account: float
    output_expansion_account: float
    variables: pd.DataFrame
    selection_status: str
    max_reconstruction_residual: float
    provenance: tuple[tuple[str, str], ...]

    @property
    def variable_count(self) -> int:
        """Number of fitted resource and outcome coordinates in the plan."""
        return len(self.variables)

    @property
    def scored_variable_count(self) -> int:
        """Number of coordinates included in the fitted SBM objective."""
        return int(self.variables["included_in_objective"].sum())


def _missing_scalar(value: object) -> bool:
    marker = pd.isna(value)
    if isinstance(marker, (bool, np.bool_)):
        return bool(marker)
    raise PlotNotAvailableError("SBM improvement identifiers must be scalar values")


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


def _false(value: object) -> bool:
    if _missing_scalar(value):
        return False
    return isinstance(value, (bool, np.bool_)) and not bool(value)


def _display(value: object) -> str | None:
    if value is None or _missing_scalar(value):
        return None
    enum_value = getattr(value, "value", value)
    text = str(enum_value).strip()
    return text or None


def _metadata(result: Any) -> Mapping[str, Any]:
    metadata = getattr(result, "metadata", None)
    if not isinstance(metadata, Mapping):
        raise PlotNotAvailableError(
            "SBM improvement plotting requires fitted result metadata"
        )
    return metadata


def _require_columns(
    frame: pd.DataFrame,
    required: frozenset[str],
    *,
    table: str,
) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise PlotNotAvailableError(
            f"SBM improvement plotting requires {table} columns: "
            f"{', '.join(sorted(missing))}"
        )


def _certificate_tolerance(metadata: Mapping[str, Any]) -> float:
    value = metadata.get("tolerance")
    if not _finite(value) or float(value) <= 0.0:
        raise PlotNotAvailableError(
            "SBM improvement plotting requires the fitted numerical tolerance"
        )
    return 10.0 * float(value)


def _period_mask(frame: pd.DataFrame, period: object | None) -> pd.Series:
    if period is None:
        return frame["period"].isna()
    return frame["period"].eq(period).fillna(False)


def _available_observations(summary: pd.DataFrame) -> str:
    labels: list[str] = []
    for row in summary[["dmu_id", "period"]].drop_duplicates().itertuples(index=False):
        label = repr(row.dmu_id)
        if not _missing_scalar(row.period):
            label = f"{label}@{row.period!r}"
        labels.append(label)
    return ", ".join(labels)


def _summary_row(
    result: Any,
    *,
    dmu_id: object,
    period: object | None,
) -> tuple[pd.Series, object | None]:
    summary = result.summary(copy=True)
    selected = summary.loc[summary["dmu_id"].eq(dmu_id).fillna(False)]
    if period is not None:
        selected = selected.loc[_period_mask(selected, period)]
    elif len(selected) > 1:
        available_periods = ", ".join(repr(value) for value in selected["period"])
        raise PlotNotAvailableError(
            f"SBM improvement plotting requires period for {dmu_id!r}; "
            f"available periods: {available_periods}"
        )
    if len(selected) != 1:
        if selected.empty:
            raise PlotNotAvailableError(
                f"unknown SBM observation {dmu_id!r}; available observations: "
                f"{_available_observations(summary)}"
            )
        raise PlotNotAvailableError(
            "SBM improvement plotting requires one summary row per observation"
        )
    row = selected.iloc[0].copy(deep=True)
    resolved_period = None if _missing_scalar(row["period"]) else row["period"]
    if _display(row.get("solver_status")) != "optimal":
        raise PlotNotAvailableError(
            "SBM improvement plotting requires an optimal certified result"
        )
    if "score_valid" not in selected or not _true(row.get("score_valid")):
        raise PlotNotAvailableError(
            "SBM improvement plotting requires score_valid=True"
        )
    if _display(row.get("score_status")) != "defined":
        raise PlotNotAvailableError(
            "SBM improvement plotting requires a defined certified score"
        )
    if not _finite(row.get("efficiency")):
        raise PlotNotAvailableError(
            "SBM improvement plotting requires a finite certified efficiency"
        )
    return row, resolved_period


def _certified_diagnostic(
    result: Any,
    *,
    dmu_id: object,
    period: object | None,
) -> None:
    diagnostics = getattr(result, "diagnostics", None)
    if not isinstance(diagnostics, pd.DataFrame):
        raise PlotNotAvailableError(
            "SBM improvement plotting requires postsolve diagnostics"
        )
    _require_columns(diagnostics, _DIAGNOSTIC_COLUMNS, table="diagnostic")
    selected = diagnostics.loc[
        diagnostics["dmu_id"].eq(dmu_id).fillna(False)
        & _period_mask(diagnostics, period)
        & diagnostics["phase"].eq(1).fillna(False)
    ]
    if len(selected) != 1:
        raise PlotNotAvailableError(
            "SBM improvement plotting requires one phase-one certificate"
        )
    row = selected.iloc[0]
    if (
        _display(row.get("solver_status")) != "optimal"
        or not _true(row.get("postsolve_certified"))
        or not _true(row.get("economic_postsolve_certified"))
    ):
        raise PlotNotAvailableError(
            "SBM improvement plotting requires both LP and operating-account "
            "postsolve certificates"
        )


def _declared_variables(
    metadata: Mapping[str, Any],
    *,
    environmental: bool,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    expanded = metadata.get("expanded_spec")
    if not isinstance(expanded, Mapping):
        raise PlotNotAvailableError(
            "SBM improvement plotting requires expanded fitted semantics"
        )
    graph = expanded.get("graph")
    expected_graph = "black_box_joint_production" if environmental else "black_box"
    if not isinstance(graph, Mapping) or _display(graph.get("kind")) != expected_graph:
        raise PlotNotAvailableError(
            "SBM improvement plotting requires its exact fitted production graph"
        )
    data_roles = expanded.get("data_roles")
    variables = data_roles.get("variables") if isinstance(data_roles, Mapping) else None
    if not isinstance(variables, Mapping):
        raise PlotNotAvailableError(
            "SBM improvement plotting requires declared input and output variables"
        )

    def sequence(role: str) -> tuple[str, ...]:
        value = variables.get(role)
        if not isinstance(value, (tuple, list)) or not value:
            raise PlotNotAvailableError(
                f"SBM improvement plotting requires declared {role}"
            )
        resolved = tuple(value)
        if not all(isinstance(item, str) and item.strip() for item in resolved):
            raise PlotNotAvailableError(
                f"SBM improvement plotting requires named {role}"
            )
        if len(set(resolved)) != len(resolved):
            raise PlotNotAvailableError(
                f"SBM improvement plotting requires unique {role}"
            )
        return resolved

    inputs = sequence("inputs")
    outputs = sequence("outputs")
    if environmental:
        bad_outputs = sequence("bad_outputs")
        expected_role_semantics = {
            "inputs": "controllable_resources",
            "outputs": "desirable_services",
            "bad_outputs": "strongly_disposable_undesirable_residuals",
        }
        if any(
            _display(data_roles.get(role)) != semantic
            for role, semantic in expected_role_semantics.items()
        ):
            raise PlotNotAvailableError(
                "environmental SBM improvement plotting requires exact resource, "
                "desirable-service, and undesirable-residual roles"
            )
    else:
        bad_outputs_value = variables.get("bad_outputs")
        if _display(
            data_roles.get("bad_outputs")
        ) != "excluded" or bad_outputs_value not in ((), []):
            raise PlotNotAvailableError(
                "SBM improvement plotting requires ordinary desirable-output roles"
            )
        bad_outputs = ()

    polluting_inputs = variables.get("polluting_inputs")
    if polluting_inputs not in ((), []):
        raise PlotNotAvailableError(
            "SBM improvement plotting does not reinterpret polluting-input roles"
        )

    counts = data_roles.get("counts")
    expected_counts = {
        "inputs": len(inputs),
        "outputs": len(outputs),
        "bad_outputs": len(bad_outputs),
        "polluting_inputs": 0,
    }
    if not isinstance(counts, Mapping) or any(
        isinstance(counts.get(role), (bool, np.bool_))
        or not isinstance(counts.get(role), (int, np.integer))
        or int(counts[role]) != count
        for role, count in expected_counts.items()
    ):
        raise PlotNotAvailableError(
            "SBM improvement declared role counts do not match its variables"
        )

    variable_sets = (set(inputs), set(outputs), set(bad_outputs))
    if any(
        variable_sets[left].intersection(variable_sets[right])
        for left in range(len(variable_sets))
        for right in range(left + 1, len(variable_sets))
    ):
        raise PlotNotAvailableError(
            "SBM improvement variable identities must be distinct across roles"
        )
    return inputs, outputs, bad_outputs


def _selected_rows(
    frame: pd.DataFrame,
    *,
    dmu_id: object,
    period: object | None,
) -> pd.DataFrame:
    return frame.loc[
        frame["dmu_id"].eq(dmu_id).fillna(False) & _period_mask(frame, period)
    ].copy(deep=True)


def prepare_sbm_improvement_data(
    result: Any,
    *,
    dmu_id: object,
    period: object | None = None,
) -> SBMImprovementPlotData:
    """Prepare one certified mainstream SBM variable-improvement account."""
    metadata = _metadata(result)
    method_id = _display(metadata.get("method_id"))
    if method_id not in _METHOD_ORIENTATIONS:
        raise PlotNotAvailableError(
            "improvement plotting is defined only for certified classic static "
            "SBM and the exact strong-separable environmental SBM"
        )
    environmental = method_id == _ENVIRONMENTAL_METHOD_ID
    if any(
        _display(metadata.get(field)) is not None
        for field in ("specialization_id", "method_specialization")
    ):
        raise PlotNotAvailableError(
            "SBM improvement plotting does not reinterpret a method specialization"
        )
    orientation = _display(metadata.get("orientation"))
    if orientation != _METHOD_ORIENTATIONS[method_id]:
        raise PlotNotAvailableError(
            "SBM improvement method and orientation metadata disagree"
        )
    expanded = metadata.get("expanded_spec")
    performance = expanded.get("performance") if isinstance(expanded, Mapping) else None
    expected_performance_orientation = (
        "non_oriented_environmental"
        if environmental
        else "non_oriented"
        if orientation == "non-oriented"
        else orientation
    )
    if (
        not isinstance(performance, Mapping)
        or _display(performance.get("orientation")) != expected_performance_orientation
    ):
        raise PlotNotAvailableError(
            "SBM improvement orientation disagrees with the fitted performance account"
        )
    if environmental:
        expected_performance = {
            "family": "slacks_based_measure",
            "orientation": "non_oriented_environmental",
            "normalization": "evaluated_dmu_values",
            "output_aggregation": "equal_weight_over_good_and_bad_dimensions",
        }
        if any(
            _display(performance.get(field)) != value
            for field, value in expected_performance.items()
        ):
            raise PlotNotAvailableError(
                "environmental SBM improvement plotting requires its exact fitted "
                "performance account"
            )
        technology = expanded.get("technology")
        if (
            not isinstance(technology, Mapping)
            or _display(technology.get("bad_output_disposal")) != "strong_separable"
        ):
            raise PlotNotAvailableError(
                "environmental SBM improvement plotting requires the fitted "
                "strong-separable technology"
            )
        expected_metadata = {
            "bad_output_disposability": "strong",
            "separability": "separable_good_and_bad_outputs",
            "bad_output_constraint": "B lambda + s_b = b_o",
            "bad_output_slack": "contraction_excess",
            "output_aggregation": "equal_weight_over_good_and_bad_dimensions",
            "classification_domain": ("evaluated_plan_within_reference_technology"),
        }
        if any(
            _display(metadata.get(field)) != value
            for field, value in expected_metadata.items()
        ) or not _false(metadata.get("null_jointness")):
            raise PlotNotAvailableError(
                "environmental SBM improvement metadata does not declare the exact "
                "strong-separable undesirable-output account"
            )
    tolerance = _certificate_tolerance(metadata)
    summary, resolved_period = _summary_row(
        result,
        dmu_id=dmu_id,
        period=period,
    )
    if _display(summary.get("orientation")) != orientation:
        raise PlotNotAvailableError(
            "SBM improvement summary and fitted orientation disagree"
        )
    returns_to_scale = _display(metadata.get("returns_to_scale"))
    if (
        returns_to_scale is None
        or _display(summary.get("returns_to_scale")) != returns_to_scale
    ):
        raise PlotNotAvailableError(
            "SBM improvement summary and returns-to-scale metadata disagree"
        )
    if environmental and (
        _display(summary.get("bad_output_disposability")) != "strong"
        or not _false(summary.get("null_jointness"))
    ):
        raise PlotNotAvailableError(
            "environmental SBM improvement summary and fitted technology disagree"
        )
    if environmental:
        if not _true(summary.get("is_within_reference_technology")):
            raise PlotNotAvailableError(
                "environmental SBM improvement plotting requires certified "
                "reference-technology membership"
            )
        if _display(summary.get("membership_status")) not in {
            "certified_by_self_inclusion",
            "certified_by_sbm_balance_account",
        }:
            raise PlotNotAvailableError(
                "environmental SBM improvement plotting requires a certified "
                "membership account"
            )
        if (
            not _true(summary.get("target_valid"))
            or _display(summary.get("target_status")) != "certified_primary_program"
        ):
            raise PlotNotAvailableError(
                "environmental SBM improvement plotting requires a certified "
                "primary-program target"
            )
    _certified_diagnostic(
        result,
        dmu_id=dmu_id,
        period=resolved_period,
    )

    targets = getattr(result, "targets", None)
    slacks = getattr(result, "slacks", None)
    if not isinstance(targets, pd.DataFrame) or not isinstance(slacks, pd.DataFrame):
        raise PlotNotAvailableError(
            "SBM improvement plotting requires target and slack tables"
        )
    _require_columns(targets, _TARGET_COLUMNS, table="target")
    _require_columns(slacks, _SLACK_COLUMNS, table="slack")
    targets = _selected_rows(
        targets,
        dmu_id=dmu_id,
        period=resolved_period,
    )
    slacks = _selected_rows(
        slacks,
        dmu_id=dmu_id,
        period=resolved_period,
    )
    if targets.empty or slacks.empty:
        raise PlotNotAvailableError(
            "SBM improvement plotting requires a published certified plan"
        )
    if set(targets["selection_status"].drop_duplicates()) != {_SELECTION_STATUS}:
        raise PlotNotAvailableError(
            "SBM improvement targets lack the solver-selected plan status"
        )

    inputs, outputs, bad_outputs = _declared_variables(
        metadata,
        environmental=environmental,
    )
    expected = (
        [("input", variable) for variable in inputs]
        + [("output", variable) for variable in outputs]
        + [("bad_output", variable) for variable in bad_outputs]
    )
    target_keys = list(zip(targets["role"], targets["variable"], strict=True))
    slack_keys = list(zip(slacks["role"], slacks["variable"], strict=True))
    if len(set(target_keys)) != len(target_keys) or set(target_keys) != set(expected):
        raise PlotNotAvailableError(
            "SBM improvement targets do not match the fitted variable roles"
        )
    if len(set(slack_keys)) != len(slack_keys) or set(slack_keys) != set(expected):
        raise PlotNotAvailableError(
            "SBM improvement slacks do not match the fitted variable roles"
        )

    target_index = targets.set_index(["role", "variable"])
    slack_index = slacks.set_index(["role", "variable"])
    rows: list[dict[str, Any]] = []
    residuals: list[float] = []
    for position, (role, variable) in enumerate(expected):
        target_row = target_index.loc[(role, variable)]
        slack_row = slack_index.loc[(role, variable)]
        values = (
            target_row["observed"],
            target_row["target"],
            slack_row["slack"],
            slack_row["normalizer"],
            slack_row["normalized_slack"],
            slack_row["average_weight"],
        )
        if not all(_finite(value) for value in values):
            raise PlotNotAvailableError("SBM improvement quantities must be finite")
        observed, target, slack, normalizer, normalized, average_weight = map(
            float, values
        )
        included = slack_row["included_in_objective"]
        if not isinstance(included, (bool, np.bool_)):
            raise PlotNotAvailableError(
                "SBM improvement objective-membership flags must be boolean"
            )
        expected_included = (
            orientation == "non-oriented"
            or (orientation == "input" and role == "input")
            or (orientation == "output" and role != "input")
        )
        if bool(included) != expected_included:
            raise PlotNotAvailableError(
                "SBM improvement objective membership disagrees with its orientation"
            )
        if observed <= 0.0 or normalizer <= 0.0 or slack < -tolerance:
            raise PlotNotAvailableError(
                "SBM improvement quantities violate the positive-data account"
            )
        implied_target = (
            observed - slack if role in {"input", "bad_output"} else observed + slack
        )
        signed_change = target - observed
        output_dimension = len(outputs) + len(bad_outputs)
        residuals.extend(
            [
                abs(observed - normalizer),
                abs(target - implied_target),
                abs(normalized - slack / observed),
                abs(
                    average_weight
                    - 1.0 / (len(inputs) if role == "input" else output_dimension)
                ),
            ]
        )
        rows.append(
            {
                "role": role,
                "variable": variable,
                "variable_label": variable.replace("_", " "),
                "observed": observed,
                "target": target,
                "slack": max(slack, 0.0),
                "normalized_slack": max(normalized, 0.0),
                "signed_change": signed_change,
                "signed_proportional_change": signed_change / observed,
                "average_weight": average_weight,
                "included_in_objective": bool(included),
                "order": position,
            }
        )

    variables = pd.DataFrame(rows)
    input_gap = float(
        variables.loc[variables["role"].eq("input"), "normalized_slack"].mean()
    )
    output_gap = float(
        variables.loc[
            variables["role"].isin(("output", "bad_output")),
            "normalized_slack",
        ].mean()
    )
    input_account = 1.0 - input_gap
    output_account = 1.0 + output_gap
    expected_efficiency = (
        input_account
        if orientation == "input"
        else 1.0 / output_account
        if orientation == "output"
        else input_account / output_account
    )
    summary_accounts = [
        summary.get("input_inefficiency"),
        summary.get("output_account_factor"),
    ]
    if environmental:
        summary_accounts.extend(
            [
                summary.get("desirable_output_inefficiency"),
                summary.get("bad_output_inefficiency"),
                summary.get("output_inefficiency"),
                summary.get("score"),
            ]
        )
    if not all(_finite(value) for value in summary_accounts):
        raise PlotNotAvailableError(
            "SBM improvement summary lacks finite operating accounts"
        )
    residuals.extend(
        [
            abs(float(summary_accounts[0]) - input_gap),
            abs(float(summary_accounts[1]) - output_account),
            abs(float(summary["efficiency"]) - expected_efficiency),
        ]
    )
    if environmental:
        desirable_output_gap = float(
            variables.loc[variables["role"].eq("output"), "normalized_slack"].mean()
        )
        bad_output_gap = float(
            variables.loc[variables["role"].eq("bad_output"), "normalized_slack"].mean()
        )
        residuals.extend(
            [
                abs(float(summary_accounts[2]) - desirable_output_gap),
                abs(float(summary_accounts[3]) - bad_output_gap),
                abs(float(summary_accounts[4]) - output_gap),
                abs(float(summary_accounts[5]) - expected_efficiency),
            ]
        )
    max_residual = max(residuals, default=0.0)
    if not math.isfinite(max_residual) or max_residual > tolerance:
        raise PlotNotAvailableError(
            "SBM improvement plan does not reconstruct its certified score account"
        )

    reference_kind = _display(metadata.get("reference_kind")) or "unspecified"
    return SBMImprovementPlotData(
        dmu_id=dmu_id,
        period=resolved_period,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        efficiency=float(summary["efficiency"]),
        input_account=input_account,
        output_expansion_account=output_account,
        variables=variables,
        selection_status=_SELECTION_STATUS,
        max_reconstruction_residual=max_residual,
        provenance=(
            ("Method", method_id),
            ("Orientation", orientation),
            ("RTS", returns_to_scale.upper()),
            ("Reference", reference_kind),
        ),
    )


def sbm_improvement_plot_applicable(result: Any) -> bool:
    """Whether at least one certified mainstream SBM plan can be prepared."""
    try:
        metadata = _metadata(result)
        if _display(metadata.get("method_id")) not in _METHOD_ORIENTATIONS:
            return False
        summary = result.summary(copy=True)
        for row in summary[["dmu_id", "period"]].itertuples(index=False):
            period = None if _missing_scalar(row.period) else row.period
            try:
                prepare_sbm_improvement_data(
                    result,
                    dmu_id=row.dmu_id,
                    period=period,
                )
            except PlotNotAvailableError:
                continue
            return True
    except (AttributeError, KeyError, PlotNotAvailableError, TypeError, ValueError):
        return False
    return False


__all__ = [
    "SBMImprovementPlotData",
    "prepare_sbm_improvement_data",
    "sbm_improvement_plot_applicable",
]
