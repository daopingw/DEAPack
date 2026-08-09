from __future__ import annotations

import pandas as pd
import pytest

from deapack import (
    DEAData,
    FGNZMalmquist,
    GlobalMalmquistDEA,
    GlobalMalmquistLuenbergerDEA,
    HicksMoorsteenDEA,
    LuenbergerDEA,
    MalmquistLuenbergerDEA,
)


def _ordinary_panel() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B"],
                "period": [0, 0, 1, 1],
                "x": [2.0, 4.0, 1.0, 2.0],
                "y": [3.0, 6.0, 6.0, 12.0],
            }
        ),
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )


def _environmental_panel() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B"],
                "period": [0, 0, 1, 1],
                "x": [1.0, 1.0, 1.0, 1.0],
                "y": [7.0, 5.0, 8.0, 5.5],
                "b": [2.0, 5.0, 1.0, 3.0],
            }
        ),
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )


@pytest.mark.parametrize(
    (
        "model",
        "environmental",
        "calculus",
        "neutral",
        "improvement_rule",
        "reference_policy",
        "distance_convention",
    ),
    [
        (
            FGNZMalmquist(),
            False,
            "multiplicative",
            1.0,
            "greater_than_one",
            "adjacent_contemporaneous",
            "farrell_efficiency_form",
        ),
        (
            GlobalMalmquistDEA(),
            False,
            "multiplicative",
            1.0,
            "greater_than_one",
            "global",
            "farrell_efficiency_form",
        ),
        (
            LuenbergerDEA(),
            False,
            "additive",
            0.0,
            "greater_than_zero",
            "adjacent_contemporaneous",
            "directional_distance_in_declared_programme_units",
        ),
        (
            HicksMoorsteenDEA(),
            False,
            "multiplicative",
            1.0,
            "greater_than_one",
            "two_contemporaneous_bilateral",
            "paired_shephard_input_output_distances",
        ),
        (
            MalmquistLuenbergerDEA(),
            True,
            "multiplicative",
            1.0,
            "greater_than_one",
            "adjacent_contemporaneous_cross_evaluation",
            "one_plus_environmental_directional_distance_factor",
        ),
        (
            GlobalMalmquistLuenbergerDEA(),
            True,
            "multiplicative",
            1.0,
            "greater_than_one",
            "global_full_sample",
            "one_plus_environmental_directional_distance_factor",
        ),
    ],
    ids=("fgnz", "global", "luenberger", "hicks_moorsteen", "cfg_ml", "oh_gml"),
)
def test_mainstream_productivity_routes_share_one_explicit_change_contract(
    model: object,
    environmental: bool,
    calculus: str,
    neutral: float,
    improvement_rule: str,
    reference_policy: str,
    distance_convention: str,
) -> None:
    data = _environmental_panel() if environmental else _ordinary_panel()
    result = model.fit(data)  # type: ignore[attr-defined]
    metadata = result.metadata

    assert metadata["change_calculus"] == calculus
    assert metadata["no_change_value"] == neutral
    assert metadata["improvement_rule"] == improvement_rule
    assert metadata["reference_information_policy"] == reference_policy
    assert metadata["distance_task_convention"] == distance_convention
    assert metadata["transition_release_policy"] == "atomic_per_transition"
    assert metadata["native_score"] == "productivity_change"
    assert metadata["solver_calls"] == metadata["unique_distance_solves"]
    assert metadata["additional_solver_calls"] == 0
