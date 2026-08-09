"""Source-independent preparation of a compact DEAPack result brief."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from html import escape
from typing import Any

import numpy as np
import pandas as pd

from deapack.visualization._types import (
    MeasureSpec,
    PlotNotAvailableError,
)
from deapack.visualization.measures import (
    measure_certification_mask,
    measure_validity_mask,
    resolve_measure_spec,
)

from ._types import (
    ReportNotAvailableError,
    ResultReport,
    _prepared_result_report,
)

_MAX_PERFORMANCE_ROWS = 24
_VALID_KINDS = ("brief",)
_VALID_DETAILS = ("brief",)
_VALID_THEMES = ("deapack",)


@dataclass(frozen=True, slots=True)
class _ResultView:
    """Minimal detached result view accepted by visualization preparation."""

    frame: pd.DataFrame
    metadata: Mapping[str, Any]

    def summary(self, *, copy: bool = True) -> pd.DataFrame:
        return self.frame.copy(deep=True) if copy else self.frame


@dataclass(frozen=True, slots=True)
class _ReportMetricData:
    """Detached measure rows prepared under reporting-specific constraints."""

    measure: MeasureSpec
    frame: pd.DataFrame
    diagnostic_frame: pd.DataFrame
    omitted_metric_count: int
    invalid_metric_count: int
    nonoptimal_metric_count: int

    @property
    def metric(self) -> str:
        return self.measure.column


def _safe(value: object) -> str:
    if value is None:
        return "Not reported"
    try:
        if bool(pd.isna(value)):
            return "Not reported"
    except (TypeError, ValueError):
        pass
    enum_value = getattr(value, "value", value)
    return escape(str(enum_value), quote=True)


def _is_missing_scalar(value: object) -> bool:
    if isinstance(value, tuple):
        return False
    marker = pd.isna(value)
    if isinstance(marker, (bool, np.bool_)):
        return bool(marker)
    try:
        return bool(marker)
    except (TypeError, ValueError) as error:
        raise ReportNotAvailableError(
            "period and dmu_id filters must be scalar values"
        ) from error


def _scalar_mask(values: pd.Series, selected: object) -> pd.Series:
    if _is_missing_scalar(selected):
        return values.isna()
    if isinstance(selected, tuple):
        return values.map(
            lambda value: isinstance(value, tuple) and value == selected,
            na_action=None,
        ).astype(bool)
    try:
        return values.eq(selected).fillna(False)
    except (TypeError, ValueError) as error:
        raise ReportNotAvailableError(
            "period and dmu_id filters must be comparable scalar values"
        ) from error


def _available_values(values: pd.Series) -> str:
    available = values.drop_duplicates().tolist()
    displayed = []
    limit = 8
    for value in available[:limit]:
        displayed.append("not reported" if _is_missing_scalar(value) else repr(value))
    if len(available) > limit:
        displayed.append(f"… (+{len(available) - limit} more)")
    return ", ".join(displayed) or "none"


def _validate_summary_schema(summary: object) -> pd.DataFrame:
    if not isinstance(summary, pd.DataFrame):
        raise ReportNotAvailableError(
            "result.summary(copy=True) must return a pandas DataFrame"
        )
    required = {
        "dmu_id",
        "period",
        "score",
        "efficiency",
        "distance",
        "is_efficient",
        "solver_status",
        "model_family",
    }
    missing = required.difference(summary.columns)
    if missing:
        raise ReportNotAvailableError(
            f"the result summary is missing reporting columns: {sorted(missing)!r}"
        )
    if summary.columns.has_duplicates:
        raise ReportNotAvailableError(
            "the result summary contains duplicate column names"
        )
    return summary


def _filter_summary(
    summary: pd.DataFrame,
    *,
    period: object | None,
    dmu_id: object | None,
) -> pd.DataFrame:
    selected = summary.copy(deep=True)
    if period is not None:
        period_mask = _scalar_mask(selected["period"], period)
        if not period_mask.any():
            raise ReportNotAvailableError(
                f"period {period!r} is not present in the result; available "
                f"periods: {_available_values(selected['period'])}"
            )
        selected = selected.loc[period_mask].copy(deep=True)
    if dmu_id is not None:
        dmu_mask = _scalar_mask(selected["dmu_id"], dmu_id)
        if not dmu_mask.any():
            raise ReportNotAvailableError(
                f"dmu_id {dmu_id!r} is not present in the selected result; "
                f"available DMUs: {_available_values(selected['dmu_id'])}"
            )
        selected = selected.loc[dmu_mask].copy(deep=True)
    if selected.empty:
        raise ReportNotAvailableError("the selected result contains no observations")
    return selected.reset_index(drop=True)


def _mapping_value(
    metadata: Mapping[str, Any],
    top_level: str,
    nested_path: tuple[str, ...],
) -> object | None:
    direct = metadata.get(top_level)
    if direct is not None:
        return direct
    current: object = metadata
    for key in nested_path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def _single_value(values: pd.Series) -> object | None:
    unique = values.drop_duplicates()
    if len(unique) != 1:
        return None
    return unique.iloc[0]


def _card(label: str, value: object) -> str:
    return (
        '<div class="card">'
        f'<span class="card-label">{escape(label, quote=True)}</span>'
        f'<span class="card-value">{_safe(value)}</span>'
        "</div>"
    )


def _table_html(frame: pd.DataFrame) -> str:
    return frame.to_html(
        index=False,
        border=0,
        classes=("deapack-table",),
        escape=True,
        na_rep="Not reported",
    )


def _status_frame(summary: pd.DataFrame) -> pd.DataFrame:
    normalized = summary["solver_status"].astype("string").fillna("not_reported")
    counts = normalized.value_counts(sort=False, dropna=False)
    return pd.DataFrame(
        {
            "Solver status": counts.index.astype(str),
            "Observations": counts.to_numpy(dtype=int),
        }
    )


def _classification_classes(values: pd.Series) -> pd.Series:
    classes = pd.Series("not_reported", index=values.index, dtype="string")
    try:
        nullable = values.astype("boolean")
    except (TypeError, ValueError):
        return classes
    reported = nullable.notna()
    classes.loc[(reported & nullable).fillna(False)] = "efficient"
    classes.loc[(reported & ~nullable).fillna(False)] = "inefficient"
    return classes


def _period_labels(values: pd.Series) -> pd.Series:
    unique = values.drop_duplicates()
    cross_section = len(unique) == 1 and _is_missing_scalar(unique.iloc[0])
    labels = pd.Series(index=values.index, dtype="string")
    for index, value in values.items():
        if cross_section:
            labels.loc[index] = "Cross-section"
        elif _is_missing_scalar(value):
            labels.loc[index] = "Period not reported"
        else:
            labels.loc[index] = f"Period {value}"
    return labels


def _prepare_report_metric(
    view: _ResultView,
    *,
    metric: str | None,
) -> _ReportMetricData:
    """Prepare all selected rows without inheriting plot facet constraints."""
    measure = resolve_measure_spec(view, metric)
    summary = view.summary(copy=True)
    converted = pd.to_numeric(summary[measure.column], errors="coerce")
    finite = pd.Series(
        np.isfinite(converted.to_numpy(dtype=np.float64, na_value=np.nan)),
        index=summary.index,
    )
    certified = measure_certification_mask(summary, measure)
    valid = measure_validity_mask(summary, measure)
    substantive = finite & certified & valid
    uncertified = finite & ~certified
    invalid = finite & certified & ~valid
    diagnostic = uncertified | invalid
    if not substantive.any():
        raise PlotNotAvailableError(
            f"performance metric {measure.column!r} has no finite optimal "
            "observations that satisfy its validity contract"
        )

    classification = measure.classification_column
    substantive_columns = ["dmu_id", "period", "solver_status"]
    if classification is not None:
        substantive_columns.append(classification)
    prepared = summary.loc[substantive, substantive_columns].copy(deep=True)
    prepared[measure.column] = converted.loc[substantive].astype(float)
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
            and evidence_column in summary
            and evidence_column not in diagnostic_columns
        ):
            diagnostic_columns.append(evidence_column)
    diagnostics = summary.loc[diagnostic, diagnostic_columns].copy(deep=True)
    diagnostics[measure.column] = converted.loc[diagnostic].astype(float)
    diagnostics["_deapack_diagnostic_reason"] = pd.Series(
        "Non-optimal — excluded",
        index=diagnostics.index,
        dtype="string",
    )
    diagnostics.loc[
        invalid.loc[diagnostics.index],
        "_deapack_diagnostic_reason",
    ] = "Measure undefined — excluded"
    diagnostics["_deapack_input_order"] = range(len(diagnostics))

    return _ReportMetricData(
        measure=measure,
        frame=prepared,
        diagnostic_frame=diagnostics,
        omitted_metric_count=int((~finite).sum()),
        invalid_metric_count=int(invalid.sum()),
        nonoptimal_metric_count=int(uncertified.sum()),
    )


def _ordered_performance_rows(data: _ReportMetricData) -> pd.DataFrame:
    substantive = data.frame.copy(deep=True)
    if data.measure.preferred_direction != "signed":
        substantive = substantive.sort_values(
            [data.metric, "_deapack_input_order"],
            ascending=[
                data.measure.preferred_direction != "higher",
                True,
            ],
            kind="stable",
        )
    substantive.insert(1, "Report period", _period_labels(substantive["period"]))
    substantive["Report status"] = substantive["_deapack_measure_class"].replace(
        {
            "reported": "Valid reported result",
            "efficient": "Efficient",
            "inefficient": "Inefficient",
            "not_reported": "Efficiency status not reported",
        }
    )
    rows = [
        substantive[["dmu_id", "Report period", data.metric, "Report status"]].rename(
            columns={
                "dmu_id": "DMU",
                data.metric: data.measure.label,
            }
        )
    ]

    if not data.diagnostic_frame.empty:
        diagnostics = data.diagnostic_frame.copy(deep=True)
        diagnostics.insert(1, "Report period", _period_labels(diagnostics["period"]))
        display_columns = [
            "dmu_id",
            "Report period",
            data.metric,
            "_deapack_diagnostic_reason",
        ]
        rename = {
            "dmu_id": "DMU",
            data.metric: data.measure.label,
            "_deapack_diagnostic_reason": "Report status",
        }
        if (
            data.measure.validity_column is not None
            and data.measure.validity_column in diagnostics
        ):
            display_columns.append(data.measure.validity_column)
            rename[data.measure.validity_column] = "Validity evidence"
        if "score_status" in diagnostics and "score_status" not in display_columns:
            display_columns.append("score_status")
            rename["score_status"] = "Validity status"
        certification_column = data.measure.certification_status_column
        if (
            certification_column in diagnostics
            and certification_column not in display_columns
        ):
            display_columns.append(certification_column)
            rename[certification_column] = (
                "Certification status"
                if certification_column == "solver_status"
                else f"Certification status ({certification_column})"
            )
        rows.append(diagnostics[display_columns].rename(columns=rename))

    combined = pd.concat(rows, ignore_index=True)
    if len(combined) <= _MAX_PERFORMANCE_ROWS:
        return combined

    period_groups = [
        group.reset_index(drop=True)
        for _, group in combined.groupby("Report period", sort=False, dropna=False)
    ]
    selected_rows: list[pd.DataFrame] = []
    depth = 0
    while len(selected_rows) < _MAX_PERFORMANCE_ROWS:
        added = False
        for group in period_groups:
            if depth < len(group):
                selected_rows.append(group.iloc[[depth]])
                added = True
                if len(selected_rows) == _MAX_PERFORMANCE_ROWS:
                    break
        if not added:
            break
        depth += 1
    return pd.concat(selected_rows, ignore_index=True)


def _metric_section(
    prepared: _ReportMetricData,
) -> tuple[str, tuple[str, ...]]:
    measure = prepared.measure
    benchmark = ""
    if measure.benchmark_value is not None:
        label = measure.benchmark_label or "Benchmark"
        benchmark = f" {escape(label, quote=True)}: {measure.benchmark_value:g}."
    note = (
        '<div class="measure-note">'
        f"<strong>{escape(measure.label, quote=True)}</strong>. "
        f"{escape(measure.direction_label, quote=True)}.{benchmark}"
        " Substantive rows require "
        f"<code>{escape(measure.certification_status_column, quote=True)}</code>"
        " = <code>optimal</code>."
        "</div>"
    )
    performance = _ordered_performance_rows(prepared)
    displayed = len(performance)
    available = len(prepared.frame) + len(prepared.diagnostic_frame)
    truncation = ""
    warnings: list[str] = []
    if displayed < available:
        message = (
            f"Showing {_MAX_PERFORMANCE_ROWS} of {available} finite result rows; "
            "the report does not alter the fitted result."
        )
        truncation = f'<p class="footnote">{escape(message)}</p>'
        warnings.append(message)
    section = (
        "<h2>Declared performance measure</h2>"
        f"{note}"
        f"{_table_html(performance)}"
        f"{truncation}"
    )
    return section, tuple(warnings)


def _scope_warnings(
    metadata: Mapping[str, Any],
    prepared: _ReportMetricData | None,
) -> tuple[str, ...]:
    """Return method-specific limits on what the selected score establishes."""
    if prepared is None:
        return ()
    method_id = metadata.get("method_id")
    if (
        method_id == "network.sbm.tone_tsutsui_2009"
        and metadata.get("all_division_efficiency_identified_by_system_one") is False
    ):
        return (
            "One or more divisions have zero weight. A network-system "
            "performance value of 1 covers only positively weighted process "
            "accounts; it does not establish efficiency for every division.",
        )
    if (
        method_id == "dynamic.network_sbm.tone_tsutsui_2014"
        and metadata.get("all_account_efficiency_identified_by_system_one") is False
    ):
        return (
            "One or more period or process accounts have zero weight. A dynamic "
            "network-system performance value of 1 covers only positively "
            "weighted period-process accounts; it does not establish efficiency "
            "for every period and process.",
        )
    return ()


def _selection_label(
    selected: pd.DataFrame,
    *,
    period: object | None,
    dmu_id: object | None,
) -> str:
    if period is not None and dmu_id is not None:
        return f"{dmu_id!s}, period {period!s}"
    if dmu_id is not None:
        return str(dmu_id)
    if period is not None:
        return f"Period {period!s}"
    periods = selected["period"].drop_duplicates()
    if len(periods) == 1 and _is_missing_scalar(periods.iloc[0]):
        return "Cross-section"
    return "All selected observations"


def _focus_section(
    selected: pd.DataFrame,
    *,
    dmu_id: object | None,
    metric: str | None,
) -> str:
    if dmu_id is None:
        return ""
    columns = [
        "dmu_id",
        "period",
        "solver_status",
        "score",
        "efficiency",
        "distance",
        "is_efficient",
        "score_valid",
        "score_status",
    ]
    if metric is not None and metric not in columns:
        columns.append(metric)
    available = [column for column in columns if column in selected]
    focus = selected.loc[:, available].rename(
        columns={
            "dmu_id": "DMU",
            "period": "Period",
            "solver_status": "Solver status",
            "score": "Native score",
            "efficiency": "Display efficiency",
            "distance": "Distance / inefficiency",
            "is_efficient": "Pareto-Koopmans status",
            "score_valid": "Measure validity",
            "score_status": "Measure validity status",
        }
    )
    return "<h2>Selected organization</h2>" + _table_html(focus)


def create_result_report(
    result: Any,
    *,
    kind: str = "brief",
    metric: str | None = None,
    period: object | None = None,
    dmu_id: object | None = None,
    detail: str = "brief",
    theme: str = "deapack",
) -> ResultReport:
    """Create a safe, source-independent HTML brief from a public result."""
    if kind not in _VALID_KINDS:
        raise ReportNotAvailableError(
            f"unknown report kind {kind!r}; available kinds: {_VALID_KINDS}"
        )
    if detail not in _VALID_DETAILS:
        raise ReportNotAvailableError(
            f"unknown report detail {detail!r}; available details: {_VALID_DETAILS}"
        )
    if theme not in _VALID_THEMES:
        raise ReportNotAvailableError(
            f"unknown report theme {theme!r}; available themes: {_VALID_THEMES}"
        )
    if metric is not None and (not isinstance(metric, str) or not metric.strip()):
        raise ReportNotAvailableError(
            "metric must be a non-empty declared summary measure"
        )
    metric = None if metric is None else metric.strip()

    summary = _validate_summary_schema(result.summary(copy=True))
    if summary.empty:
        raise ReportNotAvailableError("the result contains no observations")
    selected = _filter_summary(summary, period=period, dmu_id=dmu_id)
    metadata = result.metadata if isinstance(result.metadata, Mapping) else {}
    view = _ResultView(selected, metadata)

    prepared: _ReportMetricData | None = None
    preparation_warning: str | None = None
    try:
        prepared = _prepare_report_metric(view, metric=metric)
    except PlotNotAvailableError as error:
        if metric is not None:
            raise ReportNotAvailableError(str(error)) from error
        preparation_warning = str(error)

    normalized_status = (
        selected["solver_status"].astype("string").str.strip().str.casefold()
    )
    optimal_count = int(normalized_status.eq("optimal").fillna(False).sum())
    observation_count = len(selected)
    nonoptimal_count = observation_count - optimal_count
    reported_metric = None if prepared is None else prepared.metric
    omitted_metric_count = 0 if prepared is None else prepared.omitted_metric_count
    invalid_metric_count = 0 if prepared is None else prepared.invalid_metric_count

    method_id = _mapping_value(metadata, "method_id", ())
    orientation = _mapping_value(
        metadata,
        "orientation",
        ("expanded_spec", "performance", "orientation"),
    )
    returns_to_scale = _mapping_value(
        metadata,
        "returns_to_scale",
        ("expanded_spec", "technology", "returns_to_scale"),
    )
    reference = _mapping_value(
        metadata,
        "reference_kind",
        ("expanded_spec", "reference", "kind"),
    )
    model_family = _single_value(selected["model_family"])
    selection = _selection_label(
        selected,
        period=period,
        dmu_id=dmu_id,
    )

    cards = "".join(
        (
            _card("Method", method_id),
            _card("Model family", model_family),
            _card("Selection", selection),
            _card("Observations", observation_count),
            _card("Result-status optimal", optimal_count),
            _card("Other result statuses", nonoptimal_count),
            _card("Orientation", orientation),
            _card("Returns to scale", returns_to_scale),
            _card("Reference", reference),
        )
    )

    warnings: list[str] = []
    if preparation_warning is not None:
        warnings.append(preparation_warning)
        performance_section = (
            "<h2>Performance measure</h2>"
            '<div class="notice">'
            "No declared valid finite optimal performance measure is available for "
            "this selection. The brief reports audit coverage without inventing "
            "a score, ordering, or classification."
            "</div>"
        )
    else:
        assert prepared is not None
        performance_section, metric_warnings = _metric_section(prepared)
        warnings.extend(metric_warnings)
    warnings.extend(_scope_warnings(metadata, prepared))

    if nonoptimal_count:
        warnings.append(
            f"{nonoptimal_count} selected observation(s) do not have summary "
            "solver_status='optimal'."
        )
    if omitted_metric_count:
        warnings.append(
            f"{omitted_metric_count} missing or non-finite metric value(s) "
            "are omitted from the performance section."
        )
    if invalid_metric_count:
        warnings.append(
            f"{invalid_metric_count} finite metric value(s) are undefined under "
            "the result's validity contract and are shown only as diagnostics."
        )
    warning_html = "".join(
        f'<div class="warning">{escape(message, quote=True)}</div>'
        for message in warnings
    )

    status_section = (
        "<h2>Solver coverage</h2>"
        f"{_table_html(_status_frame(selected))}"
        '<p class="footnote">Solver coverage is an audit summary. A non-optimal '
        "completion status can coexist with a separately certified primary "
        "measure; every reported ordering still requires that measure's own "
        "solver and validity evidence.</p>"
    )
    focus_section = _focus_section(
        selected,
        dmu_id=dmu_id,
        metric=reported_metric,
    )
    body = (
        "<h1>DEAPack result brief</h1>"
        '<p class="subtitle">Declared performance and solver evidence under '
        "the fitted study design.</p>"
        f'<div class="cards">{cards}</div>'
        f"{performance_section}"
        f"{status_section}"
        f"{focus_section}"
        f"{warning_html}"
        '<p class="footnote">This descriptive report does not establish causal '
        "responsibility, economic desirability, or a uniquely implementable "
        "operating plan. Inspect the full public result tables and fitted "
        "assumptions before making decisions.</p>"
    )
    return _prepared_result_report(
        kind="brief",
        title="DEAPack result brief",
        metric=reported_metric,
        observation_count=observation_count,
        optimal_count=optimal_count,
        nonoptimal_count=nonoptimal_count,
        omitted_metric_count=omitted_metric_count,
        invalid_metric_count=invalid_metric_count,
        warnings=tuple(warnings),
        body_html=body,
    )


__all__ = ["create_result_report"]
