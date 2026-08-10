from __future__ import annotations

import builtins
import importlib.util
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from deapack import (
    DDF,
    RDM,
    SBM,
    AdditiveDEA,
    ChungFareGrosskopfDDF,
    DEAData,
    DEAResult,
    EnvironmentalDDF,
    InputSBM,
    LuenbergerDEA,
    MalmquistDEA,
    MetafrontierDEA,
    OutputSBM,
    PriceData,
    RadialDEA,
    ReferenceSpec,
    ToneSuperSBM,
    dataset_info,
    load_dataset,
    scale_efficiency,
)
from deapack.economics.profit import ProfitEfficiency
from deapack.evaluation.super_efficiency import APSuperEfficiency
from deapack.visualization import (
    PlotNotAvailableError,
    frontier_plot_applicable,
    prepare_frontier_data,
)
from deapack.visualization.performance import (
    POINT_VIEW_MAX_OBSERVATIONS,
    prepare_performance_data,
)


def _load_matplotlib_for_test(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[object, object]:
    monkeypatch.setenv("MPL_IGNORE_SYSTEM_FONTS", "1")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    pyplot = pytest.importorskip("matplotlib.pyplot")
    return matplotlib, pyplot


def _result(
    efficiencies: list[object],
    *,
    periods: list[object] | None = None,
    statuses: list[object] | None = None,
    efficient: list[object] | None = None,
    metadata_extra: dict[str, object] | None = None,
) -> DEAResult:
    count = len(efficiencies)
    summary = pd.DataFrame(
        {
            "dmu_id": [f"DMU-{index + 1}" for index in range(count)],
            "period": periods if periods is not None else [None] * count,
            "score": [10.0 + index for index in range(count)],
            "efficiency": efficiencies,
            "distance": [pd.NA] * count,
            "is_efficient": (efficient if efficient is not None else [False] * count),
            "solver_status": statuses if statuses is not None else ["optimal"] * count,
            "model_family": ["radial"] * count,
        }
    )
    return DEAResult(
        summary_frame=summary,
        metadata={
            "method_id": "static.radial",
            "expanded_spec": {
                "performance": {"orientation": "input"},
                "technology": {"returns_to_scale": "vrs"},
                "reference": {"kind": "contemporaneous"},
            },
            **({} if metadata_extra is None else metadata_extra),
        },
    )


def _productivity_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B"],
                "period": [0, 0, 1, 1],
                "x": [1.0, 2.0, 1.0, 2.0],
                "y": [1.0, 2.0, 2.0, 4.0],
            }
        ),
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )


def _frontier_result(
    *,
    orientation: str = "input",
    returns_to_scale: str = "vrs",
    compute_slacks: bool = True,
) -> DEAResult:
    frame = load_dataset("frontier_1x1")
    roles = dataset_info("frontier_1x1").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    return RadialDEA(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        compute_slacks=compute_slacks,
    ).fit(data)


def test_base_import_does_not_import_matplotlib() -> None:
    command = (
        "import sys; import deapack; "
        "assert not any(name == 'matplotlib' or "
        "name.startswith('matplotlib.') for name in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", command], check=True)


def test_available_plots_is_backend_independent_and_immutable() -> None:
    result = _result([0.8, 1.0])
    plots = result.available_plots()

    assert isinstance(plots, tuple)
    assert len(plots) == 1
    assert plots[0].kind == "performance"
    assert plots[0].default_metric == "efficiency"
    assert plots[0].measures[0].column == "efficiency"
    assert plots[0].measures[0].preferred_direction == "higher"
    assert plots[0].measures[0].benchmark_value == 1.0
    assert plots[0].install_hint == "pip install 'DEAPack[viz]'"
    with pytest.raises(TypeError):
        plots[0] = plots[0]  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        plots[0].kind = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        plots[0].measures[0].label = "Other"  # type: ignore[misc]


def test_scalar_radial_result_discovers_frontier_and_improvement_without_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ordinary_import = builtins.__import__

    def _reject_matplotlib_import(
        name: str,
        globals: Any = None,
        locals: Any = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        if name == "matplotlib" or name.startswith("matplotlib."):
            raise AssertionError("plot discovery must not import Matplotlib")
        return ordinary_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _reject_matplotlib_import)
    result = _frontier_result()
    plots = result.available_plots()

    assert [plot.kind for plot in plots] == [
        "performance",
        "frontier",
        "improvement",
        "references",
    ]
    frontier = plots[1]
    assert frontier.title == "Production frontier and targets"
    assert frontier.default_metric is None
    assert frontier.views == ("auto",)
    assert frontier.measures == ()


def test_frontier_preparation_retains_observations_targets_and_vrs_anchors() -> None:
    result = _frontier_result()
    before_summary = result.summary()
    before_targets = result.targets.copy(deep=True)
    before_intensities = result.intensities.copy(deep=True)

    prepared = prepare_frontier_data(result)

    assert prepared.period_label == "Cross-section"
    assert prepared.input_name == "input"
    assert prepared.output_name == "output"
    assert prepared.orientation == "input"
    assert prepared.returns_to_scale == "vrs"
    assert prepared.observation_count == 8
    assert prepared.target_change_count == 4
    assert prepared.omitted_observation_count == 0
    assert prepared.observations.loc[
        prepared.observations["target_changed"], "dmu_id"
    ].tolist() == list("EFGH")
    assert prepared.frontier["dmu_id"].tolist() == list("ABCD")
    assert prepared.frontier["input"].tolist() == [1.0, 2.0, 3.0, 4.0]
    assert_frame_equal(result.summary(), before_summary)
    assert_frame_equal(result.targets, before_targets)
    assert_frame_equal(result.intensities, before_intensities)


def test_crs_frontier_preparation_identifies_the_frontier_ray() -> None:
    prepared = prepare_frontier_data(
        _frontier_result(
            orientation="output",
            returns_to_scale="crs",
        )
    )

    assert prepared.orientation == "output"
    assert prepared.returns_to_scale == "crs"
    assert prepared.frontier.iloc[0][["input", "output"]].tolist() == [0.0, 0.0]
    end = prepared.frontier.iloc[-1]
    assert end["output"] / end["input"] == pytest.approx(1.25)


def test_frontier_plot_fails_closed_outside_its_result_contract() -> None:
    score_only = _frontier_result(compute_slacks=False)
    assert [plot.kind for plot in score_only.available_plots()] == [
        "performance",
        "references",
    ]
    with pytest.raises(PlotNotAvailableError, match="compute_slacks=True"):
        prepare_frontier_data(score_only)

    multidimensional = AdditiveDEA().fit(
        DEAData.from_frame(
            pd.DataFrame(
                {
                    "dmu": ["A", "B", "C"],
                    "x1": [1.0, 2.0, 2.0],
                    "x2": [2.0, 1.0, 2.0],
                    "y": [1.0, 1.0, 0.8],
                }
            ),
            dmu="dmu",
            inputs=("x1", "x2"),
            outputs="y",
        )
    )
    with pytest.raises(PlotNotAvailableError, match=r"'static\.radial'"):
        prepare_frontier_data(multidimensional)

    result = _frontier_result()
    with pytest.raises(PlotNotAvailableError, match="metric must remain omitted"):
        result.plot(kind="frontier", metric="efficiency")
    with pytest.raises(PlotNotAvailableError, match="view='auto'"):
        result.plot(kind="frontier", view="points")


@pytest.mark.parametrize(
    "validity_column",
    ["completion_valid", "target_valid", "peer_valid"],
)
def test_frontier_rejects_stale_accounts_without_layer_certificate(
    validity_column: str,
) -> None:
    result = _frontier_result()
    assert not result.targets.empty
    assert not result.intensities.empty
    result.summary_frame[validity_column] = False

    assert not frontier_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match=f"{validity_column}=True"):
        prepare_frontier_data(result)


def test_frontier_period_selection_rejects_cross_period_peers() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B"],
                "period": [2020, 2020, 2021, 2021],
                "resource": [1.0, 2.0, 1.0, 2.0],
                "service": [1.0, 1.5, 2.0, 3.0],
            }
        ),
        dmu="dmu",
        period="period",
        inputs="resource",
        outputs="service",
    )
    contemporaneous = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        reference="contemporaneous",
    ).fit(data)
    with pytest.raises(PlotNotAvailableError, match="select period"):
        prepare_frontier_data(contemporaneous)
    selected = prepare_frontier_data(contemporaneous, period=2020)
    assert selected.period == 2020
    assert selected.period_label == "Period 2020"
    assert selected.observations["dmu_id"].tolist() == ["A", "B"]

    global_result = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        reference="global",
    ).fit(data)
    with pytest.raises(
        PlotNotAvailableError,
        match=r"active peer.*selected comparison cross-section",
    ):
        prepare_frontier_data(global_result, period=2020)


def test_small_cross_section_prepares_ranked_points_without_mutation() -> None:
    result = _result(
        [0.8, 1.0, 0.9],
        statuses=["optimal", "limit_reached", "optimal"],
        efficient=[False, True, pd.NA],
    )
    before = result.summary()

    prepared = prepare_performance_data(result)

    assert prepared.observation_count == 2
    assert prepared.diagnostic_observation_count == 1
    assert prepared.facets[0].view == "points"
    assert prepared.nonoptimal_count == 1
    classes = prepared.facets[0].frame["_deapack_measure_class"].tolist()
    assert classes == ["inefficient", "not_reported"]
    assert prepared.facets[0].diagnostic_frame["dmu_id"].tolist() == ["DMU-2"]
    assert_frame_equal(result.summary(), before)


def test_radial_performance_uses_the_certified_primary_status() -> None:
    result = _result(
        [0.8, 1.0],
        statuses=["numerical_error", "optimal"],
        efficient=[pd.NA, True],
    )
    result.summary_frame["primary_solver_status"] = ["optimal", "optimal"]
    result.summary_frame["score_valid"] = [True, True]
    result.summary_frame["score_status"] = ["defined", "defined"]

    prepared = prepare_performance_data(result)

    assert prepared.observation_count == 2
    assert prepared.nonoptimal_count == 0
    assert prepared.diagnostic_observation_count == 0
    assert prepared.facets[0].frame["dmu_id"].tolist() == ["DMU-1", "DMU-2"]


def test_large_sample_uses_ecdf_and_keeps_every_observation() -> None:
    count = POINT_VIEW_MAX_OBSERVATIONS + 1
    prepared = prepare_performance_data(
        _result([0.5 + index / 200 for index in range(count)])
    )

    assert prepared.facets[0].view == "ecdf"
    assert prepared.observation_count == count
    assert len(prepared.facets[0].frame) == count


def test_explicit_view_overrides_automatic_threshold() -> None:
    count = POINT_VIEW_MAX_OBSERVATIONS + 1
    prepared = prepare_performance_data(
        _result([0.5 + index / 200 for index in range(count)]),
        view="points",
    )
    assert prepared.facets[0].view == "points"


def test_up_to_four_periods_are_faceted_and_more_require_selection() -> None:
    four = _result(
        [0.8] * 8,
        periods=[2020, 2020, 2021, 2021, 2022, 2022, 2023, 2023],
    )
    assert len(prepare_performance_data(four).facets) == 4

    five = _result(
        [0.8] * 10,
        periods=[
            2020,
            2020,
            2021,
            2021,
            2022,
            2022,
            2023,
            2023,
            2024,
            2024,
        ],
    )
    with pytest.raises(PlotNotAvailableError, match="select period"):
        prepare_performance_data(five)

    selected = prepare_performance_data(five, period=2024)
    assert len(selected.facets) == 1
    assert selected.observation_count == 2
    assert selected.facets[0].period == 2024


def test_static_period_facet_keeps_legacy_label_without_transition_evidence() -> None:
    result = _result([0.8, 0.9], periods=[2021, 2021])

    prepared = prepare_performance_data(result, period=2021)

    assert prepared.facets[0].label == "Period 2021"


@pytest.mark.parametrize(
    ("base_period", "comparison_period", "expected"),
    [
        ("FY2020", "FY2021", "FY2020 \u2192 FY2021"),
        (
            pd.Timestamp("2020-12-31"),
            pd.Timestamp("2021-12-31"),
            "2020-12-31 00:00:00 \u2192 2021-12-31 00:00:00",
        ),
    ],
)
def test_complete_consistent_transition_pair_labels_the_facet(
    base_period: object,
    comparison_period: object,
    expected: str,
) -> None:
    result = _result(
        [1.01, 1.02],
        periods=[comparison_period, comparison_period],
    )
    result.summary_frame["base_period"] = [base_period, base_period]
    result.summary_frame["comparison_period"] = [
        comparison_period,
        comparison_period,
    ]
    before = result.summary()

    prepared = prepare_performance_data(result, period=comparison_period)

    assert prepared.facets[0].label == expected
    assert_frame_equal(result.summary(), before)


def test_transition_label_sanitizes_and_bounds_third_party_period_text() -> None:
    base_period = f"FY2020\n{'private' * 8}"
    comparison_period = f"FY2021\t{'private' * 8}"
    result = _result([1.01], periods=[comparison_period])
    result.summary_frame["base_period"] = [base_period]
    result.summary_frame["comparison_period"] = [comparison_period]

    prepared = prepare_performance_data(result)
    label = prepared.facets[0].label
    base_label, comparison_label = label.split(" \u2192 ")

    assert "\n" not in label
    assert "\t" not in label
    assert len(base_label) <= 32
    assert len(comparison_label) <= 32
    assert base_label.endswith("\u2026")
    assert comparison_label.endswith("\u2026")


@pytest.mark.parametrize(
    ("base_periods", "comparison_periods"),
    [
        ([2020, 2019], [2021, 2021]),
        ([2020, pd.NA], [2021, 2021]),
        ([2021, 2021], [2021, 2021]),
        ([2020, 2020], [2022, 2022]),
        ([2020, 2020], [2021, pd.NA]),
    ],
)
def test_incomplete_or_incoherent_transition_pair_keeps_legacy_label(
    base_periods: list[object],
    comparison_periods: list[object],
) -> None:
    result = _result([1.01, 1.02], periods=[2021, 2021])
    result.summary_frame["base_period"] = base_periods
    result.summary_frame["comparison_period"] = comparison_periods

    prepared = prepare_performance_data(result, period=2021)

    assert prepared.facets[0].label == "Period 2021"


def test_nonfinite_headlines_have_bounded_status_ledger_and_no_coordinates() -> None:
    result = _result(
        [float("nan"), 1.038969, 1.044245, float("nan"), 1.045057, 1.051619],
        periods=[2021] * 6,
        statuses=[
            "infeasible",
            "optimal",
            "optimal",
            "infeasible",
            "optimal",
            "optimal",
        ],
    )
    result.summary_frame["dmu_id"] = [
        "North",
        "South",
        "East",
        "West",
        "Central",
        "Coastal",
    ]
    result.summary_frame["base_period"] = [2020] * 6
    result.summary_frame["comparison_period"] = [2021] * 6
    result.summary_frame["score_valid"] = [False, True, True, False, True, True]
    result.summary_frame["score_status"] = [
        "solver_failed",
        "defined",
        "defined",
        "solver_failed",
        "defined",
        "defined",
    ]

    prepared = prepare_performance_data(result, period=2021)
    facet = prepared.facets[0]

    assert facet.label == "2020 \u2192 2021"
    assert facet.frame["dmu_id"].tolist() == ["South", "East", "Central", "Coastal"]
    assert facet.diagnostic_frame.empty
    assert prepared.omitted_metric_count == 2
    assert prepared.diagnostic_observation_count == 0
    assert [row.dmu_id for row in prepared.unavailable_observations] == [
        "North",
        "West",
    ]
    assert [row.reason for row in prepared.unavailable_observations] == [
        "solver/certification unavailable",
        "solver/certification unavailable",
    ]
    assert [row.certification_status for row in prepared.unavailable_observations] == [
        "infeasible",
        "infeasible",
    ]
    assert [row.score_status for row in prepared.unavailable_observations] == [
        "solver_failed",
        "solver_failed",
    ]


def test_nonfinite_reason_uses_declared_certification_and_validity_contracts() -> None:
    result = _result(
        [0.9, float("nan"), float("nan"), float("nan")],
        statuses=["optimal", "optimal", "optimal", "optimal"],
    )
    result.summary_frame["primary_solver_status"] = [
        "optimal",
        "infeasible",
        "optimal",
        "optimal",
    ]
    result.summary_frame["score_valid"] = [True, False, False, True]
    result.summary_frame["score_status"] = [
        "defined",
        "solver_failed",
        "undefined_external_reference",
        "defined",
    ]

    prepared = prepare_performance_data(result)

    assert [row.reason for row in prepared.unavailable_observations] == [
        "solver/certification unavailable",
        "measure undefined",
        "metric missing/non-finite",
    ]
    first = prepared.unavailable_observations[0]
    assert first.certification_status_column == "primary_solver_status"
    assert first.certification_status == "infeasible"
    assert first.validity_status_column == "score_valid"
    assert first.validity_status == "False"


def test_unavailable_roster_is_stable_sanitized_and_truncated() -> None:
    count = 10
    result = _result(
        [0.9, *([float("nan")] * count)],
        statuses=["optimal", *(["infeasible\nprivate detail"] * count)],
    )
    result.summary_frame["dmu_id"] = [
        "valid",
        "DMU-01\nprivate",
        *(f"DMU-{index:02d}-{'x' * 80}" for index in range(2, count + 1)),
    ]
    result.summary_frame["score_status"] = [
        "defined",
        *(["solver_failed\tprivate detail"] * count),
    ]
    result.summary_frame.index = [7] * (count + 1)

    prepared = prepare_performance_data(result)

    assert prepared.omitted_metric_count == count
    assert len(prepared.unavailable_observations) == 6
    assert prepared.unavailable_observation_overflow == 4
    assert prepared.unavailable_observations[0].dmu_id == "DMU-01 private"
    assert "\n" not in prepared.unavailable_observations[0].certification_status
    assert "\t" not in prepared.unavailable_observations[0].score_status
    assert prepared.unavailable_observations[-1].dmu_id.endswith("\u2026")
    assert all(len(row.dmu_id) <= 48 for row in prepared.unavailable_observations)


def test_finite_nonoptimal_result_remains_diagnostic_not_unavailable() -> None:
    result = _result(
        [0.9, 0.7],
        statuses=["optimal", "infeasible"],
    )
    result.summary_frame["score_status"] = ["defined", "solver_failed"]

    prepared = prepare_performance_data(result)

    assert prepared.omitted_metric_count == 0
    assert prepared.unavailable_observations == ()
    assert prepared.facets[0].diagnostic_frame["dmu_id"].tolist() == ["DMU-2"]


def test_diagnostic_only_period_is_kept_when_another_period_is_certified() -> None:
    result = _result(
        [0.6, 0.9],
        periods=[2020, 2021],
        statuses=["infeasible", "optimal"],
    )

    prepared = prepare_performance_data(result)
    by_period = {facet.period: facet for facet in prepared.facets}

    assert by_period[2020].frame.empty
    assert by_period[2020].diagnostic_frame["dmu_id"].tolist() == ["DMU-1"]
    assert by_period[2020].diagnostic_frame["_deapack_diagnostic_reason"].tolist() == [
        "Non-optimal — excluded"
    ]
    assert by_period[2021].frame["dmu_id"].tolist() == ["DMU-2"]
    assert by_period[2021].diagnostic_frame.empty
    assert prepared.observation_count == 1
    assert prepared.diagnostic_observation_count == 1
    with pytest.raises(PlotNotAvailableError, match="no finite optimal"):
        prepare_performance_data(result, metric="efficiency", period=2020)


def test_missing_period_representations_form_one_cross_section() -> None:
    result = _result(
        [0.8, 0.9, 1.0],
        periods=[None, float("nan"), pd.NA],
    )

    prepared = prepare_performance_data(result)

    assert len(prepared.facets) == 1
    assert prepared.facets[0].label == "Cross-section"
    assert prepared.observation_count == 3


def test_metric_is_never_silently_replaced_by_score() -> None:
    result = _result([0.8, 0.9])
    result.summary_frame.drop(columns="efficiency", inplace=True)
    with pytest.raises(PlotNotAvailableError, match="does not fall back to 'score'"):
        prepare_performance_data(result, metric="efficiency")

    with pytest.raises(PlotNotAvailableError, match="no declared plotting semantics"):
        prepare_performance_data(result, metric="score")

    declared = _result(
        [0.8, 0.9],
        metadata_extra={
            "native_score": "profit_gap",
            "score_direction": "lower_is_better",
        },
    )
    declared.summary_frame.drop(columns="efficiency", inplace=True)
    explicit_score = prepare_performance_data(declared, metric="score")
    assert explicit_score.metric == "score"
    assert explicit_score.measure.preferred_direction == "lower"


@pytest.mark.parametrize("values", [[pd.NA, None], [float("nan"), float("inf")]])
def test_all_missing_or_nonfinite_metric_is_not_available(
    values: list[object],
) -> None:
    result = _result(values)
    assert result.available_plots() == ()
    with pytest.raises(PlotNotAvailableError, match="no finite optimal observations"):
        prepare_performance_data(result, metric="efficiency")


def test_additive_distance_is_a_declared_lower_is_better_default() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "x1": [1.0, 3.0, 3.0],
                "x2": [3.0, 1.0, 3.0],
                "y": [1.0, 1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    result = AdditiveDEA().fit(data)

    plots = result.available_plots()
    assert [plot.kind for plot in plots] == ["performance", "references"]
    assert plots[0].default_metric == "score"
    prepared = prepare_performance_data(result)
    assert prepared.measure.label == "Weighted Slack Sum"
    assert prepared.measure.preferred_direction == "lower"
    assert prepared.measure.benchmark_value == 0.0
    assert set(prepared.facets[0].frame["_deapack_measure_class"]) == {"reported"}


def test_directional_distance_defaults_to_native_beta_not_display_efficiency() -> None:
    ordinary_data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "C"],
                "x": [1.0, 2.0],
                "y": [2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    environmental_data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "C"],
                "x": [1.0, 1.0],
                "y": [2.0, 1.0],
                "b": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )

    ordinary_result = DDF().fit(ordinary_data)
    environmental_result = EnvironmentalDDF().fit(environmental_data)

    for result in (ordinary_result, environmental_result):
        assert result.available_plots()[0].default_metric == "score"
        prepared = prepare_performance_data(result)
        assert prepared.measure.label == "Directional Distance"
        assert prepared.measure.preferred_direction == "lower"
        assert prepared.measure.benchmark_value == 0.0


def test_negative_cfg_distance_has_zero_centred_nonmonotone_plot_semantics() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["old", "new"],
                "x": [1.0, 1.0],
                "y": [1.0, 2.0],
                "b": [2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )
    result = ChungFareGrosskopfDDF(
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
        compute_slacks=False,
    ).fit(data)

    prepared = prepare_performance_data(result)
    assert result.summary().set_index("dmu_id").loc["new", "score"] == pytest.approx(
        -3.0 / 5.0
    )
    assert prepared.measure.preferred_direction == "signed"
    assert prepared.measure.benchmark_value == 0.0
    assert "outside the selected reference technology" in (
        prepared.measure.direction_label
    )


def test_rdm_efficiency_has_dedicated_non_strong_plot_semantics() -> None:
    frame = load_dataset("range_directional_signed")
    roles = dataset_info("range_directional_signed").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    result = RDM().fit(data)

    plots = result.available_plots()
    declared = {measure.column: measure for measure in plots[0].measures}
    prepared = prepare_performance_data(result, metric="rdm_efficiency")

    assert plots[0].default_metric == "beta"
    assert declared["rdm_efficiency"].label == "Range Directional Efficiency"
    assert declared["rdm_efficiency"].classification_column is None
    assert prepared.measure.direction_label == (
        "Higher means less of the remaining range is jointly attainable"
    )
    assert prepared.measure.benchmark_value == 1.0
    assert prepared.measure.benchmark_label == (
        "No positive common range-directional improvement"
    )
    assert prepared.measure.classification_column is None
    assert set(prepared.facets[0].frame["_deapack_measure_class"]) == {"reported"}
    c_value = prepared.facets[0].frame.set_index("dmu_id").loc["C", "rdm_efficiency"]
    assert c_value == pytest.approx(1.0 / 3.0)


def test_rdm_efficiency_one_click_plot_uses_dedicated_label(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, pyplot = _load_matplotlib_for_test(monkeypatch, tmp_path)
    frame = load_dataset("range_directional_signed")
    roles = dataset_info("range_directional_signed").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    result = RDM().fit(data)

    figure = result.plot(metric="rdm_efficiency")
    axis = figure.axes[0]

    assert axis.get_xlabel() == "Range Directional Efficiency"
    assert any(
        "No positive common range-directional improvement" in text.get_text()
        for text in figure.texts
    )
    pyplot.close(figure)


def test_oriented_sbm_performance_uses_criterion_specific_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from deapack.visualization import _matplotlib

    rendered_payloads: list[object] = []
    figure_sentinel = object()

    def _capture_rendered_payload(data: object, *, theme: str) -> object:
        assert theme == "deapack"
        rendered_payloads.append(data)
        return figure_sentinel

    monkeypatch.setattr(
        _matplotlib,
        "render_performance",
        _capture_rendered_payload,
    )
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "O"],
            "x1": [2.0, 4.0, 4.0],
            "x2": [4.0, 2.0, 4.0],
            "y1": [1.0, 2.0, 1.0],
            "y2": [2.0, 1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )
    cases = (
        (
            InputSBM,
            "Resource-Conservation Efficiency",
            "Higher means less avoidable proportional resource use",
            "Resource-conservation efficient under the fitted technology",
        ),
        (
            OutputSBM,
            "Service-Expansion Efficiency",
            "Higher means less attainable proportional service expansion",
            "Service-expansion efficient under the fitted technology",
        ),
    )

    for model, label, direction_label, benchmark_label in cases:
        result = model(returns_to_scale="vrs").fit(data)
        summary = result.summary()
        plot_info = result.available_plots()[0]
        figure = result.plot()
        prepared = rendered_payloads[-1]

        assert summary["is_efficient"].isna().all()
        assert figure is figure_sentinel
        assert plot_info.default_metric == "efficiency"
        assert prepared.measure.column == "efficiency"
        assert prepared.measure.label == label
        assert prepared.measure.direction_label == direction_label
        assert prepared.measure.benchmark_label == benchmark_label
        assert prepared.measure.classification_column == "is_sbm_efficient"
        assert prepared.facets[0].frame["_deapack_measure_class"].tolist() == [
            "efficient",
            "efficient",
            "inefficient",
        ]


def test_nonoriented_sbm_keeps_general_strong_efficiency_plot_semantics() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "O"],
                "x1": [2.0, 4.0, 4.0],
                "x2": [4.0, 2.0, 4.0],
                "y1": [1.0, 2.0, 1.0],
                "y2": [2.0, 1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )

    result = SBM(returns_to_scale="vrs").fit(data)
    prepared = prepare_performance_data(result)

    assert prepared.measure.label == "Efficiency"
    assert prepared.measure.classification_column == "is_efficient"
    assert prepared.facets[0].frame["_deapack_measure_class"].tolist() == [
        "efficient",
        "efficient",
        "inefficient",
    ]


def test_profit_gap_is_declared_without_fabricating_bounded_efficiency() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "input": [2.0, 1.0, 3.0],
                "output": [1.0, 3.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    prices = PriceData.common(
        input_prices={"input": 1.0},
        output_prices={"output": 2.0},
    )
    result = ProfitEfficiency().fit(data, prices)

    assert result.summary()["efficiency"].isna().all()
    assert result.available_plots()[0].default_metric == "profit_gap"
    prepared = prepare_performance_data(result)
    assert prepared.measure.column == "profit_gap"
    assert prepared.measure.preferred_direction == "lower"
    assert prepared.measure.benchmark_value == 0.0


def test_undefined_external_profit_gap_is_excluded_by_shared_validity_mask() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "input": [5.0, 1.0],
                "output": [1.0, 5.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    prices = PriceData.common(
        input_prices={"input": 1.0},
        output_prices={"output": 1.0},
    )
    result = ProfitEfficiency(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(data, prices)

    prepared = prepare_performance_data(result)

    assert prepared.measure.validity_column == "score_valid"
    assert prepared.facets[0].frame["dmu_id"].tolist() == ["reference"]
    assert prepared.facets[0].diagnostic_frame["dmu_id"].tolist() == ["evaluated"]
    assert prepared.invalid_metric_count == 1
    assert prepared.nonoptimal_count == 0
    assert prepared.facets[0].diagnostic_frame[
        "_deapack_diagnostic_reason"
    ].tolist() == ["Measure undefined — excluded"]
    assert prepared.facets[0].diagnostic_frame["score_status"].tolist() == [
        "undefined_external_reference"
    ]


def test_ap_super_efficiency_is_labeled_as_peer_replacement_exposure() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "input": [1.0, 2.0],
                "output": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    result = APSuperEfficiency(returns_to_scale="crs").fit(data)

    prepared = prepare_performance_data(result, metric="efficiency")

    assert prepared.measure.label == "Leave-One-Out Peer-Replacement Exposure"
    assert "remaining peers" in prepared.measure.direction_label
    assert prepared.measure.classification_column is None
    assert set(prepared.facets[0].frame["_deapack_measure_class"]) == {"reported"}


def test_scale_efficiency_is_the_default_visualization_measure() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "C"],
                "input": [1.0, 2.0, 1.0],
                "output": [1.0, 1.0, 0.5],
            }
        ),
        dmu="unit",
        inputs="input",
        outputs="output",
    )
    result = scale_efficiency(data)

    assert result.available_plots()[0].default_metric == "scale_efficiency"
    assert prepare_performance_data(result).metric == "scale_efficiency"


def test_super_sbm_plot_reports_peer_replacement_exposure_not_efficiency() -> None:
    frame = load_dataset("super_sbm_peer_replacement")
    roles = dataset_info("super_sbm_peer_replacement").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    result = ToneSuperSBM().fit(data)

    plots = result.available_plots()
    prepared = prepare_performance_data(result)

    assert plots[0].default_metric == "super_sbm_score"
    assert prepared.measure.label == "Super-SBM Peer-Replacement Exposure"
    assert prepared.measure.preferred_direction == "higher"
    assert prepared.measure.benchmark_value == 1.0
    assert "harder" in prepared.measure.direction_label
    assert prepared.facets[0].frame["dmu_id"].tolist() == [
        "Lean",
        "Balanced",
        "Automation",
    ]


def test_metafrontier_plot_reports_opportunity_proximity_not_management_score() -> None:
    frame = load_dataset("metafrontier_groups")
    roles = dataset_info("metafrontier_groups").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        group=roles["group"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    result = MetafrontierDEA(compute_slacks=False).fit(data)

    plots = result.available_plots()
    prepared = prepare_performance_data(result)

    assert plots[0].default_metric == "metatechnology_ratio"
    assert prepared.measure.label == "Metatechnology Ratio"
    assert prepared.measure.preferred_direction == "higher"
    assert prepared.measure.benchmark_value == 1.0
    assert "group frontier is closer" in prepared.measure.direction_label
    assert prepared.measure.classification_column is None
    assert prepared.facets[0].frame["dmu_id"].tolist() == list("ABCDEF")


def test_productivity_neutral_value_follows_additive_or_multiplicative_contract() -> (
    None
):
    multiplicative = prepare_performance_data(MalmquistDEA().fit(_productivity_data()))
    additive = prepare_performance_data(LuenbergerDEA().fit(_productivity_data()))

    assert multiplicative.measure.column == "productivity_change"
    assert multiplicative.measure.benchmark_value == 1.0
    assert multiplicative.measure.direction_label == ("Above 1 indicates improvement")
    assert additive.measure.column == "productivity_change"
    assert additive.measure.benchmark_value == 0.0
    assert additive.measure.direction_label == ("Positive values indicate improvement")


def test_real_malmquist_summary_uses_its_evidenced_transition_pair() -> None:
    result = MalmquistDEA().fit(_productivity_data())
    before = result.summary()

    prepared = prepare_performance_data(result)

    assert len(prepared.facets) == 1
    assert prepared.facets[0].period == 1
    assert prepared.facets[0].label == "0 \u2192 1"
    assert_frame_equal(result.summary(), before)


def test_non_efficiency_metric_does_not_inherit_generic_classification() -> None:
    result = _result(
        [0.8, 1.0],
        efficient=[False, True],
    )
    result.summary_frame["technically_adjusted_capacity_utilization"] = [
        0.6,
        1.0,
    ]

    prepared = prepare_performance_data(
        result,
        metric="technically_adjusted_capacity_utilization",
    )

    assert prepared.measure.classification_column is None
    assert prepared.facets[0].frame["_deapack_measure_class"].tolist() == [
        "reported",
        "reported",
    ]


def test_system_efficiency_uses_system_radial_classification() -> None:
    result = _result(
        [1.0, 0.8],
        efficient=[True, False],
    )
    result.summary_frame["system_efficiency"] = [0.8, 1.0]
    result.summary_frame["is_system_radially_efficient"] = [False, True]

    plots = result.available_plots()
    prepared = prepare_performance_data(result)

    assert plots[0].default_metric == "system_efficiency"
    assert prepared.measure.classification_column == "is_system_radially_efficient"
    assert prepared.facets[0].frame["_deapack_measure_class"].tolist() == [
        "inefficient",
        "efficient",
    ]


@pytest.mark.parametrize(
    ("method_id", "native_score", "default_metric", "label", "benchmark_label"),
    [
        (
            "dynamic.sbm.tone_tsutsui_2010",
            "efficiency",
            "efficiency",
            "Intertemporal Operating-Plan Performance",
            "No scored burden or shortfall in positively weighted dynamic accounts",
        ),
        (
            "network.sbm.tone_tsutsui_2009",
            "system_efficiency",
            "system_efficiency",
            "Network-System Performance",
            ("No scored burden or shortfall in positively weighted process accounts"),
        ),
        (
            "dynamic.network_sbm.tone_tsutsui_2014",
            "system_efficiency",
            "system_efficiency",
            "Dynamic Network-System Performance",
            (
                "No scored burden or shortfall in positively weighted "
                "period-process accounts"
            ),
        ),
    ],
)
def test_account_models_use_managerial_criterion_language(
    method_id: str,
    native_score: str,
    default_metric: str,
    label: str,
    benchmark_label: str,
) -> None:
    result = _result(
        [0.75, 1.0],
        metadata_extra={
            "method_id": method_id,
            "native_score": native_score,
            "score_direction": "higher_is_better",
        },
    )
    result.summary_frame["score"] = [0.75, 1.0]
    result.summary_frame["distance"] = [0.25, 0.0]
    if native_score == "system_efficiency":
        result.summary_frame["system_efficiency"] = [0.75, 1.0]

    default = prepare_performance_data(result)
    explicit_score = prepare_performance_data(result, metric="score")
    gap = prepare_performance_data(result, metric="distance")

    assert default.metric == default_metric
    assert default.measure.label == label
    assert default.measure.benchmark_label == benchmark_label
    assert default.measure.classification_column is None
    assert explicit_score.measure.label == label
    assert explicit_score.measure.classification_column is None
    assert gap.measure.label.endswith("Gap")
    assert gap.measure.preferred_direction == "lower"
    assert gap.measure.benchmark_label == benchmark_label


def test_arbitrary_numeric_summary_column_is_not_a_declared_measure() -> None:
    result = _result([0.8, 1.0])
    result.summary_frame["made_up_ratio"] = [100.0, 200.0]

    assert "made_up_ratio" not in {
        measure.column for measure in result.available_plots()[0].measures
    }
    with pytest.raises(PlotNotAvailableError, match="no declared plotting semantics"):
        prepare_performance_data(result, metric="made_up_ratio")


def test_external_value_is_not_clipped_and_nonoptimal_value_is_diagnostic() -> None:
    result = _result(
        [1.25, 0.8, 0.6],
        statuses=["optimal", "optimal", "limit_reached"],
        efficient=[pd.NA, False, pd.NA],
    )

    prepared = prepare_performance_data(result)

    assert prepared.facets[0].frame["efficiency"].max() == pytest.approx(1.25)
    assert prepared.facets[0].diagnostic_frame["efficiency"].tolist() == [0.6]
    assert prepared.observation_count == 2
    assert prepared.diagnostic_observation_count == 1


def test_unknown_kind_has_approximate_suggestion_without_loading_backend() -> None:
    with pytest.raises(PlotNotAvailableError, match="did you mean 'performance'"):
        _result([0.8]).plot(kind="performnce")


def test_invalid_period_view_and_theme_fail_explicitly() -> None:
    result = _result([0.8], periods=[2020])
    with pytest.raises(PlotNotAvailableError, match="available periods"):
        prepare_performance_data(result, period=2019)
    with pytest.raises(PlotNotAvailableError, match="unknown performance view"):
        prepare_performance_data(result, view="histogram")
    with pytest.raises(PlotNotAvailableError, match="unknown theme"):
        result.plot(theme="paper")


def test_missing_matplotlib_reports_the_viz_install_command() -> None:
    if importlib.util.find_spec("matplotlib") is not None:
        pytest.skip("Matplotlib is installed in this environment")
    with pytest.raises(ImportError, match=r"pip install 'DEAPack\[viz\]'"):
        _result([0.8]).plot()


def test_transition_preparation_remains_backend_lazy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ordinary_import = builtins.__import__

    def _reject_matplotlib_import(
        name: str,
        globals: Any = None,
        locals: Any = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        if name == "matplotlib" or name.startswith("matplotlib."):
            raise AssertionError("pure-data preparation must not import Matplotlib")
        return ordinary_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _reject_matplotlib_import)
    result = _result([0.9], periods=[2021])
    result.summary_frame["base_period"] = [2020]
    result.summary_frame["comparison_period"] = [2021]

    prepared = prepare_performance_data(result)

    assert prepared.facets[0].label == "2020 \u2192 2021"


def test_transition_render_labels_transfer_and_explains_unavailable_roster(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, pyplot = _load_matplotlib_for_test(monkeypatch, tmp_path)
    result = _result(
        [1.04, *([float("nan")] * 6)],
        periods=[2021] * 7,
        statuses=["optimal", *(["infeasible"] * 6)],
    )
    result.summary_frame["dmu_id"] = [
        "Central",
        "North",
        "West",
        "Rural",
        "Urban",
        "Coastal",
        "Inland",
    ]
    result.summary_frame["base_period"] = [2020] * 7
    result.summary_frame["comparison_period"] = [2021] * 7
    result.summary_frame["score_valid"] = [True, *([False] * 6)]
    result.summary_frame["score_status"] = ["defined", *(["solver_failed"] * 6)]
    before = result.summary()

    figure = result.plot(kind="performance", period=2021)
    figure.canvas.draw()
    axis = figure.axes[0]
    footer = figure.texts[-1]
    footer_text = footer.get_text()

    assert axis.get_title() == "2020 \u2192 2021"
    assert (
        "6 organizations omitted because their headline results are unavailable"
        in footer_text
    )
    assert all(name in footer_text for name in ("North", "West", "Inland"))
    assert "solver/certification unavailable" in footer_text
    assert "solver=infeasible" in footer_text
    assert sum(len(collection.get_offsets()) for collection in axis.collections) == 1
    assert axis.get_yticklabels()[0].get_text() == "Central"
    renderer = figure.canvas.get_renderer()
    footer_box = footer.get_window_extent(renderer=renderer).transformed(
        figure.transFigure.inverted()
    )
    assert footer_box.y1 < axis.get_position().y0
    assert_frame_equal(result.summary(), before)
    pyplot.close(figure)


def test_unavailable_footer_uses_grammatical_singular(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, pyplot = _load_matplotlib_for_test(monkeypatch, tmp_path)
    result = _result(
        [0.9, float("nan")],
        statuses=["optimal", "infeasible"],
    )

    figure = result.plot()
    footer_text = figure.texts[-1].get_text()

    assert (
        "1 organization omitted because its headline result is unavailable"
        in footer_text
    )
    assert "result(s)" not in footer_text
    pyplot.close(figure)


def test_matplotlib_render_returns_figure_and_preserves_global_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    matplotlib, pyplot = _load_matplotlib_for_test(monkeypatch, tmp_path)
    figure_type = pytest.importorskip("matplotlib.figure").Figure
    result = _result(
        [0.75, 1.0, 1.2],
        statuses=["optimal", "limit_reached", "optimal"],
        efficient=[False, True, pd.NA],
    )
    before_frame = result.summary()
    before_rc = {
        key: matplotlib.rcParams[key]
        for key in ("axes.edgecolor", "font.size", "grid.color")
    }

    def _show_is_forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("plot() must not call pyplot.show()")

    monkeypatch.setattr(pyplot, "show", _show_is_forbidden)
    figure = result.plot()

    assert isinstance(figure, figure_type)
    assert len(figure.axes) == 1
    assert figure.axes[0].get_xlim()[1] > 1.0
    assert any(
        "1 non-optimal" in text.get_text() and "excluded" in text.get_text()
        for text in figure.texts
    )
    assert any(
        "excluded from ranking" in text.get_text() for text in figure.axes[0].texts
    )
    assert any(
        text.get_text() == "Efficiency status not reported"
        for legend in figure.legends
        for text in legend.get_texts()
    )
    assert {
        key: matplotlib.rcParams[key]
        for key in ("axes.edgecolor", "font.size", "grid.color")
    } == before_rc
    assert_frame_equal(result.summary(), before_frame)
    pyplot.close(figure)


def test_matplotlib_frontier_renders_targets_and_managerial_caveat(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    matplotlib, pyplot = _load_matplotlib_for_test(monkeypatch, tmp_path)
    figure_type = pytest.importorskip("matplotlib.figure").Figure
    result = _frontier_result()
    before_summary = result.summary()
    before_targets = result.targets.copy(deep=True)
    before_rc = {
        key: matplotlib.rcParams[key]
        for key in ("axes.edgecolor", "font.size", "grid.color")
    }

    figure = result.plot(kind="frontier")
    axis = figure.axes[0]

    assert isinstance(figure, figure_type)
    assert axis.get_xlabel() == "input"
    assert axis.get_ylabel() == "output"
    assert "Resource-saving opportunities" in axis.get_title()
    assert any(
        "not causal or prescriptive claims" in text.get_text() for text in figure.texts
    )
    assert any(
        text.get_text() == "Reported DEA target"
        for text in axis.get_legend().get_texts()
    )
    assert {text.get_text() for text in axis.texts}.issuperset(set("ABCDEFGH"))
    assert {
        key: matplotlib.rcParams[key]
        for key in ("axes.edgecolor", "font.size", "grid.color")
    } == before_rc
    assert_frame_equal(result.summary(), before_summary)
    assert_frame_equal(result.targets, before_targets)
    pyplot.close(figure)


def test_matplotlib_ecdf_uses_all_observations(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, pyplot = _load_matplotlib_for_test(monkeypatch, tmp_path)
    count = POINT_VIEW_MAX_OBSERVATIONS + 7

    figure = _result([0.4 + index / 100 for index in range(count)]).plot(view="auto")

    ecdf_line = next(
        line for line in figure.axes[0].lines if line.get_linestyle() == "-"
    )
    assert len(ecdf_line.get_xdata()) == count
    pyplot.close(figure)


def test_matplotlib_ecdf_excludes_nonoptimal_values_from_distribution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, pyplot = _load_matplotlib_for_test(monkeypatch, tmp_path)
    count = POINT_VIEW_MAX_OBSERVATIONS + 7
    result = _result(
        [0.4 + index / 100 for index in range(count)],
        statuses=["optimal"] * (count - 2) + ["limit_reached", "failed"],
    )

    figure = result.plot(view="auto")

    ecdf_line = next(
        line for line in figure.axes[0].lines if line.get_linestyle() == "-"
    )
    assert len(ecdf_line.get_xdata()) == count - 2
    assert any("excluded from ECDF" in text.get_text() for text in figure.axes[0].texts)
    pyplot.close(figure)


def test_matplotlib_uses_declared_label_direction_and_benchmark(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, pyplot = _load_matplotlib_for_test(monkeypatch, tmp_path)
    result = _result(
        [pd.NA, pd.NA, pd.NA],
        metadata_extra={
            "native_score": "profit_gap",
            "score_direction": "lower_is_better",
        },
    )
    result.summary_frame["score"] = [5.0, 0.0, 4.0]

    figure = result.plot()
    axis = figure.axes[0]

    assert axis.get_xlabel() == "Profit Gap"
    benchmark = next(line for line in axis.lines if line.get_linestyle() == ":")
    assert list(benchmark.get_xdata()) == [0.0, 0.0]
    assert axis.get_yticklabels()[-1].get_text() == "DMU-2"
    assert any("Lower is better" in text.get_text() for text in figure.texts)
    pyplot.close(figure)


def test_matplotlib_creates_one_visible_axis_per_period(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, pyplot = _load_matplotlib_for_test(monkeypatch, tmp_path)
    result = _result(
        [0.8] * 6,
        periods=[2020, 2020, 2021, 2021, 2022, 2022],
    )

    figure = result.plot()

    assert len(figure.axes) == 3
    assert {axis.get_title() for axis in figure.axes} == {
        "Period 2020",
        "Period 2021",
        "Period 2022",
    }
    pyplot.close(figure)
