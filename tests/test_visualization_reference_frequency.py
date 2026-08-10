from __future__ import annotations

import builtins
from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd
import pytest

from deapack import CCR, FDH, DEAData, DEAResult
from deapack.visualization import (
    PlotNotAvailableError,
    prepare_reference_frequency_data,
    reference_frequency_plot_applicable,
)
from deapack.visualization.reference_frequency import MAX_REFERENCE_BARS


def _data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C", "D"],
                "input": [1.0, 2.0, 1.5, 3.0],
                "output": [1.0, 1.0, 0.6, 1.2],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )


@pytest.fixture
def source_result() -> DEAResult:
    return CCR().fit(_data())


def _large_certified_result(
    count: int,
    *,
    identifiers: list[object] | None = None,
) -> DEAResult:
    source = CCR().fit(_data())
    ids = list(range(count)) if identifiers is None else identifiers
    assert len(ids) == count and count >= 2
    summary = pd.DataFrame(
        {
            "dmu_id": ids,
            "period": pd.Series([None] * count, dtype=object),
            "score": np.ones(count),
            "efficiency": np.ones(count),
            "distance": np.zeros(count),
            "is_efficient": np.ones(count, dtype=bool),
            "solver_status": np.repeat("optimal", count),
            "model_family": np.repeat("radial", count),
            "peer_valid": np.ones(count, dtype=bool),
            "peer_status": np.repeat("certified_primary_program", count),
        }
    )
    evaluated: list[object] = []
    references: list[object] = []
    for position, identifier in enumerate(ids):
        evaluated.extend((identifier, identifier))
        references.extend((identifier, ids[1] if position == 0 else ids[0]))
    intensities = pd.DataFrame(
        {
            "dmu_id": evaluated,
            "period": pd.Series([None] * (2 * count), dtype=object),
            "reference_dmu_id": references,
            "reference_period": pd.Series([None] * (2 * count), dtype=object),
            "lambda": np.full(2 * count, 0.5),
        }
    )
    return replace(source, summary_frame=summary, intensities=intensities)


def _certified_result_from_single_edges(
    identifiers: list[object],
    references: list[object],
) -> DEAResult:
    source = CCR().fit(_data())
    count = len(identifiers)
    assert count == len(references) and count >= 2
    summary = pd.DataFrame(
        {
            "dmu_id": identifiers,
            "period": pd.Series([None] * count, dtype=object),
            "score": np.ones(count),
            "efficiency": np.ones(count),
            "distance": np.zeros(count),
            "is_efficient": np.ones(count, dtype=bool),
            "solver_status": np.repeat("optimal", count),
            "model_family": np.repeat("radial", count),
            "peer_valid": np.ones(count, dtype=bool),
            "peer_status": np.repeat("certified_primary_program", count),
        }
    )
    intensities = pd.DataFrame(
        {
            "dmu_id": identifiers,
            "period": pd.Series([None] * count, dtype=object),
            "reference_dmu_id": references,
            "reference_period": pd.Series([None] * count, dtype=object),
            "lambda": np.ones(count),
        }
    )
    return replace(source, summary_frame=summary, intensities=intensities)


def _all_figure_text(figure: Any) -> str:
    return "\n".join(
        " ".join(artist.get_text().split())
        for artist in figure.findobj()
        if hasattr(artist, "get_text")
    )


def test_reference_frequency_discovery_is_backend_lazy_and_result_aware(
    source_result: DEAResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ordinary_import = builtins.__import__

    def guarded_import(
        name: str,
        globals: Any = None,
        locals: Any = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        if name == "matplotlib" or name.startswith("matplotlib."):
            raise AssertionError("plot discovery must not import Matplotlib")
        return ordinary_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    before_calls = source_result.metadata["solver_calls"]

    available = source_result.available_plots()

    references = next(item for item in available if item.kind == "references")
    assert references.title == "Selected-plan peer use"
    assert "solver-selected plan" in references.description
    assert "above the fitted threshold" in references.description
    assert source_result.metadata["solver_calls"] == before_calls
    assert not reference_frequency_plot_applicable(FDH().fit(_data()))


def test_preparer_consumes_public_analysis_and_reconstructs_every_count(
    source_result: DEAResult,
) -> None:
    analysis = source_result.reference_frequency()
    before_summary = source_result.summary()
    before_intensities = source_result.intensities.copy(deep=True)
    before_calls = source_result.metadata["solver_calls"]

    prepared = prepare_reference_frequency_data(source_result)

    expected = (
        analysis.reference_frame.loc[
            analysis.reference_frame["reference_frequency"].gt(0)
        ]
        .sort_values(
            ["other_reference_frequency", "reference_frequency"],
            ascending=False,
            kind="stable",
        )
        .reset_index(drop=True)
    )
    assert (
        prepared.references["reference_dmu_id"].tolist()
        == expected["reference_dmu_id"].tolist()
    )
    np.testing.assert_array_equal(
        prepared.references["reference_frequency"],
        prepared.references["self_reference_frequency"]
        + prepared.references["other_reference_frequency"],
    )
    assert prepared.active_edge_count == len(analysis.edge_frame)
    assert prepared.observation_count == len(before_summary)
    assert prepared.displayed_reference_count == 1
    assert prepared.selected_reference_count == 1
    assert prepared.omitted_selected_reference_count == 0
    assert prepared.zero_frequency_count == 3
    assert prepared.omitted_reference_count == 3
    assert prepared.source_peer_tolerance == pytest.approx(1.0e-7)
    assert prepared.source_method_id == source_result.metadata["method_id"]
    assert source_result.metadata["solver_calls"] == before_calls
    pd.testing.assert_frame_equal(source_result.summary(), before_summary)
    pd.testing.assert_frame_equal(source_result.intensities, before_intensities)

    prepared.references.loc[0, "reference_frequency"] = 999
    assert analysis.reference_frame["reference_frequency"].max() != 999


def test_large_roster_uses_stable_top_n_and_discloses_exact_omission() -> None:
    result = _large_certified_result(MAX_REFERENCE_BARS + 20)
    before_calls = result.metadata["solver_calls"]

    prepared = prepare_reference_frequency_data(result)

    assert prepared.displayed_reference_count == MAX_REFERENCE_BARS
    assert prepared.omitted_reference_count == 20
    assert prepared.omitted_selected_reference_count == 20
    assert prepared.zero_frequency_count == 0
    assert prepared.total_reference_count == MAX_REFERENCE_BARS + 20
    assert prepared.references.iloc[0]["reference_dmu_id"] == 0
    assert prepared.references.iloc[0]["other_reference_frequency"] == 49
    assert prepared.references.iloc[1]["reference_dmu_id"] == 1
    assert prepared.active_edge_count == 2 * (MAX_REFERENCE_BARS + 20)
    assert result.metadata["solver_calls"] == before_calls


def test_ranking_prioritizes_use_by_other_organizations() -> None:
    result = _certified_result_from_single_edges(
        ["self-only", "transfer-a", "transfer-b"],
        ["self-only", "transfer-b", "transfer-a"],
    )

    prepared = prepare_reference_frequency_data(result)

    assert prepared.references["reference_dmu_id"].tolist() == [
        "transfer-a",
        "transfer-b",
        "self-only",
    ]
    assert prepared.references["other_reference_frequency"].tolist() == [1, 1, 0]


def test_display_labels_are_bounded_control_free_and_unambiguous() -> None:
    stem = "Hospital-with-a-very-long-public-reporting-identifier-"
    result = _large_certified_result(
        4,
        identifiers=[f"{stem}A\nprivate", f"{stem}B\tprivate", 1, "1"],
    )

    labels = (
        prepare_reference_frequency_data(result).references["display_label"].tolist()
    )

    assert len(labels) == len(set(labels))
    assert all(len(label) <= 48 for label in labels)
    assert all("\n" not in label and "\t" not in label for label in labels)
    assert any(label.endswith("[2]") for label in labels)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"metric": "reference_frequency"},
        {"period": 2024},
        {"dmu_id": "A"},
        {"variable": "input"},
        {"view": "points"},
    ],
)
def test_references_plot_rejects_selectors_that_change_the_common_account(
    source_result: DEAResult,
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(PlotNotAvailableError):
        source_result.plot(kind="references", **kwargs)  # type: ignore[arg-type]


def test_forged_analysis_result_fails_closed(
    source_result: DEAResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = source_result.reference_frequency()
    forged = analysis.reference_frame.copy(deep=True)
    forged.loc[0, "other_reference_frequency"] += 1
    forged_result = replace(analysis, reference_frame=forged)
    monkeypatch.setattr(
        DEAResult,
        "reference_frequency",
        lambda self: forged_result,
    )

    assert not reference_frequency_plot_applicable(source_result)
    with pytest.raises(PlotNotAvailableError, match="do not reconstruct"):
        prepare_reference_frequency_data(source_result)


def test_reporting_threshold_and_source_provenance_fail_closed(
    source_result: DEAResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = source_result.reference_frequency()
    threshold_edges = analysis.edge_frame.copy(deep=True)
    threshold_edges.loc[0, "lambda"] = analysis.metadata["source_peer_tolerance"]
    at_threshold = replace(analysis, edge_frame=threshold_edges)
    monkeypatch.setattr(
        DEAResult,
        "reference_frequency",
        lambda self: at_threshold,
    )
    with pytest.raises(PlotNotAvailableError, match="strictly above"):
        prepare_reference_frequency_data(source_result)

    forged_metadata = {
        **dict(analysis.metadata),
        "source_expanded_spec": {"forged": True},
    }
    wrong_source = replace(analysis, metadata=forged_metadata)
    monkeypatch.setattr(
        DEAResult,
        "reference_frequency",
        lambda self: wrong_source,
    )
    with pytest.raises(PlotNotAvailableError, match="provenance"):
        prepare_reference_frequency_data(source_result)

    boolean_solve_ledger = replace(
        analysis,
        metadata={**dict(analysis.metadata), "additional_solver_calls": False},
    )
    monkeypatch.setattr(
        DEAResult,
        "reference_frequency",
        lambda self: boolean_solve_ledger,
    )
    with pytest.raises(PlotNotAvailableError, match="zero additional solves"):
        prepare_reference_frequency_data(source_result)


def test_renderer_separates_self_and_other_and_states_claim_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MPL_IGNORE_SYSTEM_FONTS", "1")
    matplotlib = pytest.importorskip("matplotlib")
    pyplot = pytest.importorskip("matplotlib.pyplot")

    result = _large_certified_result(MAX_REFERENCE_BARS + 2)
    before = {
        key: matplotlib.rcParams[key]
        for key in ("axes.edgecolor", "font.size", "grid.color")
    }

    def forbidden_show(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise AssertionError("plot() must not call pyplot.show()")

    monkeypatch.setattr(pyplot, "show", forbidden_show)
    figure = result.plot(kind="references")
    text = _all_figure_text(figure)

    assert len(figure.axes[0].containers) == 2
    assert "Selected by other organizations" in text
    assert "Self-reference" in text
    assert "one certified solver-selected plan" in text
    assert "strictly above the fitted source threshold" in text
    assert "does not identify exact mathematical support" in text
    assert "does not enumerate alternate optima" in text
    assert "identify a global reference set" in text
    assert "diagnose outliers" in text
    assert "statistical inference" in text
    assert "2 selected references omitted by the explicit top-30" in text
    assert "zero additional solver calls" in text
    assert {
        key: matplotlib.rcParams[key]
        for key in ("axes.edgecolor", "font.size", "grid.color")
    } == before
    pyplot.close(figure)
