"""Prepared data for a certified Dynamic-SBM carry-over trajectory plot.

The plot contract is intentionally narrow.  It visualizes one carry-over from
the classic Tone--Tsutsui Dynamic SBM result and never infers a dynamic path
from repeated static scores or from a generic panel.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from ._types import PlotNotAvailableError

MAX_TRAJECTORY_PERIODS = 24

_METHOD_ID = "dynamic.sbm.tone_tsutsui_2010"
_CARRYOVER_ROLES = frozenset(
    {
        "good_carryover",
        "bad_carryover",
        "free_carryover",
        "fixed_carryover",
    }
)
_TARGET_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "role",
        "variable",
        "observed",
        "target",
        "balance_residual",
        "selection_status",
    }
)
_COMPONENT_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "component_type",
        "component_id",
        "efficiency",
        "input_account",
        "output_expansion_account",
        "effective_period_weight",
        "selection_status",
    }
)
_LINK_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "carryover",
        "carryover_kind",
        "source_period",
        "target_period",
        "observed",
        "source_target",
        "next_period_target",
        "continuity_residual",
        "boundary_status",
        "selection_status",
    }
)
_SLACK_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "role",
        "variable",
        "included_in_optimization_objective",
        "included_in_reported_score",
        "slack",
        "score_variant",
        "selection_status",
    }
)

_SELECTION_STATUS = "solver_selected_not_uniqueness_certified"


@dataclass(frozen=True, slots=True)
class TrajectoryPlotData:
    """Detached payload for one certified intertemporal carry-over account."""

    dmu_id: object
    variable: str
    variable_label: str
    role: str
    carryover_kind: str
    quantity: pd.DataFrame
    transitions: pd.DataFrame
    period_accounts: pd.DataFrame
    horizon_efficiency: float
    max_continuity_residual: float
    terminal_boundary_status: str
    carryover_score_policy: str
    selection_status: str
    provenance: tuple[tuple[str, str], ...]

    @property
    def period_count(self) -> int:
        """Number of periods in the certified horizon."""
        return len(self.quantity)

    @property
    def transition_count(self) -> int:
        """Number of certified adjacent-period carry-over transitions."""
        return len(self.transitions)


def _missing_scalar(value: object) -> bool:
    marker = pd.isna(value)
    if isinstance(marker, (bool, np.bool_)):
        return bool(marker)
    raise PlotNotAvailableError("trajectory identifiers must be scalar values")


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


def _display(value: object) -> str | None:
    if value is None or _missing_scalar(value):
        return None
    enum_value = getattr(value, "value", value)
    text = str(enum_value).strip()
    return text or None


def _metadata(result: Any) -> Mapping[str, Any]:
    metadata = getattr(result, "metadata", None)
    if not isinstance(metadata, Mapping):
        raise PlotNotAvailableError("trajectory plotting requires result metadata")
    return metadata


def _require_method(result: Any) -> Mapping[str, Any]:
    metadata = _metadata(result)
    method_id = _display(metadata.get("method_id"))
    if method_id != _METHOD_ID:
        raise PlotNotAvailableError(
            "trajectory plotting is defined only for the certified classic "
            "Tone--Tsutsui Dynamic SBM result"
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
            f"trajectory plotting requires {table} columns: "
            f"{', '.join(sorted(missing))}"
        )


def _period_order(metadata: Mapping[str, Any]) -> tuple[object, ...]:
    value = metadata.get("period_order")
    if not isinstance(value, (tuple, list)) or not value:
        raise PlotNotAvailableError(
            "trajectory plotting requires the fitted Dynamic-SBM period order"
        )
    order = tuple(value)
    index = pd.Index(order)
    if index.hasnans or not index.is_unique:
        raise PlotNotAvailableError(
            "trajectory plotting requires unique, non-missing horizon periods"
        )
    return order


def _certificate_tolerance(metadata: Mapping[str, Any]) -> float:
    value = metadata.get("tolerance")
    if not _finite(value) or float(value) <= 0:
        raise PlotNotAvailableError(
            "trajectory plotting requires the fitted numerical tolerance"
        )
    return 10.0 * float(value)


def _order_by_period(
    frame: pd.DataFrame,
    *,
    periods: tuple[object, ...],
    column: str,
    table: str,
) -> pd.DataFrame:
    if frame[column].isna().any() or frame[column].duplicated().any():
        raise PlotNotAvailableError(
            f"trajectory {table} must contain one row per non-missing period"
        )
    period_index = pd.Index(periods)
    positions = period_index.get_indexer(frame[column])
    if (positions < 0).any() or set(positions.tolist()) != set(range(len(periods))):
        raise PlotNotAvailableError(
            f"trajectory {table} periods do not match the fitted horizon"
        )
    ordered = frame.copy(deep=True)
    ordered["_deapack_period_position"] = positions
    return ordered.sort_values("_deapack_period_position", kind="stable").reset_index(
        drop=True
    )


def _available_dmus(summary: pd.DataFrame) -> str:
    return ", ".join(repr(value) for value in summary["dmu_id"].drop_duplicates())


def _summary_row(result: Any, *, dmu_id: object) -> pd.Series:
    summary = result.summary(copy=True)
    selected = summary.loc[summary["dmu_id"].eq(dmu_id).fillna(False)]
    if len(selected) != 1:
        if selected.empty:
            raise PlotNotAvailableError(
                f"unknown trajectory dmu_id {dmu_id!r}; available DMUs: "
                f"{_available_dmus(summary)}"
            )
        raise PlotNotAvailableError(
            "trajectory plotting requires one horizon summary row per DMU"
        )
    row = selected.iloc[0]
    if str(row.get("solver_status", "")).strip().casefold() != "optimal":
        raise PlotNotAvailableError(
            "trajectory plotting requires an optimal certified horizon result"
        )
    if "score_valid" not in selected or not _true(row.get("score_valid")):
        raise PlotNotAvailableError(
            "trajectory plotting requires score_valid=True for the selected horizon"
        )
    if _display(row.get("score_status")) != "defined":
        raise PlotNotAvailableError(
            "trajectory plotting requires a defined certified horizon score"
        )
    if not _finite(row.get("efficiency")):
        raise PlotNotAvailableError(
            "trajectory plotting requires a finite certified horizon efficiency"
        )
    return row.copy(deep=True)


def _carryover_selection(
    targets: pd.DataFrame,
    *,
    dmu_id: object,
    variable: str | None,
) -> tuple[str, str, pd.DataFrame]:
    selected = targets.loc[
        targets["dmu_id"].eq(dmu_id).fillna(False)
        & targets["role"].isin(_CARRYOVER_ROLES)
    ].copy(deep=True)
    identities = selected[["role", "variable"]].drop_duplicates()
    if variable is None:
        if len(identities) != 1:
            choices = ", ".join(
                f"{row.variable!r} ({row.role})"
                for row in identities.itertuples(index=False)
            )
            raise PlotNotAvailableError(
                "trajectory variable must be specified when the result contains "
                f"multiple carry-overs; available choices: {choices or 'none'}"
            )
        role = str(identities.iloc[0]["role"])
        resolved_variable = str(identities.iloc[0]["variable"])
    else:
        if not isinstance(variable, str) or not variable.strip():
            raise PlotNotAvailableError(
                "trajectory variable must be a non-empty carry-over name"
            )
        matches = identities.loc[identities["variable"].eq(variable)]
        if matches.empty:
            choices = ", ".join(repr(value) for value in identities["variable"])
            raise PlotNotAvailableError(
                f"unknown trajectory variable {variable!r}; available carry-overs: "
                f"{choices or 'none'}"
            )
        if len(matches) != 1:
            raise PlotNotAvailableError(
                f"trajectory variable {variable!r} is ambiguous across carry-over roles"
            )
        role = str(matches.iloc[0]["role"])
        resolved_variable = variable
    rows = selected.loc[
        selected["role"].eq(role) & selected["variable"].eq(resolved_variable)
    ].copy(deep=True)
    return role, resolved_variable, rows


def _scaled_close(left: float, right: float, *, tolerance: float) -> bool:
    scale = max(1.0, abs(left), abs(right))
    return abs(left - right) <= tolerance * scale


def _require_diagnostics(result: Any, *, dmu_id: object) -> None:
    diagnostics = getattr(result, "diagnostics", None)
    if not isinstance(diagnostics, pd.DataFrame):
        raise PlotNotAvailableError(
            "trajectory plotting requires Dynamic-SBM certificate diagnostics"
        )
    required = {
        "dmu_id",
        "postsolve_certified",
        "economic_postsolve_certified",
        "certification_reason",
        "economic_certification_reason",
    }
    missing = required.difference(diagnostics.columns)
    if missing:
        raise PlotNotAvailableError(
            "trajectory plotting requires diagnostic columns: "
            f"{', '.join(sorted(missing))}"
        )
    selected = diagnostics.loc[diagnostics["dmu_id"].eq(dmu_id).fillna(False)]
    if len(selected) != 1:
        raise PlotNotAvailableError(
            "trajectory plotting requires one certificate record for the "
            "selected horizon"
        )
    row = selected.iloc[0]
    if not _true(row["postsolve_certified"]) or not _true(
        row["economic_postsolve_certified"]
    ):
        raise PlotNotAvailableError(
            "trajectory plotting requires certified LP and economic accounts"
        )
    if (
        _display(row["certification_reason"]) != "certified"
        or _display(row["economic_certification_reason"]) != "certified"
    ):
        raise PlotNotAvailableError(
            "trajectory plotting requires explicit certified diagnostic reasons"
        )


def _prepare_transitions(
    links: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    dmu_id: object,
    variable: str,
    periods: tuple[object, ...],
    tolerance: float,
) -> tuple[pd.DataFrame, str, str]:
    selected = links.loc[
        links["dmu_id"].eq(dmu_id).fillna(False)
        & links["carryover"].eq(variable).fillna(False)
    ].copy(deep=True)
    ordered = _order_by_period(
        selected,
        periods=periods,
        column="source_period",
        table="carry-over link account",
    )
    if len(ordered) != len(periods):
        raise PlotNotAvailableError(
            "trajectory link account must cover every horizon period"
        )

    target_values = pd.to_numeric(targets["target"], errors="coerce").to_numpy()
    observed_values = pd.to_numeric(targets["observed"], errors="coerce").to_numpy()
    transitions: list[dict[str, Any]] = []
    for position, row in enumerate(ordered.itertuples(index=False)):
        if _missing_scalar(row.period) or row.period != row.source_period:
            raise PlotNotAvailableError(
                "trajectory link period and source period do not agree"
            )
        if _display(row.selection_status) != _SELECTION_STATUS:
            raise PlotNotAvailableError(
                "trajectory link account lacks the certified path-selection status"
            )
        link_observed = float(row.observed) if _finite(row.observed) else np.nan
        if not math.isfinite(link_observed) or not _scaled_close(
            link_observed,
            float(observed_values[position]),
            tolerance=tolerance,
        ):
            raise PlotNotAvailableError(
                "trajectory observed quantities do not reconstruct the link account"
            )
        source_target = (
            float(row.source_target) if _finite(row.source_target) else np.nan
        )
        if not math.isfinite(source_target) or not _scaled_close(
            source_target,
            float(target_values[position]),
            tolerance=tolerance,
        ):
            raise PlotNotAvailableError(
                "trajectory source targets do not reconstruct the published "
                "target table"
            )
        if position == len(periods) - 1:
            if not _missing_scalar(row.target_period) or not _missing_scalar(
                row.next_period_target
            ):
                raise PlotNotAvailableError(
                    "trajectory terminal period must not fabricate a successor target"
                )
            if not _missing_scalar(row.continuity_residual):
                raise PlotNotAvailableError(
                    "trajectory terminal period must not fabricate a "
                    "continuity residual"
                )
            terminal_status = str(row.boundary_status)
            if terminal_status != "observed_terminal_no_outgoing_continuity":
                raise PlotNotAvailableError(
                    "trajectory terminal boundary status is not source-compatible"
                )
            continue

        expected_period = periods[position + 1]
        if _missing_scalar(row.target_period) or row.target_period != expected_period:
            raise PlotNotAvailableError(
                "trajectory link account does not follow the fitted "
                "adjacent-period order"
            )
        if _display(row.boundary_status) != "adjacent_period_continuity":
            raise PlotNotAvailableError(
                "trajectory nonterminal boundary lacks adjacent-period "
                "continuity status"
            )
        inherited = (
            float(row.next_period_target) if _finite(row.next_period_target) else np.nan
        )
        residual = (
            float(row.continuity_residual)
            if _finite(row.continuity_residual)
            else np.nan
        )
        if not math.isfinite(inherited) or not _scaled_close(
            source_target,
            inherited,
            tolerance=tolerance,
        ):
            raise PlotNotAvailableError(
                "trajectory outgoing and inherited carry-over targets do not match"
            )
        residual_scale = max(1.0, abs(source_target), abs(inherited))
        if not math.isfinite(residual) or abs(residual) > tolerance * residual_scale:
            raise PlotNotAvailableError(
                "trajectory carry-over continuity is not certified for plotting"
            )
        transitions.append(
            {
                "source_period": row.source_period,
                "target_period": row.target_period,
                "source_target": source_target,
                "inherited_target": inherited,
                "continuity_residual": residual,
                "boundary_status": row.boundary_status,
            }
        )

    transition_frame = pd.DataFrame(transitions)
    carryover_kinds = ordered["carryover_kind"].drop_duplicates()
    if len(carryover_kinds) != 1:
        raise PlotNotAvailableError(
            "trajectory carry-over kind must be stable across the fitted horizon"
        )
    return transition_frame, str(carryover_kinds.iloc[0]), terminal_status


def _prepare_score_inclusion(
    slacks: pd.DataFrame,
    *,
    dmu_id: object,
    role: str,
    variable: str,
    periods: tuple[object, ...],
    orientation: str,
    score_variant: str,
    raw_tolerance: float,
) -> tuple[pd.DataFrame, str]:
    selected = slacks.loc[
        slacks["dmu_id"].eq(dmu_id).fillna(False)
        & slacks["role"].eq(role).fillna(False)
        & slacks["variable"].eq(variable).fillna(False)
    ].copy(deep=True)
    if role == "fixed_carryover":
        if not selected.empty:
            raise PlotNotAvailableError(
                "trajectory fixed carry-over must not fabricate slack-score rows"
            )
        return (
            pd.DataFrame(
                {
                    "period": periods,
                    "included_in_optimization_objective": False,
                    "included_in_reported_score": False,
                    "slack": 0.0,
                }
            ),
            "fixed_commitment_not_in_reported_score",
        )
    ordered = _order_by_period(
        selected,
        periods=periods,
        column="period",
        table="carry-over score account",
    )
    if len(ordered) != len(periods):
        raise PlotNotAvailableError(
            "trajectory carry-over score account must cover every horizon period"
        )
    if not ordered["selection_status"].eq(_SELECTION_STATUS).all():
        raise PlotNotAvailableError(
            "trajectory slack account lacks the certified path-selection status"
        )
    if not ordered["score_variant"].eq(score_variant).all():
        raise PlotNotAvailableError(
            "trajectory slack and horizon score variants do not agree"
        )
    for column in (
        "included_in_optimization_objective",
        "included_in_reported_score",
    ):
        values = ordered[column]
        if (
            values.isna().any()
            or not values.map(lambda value: isinstance(value, (bool, np.bool_))).all()
        ):
            raise PlotNotAvailableError(
                "trajectory carry-over score inclusion must be explicitly reported"
            )
        ordered[column] = values.astype(bool)
    slacks_numeric = pd.to_numeric(ordered["slack"], errors="coerce")
    if not slacks_numeric.map(math.isfinite).all():
        raise PlotNotAvailableError(
            "trajectory slack account must contain finite source deviations"
        )
    if role == "bad_carryover":
        expected_optimization = orientation in {"input", "non-oriented"}
    elif role == "good_carryover":
        expected_optimization = orientation in {"output", "non-oriented"}
    elif role == "free_carryover":
        expected_optimization = False
    else:
        raise PlotNotAvailableError(
            "trajectory slack-score semantics are unavailable for this role"
        )
    expected_optimization_values = np.full(
        len(ordered), expected_optimization, dtype=bool
    )
    if role != "free_carryover" or score_variant == "base":
        expected_reported_values = expected_optimization_values.copy()
    elif score_variant == "free_adjusted_post":
        expected_reported_values = np.asarray(
            [
                orientation in {"input", "non-oriented"}
                if slack > raw_tolerance
                else orientation in {"output", "non-oriented"}
                if slack < -raw_tolerance
                else True
                for slack in slacks_numeric.to_numpy(dtype=float)
            ],
            dtype=bool,
        )
    else:
        raise PlotNotAvailableError(
            "trajectory plotting requires a source-qualified score variant"
        )
    if not np.array_equal(
        ordered["included_in_optimization_objective"].to_numpy(dtype=bool),
        expected_optimization_values,
    ) or not np.array_equal(
        ordered["included_in_reported_score"].to_numpy(dtype=bool),
        expected_reported_values,
    ):
        raise PlotNotAvailableError(
            "trajectory slack-score flags do not reconstruct from source semantics"
        )
    ordered["slack"] = slacks_numeric.astype(float)
    reported = ordered["included_in_reported_score"]
    if reported.all():
        policy = "included_in_reported_score"
    elif (~reported).all():
        policy = "feasibility_only_not_in_reported_score"
    else:
        policy = "period_specific_reported_score_inclusion"
    return (
        ordered[
            [
                "period",
                "included_in_optimization_objective",
                "included_in_reported_score",
                "slack",
            ]
        ].copy(deep=True),
        policy,
    )


def _prepare_period_accounts(
    components: pd.DataFrame,
    *,
    dmu_id: object,
    periods: tuple[object, ...],
    summary: pd.Series,
    tolerance: float,
) -> pd.DataFrame:
    dmu_components = components.loc[components["dmu_id"].eq(dmu_id).fillna(False)].copy(
        deep=True
    )
    selected = dmu_components.loc[
        dmu_components["component_type"].eq("period").fillna(False)
    ].copy(deep=True)
    ordered = _order_by_period(
        selected,
        periods=periods,
        column="period",
        table="period account",
    )
    if len(ordered) != len(periods):
        raise PlotNotAvailableError(
            "trajectory period account must cover every horizon period"
        )
    expected_component_ids = [
        f"period_{position + 1}" for position in range(len(periods))
    ]
    if [_display(value) for value in ordered["component_id"]] != expected_component_ids:
        raise PlotNotAvailableError(
            "trajectory period component identities do not match the fitted horizon"
        )
    if not ordered["selection_status"].eq(_SELECTION_STATUS).all():
        raise PlotNotAvailableError(
            "trajectory period account lacks the certified path-selection status"
        )
    efficiencies = pd.to_numeric(ordered["efficiency"], errors="coerce")
    input_accounts = pd.to_numeric(ordered["input_account"], errors="coerce")
    output_accounts = pd.to_numeric(
        ordered["output_expansion_account"], errors="coerce"
    )
    effective_weights = pd.to_numeric(
        ordered["effective_period_weight"], errors="coerce"
    )
    if not all(
        values.map(math.isfinite).all()
        for values in (
            efficiencies,
            input_accounts,
            output_accounts,
            effective_weights,
        )
    ):
        raise PlotNotAvailableError(
            "trajectory period accounts must contain finite certified values"
        )
    if (
        (input_accounts < -tolerance).any()
        or (input_accounts > 1.0 + tolerance).any()
        or (output_accounts < 1.0 - tolerance).any()
        or (effective_weights <= 0.0).any()
        or not _scaled_close(float(effective_weights.sum()), 1.0, tolerance=tolerance)
    ):
        raise PlotNotAvailableError(
            "trajectory period accounts fall outside the source score domain"
        )

    orientation = _display(summary.get("orientation"))
    inputs = input_accounts.to_numpy(dtype=float)
    outputs = output_accounts.to_numpy(dtype=float)
    weights = effective_weights.to_numpy(dtype=float)
    if orientation == "input":
        reconstructed_periods = inputs
    elif orientation == "output":
        if (outputs <= tolerance).any():
            raise PlotNotAvailableError(
                "trajectory output accounts cannot reconstruct finite scores"
            )
        reconstructed_periods = 1.0 / outputs
    elif orientation == "non-oriented":
        if (outputs <= tolerance).any():
            raise PlotNotAvailableError(
                "trajectory output accounts cannot reconstruct finite scores"
            )
        reconstructed_periods = inputs / outputs
    else:
        raise PlotNotAvailableError(
            "trajectory plotting requires a source-qualified orientation"
        )
    if any(
        not _scaled_close(float(reported), float(reconstructed), tolerance=tolerance)
        for reported, reconstructed in zip(
            efficiencies, reconstructed_periods, strict=True
        )
    ):
        raise PlotNotAvailableError(
            "trajectory period efficiencies do not reconstruct from score accounts"
        )

    aggregate_input = float(np.dot(weights, inputs))
    aggregate_output = float(np.dot(weights, outputs))
    if aggregate_output <= tolerance:
        raise PlotNotAvailableError(
            "trajectory horizon output account cannot reconstruct a finite score"
        )
    if orientation == "input":
        reconstructed_horizon = aggregate_input
    elif orientation == "output":
        reconstructed_horizon = 1.0 / aggregate_output
    else:
        reconstructed_horizon = aggregate_input / aggregate_output

    system = dmu_components.loc[
        dmu_components["component_type"].eq("system").fillna(False)
    ]
    if len(system) != 1:
        raise PlotNotAvailableError(
            "trajectory plotting requires one certified horizon component"
        )
    system_row = system.iloc[0]
    if not _missing_scalar(system_row["period"]):
        raise PlotNotAvailableError(
            "trajectory horizon component must not be assigned to one period"
        )
    if _display(system_row["component_id"]) != "horizon":
        raise PlotNotAvailableError(
            "trajectory system component is not the source horizon account"
        )
    if _display(system_row["selection_status"]) != _SELECTION_STATUS:
        raise PlotNotAvailableError(
            "trajectory horizon component lacks the certified path-selection status"
        )
    horizon_checks = (
        (system_row["input_account"], aggregate_input),
        (system_row["output_expansion_account"], aggregate_output),
        (system_row["efficiency"], reconstructed_horizon),
        (summary.get("overall_input_account"), aggregate_input),
        (summary.get("overall_output_expansion_account"), aggregate_output),
        (summary.get("efficiency"), reconstructed_horizon),
        (summary.get("score"), reconstructed_horizon),
    )
    if any(
        not _finite(reported)
        or not _scaled_close(float(reported), float(reconstructed), tolerance=tolerance)
        for reported, reconstructed in horizon_checks
    ):
        raise PlotNotAvailableError(
            "trajectory horizon score does not reconstruct from period accounts"
        )

    prepared = ordered[
        [
            "period",
            "efficiency",
            "input_account",
            "output_expansion_account",
            "effective_period_weight",
        ]
    ].copy(deep=True)
    prepared["efficiency"] = efficiencies.astype(float)
    prepared["input_account"] = input_accounts.astype(float)
    prepared["output_expansion_account"] = output_accounts.astype(float)
    prepared["effective_period_weight"] = effective_weights.astype(float)
    return prepared


def _provenance(
    metadata: Mapping[str, Any],
    summary: pd.Series,
) -> tuple[tuple[str, str], ...]:
    candidates = (
        ("method", metadata.get("method_id")),
        ("orientation", summary.get("orientation")),
        ("RTS", summary.get("returns_to_scale")),
        ("score variant", summary.get("score_variant")),
        ("boundary", summary.get("boundary_policy")),
    )
    return tuple(
        (label, displayed)
        for label, value in candidates
        if (displayed := _display(value)) is not None
    )


def prepare_trajectory_data(
    result: Any,
    *,
    dmu_id: object,
    variable: str | None = None,
) -> TrajectoryPlotData:
    """Prepare one certified Dynamic-SBM carry-over trajectory.

    The returned frames are detached from ``result``.  The function fails
    closed when horizon certification, period coverage, published targets, or
    adjacent-period continuity cannot be reconstructed.
    """
    metadata = _require_method(result)
    periods = _period_order(metadata)
    if len(periods) > MAX_TRAJECTORY_PERIODS:
        raise PlotNotAvailableError(
            "trajectory plotting is limited to "
            f"{MAX_TRAJECTORY_PERIODS} fitted periods; select a declared shorter "
            "study horizon before fitting rather than silently compressing the "
            "certified path"
        )
    tolerance = _certificate_tolerance(metadata)
    summary = _summary_row(result, dmu_id=dmu_id)
    _require_diagnostics(result, dmu_id=dmu_id)
    n_periods = summary.get("n_periods")
    if not _finite(n_periods) or float(n_periods) != float(len(periods)):
        raise PlotNotAvailableError(
            "trajectory summary period count does not match the fitted horizon"
        )
    horizon_start = summary.get("horizon_start")
    horizon_end = summary.get("horizon_end")
    if (
        _missing_scalar(horizon_start)
        or horizon_start != periods[0]
        or _missing_scalar(horizon_end)
        or horizon_end != periods[-1]
    ):
        raise PlotNotAvailableError(
            "trajectory summary horizon bounds do not match the fitted period order"
        )
    if _display(summary.get("boundary_policy")) != "tone_tsutsui_2010":
        raise PlotNotAvailableError(
            "trajectory plotting requires the source Dynamic-SBM boundary policy"
        )
    if _display(summary.get("selection_status")) != _SELECTION_STATUS:
        raise PlotNotAvailableError(
            "trajectory plotting requires the certified solver-selected path status"
        )

    targets = getattr(result, "targets", None)
    components = getattr(result, "components", None)
    links = getattr(result, "links", None)
    slacks = getattr(result, "slacks", None)
    if (
        not isinstance(targets, pd.DataFrame)
        or not isinstance(components, pd.DataFrame)
        or not isinstance(links, pd.DataFrame)
        or not isinstance(slacks, pd.DataFrame)
    ):
        raise PlotNotAvailableError(
            "trajectory plotting requires target, slack, period-component, "
            "and link tables"
        )
    _require_columns(targets, _TARGET_COLUMNS, table="target")
    _require_columns(components, _COMPONENT_COLUMNS, table="component")
    _require_columns(links, _LINK_COLUMNS, table="link")
    _require_columns(slacks, _SLACK_COLUMNS, table="slack")

    role, resolved_variable, target_rows = _carryover_selection(
        targets,
        dmu_id=dmu_id,
        variable=variable,
    )
    ordered_targets = _order_by_period(
        target_rows,
        periods=periods,
        column="period",
        table="target account",
    )
    if len(ordered_targets) != len(periods):
        raise PlotNotAvailableError(
            "trajectory target account must cover every horizon period"
        )
    observed = pd.to_numeric(ordered_targets["observed"], errors="coerce")
    outgoing = pd.to_numeric(ordered_targets["target"], errors="coerce")
    if not observed.map(math.isfinite).all() or not outgoing.map(math.isfinite).all():
        raise PlotNotAvailableError(
            "trajectory observed and target quantities must be finite"
        )
    balance_residuals = pd.to_numeric(
        ordered_targets["balance_residual"], errors="coerce"
    )
    if not ordered_targets["selection_status"].eq(_SELECTION_STATUS).all():
        raise PlotNotAvailableError(
            "trajectory target account lacks the certified path-selection status"
        )
    if not balance_residuals.map(math.isfinite).all() or any(
        abs(float(residual))
        > tolerance * max(1.0, abs(float(observed_value)), abs(float(target_value)))
        for residual, observed_value, target_value in zip(
            balance_residuals, observed, outgoing, strict=True
        )
    ):
        raise PlotNotAvailableError(
            "trajectory target balance account is not certified for plotting"
        )

    transitions, carryover_kind, terminal_status = _prepare_transitions(
        links,
        ordered_targets,
        dmu_id=dmu_id,
        variable=resolved_variable,
        periods=periods,
        tolerance=tolerance,
    )
    if carryover_kind != role.removesuffix("_carryover"):
        raise PlotNotAvailableError(
            "trajectory carry-over role and link kind do not agree"
        )
    if role == "fixed_carryover":
        if any(
            not _scaled_close(
                float(observed_value),
                float(target_value),
                tolerance=tolerance,
            )
            for observed_value, target_value in zip(observed, outgoing, strict=True)
        ):
            raise PlotNotAvailableError(
                "trajectory fixed carry-over targets must preserve observed commitments"
            )
        fixed_residual = summary.get("max_fixed_account_residual")
        if not _finite(fixed_residual) or abs(float(fixed_residual)) > tolerance:
            raise PlotNotAvailableError(
                "trajectory fixed carry-over account is not certified for plotting"
            )
    orientation = _display(summary.get("orientation"))
    score_variant = _display(summary.get("score_variant"))
    returns_to_scale = _display(summary.get("returns_to_scale"))
    if orientation not in {"input", "output", "non-oriented"}:
        raise PlotNotAvailableError(
            "trajectory plotting requires a source-qualified orientation"
        )
    if score_variant not in {"base", "free_adjusted_post"}:
        raise PlotNotAvailableError(
            "trajectory plotting requires a source-qualified score variant"
        )
    if returns_to_scale not in {"crs", "vrs"}:
        raise PlotNotAvailableError(
            "trajectory plotting requires source-qualified CRS or VRS technology"
        )
    if (
        _display(metadata.get("orientation")) != orientation
        or _display(metadata.get("score_variant")) != score_variant
        or _display(metadata.get("returns_to_scale")) != returns_to_scale
        or _display(metadata.get("boundary_policy"))
        != _display(summary.get("boundary_policy"))
        or _display(metadata.get("selection_status")) != _SELECTION_STATUS
    ):
        raise PlotNotAvailableError(
            "trajectory metadata and horizon score semantics do not agree"
        )
    inclusion, score_policy = _prepare_score_inclusion(
        slacks,
        dmu_id=dmu_id,
        role=role,
        variable=resolved_variable,
        periods=periods,
        orientation=orientation,
        score_variant=score_variant,
        raw_tolerance=float(metadata["tolerance"]),
    )
    if role != "fixed_carryover":
        slack_values = inclusion["slack"].to_numpy(dtype=float)
        observed_values = observed.to_numpy(dtype=float)
        if role == "good_carryover":
            reconstructed_targets = observed_values + slack_values
        else:
            reconstructed_targets = observed_values - slack_values
        if any(
            not _scaled_close(
                float(reported),
                float(reconstructed),
                tolerance=tolerance,
            )
            for reported, reconstructed in zip(
                outgoing, reconstructed_targets, strict=True
            )
        ):
            raise PlotNotAvailableError(
                "trajectory targets do not reconstruct from carry-over slacks"
            )
    inherited = np.full(len(periods), np.nan, dtype=np.float64)
    if not transitions.empty:
        inherited[1:] = transitions["inherited_target"].to_numpy(dtype=float)
    quantity = pd.DataFrame(
        {
            "period": periods,
            "observed": observed.to_numpy(dtype=float),
            "outgoing_target": outgoing.to_numpy(dtype=float),
            "inherited_target": inherited,
            "adjustment": outgoing.to_numpy(dtype=float)
            - observed.to_numpy(dtype=float),
            "included_in_optimization_objective": inclusion[
                "included_in_optimization_objective"
            ].to_numpy(dtype=bool),
            "included_in_reported_score": inclusion[
                "included_in_reported_score"
            ].to_numpy(dtype=bool),
        }
    )
    period_accounts = _prepare_period_accounts(
        components,
        dmu_id=dmu_id,
        periods=periods,
        summary=summary,
        tolerance=tolerance,
    )

    max_continuity = summary.get("max_continuity_residual")
    if not _finite(max_continuity) or abs(float(max_continuity)) > tolerance:
        raise PlotNotAvailableError(
            "trajectory summary does not certify adjacent-period continuity"
        )
    selection_status = str(summary.get("selection_status", "not_reported"))
    return TrajectoryPlotData(
        dmu_id=dmu_id,
        variable=resolved_variable,
        variable_label=resolved_variable.replace("_", " ").strip().title(),
        role=role,
        carryover_kind=carryover_kind,
        quantity=quantity,
        transitions=transitions.copy(deep=True),
        period_accounts=period_accounts,
        horizon_efficiency=float(summary["efficiency"]),
        max_continuity_residual=abs(float(max_continuity)),
        terminal_boundary_status=terminal_status,
        carryover_score_policy=score_policy,
        selection_status=selection_status,
        provenance=_provenance(metadata, summary),
    )


def trajectory_plot_applicable(result: Any) -> bool:
    """Whether at least one certified carry-over trajectory can be prepared."""
    try:
        _require_method(result)
        targets = getattr(result, "targets", None)
        if not isinstance(targets, pd.DataFrame):
            return False
        _require_columns(targets, _TARGET_COLUMNS, table="target")
        identities = targets.loc[
            targets["role"].isin(_CARRYOVER_ROLES),
            ["dmu_id", "variable"],
        ].drop_duplicates()
        for identity in identities.itertuples(index=False):
            try:
                prepare_trajectory_data(
                    result,
                    dmu_id=identity.dmu_id,
                    variable=str(identity.variable),
                )
            except (PlotNotAvailableError, KeyError, TypeError, ValueError):
                continue
            return True
        return False
    except (PlotNotAvailableError, KeyError, TypeError, ValueError, AttributeError):
        return False


__all__ = [
    "MAX_TRAJECTORY_PERIODS",
    "TrajectoryPlotData",
    "prepare_trajectory_data",
    "trajectory_plot_applicable",
]
