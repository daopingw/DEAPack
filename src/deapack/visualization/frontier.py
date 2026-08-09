"""Pure-data preparation for the scalar production-frontier result plot.

The plot is intentionally narrow.  It visualizes a fitted, self-contained
one-input/one-output radial DEA result only when the result already carries
strongly completed targets and the reference organizations are represented in
the selected cross-section.  No plotting backend is imported here.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from ._types import PlotNotAvailableError
from .performance import (
    _available_periods,
    _is_missing_scalar,
    _period_label,
    _period_mask,
    _provenance,
    _unique_period_values,
)

MAX_FRONTIER_OBSERVATIONS = 200
_SUPPORTED_RTS = frozenset({"crs", "vrs"})
_TARGET_COLUMNS = frozenset(
    {"dmu_id", "period", "role", "variable", "observed", "target"}
)
_SUMMARY_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "efficiency",
        "is_efficient",
        "solver_status",
        "completion_valid",
        "target_valid",
        "peer_valid",
    }
)


@dataclass(frozen=True, slots=True)
class FrontierPlotData:
    """Backend-independent payload for one scalar production-frontier figure."""

    period: object
    period_label: str
    input_name: str
    output_name: str
    orientation: str
    returns_to_scale: str
    observations: pd.DataFrame
    frontier: pd.DataFrame
    omitted_observation_count: int
    provenance: tuple[tuple[str, str], ...]

    @property
    def observation_count(self) -> int:
        """Number of certified operating plans shown in the figure."""
        return len(self.observations)

    @property
    def target_change_count(self) -> int:
        """Number of plans with a nonzero move to the reported DEA target."""
        return int(self.observations["target_changed"].sum())


def _metadata_value(
    metadata: Mapping[str, Any],
    key: str,
    nested_path: tuple[str, ...],
) -> object | None:
    direct = metadata.get(key)
    if direct is not None:
        return direct
    current: object = metadata
    for part in nested_path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
        if current is None:
            return None
    return current


def _normalized_metadata_text(
    metadata: Mapping[str, Any],
    key: str,
    nested_path: tuple[str, ...],
) -> str | None:
    value = _metadata_value(metadata, key, nested_path)
    if value is None:
        return None
    value = getattr(value, "value", value)
    if not isinstance(value, str):
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _is_finite(value: object) -> bool:
    if _is_missing_scalar(value):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _explicit_true(value: object) -> bool:
    """Accept only an explicit Boolean validity certificate."""

    return isinstance(value, (bool, np.bool_)) and bool(value)


def _same_period(left: object, right: object) -> bool:
    if _is_missing_scalar(left) and _is_missing_scalar(right):
        return True
    if _is_missing_scalar(left) or _is_missing_scalar(right):
        return False
    try:
        equal = left == right
        return bool(equal)
    except (TypeError, ValueError):
        return False


def _result_contract(result: Any) -> tuple[Mapping[str, Any], str, str]:
    metadata = result.metadata if isinstance(result.metadata, Mapping) else {}
    method_id = _normalized_metadata_text(metadata, "method_id", ())
    if method_id != "static.radial":
        raise PlotNotAvailableError(
            "frontier plotting currently requires a 'static.radial' result"
        )
    orientation = _normalized_metadata_text(
        metadata,
        "orientation",
        ("expanded_spec", "performance", "orientation"),
    )
    if orientation not in {"input", "output"}:
        raise PlotNotAvailableError(
            "frontier plotting requires an input- or output-oriented radial result"
        )
    returns_to_scale = _normalized_metadata_text(
        metadata,
        "returns_to_scale",
        ("expanded_spec", "technology", "returns_to_scale"),
    )
    if returns_to_scale not in _SUPPORTED_RTS:
        raise PlotNotAvailableError(
            "frontier plotting currently supports only CRS or VRS radial results"
        )
    if metadata.get("compute_slacks") is not True:
        raise PlotNotAvailableError(
            "frontier plotting requires compute_slacks=True so target and "
            "strong-efficiency accounts are certified"
        )
    return metadata, orientation, returns_to_scale


def _target_variables(targets: pd.DataFrame) -> tuple[str, str]:
    missing = _TARGET_COLUMNS.difference(targets.columns)
    if missing:
        raise PlotNotAvailableError(
            "frontier plotting requires target columns: "
            + ", ".join(sorted(_TARGET_COLUMNS))
        )
    input_names = targets.loc[targets["role"].eq("input"), "variable"].drop_duplicates()
    output_names = targets.loc[
        targets["role"].eq("output"), "variable"
    ].drop_duplicates()
    if len(input_names) != 1 or len(output_names) != 1:
        raise PlotNotAvailableError(
            "frontier plotting requires exactly one input and one desirable output"
        )
    return str(input_names.iloc[0]), str(output_names.iloc[0])


def frontier_plot_applicable(result: Any) -> bool:
    """Return whether at least one result cross-section passes the full contract."""
    try:
        _result_contract(result)
        summary = result.summary(copy=True)
        if summary.empty or _SUMMARY_COLUMNS.difference(summary.columns):
            return False
        targets = result.targets.copy(deep=True)
        if targets.empty:
            return False
        _target_variables(targets)
    except (AttributeError, PlotNotAvailableError, TypeError, ValueError):
        return False
    periods = _unique_period_values(summary["period"])
    for value in periods:
        count = int(_period_mask(summary["period"], value).sum())
        if not 0 < count <= MAX_FRONTIER_OBSERVATIONS:
            continue
        try:
            prepare_frontier_data(result, period=value)
        except (AttributeError, PlotNotAvailableError, TypeError, ValueError):
            continue
        return True
    return False


def _select_period(
    summary: pd.DataFrame,
    period: object | None,
) -> tuple[pd.DataFrame, object, str]:
    period_values = _unique_period_values(summary["period"])
    if period is None:
        if len(period_values) != 1:
            available = _available_periods(period_values)
            raise PlotNotAvailableError(
                "frontier plotting shows one production technology at a time; "
                f"select period=... from: {available}"
            )
        selected_period = period_values[0]
    else:
        selected_period = period
        if not _period_mask(summary["period"], selected_period).any():
            available = _available_periods(period_values)
            raise PlotNotAvailableError(
                f"period {period!r} is not present in the result; "
                f"available periods: {available}"
            )
    selected = summary.loc[_period_mask(summary["period"], selected_period)].copy(
        deep=True
    )
    cross_section = len(period_values) == 1 and _is_missing_scalar(selected_period)
    return (
        selected,
        selected_period,
        _period_label(selected_period, cross_section=cross_section),
    )


def _target_account(
    targets: pd.DataFrame,
    *,
    selected_period: object,
    input_name: str,
    output_name: str,
) -> pd.DataFrame:
    selected = targets.loc[
        _period_mask(targets["period"], selected_period)
        & targets["role"].isin(["input", "output"])
    ].copy(deep=True)
    selected = selected.loc[
        (selected["role"].eq("input") & selected["variable"].astype(str).eq(input_name))
        | (
            selected["role"].eq("output")
            & selected["variable"].astype(str).eq(output_name)
        )
    ]
    if selected.duplicated(["dmu_id", "role"], keep=False).any():
        raise PlotNotAvailableError(
            "frontier target rows are not unique by organization and variable role"
        )
    input_rows = selected.loc[
        selected["role"].eq("input"),
        ["dmu_id", "observed", "target"],
    ].rename(
        columns={
            "observed": "input_observed",
            "target": "input_target",
        }
    )
    output_rows = selected.loc[
        selected["role"].eq("output"),
        ["dmu_id", "observed", "target"],
    ].rename(
        columns={
            "observed": "output_observed",
            "target": "output_target",
        }
    )
    return input_rows.merge(
        output_rows,
        on="dmu_id",
        how="outer",
        validate="one_to_one",
    )


def _validate_reference_population(
    result: Any,
    *,
    observations: pd.DataFrame,
    selected_period: object,
) -> None:
    intensities = result.intensities.copy(deep=True)
    required = {"dmu_id", "period", "reference_dmu_id", "reference_period"}
    if intensities.empty or required.difference(intensities.columns):
        raise PlotNotAvailableError(
            "frontier plotting requires peer rows with evaluated and reference IDs"
        )
    selected_ids = set(observations["dmu_id"].tolist())
    rows = intensities.loc[
        intensities["dmu_id"].isin(selected_ids)
        & _period_mask(intensities["period"], selected_period)
    ]
    if rows.empty:
        raise PlotNotAvailableError(
            "frontier plotting found no peer evidence for the selected observations"
        )
    outside_ids = set(rows["reference_dmu_id"].tolist()).difference(selected_ids)
    outside_period = any(
        not _same_period(reference_period, selected_period)
        for reference_period in rows["reference_period"]
    )
    if outside_ids or outside_period:
        raise PlotNotAvailableError(
            "frontier plotting currently requires every active peer to belong to "
            "the selected comparison cross-section"
        )


def _vrs_frontier(observations: pd.DataFrame) -> pd.DataFrame:
    efficient = observations.loc[
        observations["is_efficient"],
        ["dmu_id", "input_observed", "output_observed"],
    ].copy(deep=True)
    if efficient.empty:
        raise PlotNotAvailableError(
            "frontier plotting requires at least one certified strongly efficient "
            "organization"
        )
    efficient = efficient.sort_values(
        ["input_observed", "output_observed"],
        ascending=[True, False],
        kind="stable",
    )
    efficient = efficient.drop_duplicates(
        ["input_observed"],
        keep="first",
    ).sort_values("input_observed", kind="stable")
    output_differences = efficient["output_observed"].diff().dropna()
    scale = max(1.0, float(efficient["output_observed"].abs().max()))
    if (output_differences < -1e-8 * scale).any():
        raise PlotNotAvailableError(
            "certified efficient observations do not form a monotone scalar VRS "
            "frontier"
        )
    return efficient.rename(
        columns={
            "input_observed": "input",
            "output_observed": "output",
        }
    ).reset_index(drop=True)


def _crs_frontier(observations: pd.DataFrame) -> pd.DataFrame:
    efficient = observations.loc[
        observations["is_efficient"],
        ["dmu_id", "input_observed", "output_observed"],
    ].copy(deep=True)
    if efficient.empty:
        raise PlotNotAvailableError(
            "frontier plotting requires at least one certified strongly efficient "
            "organization"
        )
    if (
        efficient["input_observed"].le(0).any()
        or efficient["output_observed"].lt(0).any()
    ):
        raise PlotNotAvailableError(
            "the scalar CRS frontier ray requires positive input and nonnegative "
            "output coordinates"
        )
    slopes = efficient["output_observed"] / efficient["input_observed"]
    slope = float(slopes.max())
    tolerance = 1e-7 * max(1.0, abs(slope))
    if ((slopes - slope).abs() > tolerance).any():
        raise PlotNotAvailableError(
            "certified efficient observations do not identify one scalar CRS "
            "frontier ray"
        )
    input_limit = float(observations[["input_observed", "input_target"]].max().max())
    input_limit *= 1.04
    return pd.DataFrame(
        {
            "dmu_id": [pd.NA, pd.NA],
            "input": [0.0, input_limit],
            "output": [0.0, slope * input_limit],
        }
    )


def prepare_frontier_data(
    result: Any,
    *,
    period: object | None = None,
) -> FrontierPlotData:
    """Prepare a one-input/one-output production-frontier plot.

    The selected result must be a CRS or VRS ``static.radial`` fit with
    ``compute_slacks=True``.  Every displayed observation must have an optimal
    solve, a certified strong-efficiency status, finite observed and target
    coordinates, and peer evidence confined to the selected cross-section.
    This gate prevents a teaching diagram from silently inventing a frontier
    for a multi-dimensional, external-reference, or incompletely solved model.
    """
    metadata, orientation, returns_to_scale = _result_contract(result)
    summary = result.summary(copy=True)
    missing_summary = _SUMMARY_COLUMNS.difference(summary.columns)
    if missing_summary:
        raise PlotNotAvailableError(
            "frontier plotting requires summary columns: "
            + ", ".join(sorted(_SUMMARY_COLUMNS))
        )
    if summary.empty:
        raise PlotNotAvailableError("frontier plotting found no observations")
    selected, selected_period, period_label = _select_period(summary, period)
    if selected["dmu_id"].duplicated().any():
        raise PlotNotAvailableError(
            "frontier plotting requires one row per organization in the selected "
            "cross-section"
        )
    if len(selected) > MAX_FRONTIER_OBSERVATIONS:
        raise PlotNotAvailableError(
            "frontier plotting is limited to "
            f"{MAX_FRONTIER_OBSERVATIONS} organizations; use the performance "
            "plot or select a smaller declared study population"
        )

    targets = result.targets.copy(deep=True)
    if targets.empty:
        raise PlotNotAvailableError(
            "frontier plotting requires target rows; refit with compute_slacks=True"
        )
    input_name, output_name = _target_variables(targets)
    accounts = _target_account(
        targets,
        selected_period=selected_period,
        input_name=input_name,
        output_name=output_name,
    )
    prepared = selected[
        [
            "dmu_id",
            "period",
            "efficiency",
            "is_efficient",
            "solver_status",
            "completion_valid",
            "target_valid",
            "peer_valid",
        ]
    ].merge(
        accounts,
        on="dmu_id",
        how="left",
        validate="one_to_one",
    )
    try:
        classifications = prepared["is_efficient"].astype("boolean")
    except (TypeError, ValueError) as error:
        raise PlotNotAvailableError(
            "frontier strong-efficiency status is not boolean"
        ) from error
    coordinate_columns = (
        "input_observed",
        "output_observed",
        "input_target",
        "output_target",
    )
    finite = pd.Series(True, index=prepared.index)
    for column in coordinate_columns:
        finite &= prepared[column].map(_is_finite)
    optimal = (
        prepared["solver_status"].astype("string").str.casefold().eq("optimal")
    ).fillna(False)
    completion_valid = prepared["completion_valid"].map(_explicit_true)
    target_valid = prepared["target_valid"].map(_explicit_true)
    peer_valid = prepared["peer_valid"].map(_explicit_true)
    certified = (
        finite
        & optimal
        & classifications.notna()
        & completion_valid
        & target_valid
        & peer_valid
    )
    omitted = int((~certified).sum())
    observations = prepared.loc[certified].copy(deep=True)
    if observations.empty:
        raise PlotNotAvailableError(
            "frontier plotting found no observations with optimal, finite, "
            "strongly certified target accounts and completion_valid=True, "
            "target_valid=True, peer_valid=True"
        )
    observations["is_efficient"] = classifications.loc[certified].astype(bool)
    for column in (*coordinate_columns, "efficiency"):
        observations[column] = pd.to_numeric(
            observations[column],
            errors="coerce",
        ).astype(float)
    coordinate_scale = observations[list(coordinate_columns)].abs().max(axis=1)
    coordinate_scale = coordinate_scale.clip(lower=1.0)
    movement = (observations["input_observed"] - observations["input_target"]).abs() + (
        observations["output_observed"] - observations["output_target"]
    ).abs()
    observations["target_changed"] = movement > 1e-8 * coordinate_scale
    observations["_deapack_input_order"] = range(len(observations))

    _validate_reference_population(
        result,
        observations=observations,
        selected_period=selected_period,
    )
    if returns_to_scale == "vrs":
        frontier = _vrs_frontier(observations)
    else:
        frontier = _crs_frontier(observations)

    return FrontierPlotData(
        period=selected_period,
        period_label=period_label,
        input_name=input_name,
        output_name=output_name,
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        observations=observations.reset_index(drop=True),
        frontier=frontier,
        omitted_observation_count=omitted,
        provenance=_provenance(metadata),
    )


__all__ = [
    "MAX_FRONTIER_OBSERVATIONS",
    "FrontierPlotData",
    "frontier_plot_applicable",
    "prepare_frontier_data",
]
