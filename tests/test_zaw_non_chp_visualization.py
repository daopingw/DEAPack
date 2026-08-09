from __future__ import annotations

import pandas as pd
import pytest

from deapack import DEAResult
from deapack.visualization.performance import prepare_performance_data

_METHOD_ID = (
    "environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp"
)


def _result(index_name: str = "ecpi_1") -> DEAResult:
    return DEAResult(
        summary_frame=pd.DataFrame(
            {
                "dmu_id": ["valid", "uncertified-account"],
                "period": [None, None],
                "score": [0.375, 0.2],
                "efficiency": [0.375, 0.2],
                "performance_index": [0.375, 0.2],
                "performance_index_name": [index_name, index_name],
                "distance": [0.5, 0.8],
                "directional_nonradial_distance": [0.5, 0.8],
                "is_efficient": [pd.NA, pd.NA],
                "score_direction": ["higher_is_better", "higher_is_better"],
                "distance_direction": [
                    "higher_is_more_unrealized_opportunity",
                    "higher_is_more_unrealized_opportunity",
                ],
                "score_valid": [True, False],
                "solver_status": ["optimal", "optimal"],
                "model_family": [
                    "zhou_ang_wang_non_chp_energy_carbon",
                    "zhou_ang_wang_non_chp_energy_carbon",
                ],
            }
        ),
        metadata={
            "method_id": _METHOD_ID,
            "native_score": "performance_index",
            "score_direction": "higher_is_better",
            "returns_to_scale": "crs",
            "source_account": "integrated_energy_carbon",
        },
    )


@pytest.mark.parametrize(
    ("index_name", "label"),
    [
        ("epi_1", "Energy Performance Index (EPI1)"),
        ("cpi_1", "Carbon Performance Index (CPI1)"),
        (
            "ecpi_1",
            "Integrated Energy-Carbon Performance Index (ECPI1)",
        ),
    ],
)
def test_source_index_is_the_management_facing_default(
    index_name: str,
    label: str,
) -> None:
    result = _result(index_name)

    plot = result.available_plots()[0]
    prepared = prepare_performance_data(result)

    assert plot.default_metric == "performance_index"
    assert prepared.measure.label == label
    assert prepared.measure.preferred_direction == "higher"
    assert prepared.measure.benchmark_value == 1.0
    assert prepared.measure.benchmark_label == "Source-directional best practice"
    assert "less unrealized improvement opportunity" in (
        prepared.measure.direction_label
    )
    assert prepared.measure.classification_column is None


def test_raw_distance_is_lower_preferred_and_invalid_rows_are_diagnostic() -> None:
    prepared = prepare_performance_data(
        _result(),
        metric="directional_nonradial_distance",
    )

    assert prepared.measure.label == "Directional Non-Radial Unrealized Opportunity"
    assert prepared.measure.preferred_direction == "lower"
    assert prepared.measure.benchmark_value == 0.0
    assert prepared.measure.direction_label.startswith("Larger means more unrealized")
    assert prepared.facets[0].frame["dmu_id"].tolist() == ["valid"]
    assert prepared.facets[0].diagnostic_frame["dmu_id"].tolist() == [
        "uncertified-account"
    ]
    assert prepared.invalid_metric_count == 1
