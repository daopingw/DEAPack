from __future__ import annotations

import pandas as pd

from deapack import DEAResult
from deapack.visualization.performance import prepare_performance_data


def _directional_super_result() -> DEAResult:
    return DEAResult(
        summary_frame=pd.DataFrame(
            {
                "dmu_id": ["valid", "negative-output-boundary"],
                "period": [None, None],
                "score": [1.4, 2.4],
                "efficiency": [1.4, 2.4],
                "distance": [-0.4, -1.4],
                "beta": [-0.4, -1.4],
                "nl_super_efficiency": [1.4, 2.4],
                "is_efficient": [pd.NA, pd.NA],
                "solver_status": ["optimal", "optimal"],
                "score_valid": [True, False],
                "model_family": [
                    "ray_directional_super_efficiency",
                    "ray_directional_super_efficiency",
                ],
            }
        ),
        metadata={
            "method_id": "evaluation.super.directional.ray_2008",
            "native_score": "nl_super_efficiency",
            "score_direction": "higher_is_more_exposed",
            "returns_to_scale": "vrs",
            "reference_kind": "global",
        },
    )


def test_ray_plot_uses_peer_replacement_language_and_native_default() -> None:
    result = _directional_super_result()

    plot = result.available_plots()[0]
    measures = {measure.column: measure for measure in plot.measures}
    prepared = prepare_performance_data(result)

    assert plot.default_metric == "nl_super_efficiency"
    assert prepared.measure.label == "Nerlove-Luenberger Peer-Replacement Exposure"
    assert prepared.measure.preferred_direction == "higher"
    assert prepared.measure.benchmark_value == 1.0
    assert prepared.measure.benchmark_label == "No joint peer-replacement concession"
    assert "joint resource-and-service concession" in (prepared.measure.direction_label)
    assert measures["efficiency"].label == prepared.measure.label
    assert measures["efficiency"].classification_column is None
    assert measures["beta"].label == "Directional Peer-Replacement Distance"
    assert measures["beta"].preferred_direction == "lower"


def test_ray_plot_excludes_negative_output_projection_from_ranking() -> None:
    prepared = prepare_performance_data(_directional_super_result())

    assert prepared.facets[0].frame["dmu_id"].tolist() == ["valid"]
    assert prepared.facets[0].diagnostic_frame["dmu_id"].tolist() == [
        "negative-output-boundary"
    ]
    assert prepared.invalid_metric_count == 1
    assert prepared.facets[0].diagnostic_frame[
        "_deapack_diagnostic_reason"
    ].tolist() == ["Measure undefined — excluded"]
