"""Pure-data preparation for the performance result plot.

This module deliberately depends only on pandas and the Python standard
library.  Rendering backends consume its detached data structures.
"""

from __future__ import annotations

import math
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pandas as pd

from ._types import MeasureSpec, PlotNotAvailableError
from .measures import (
    measure_certification_mask,
    measure_validity_mask,
    resolve_measure_spec,
)

MAX_AUTO_FACETS = 4
POINT_VIEW_MAX_OBSERVATIONS = 50
UNAVAILABLE_ROSTER_LIMIT = 6
UNAVAILABLE_TEXT_LIMIT = 48
TRANSITION_PERIOD_TEXT_LIMIT = 32
_VALID_VIEWS = ("auto", "points", "ecdf")


@dataclass(frozen=True, slots=True)
class PerformanceFacet:
    """Prepared observations for one cross-section or period."""

    period: object
    label: str
    view: str
    frame: pd.DataFrame
    diagnostic_frame: pd.DataFrame


@dataclass(frozen=True, slots=True)
class PerformanceUnavailableObservation:
    """Bounded display summary for one non-finite headline result.

    These strings are detached from the result, stripped of control characters,
    and length limited before they enter a rendering backend.  The records are
    explanatory only: unavailable observations never become plot coordinates.
    """

    facet_label: str
    dmu_id: str
    reason: str
    certification_status_column: str
    certification_status: str
    validity_status_column: str | None
    validity_status: str | None
    score_status: str


@dataclass(frozen=True, slots=True)
class PerformancePlotData:
    """Backend-independent payload for a performance figure."""

    measure: MeasureSpec
    facets: tuple[PerformanceFacet, ...]
    nonoptimal_count: int
    invalid_metric_count: int
    omitted_metric_count: int
    provenance: tuple[tuple[str, str], ...]
    unavailable_observations: tuple[PerformanceUnavailableObservation, ...] = ()
    unavailable_observation_overflow: int = 0

    @property
    def metric(self) -> str:
        """Backward-compatible name of the prepared summary measure."""
        return self.measure.column

    @property
    def observation_count(self) -> int:
        """Number of certified finite observations in substantive layers."""
        return sum(len(facet.frame) for facet in self.facets)

    @property
    def diagnostic_observation_count(self) -> int:
        """Number of finite excluded observations in diagnostic layers."""
        return sum(len(facet.diagnostic_frame) for facet in self.facets)


def _is_missing_scalar(value: object) -> bool:
    marker = pd.isna(value)
    if isinstance(marker, bool):
        return marker
    try:
        return bool(marker)
    except (TypeError, ValueError) as error:
        raise PlotNotAvailableError("period must be a scalar value") from error


def _period_mask(periods: pd.Series, value: object) -> pd.Series:
    if _is_missing_scalar(value):
        return periods.isna()
    return periods.eq(value).fillna(False)


def _period_label(value: object, *, cross_section: bool) -> str:
    if cross_section:
        return "Cross-section"
    if _is_missing_scalar(value):
        return "Period not reported"
    return f"Period {value}"


def _consistent_complete_value(values: pd.Series) -> object | None:
    """Return one shared non-missing value, or ``None`` when evidence is mixed."""
    if values.empty or values.isna().any():
        return None
    distinct = values.drop_duplicates()
    if len(distinct) != 1:
        return None
    return distinct.iloc[0]


def _facet_label(
    frame: pd.DataFrame,
    *,
    period_value: object,
    cross_section: bool,
) -> str:
    """Prefer an evidenced transition pair and otherwise keep legacy labels."""
    if {"base_period", "comparison_period"}.issubset(frame.columns):
        base_period = _consistent_complete_value(frame["base_period"])
        comparison_period = _consistent_complete_value(frame["comparison_period"])
        if (
            base_period is not None
            and comparison_period is not None
            and _scalar_equal(comparison_period, period_value)
            and not _scalar_equal(base_period, comparison_period)
        ):
            base_label = _bounded_display_text(
                base_period,
                fallback="base period not reported",
                limit=TRANSITION_PERIOD_TEXT_LIMIT,
            )
            comparison_label = _bounded_display_text(
                comparison_period,
                fallback="comparison period not reported",
                limit=TRANSITION_PERIOD_TEXT_LIMIT,
            )
            return f"{base_label} \u2192 {comparison_label}"
    return _period_label(period_value, cross_section=cross_section)


def _scalar_equal(left: object, right: object) -> bool:
    """Compare period scalars without allowing ambiguous array-like truth."""
    if _is_missing_scalar(left) or _is_missing_scalar(right):
        return False
    try:
        return bool(left == right)
    except (TypeError, ValueError):
        return False


def _available_periods(values: list[object]) -> str:
    return ", ".join(
        "not reported" if _is_missing_scalar(value) else repr(value) for value in values
    )


def _unique_period_values(periods: pd.Series) -> list[object]:
    values: list[object] = []
    missing_seen = False
    for value in periods.drop_duplicates():
        if _is_missing_scalar(value):
            if not missing_seen:
                values.append(value)
                missing_seen = True
        else:
            values.append(value)
    return values


def _is_finite(value: object) -> bool:
    if _is_missing_scalar(value):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _bounded_display_text(
    value: object,
    *,
    fallback: str,
    limit: int = UNAVAILABLE_TEXT_LIMIT,
) -> str:
    """Return compact backend-safe text without exposing unbounded raw values."""
    if _is_missing_scalar(value):
        return fallback
    text = str(value.value if isinstance(value, Enum) else value)
    text = "".join(
        " " if unicodedata.category(character).startswith("C") else character
        for character in text
    )
    text = " ".join(text.split()).strip()
    if not text:
        return fallback
    if len(text) > limit:
        return f"{text[: limit - 1]}\u2026"
    return text


def _unavailable_summaries(
    frame: pd.DataFrame,
    *,
    finite: pd.Series,
    certified: pd.Series,
    valid: pd.Series,
    measure: MeasureSpec,
    facet_label: str,
    limit: int,
) -> tuple[PerformanceUnavailableObservation, ...]:
    """Summarize at most ``limit`` non-finite rows in stable input order."""
    if limit <= 0:
        return ()
    columns = ["dmu_id", measure.certification_status_column]
    if measure.validity_column is not None:
        columns.append(measure.validity_column)
    if "score_status" in frame:
        columns.append("score_status")
    columns = [column for column in dict.fromkeys(columns) if column in frame.columns]
    unavailable_positions: list[int] = []
    for position, is_finite in enumerate(finite.array):
        if not bool(is_finite):
            unavailable_positions.append(position)
            if len(unavailable_positions) == limit:
                break
    summaries: list[PerformanceUnavailableObservation] = []
    for position in unavailable_positions:
        row = frame.iloc[position][columns]
        if not bool(certified.iloc[position]):
            reason = "solver/certification unavailable"
        elif not bool(valid.iloc[position]):
            reason = "measure undefined"
        else:
            reason = "metric missing/non-finite"
        validity_status = (
            None
            if measure.validity_column is None
            else _bounded_display_text(
                row.get(measure.validity_column),
                fallback="not reported",
            )
        )
        summaries.append(
            PerformanceUnavailableObservation(
                facet_label=facet_label,
                dmu_id=_bounded_display_text(
                    row.get("dmu_id"),
                    fallback="DMU not reported",
                ),
                reason=reason,
                certification_status_column=_bounded_display_text(
                    measure.certification_status_column,
                    fallback="certification status",
                ),
                certification_status=_bounded_display_text(
                    row.get(measure.certification_status_column),
                    fallback="not reported",
                ),
                validity_status_column=(
                    None
                    if measure.validity_column is None
                    else _bounded_display_text(
                        measure.validity_column,
                        fallback="validity status",
                    )
                ),
                validity_status=validity_status,
                score_status=_bounded_display_text(
                    row.get("score_status"),
                    fallback="not reported",
                ),
            )
        )
    return tuple(summaries)


def _classification_classes(values: pd.Series) -> pd.Series:
    classes = pd.Series(
        "not_reported",
        index=values.index,
        dtype="string",
    )
    try:
        nullable = values.astype("boolean")
    except (TypeError, ValueError):
        return classes
    reported = nullable.notna()
    efficient = (reported & nullable).fillna(False)
    inefficient = (reported & ~nullable).fillna(False)
    classes.loc[efficient] = "efficient"
    classes.loc[inefficient] = "inefficient"
    return classes


def _mapping_value(
    metadata: Mapping[str, Any],
    top_level: str,
    nested_path: tuple[str, ...],
) -> object | None:
    value = metadata.get(top_level)
    if value is not None:
        return value
    current: object = metadata
    for key in nested_path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def _display_value(value: object) -> str | None:
    if value is None:
        return None
    enum_value = getattr(value, "value", value)
    if isinstance(enum_value, (str, int, float, bool)):
        text = str(enum_value).strip()
        return text or None
    return None


def _provenance(metadata: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    candidates = (
        ("method", "method_id", ()),
        (
            "orientation",
            "orientation",
            ("expanded_spec", "performance", "orientation"),
        ),
        (
            "RTS",
            "returns_to_scale",
            ("expanded_spec", "technology", "returns_to_scale"),
        ),
        (
            "reference",
            "reference_kind",
            ("expanded_spec", "reference", "kind"),
        ),
    )
    entries: list[tuple[str, str]] = []
    for label, top_level, nested_path in candidates:
        value = _display_value(_mapping_value(metadata, top_level, nested_path))
        if value is not None:
            entries.append((label, value))
    return tuple(entries)


def _prepare_facet(
    frame: pd.DataFrame,
    *,
    measure: MeasureSpec,
    period_value: object,
    label: str,
    requested_view: str,
    unavailable_summary_limit: int,
) -> tuple[
    PerformanceFacet,
    int,
    int,
    int,
    tuple[PerformanceUnavailableObservation, ...],
]:
    metric = measure.column
    converted = pd.to_numeric(frame[metric], errors="coerce")
    finite = converted.map(_is_finite)
    omitted = int((~finite).sum())
    certified = measure_certification_mask(frame, measure)
    valid = measure_validity_mask(frame, measure)
    unavailable = _unavailable_summaries(
        frame,
        finite=finite,
        certified=certified,
        valid=valid,
        measure=measure,
        facet_label=label,
        limit=unavailable_summary_limit,
    )
    substantive = finite & certified & valid
    uncertified = finite & ~certified
    invalid = finite & certified & ~valid
    diagnostic = uncertified | invalid
    classification = measure.classification_column
    base_columns = ["dmu_id", "period", "solver_status"]
    if classification is not None:
        base_columns.append(classification)
    prepared = frame.loc[
        substantive,
        base_columns,
    ].copy(deep=True)
    prepared[metric] = converted.loc[substantive].astype(float)
    if classification is None:
        prepared["_deapack_measure_class"] = pd.Series(
            "reported",
            index=prepared.index,
            dtype="string",
        )
    else:
        prepared["_deapack_measure_class"] = _classification_classes(
            prepared[classification]
        )
    prepared["_deapack_input_order"] = range(len(prepared))

    diagnostic_columns = ["dmu_id", "period", "solver_status"]
    for evidence_column in (
        measure.certification_status_column,
        measure.validity_column,
        "score_valid",
        "score_status",
    ):
        if (
            evidence_column is not None
            and evidence_column in frame
            and evidence_column not in diagnostic_columns
        ):
            diagnostic_columns.append(evidence_column)
    diagnostic_frame = frame.loc[diagnostic, diagnostic_columns].copy(deep=True)
    diagnostic_frame[metric] = converted.loc[diagnostic].astype(float)
    diagnostic_frame["_deapack_diagnostic_reason"] = pd.Series(
        "Non-optimal — excluded",
        index=diagnostic_frame.index,
        dtype="string",
    )
    diagnostic_frame.loc[
        invalid.loc[diagnostic_frame.index],
        "_deapack_diagnostic_reason",
    ] = "Measure undefined — excluded"
    diagnostic_frame["_deapack_input_order"] = range(len(diagnostic_frame))

    resolved_view = requested_view
    if requested_view == "auto":
        resolved_view = (
            "points" if len(prepared) <= POINT_VIEW_MAX_OBSERVATIONS else "ecdf"
        )
    return (
        PerformanceFacet(
            period=period_value,
            label=label,
            view=resolved_view,
            frame=prepared,
            diagnostic_frame=diagnostic_frame,
        ),
        omitted,
        int(uncertified.sum()),
        int(invalid.sum()),
        unavailable,
    )


def prepare_performance_data(
    result: Any,
    *,
    metric: str | None = None,
    period: object | None = None,
    view: str = "auto",
) -> PerformancePlotData:
    """Prepare a performance plot without importing a plotting backend.

    When ``metric`` is omitted, the result's safest finite declared measure is
    selected. An explicit metric must have known plotting semantics; arbitrary
    numeric columns are not guessed. Missing or non-finite values are omitted.
    Non-optimal values and values that fail the measure's declared validity
    contract are retained only in a diagnostic layer.
    """
    if view not in _VALID_VIEWS:
        raise PlotNotAvailableError(
            f"unknown performance view {view!r}; choose from {_VALID_VIEWS}"
        )

    measure = resolve_measure_spec(result, metric)
    metric = measure.column
    summary = result.summary(copy=True)
    if summary.empty:
        raise PlotNotAvailableError(
            f"performance metric {metric!r} has no observations to plot"
        )

    period_values = _unique_period_values(summary["period"])
    if period is not None:
        selected_mask = _period_mask(summary["period"], period)
        if not selected_mask.any():
            available = _available_periods(period_values)
            raise PlotNotAvailableError(
                f"period {period!r} is not present in the result; "
                f"available periods: {available}"
            )
        selected = summary.loc[selected_mask].copy(deep=True)
        facet_values = [period]
    else:
        selected = summary.copy(deep=True)
        facet_values = period_values
        if len(facet_values) > MAX_AUTO_FACETS:
            raise PlotNotAvailableError(
                f"performance plot found {len(facet_values)} periods; "
                f"select period=... when more than {MAX_AUTO_FACETS} are present"
            )

    cross_section = len(facet_values) == 1 and _is_missing_scalar(facet_values[0])
    facets: list[PerformanceFacet] = []
    omitted_total = 0
    nonoptimal_total = 0
    invalid_total = 0
    unavailable: list[PerformanceUnavailableObservation] = []
    for facet_value in facet_values:
        facet_frame = selected.loc[_period_mask(selected["period"], facet_value)].copy(
            deep=True
        )
        label = _facet_label(
            facet_frame,
            period_value=facet_value,
            cross_section=cross_section,
        )
        facet, omitted, nonoptimal, invalid, unavailable_facet = _prepare_facet(
            facet_frame,
            measure=measure,
            period_value=facet_value,
            label=label,
            requested_view=view,
            unavailable_summary_limit=(UNAVAILABLE_ROSTER_LIMIT - len(unavailable)),
        )
        facets.append(facet)
        unavailable.extend(unavailable_facet)
        omitted_total += omitted
        nonoptimal_total += nonoptimal
        invalid_total += invalid

    if not any(not facet.frame.empty for facet in facets):
        raise PlotNotAvailableError(
            f"performance metric {metric!r} has no finite optimal observations "
            "that satisfy its validity contract for the selected periods"
        )

    metadata = result.metadata if isinstance(result.metadata, Mapping) else {}
    return PerformancePlotData(
        measure=measure,
        facets=tuple(facets),
        nonoptimal_count=nonoptimal_total,
        invalid_metric_count=invalid_total,
        omitted_metric_count=omitted_total,
        provenance=_provenance(metadata),
        unavailable_observations=tuple(unavailable),
        unavailable_observation_overflow=max(
            0,
            omitted_total - len(unavailable),
        ),
    )


__all__ = [
    "MAX_AUTO_FACETS",
    "POINT_VIEW_MAX_OBSERVATIONS",
    "TRANSITION_PERIOD_TEXT_LIMIT",
    "UNAVAILABLE_ROSTER_LIMIT",
    "UNAVAILABLE_TEXT_LIMIT",
    "PerformanceFacet",
    "PerformancePlotData",
    "PerformanceUnavailableObservation",
    "prepare_performance_data",
]
