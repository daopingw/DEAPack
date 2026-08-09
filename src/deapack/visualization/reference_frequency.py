"""Prepared data for certified selected-plan reference-frequency plots.

The plot consumes :meth:`DEAResult.reference_frequency` rather than counting
intensity rows itself.  It therefore inherits the analysis contract that every
evaluated organization contributes one complete, certified solver-selected
peer plan and that peer use means a reported intensity strictly above the
source threshold.  The display does not enumerate alternate optima, identify
exact mathematical support or a global reference set, diagnose outliers, or
provide statistical inference.
"""

from __future__ import annotations

import math
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype
from pandas.errors import InvalidIndexError

from ..exceptions import ModelSpecificationError
from ._types import PlotNotAvailableError

_METHOD_ID = "analysis.reference_frequency.selected_plan"
_SELECTED_PLAN_STATUS = "certified_solver_selected_peer_account"

MAX_REFERENCE_BARS = 30
_DISPLAY_LABEL_LIMIT = 48

_REFERENCE_COLUMNS = frozenset(
    {
        "reference_dmu_id",
        "reference_period",
        "reference_frequency",
        "self_reference_frequency",
        "other_reference_frequency",
        "reference_rate",
        "is_referenced",
    }
)
_EDGE_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "reference_dmu_id",
        "reference_period",
        "lambda",
        "is_self_reference",
    }
)
_DIAGNOSTIC_COLUMNS = frozenset(
    {
        "dmu_id",
        "period",
        "active_peer_count",
        "self_peer_count",
        "other_peer_count",
        "selected_plan_valid",
        "selected_plan_status",
        "source_peer_status",
    }
)


@dataclass(frozen=True, slots=True)
class ReferenceFrequencyPlotData:
    """Detached top-reference display for one certified selected peer plan."""

    references: pd.DataFrame
    observation_count: int
    active_edge_count: int
    selected_reference_count: int
    displayed_reference_count: int
    omitted_reference_count: int
    omitted_selected_reference_count: int
    zero_frequency_count: int
    source_method_id: str
    source_peer_tolerance: float
    display_limit: int
    provenance: tuple[tuple[str, str], ...]

    @property
    def total_reference_count(self) -> int:
        """Number of potential references in the complete fitted sample."""

        return self.displayed_reference_count + self.omitted_reference_count


def _missing_scalar(value: object) -> bool:
    marker = pd.isna(value)
    if isinstance(marker, (bool, np.bool_)):
        return bool(marker)
    raise PlotNotAvailableError("reference-frequency identifiers must be scalar")


def _display(value: object) -> str | None:
    if value is None or _missing_scalar(value):
        return None
    enum_value = getattr(value, "value", value)
    rendered = str(enum_value).strip()
    return rendered or None


def _require_columns(
    frame: pd.DataFrame,
    required: frozenset[str],
    *,
    table: str,
) -> None:
    if frame.columns.has_duplicates:
        raise PlotNotAvailableError(
            f"reference-frequency {table} has duplicate column names"
        )
    missing = required.difference(frame.columns)
    if missing:
        raise PlotNotAvailableError(
            f"reference-frequency {table} is missing columns: "
            f"{', '.join(sorted(missing))}"
        )


def _integer_counts(series: pd.Series, *, field: str) -> np.ndarray:
    if is_bool_dtype(series.dtype) or not is_numeric_dtype(series.dtype):
        raise PlotNotAvailableError(
            f"reference-frequency {field} must contain integer counts"
        )
    values = series.to_numpy(dtype=np.float64, copy=True)
    if (
        not np.isfinite(values).all()
        or np.any(values < 0.0)
        or not np.equal(values, np.floor(values)).all()
    ):
        raise PlotNotAvailableError(
            f"reference-frequency {field} must contain finite non-negative "
            "integer counts"
        )
    return values.astype(np.int64, copy=False)


def _integer_metadata(metadata: Mapping[str, Any], field: str) -> int:
    value = metadata.get(field)
    if (
        isinstance(value, (bool, np.bool_))
        or not isinstance(value, Integral)
        or int(value) < 0
    ):
        raise PlotNotAvailableError(
            f"reference-frequency metadata {field} must be a non-negative integer"
        )
    return int(value)


def _false_claim(metadata: Mapping[str, Any], field: str) -> bool:
    value = metadata.get(field)
    return isinstance(value, (bool, np.bool_)) and not bool(value)


def _reporting_threshold(metadata: Mapping[str, Any]) -> float:
    value = metadata.get("source_peer_tolerance")
    if (
        isinstance(value, (bool, np.bool_))
        or not isinstance(value, Real)
        or not math.isfinite(float(value))
        or float(value) < 0.0
    ):
        raise PlotNotAvailableError(
            "reference-frequency source_peer_tolerance must be finite and non-negative"
        )
    return float(value)


def _validate_metadata(
    metadata: object,
) -> tuple[Mapping[str, Any], str, float]:
    if not isinstance(metadata, Mapping):
        raise PlotNotAvailableError(
            "reference-frequency plotting requires immutable analysis metadata"
        )
    source_method_id = _display(metadata.get("source_method_id"))
    additional_solver_calls = metadata.get("additional_solver_calls")
    if (
        _display(metadata.get("method_id")) != _METHOD_ID
        or source_method_id is None
        or not source_method_id.startswith("static.")
        or _display(metadata.get("frequency_unit"))
        != "reported_active_solver_selected_peer_edge"
        or _display(metadata.get("reference_rate_denominator"))
        != "all_evaluated_organizations"
        or _display(metadata.get("intensity_aggregation_across_evaluations"))
        != "not_computed"
        or not _false_claim(metadata, "alternate_optima_assessed")
        or not _false_claim(metadata, "global_reference_set_claim")
        or not _false_claim(metadata, "outlier_claim")
        or _display(metadata.get("inference")) != "none"
        or isinstance(additional_solver_calls, (bool, np.bool_))
        or not isinstance(additional_solver_calls, Integral)
        or int(additional_solver_calls) != 0
    ):
        raise PlotNotAvailableError(
            "reference-frequency plotting requires the certified selected-plan "
            "analysis boundary with zero additional solves"
        )

    source_peer_tolerance = _reporting_threshold(metadata)
    expanded = metadata.get("expanded_spec")
    if not isinstance(expanded, Mapping):
        raise PlotNotAvailableError(
            "reference-frequency plotting requires expanded analysis semantics"
        )
    reference = expanded.get("reference")
    protocol = expanded.get("evaluation_protocol")
    analysis = expanded.get("analysis")
    performance = expanded.get("performance")
    uncertainty = expanded.get("uncertainty")
    if (
        not isinstance(reference, Mapping)
        or reference.get("kind") != "global"
        or reference.get("account")
        != (
            "reported_solver_selected_active_peer_edges_strictly_above_"
            "source_peer_tolerance"
        )
        or reference.get("peer_reporting_threshold") != source_peer_tolerance
        or not isinstance(protocol, Mapping)
        or protocol.get("kind") != "selected_peer_plan_accounting"
        or protocol.get("alternate_optima_assessed") is not False
        or not isinstance(analysis, Mapping)
        or analysis.get("kind") != "reference_frequency"
        or analysis.get("claim") != "one_certified_solver_selected_plan"
        or not isinstance(performance, Mapping)
        or performance.get("unit") != "reported_active_peer_edge_count"
        or not isinstance(uncertainty, Mapping)
        or uncertainty.get("kind") != "deterministic"
        or uncertainty.get("inference") != "none"
    ):
        raise PlotNotAvailableError(
            "reference-frequency expanded semantics do not preserve the "
            "selected-plan claim boundary"
        )
    return metadata, source_method_id, source_peer_tolerance


def _validate_reference_account(
    analysis_result: object,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    Mapping[str, Any],
    str,
    float,
]:
    try:
        references = analysis_result.summary(copy=True)
        edges = analysis_result.edges(copy=True)
        diagnostics = analysis_result.diagnostics.copy(deep=True)
        raw_metadata = analysis_result.metadata
    except (AttributeError, TypeError) as error:
        raise PlotNotAvailableError(
            "reference-frequency plotting requires the public "
            "ReferenceFrequencyResult contract"
        ) from error
    if not all(
        isinstance(frame, pd.DataFrame) for frame in (references, edges, diagnostics)
    ):
        raise PlotNotAvailableError(
            "reference-frequency plotting requires tabular public accounts"
        )
    _require_columns(references, _REFERENCE_COLUMNS, table="summary")
    _require_columns(edges, _EDGE_COLUMNS, table="edge account")
    _require_columns(diagnostics, _DIAGNOSTIC_COLUMNS, table="diagnostic")
    metadata, source_method_id, source_peer_tolerance = _validate_metadata(raw_metadata)

    if references.empty or edges.empty or diagnostics.empty:
        raise PlotNotAvailableError(
            "reference-frequency plotting requires complete non-empty accounts"
        )
    if (
        references["reference_dmu_id"].isna().any()
        or not references["reference_period"].isna().all()
        or edges["dmu_id"].isna().any()
        or edges["reference_dmu_id"].isna().any()
        or not edges["period"].isna().all()
        or not edges["reference_period"].isna().all()
        or diagnostics["dmu_id"].isna().any()
        or not diagnostics["period"].isna().all()
    ):
        raise PlotNotAvailableError(
            "reference-frequency plotting requires complete cross-section labels"
        )
    try:
        duplicate_references = references["reference_dmu_id"].duplicated().any()
        duplicate_diagnostics = diagnostics["dmu_id"].duplicated().any()
    except TypeError as error:
        raise PlotNotAvailableError(
            "reference-frequency labels must be hashable"
        ) from error
    if duplicate_references or duplicate_diagnostics:
        raise PlotNotAvailableError(
            "reference-frequency plotting requires one row per organization"
        )

    roster = pd.Index(references["reference_dmu_id"], dtype=object)
    try:
        evaluation_codes = roster.get_indexer(edges["dmu_id"])
        reference_codes = roster.get_indexer(edges["reference_dmu_id"])
        diagnostic_codes = roster.get_indexer(diagnostics["dmu_id"])
    except (InvalidIndexError, TypeError) as error:
        raise PlotNotAvailableError(
            "reference-frequency labels must be hashable and unambiguous"
        ) from error
    if (
        np.any(evaluation_codes < 0)
        or np.any(reference_codes < 0)
        or np.any(diagnostic_codes < 0)
        or len(np.unique(diagnostic_codes)) != len(roster)
    ):
        raise PlotNotAvailableError(
            "reference-frequency edge and diagnostic rosters must match the sample"
        )

    encoded_edges = pd.MultiIndex.from_arrays([evaluation_codes, reference_codes])
    if encoded_edges.has_duplicates:
        raise PlotNotAvailableError(
            "reference-frequency plotting rejects duplicate selected peer edges"
        )
    lambdas = edges["lambda"]
    if is_bool_dtype(lambdas.dtype) or not is_numeric_dtype(lambdas.dtype):
        raise PlotNotAvailableError(
            "reference-frequency selected intensities must be numeric"
        )
    lambda_values = lambdas.to_numpy(dtype=np.float64, copy=True)
    if not np.isfinite(lambda_values).all() or np.any(
        lambda_values <= source_peer_tolerance
    ):
        raise PlotNotAvailableError(
            "reference-frequency reported intensities must be finite and "
            "strictly above the source peer-reporting threshold"
        )
    try:
        self_flags = edges["is_self_reference"].astype("boolean")
    except (TypeError, ValueError) as error:
        raise PlotNotAvailableError(
            "reference-frequency self-edge flags must be boolean"
        ) from error
    expected_self = evaluation_codes == reference_codes
    if self_flags.isna().any() or not np.array_equal(
        self_flags.to_numpy(dtype=bool),
        expected_self,
    ):
        raise PlotNotAvailableError(
            "reference-frequency self-edge flags do not match the selected plan"
        )

    n_observations = len(roster)
    reconstructed_total = np.bincount(
        reference_codes,
        minlength=n_observations,
    ).astype(np.int64, copy=False)
    reconstructed_self = np.bincount(
        reference_codes[expected_self],
        minlength=n_observations,
    ).astype(np.int64, copy=False)
    reconstructed_other = reconstructed_total - reconstructed_self
    total = _integer_counts(
        references["reference_frequency"],
        field="reference_frequency",
    )
    self_count = _integer_counts(
        references["self_reference_frequency"],
        field="self_reference_frequency",
    )
    other_count = _integer_counts(
        references["other_reference_frequency"],
        field="other_reference_frequency",
    )
    if (
        not np.array_equal(total, self_count + other_count)
        or not np.array_equal(total, reconstructed_total)
        or not np.array_equal(self_count, reconstructed_self)
        or not np.array_equal(other_count, reconstructed_other)
    ):
        raise PlotNotAvailableError(
            "reference-frequency counts do not reconstruct from selected peer edges"
        )
    rates = pd.to_numeric(
        references["reference_rate"],
        errors="coerce",
    ).to_numpy(dtype=np.float64, copy=True)
    expected_rates = total.astype(np.float64) / float(n_observations)
    if not np.isfinite(rates).all() or not np.allclose(
        rates,
        expected_rates,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise PlotNotAvailableError(
            "reference-frequency rates do not use the complete sample denominator"
        )
    try:
        referenced = references["is_referenced"].astype("boolean")
    except (TypeError, ValueError) as error:
        raise PlotNotAvailableError(
            "reference-frequency selection flags must be boolean"
        ) from error
    if referenced.isna().any() or not np.array_equal(
        referenced.to_numpy(dtype=bool),
        total > 0,
    ):
        raise PlotNotAvailableError(
            "reference-frequency selection flags do not match the edge counts"
        )

    active_by_evaluation = np.bincount(
        evaluation_codes,
        minlength=n_observations,
    ).astype(np.int64, copy=False)
    self_by_evaluation = np.bincount(
        evaluation_codes[expected_self],
        minlength=n_observations,
    ).astype(np.int64, copy=False)
    active_diagnostic = _integer_counts(
        diagnostics["active_peer_count"],
        field="diagnostic active_peer_count",
    )
    self_diagnostic = _integer_counts(
        diagnostics["self_peer_count"],
        field="diagnostic self_peer_count",
    )
    other_diagnostic = _integer_counts(
        diagnostics["other_peer_count"],
        field="diagnostic other_peer_count",
    )
    ordered_active = np.empty(n_observations, dtype=np.int64)
    ordered_self = np.empty(n_observations, dtype=np.int64)
    ordered_other = np.empty(n_observations, dtype=np.int64)
    ordered_active[diagnostic_codes] = active_diagnostic
    ordered_self[diagnostic_codes] = self_diagnostic
    ordered_other[diagnostic_codes] = other_diagnostic
    if (
        np.any(active_by_evaluation == 0)
        or not np.array_equal(ordered_active, active_by_evaluation)
        or not np.array_equal(ordered_self, self_by_evaluation)
        or not np.array_equal(
            ordered_other,
            active_by_evaluation - self_by_evaluation,
        )
    ):
        raise PlotNotAvailableError(
            "reference-frequency diagnostics do not reconstruct evaluation accounts"
        )
    valid = diagnostics["selected_plan_valid"]
    if not all(
        isinstance(value, (bool, np.bool_)) and bool(value) for value in valid.tolist()
    ):
        raise PlotNotAvailableError(
            "reference-frequency diagnostics require selected_plan_valid=True"
        )
    if not all(
        value == _SELECTED_PLAN_STATUS
        for value in diagnostics["selected_plan_status"].tolist()
    ) or not all(
        isinstance(value, str) and value.startswith("certified")
        for value in diagnostics["source_peer_status"].tolist()
    ):
        raise PlotNotAvailableError(
            "reference-frequency diagnostics require certified selected-plan status"
        )

    expected_metadata = {
        "observation_count": n_observations,
        "active_edge_count": len(edges),
        "selected_reference_count": int(np.count_nonzero(total)),
        "unselected_reference_count": int(np.count_nonzero(total == 0)),
        "self_edge_count": int(expected_self.sum()),
        "other_edge_count": int((~expected_self).sum()),
    }
    for field, expected in expected_metadata.items():
        if _integer_metadata(metadata, field) != expected:
            raise PlotNotAvailableError(
                f"reference-frequency metadata {field} does not reconstruct"
            )
    return (
        references,
        edges,
        diagnostics,
        metadata,
        source_method_id,
        source_peer_tolerance,
    )


def _safe_labels(values: pd.Series) -> list[str]:
    labels: list[str] = []
    occurrences: dict[str, int] = {}
    for value in values.tolist():
        text = str(value)
        text = "".join(
            " " if unicodedata.category(character).startswith("C") else character
            for character in text
        )
        text = " ".join(text.split()).strip() or "DMU not reported"
        if len(text) > _DISPLAY_LABEL_LIMIT:
            text = f"{text[: _DISPLAY_LABEL_LIMIT - 1]}…"
        count = occurrences.get(text, 0) + 1
        occurrences[text] = count
        if count > 1:
            suffix = f" [{count}]"
            text = f"{text[: _DISPLAY_LABEL_LIMIT - len(suffix)]}{suffix}"
        labels.append(text)
    return labels


def prepare_reference_frequency_data(result: Any) -> ReferenceFrequencyPlotData:
    """Prepare the top peer-use account from ``result.reference_frequency()``.

    At most :data:`MAX_REFERENCE_BARS` selected references are displayed. Zero
    rows are not drawn. Ranking uses reported use by other organizations,
    total reported use, and stable fitted input order. Exact selected and zero
    omission counts remain in the returned payload and figure note, so the
    readability rule never becomes silent data deletion.
    """

    analysis = getattr(result, "reference_frequency", None)
    if not callable(analysis):
        raise PlotNotAvailableError(
            "reference-frequency plotting requires DEAResult.reference_frequency()"
        )
    source_metadata = getattr(result, "metadata", None)
    source_solver_calls = (
        source_metadata.get("solver_calls")
        if isinstance(source_metadata, Mapping)
        else None
    )
    try:
        analysis_result = analysis()
    except (ModelSpecificationError, TypeError, ValueError) as error:
        raise PlotNotAvailableError(str(error)) from error
    after_metadata = getattr(result, "metadata", None)
    after_solver_calls = (
        after_metadata.get("solver_calls")
        if isinstance(after_metadata, Mapping)
        else None
    )
    if after_solver_calls != source_solver_calls:
        raise PlotNotAvailableError(
            "reference-frequency preparation changed the fitted solver-call account"
        )
    (
        references,
        edges,
        _diagnostics,
        metadata,
        source_method_id,
        source_peer_tolerance,
    ) = _validate_reference_account(analysis_result)
    if (
        not isinstance(source_metadata, Mapping)
        or _display(source_metadata.get("method_id")) != source_method_id
        or metadata.get("source_expanded_spec") != source_metadata.get("expanded_spec")
        or source_peer_tolerance != source_metadata.get("peer_tolerance")
    ):
        raise PlotNotAvailableError(
            "reference-frequency provenance does not match the fitted result"
        )

    ranked = references.copy(deep=True)
    ranked["_deapack_input_order"] = np.arange(len(ranked), dtype=np.int64)
    ranked = ranked.loc[ranked["reference_frequency"].gt(0)].copy(deep=True)
    ranked = ranked.sort_values(
        [
            "other_reference_frequency",
            "reference_frequency",
            "_deapack_input_order",
        ],
        ascending=[False, False, True],
        kind="stable",
    )
    displayed = ranked.head(MAX_REFERENCE_BARS).copy(deep=True)
    displayed["display_label"] = _safe_labels(displayed["reference_dmu_id"])
    displayed = displayed[
        [
            "reference_dmu_id",
            "display_label",
            "reference_frequency",
            "self_reference_frequency",
            "other_reference_frequency",
            "reference_rate",
            "is_referenced",
            "_deapack_input_order",
        ]
    ].reset_index(drop=True)
    selected_reference_count = _integer_metadata(
        metadata,
        "selected_reference_count",
    )
    zero_frequency_count = _integer_metadata(
        metadata,
        "unselected_reference_count",
    )
    omitted_selected = selected_reference_count - len(displayed)
    omitted = omitted_selected + zero_frequency_count
    return ReferenceFrequencyPlotData(
        references=displayed,
        observation_count=_integer_metadata(metadata, "observation_count"),
        active_edge_count=len(edges),
        selected_reference_count=selected_reference_count,
        displayed_reference_count=len(displayed),
        omitted_reference_count=omitted,
        omitted_selected_reference_count=omitted_selected,
        zero_frequency_count=zero_frequency_count,
        source_method_id=source_method_id,
        source_peer_tolerance=source_peer_tolerance,
        display_limit=MAX_REFERENCE_BARS,
        provenance=(
            ("Analysis", _METHOD_ID),
            ("Source method", source_method_id),
            (
                "Frequency unit",
                "reported selected-plan peer edge above threshold",
            ),
            ("Peer reporting threshold", f"> {source_peer_tolerance:g}"),
        ),
    )


def reference_frequency_plot_applicable(result: Any) -> bool:
    """Whether one certified selected-plan frequency account is plottable."""

    try:
        prepare_reference_frequency_data(result)
    except (PlotNotAvailableError, AttributeError, KeyError, TypeError, ValueError):
        return False
    return True


__all__ = [
    "MAX_REFERENCE_BARS",
    "ReferenceFrequencyPlotData",
    "prepare_reference_frequency_data",
    "reference_frequency_plot_applicable",
]
