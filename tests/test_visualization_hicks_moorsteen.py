from __future__ import annotations

import pandas as pd
import pytest

from deapack import DEAData, DEAResult, HicksMoorsteenDEA, load_dataset
from deapack.visualization import PlotNotAvailableError, prepare_performance_data


def _productivity_result() -> DEAResult:
    frame = load_dataset("productivity_panel")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=("capital", "labor"),
        outputs="output",
    )
    return HicksMoorsteenDEA(returns_to_scale="vrs").fit(data)


def test_combined_quantity_indexes_have_descriptive_2021_plot_semantics() -> None:
    result = _productivity_result()

    performance = result.available_plots()[0]
    measures = {measure.column: measure for measure in performance.measures}

    assert performance.kind == "performance"
    assert performance.default_metric == "productivity_change"
    assert set(measures) == {
        "score",
        "productivity_change",
        "output_quantity_index",
        "input_quantity_index",
    }
    assert not any(column.endswith(("_s", "_t")) for column in measures)

    for metric, quantity, label_fragment in (
        ("output_quantity_index", "output", "Combined Output Quantity Index"),
        ("input_quantity_index", "input", "Combined Input Quantity Index"),
    ):
        measure = measures[metric]
        assert label_fragment in measure.label
        assert measure.preferred_direction == "signed"
        assert measure.benchmark_value == 1.0
        assert measure.benchmark_label == f"No aggregate {quantity} quantity change"
        assert "not an improvement or ranking measure" in measure.direction_label
        assert measure.classification_column is None

    assert (
        "above 1 means aggregate input growth"
        in measures["input_quantity_index"].direction_label
    )
    assert (
        "Above 1 indicates improvement"
        not in measures["input_quantity_index"].direction_label
    )

    headline = prepare_performance_data(result, period=2021, view="points")
    output = prepare_performance_data(
        result,
        metric="output_quantity_index",
        period=2021,
        view="points",
    )
    inputs = prepare_performance_data(
        result,
        metric="input_quantity_index",
        period=2021,
        view="points",
    )

    assert headline.metric == "productivity_change"
    assert headline.measure.preferred_direction == "higher"
    assert output.facets[0].frame["dmu_id"].tolist() == list("ABCDE")
    assert inputs.facets[0].frame["dmu_id"].tolist() == list("ABCDE")

    unit_d_output = (
        output.facets[0].frame.set_index("dmu_id").loc["D", "output_quantity_index"]
    )
    unit_d_input = (
        inputs.facets[0].frame.set_index("dmu_id").loc["D", "input_quantity_index"]
    )
    unit_d_hm = (
        headline.facets[0].frame.set_index("dmu_id").loc["D", "productivity_change"]
    )
    assert unit_d_output == pytest.approx(1.1532777777777776, abs=1e-12)
    assert unit_d_input == pytest.approx(1.02, abs=1e-12)
    assert unit_d_hm == pytest.approx(1.1306644880174292, abs=1e-12)
    assert unit_d_hm == pytest.approx(unit_d_output / unit_d_input, abs=1e-12)


@pytest.mark.parametrize(
    "metric",
    ["output_quantity_index", "input_quantity_index"],
)
def test_combined_quantity_plot_respects_score_valid(metric: str) -> None:
    result = _productivity_result()
    assert result.summary_frame["score_valid"].eq(True).all()
    invalid = result.summary_frame["dmu_id"].eq("D") & result.summary_frame[
        "period"
    ].eq(2021)
    result.summary_frame.loc[invalid, "score_valid"] = False

    prepared = prepare_performance_data(
        result,
        metric=metric,
        period=2021,
        view="points",
    )

    facet = prepared.facets[0]
    assert prepared.invalid_metric_count == 1
    assert facet.frame["dmu_id"].tolist() == ["A", "B", "C", "E"]
    assert facet.diagnostic_frame["dmu_id"].tolist() == ["D"]
    assert facet.diagnostic_frame["score_valid"].tolist() == [False]
    assert facet.diagnostic_frame["_deapack_diagnostic_reason"].tolist() == [
        "Measure undefined — excluded"
    ]


def test_quantity_semantics_require_the_exact_hicks_moorsteen_method_id() -> None:
    exact = _productivity_result()
    summary = exact.summary(copy=True)
    unrelated = DEAResult(
        summary_frame=summary,
        metadata={
            "method_id": "productivity.hicks_moorsteen.paper_specific_variant",
            "native_score": "productivity_change",
            "score_direction": "greater_than_one_is_improvement",
        },
    )

    declared = {measure.column for measure in unrelated.available_plots()[0].measures}
    assert "productivity_change" in declared
    assert "output_quantity_index" not in declared
    assert "input_quantity_index" not in declared
    with pytest.raises(PlotNotAvailableError, match="no declared plotting semantics"):
        prepare_performance_data(unrelated, metric="output_quantity_index")


def test_prepared_combined_quantity_frames_are_detached() -> None:
    result = _productivity_result()
    before = result.summary(copy=True)
    prepared = prepare_performance_data(
        result,
        metric="output_quantity_index",
        period=2021,
    )

    prepared.facets[0].frame.loc[:, "output_quantity_index"] = -100.0

    pd.testing.assert_frame_equal(result.summary(), before)
