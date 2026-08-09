from __future__ import annotations

import pandas as pd
import pytest

from deapack import (
    DEAData,
    FGNZEnhancedMalmquist,
    RayDesliMalmquist,
)


def _positive_adjacent_panel() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B"],
                "period": [0, 0, 1, 1],
                "capital": [1.0, 2.0, 1.1, 2.1],
                "labor": [2.0, 1.0, 1.9, 1.1],
                "service": [2.0, 2.4, 2.3, 2.7],
            }
        ),
        dmu="dmu",
        period="period",
        inputs=["capital", "labor"],
        outputs="service",
    )


@pytest.mark.parametrize(
    ("model", "method_id", "partial_policy"),
    [
        (
            FGNZEnhancedMalmquist(),
            "productivity.malmquist.decomposition.fgnz_pure_scale_extension",
            "valid_crs_productivity_efficiency_and_technical_change_are_"
            "retained_when_an_auxiliary_vrs_own_period_task_fails",
        ),
        (
            RayDesliMalmquist(),
            "productivity.malmquist.decomposition.ray_desli",
            "valid_crs_productivity_and_own_period_vrs_pure_efficiency_are_"
            "retained_when_a_vrs_cross_period_task_fails",
        ),
    ],
    ids=("enhanced_fgnz", "ray_desli"),
)
def test_named_malmquist_decompositions_publish_the_unified_change_metadata(
    model: object,
    method_id: str,
    partial_policy: str,
) -> None:
    result = model.fit(_positive_adjacent_panel())  # type: ignore[attr-defined]
    metadata = result.metadata

    assert {
        "change_calculus": metadata["change_calculus"],
        "no_change_value": metadata["no_change_value"],
        "improvement_rule": metadata["improvement_rule"],
        "reference_information_policy": metadata["reference_information_policy"],
        "distance_task_convention": metadata["distance_task_convention"],
        "transition_release_policy": metadata["transition_release_policy"],
    } == {
        "change_calculus": "multiplicative",
        "no_change_value": 1.0,
        "improvement_rule": "greater_than_one",
        "reference_information_policy": "adjacent_contemporaneous",
        "distance_task_convention": "farrell_efficiency_form",
        "transition_release_policy": "component_scoped_per_transition",
    }
    assert metadata["method_id"] == method_id
    assert metadata["partial_decomposition_policy"] == partial_policy
    assert metadata["transition_release_policy"] != "atomic_per_transition"
