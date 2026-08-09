from __future__ import annotations

from fractions import Fraction

import numpy as np
import pandas as pd

from deapack import FDH, DEAData


def test_exact_fdh_certificate_exhausts_observed_activities() -> None:
    inputs = [(1, 4), (4, 1), (2, 2), (4, 4), (3, 3)]
    outputs = [(4, 1), (1, 4), (3, 3), (2, 2), (1, 1)]

    input_scores: list[Fraction] = []
    output_scores: list[Fraction] = []
    for x_o, y_o in zip(inputs, outputs, strict=True):
        input_candidates = [
            max(Fraction(x_j[i], x_o[i]) for i in range(2))
            for x_j, y_j in zip(inputs, outputs, strict=True)
            if all(y_j[r] >= y_o[r] for r in range(2))
        ]
        output_candidates = [
            min(Fraction(y_j[r], y_o[r]) for r in range(2))
            for x_j, y_j in zip(inputs, outputs, strict=True)
            if all(x_j[i] <= x_o[i] for i in range(2))
        ]
        input_scores.append(min(input_candidates))
        output_scores.append(max(output_candidates))

    assert input_scores == [
        Fraction(1),
        Fraction(1),
        Fraction(1),
        Fraction(1, 2),
        Fraction(2, 3),
    ]
    assert output_scores == [
        Fraction(1),
        Fraction(1),
        Fraction(1),
        Fraction(3, 2),
        Fraction(3),
    ]


def _exact_fdh_fixture() -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D", "E"],
            "x1": [1.0, 4.0, 2.0, 4.0, 3.0],
            "x2": [4.0, 1.0, 2.0, 4.0, 3.0],
            "y1": [4.0, 1.0, 3.0, 2.0, 1.0],
            "y2": [1.0, 4.0, 3.0, 2.0, 1.0],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )


def _assert_target_and_residual_account(
    result: object,
    dmu_id: str,
    *,
    expected_input_slacks: list[float],
    expected_output_slacks: list[float],
) -> None:
    peers = result.peers(dmu_id)
    assert peers["reference_dmu_id"].tolist() == ["C"]
    assert peers["lambda"].tolist() == [1.0]
    assert peers["is_primary"].tolist() == [True]

    targets = result.targets_for(dmu_id).set_index(["role", "variable"])
    assert np.allclose(
        targets.loc[[("input", "x1"), ("input", "x2")], "target"],
        [2.0, 2.0],
    )
    assert np.allclose(
        targets.loc[[("output", "y1"), ("output", "y2")], "target"],
        [3.0, 3.0],
    )

    slacks = result.slacks.query("dmu_id == @dmu_id").set_index(["role", "variable"])
    assert np.allclose(
        slacks.loc[[("input", "x1"), ("input", "x2")], "slack"],
        expected_input_slacks,
    )
    assert np.allclose(
        slacks.loc[[("output", "y1"), ("output", "y2")], "slack"],
        expected_output_slacks,
    )


def test_public_fdh_matches_exact_finite_activity_certificate() -> None:
    data = _exact_fdh_fixture()

    input_result = FDH(orientation="input").fit(data)
    input_summary = input_result.summary().set_index("dmu_id")
    assert np.allclose(
        input_summary["score"],
        [1.0, 1.0, 1.0, 1.0 / 2.0, 2.0 / 3.0],
    )
    assert np.allclose(input_summary["efficiency"], input_summary["score"])
    assert input_summary["candidate_count"].tolist() == [1, 1, 1, 2, 5]
    assert input_summary["is_radially_efficient"].tolist() == [
        True,
        True,
        True,
        False,
        False,
    ]
    assert input_summary["is_efficient"].tolist() == [
        True,
        True,
        True,
        False,
        False,
    ]
    _assert_target_and_residual_account(
        input_result,
        "D",
        expected_input_slacks=[0.0, 0.0],
        expected_output_slacks=[1.0, 1.0],
    )
    _assert_target_and_residual_account(
        input_result,
        "E",
        expected_input_slacks=[0.0, 0.0],
        expected_output_slacks=[2.0, 2.0],
    )

    output_result = FDH(orientation="output").fit(data)
    output_summary = output_result.summary().set_index("dmu_id")
    assert np.allclose(output_summary["score"], [1.0, 1.0, 1.0, 1.5, 3.0])
    assert np.allclose(
        output_summary["efficiency"],
        [1.0, 1.0, 1.0, 2.0 / 3.0, 1.0 / 3.0],
    )
    assert output_summary["candidate_count"].tolist() == [1, 1, 1, 5, 2]
    assert output_summary["is_radially_efficient"].tolist() == [
        True,
        True,
        True,
        False,
        False,
    ]
    assert output_summary["is_efficient"].tolist() == [
        True,
        True,
        True,
        False,
        False,
    ]
    _assert_target_and_residual_account(
        output_result,
        "D",
        expected_input_slacks=[2.0, 2.0],
        expected_output_slacks=[0.0, 0.0],
    )
    _assert_target_and_residual_account(
        output_result,
        "E",
        expected_input_slacks=[1.0, 1.0],
        expected_output_slacks=[0.0, 0.0],
    )
