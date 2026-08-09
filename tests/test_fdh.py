from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import (
    BCC,
    FDH,
    DEAData,
    FreeDisposalHullDEA,
    ReferenceSpec,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError


def _data(frame: pd.DataFrame) -> DEAData:
    input_columns = [column for column in frame if column.startswith("x")]
    output_columns = [column for column in frame if column.startswith("y")]
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=input_columns,
        outputs=output_columns,
    )


def test_hand_calculated_input_and_output_scores() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "x": [1.0, 2.0, 3.0],
                "y": [1.0, 2.0, 1.5],
            }
        )
    )

    input_summary = FDH(orientation="input").fit(data).summary().set_index("dmu_id")
    output_summary = FDH(orientation="output").fit(data).summary().set_index("dmu_id")

    assert np.isclose(input_summary.loc["C", "score"], 2.0 / 3.0)
    assert np.isclose(input_summary.loc["C", "efficiency"], 2.0 / 3.0)
    assert np.isclose(output_summary.loc["C", "score"], 4.0 / 3.0)
    assert np.isclose(output_summary.loc["C", "efficiency"], 0.75)


def test_input_zero_denominator_requires_zero_peer_input() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "x1": [0.0, 0.0, 1.0],
                "x2": [1.0, 2.0, 0.5],
                "y": [1.0, 1.0, 1.0],
            }
        )
    )
    result = FDH(orientation="input").fit(data)
    summary = result.summary().set_index("dmu_id")

    assert np.isclose(summary.loc["B", "efficiency"], 0.5)
    assert result.peers("B")["reference_dmu_id"].tolist() == ["A"]


def test_zero_output_component_does_not_enter_output_ratio() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 1.0],
                "y1": [1.0, 2.0],
                "y2": [0.0, 3.0],
            }
        )
    )
    result = FDH(orientation="output").fit(data)
    summary = result.summary().set_index("dmu_id")

    assert np.isclose(summary.loc["A", "score"], 2.0)
    assert np.isclose(summary.loc["A", "efficiency"], 0.5)
    y2_slack = result.slacks.query(
        "dmu_id == 'A' and role == 'output' and variable == 'y2'"
    )["slack"].iloc[0]
    assert np.isclose(y2_slack, 3.0)


def test_zero_output_factor_has_missing_reciprocal_efficiency() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 1.0],
                "y1": [0.0, 1.0],
                "y2": [1.0, 0.0],
            }
        )
    )
    result = FDH(
        orientation="output",
        reference=ReferenceSpec("custom", custom_rows=[0]),
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["B"]

    assert np.isclose(row["score"], 0.0)
    assert np.isnan(row["efficiency"])
    assert not bool(row["is_within_reference_technology"])
    assert pd.isna(row["is_radially_efficient"])


def test_all_radial_ties_are_reported_as_alternative_single_peers() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "x": [1.0, 1.0, 2.0],
                "y": [2.0, 2.0, 1.0],
            }
        )
    )
    result = FDH(orientation="input").fit(data)
    peers = result.peers("C")

    assert peers["reference_dmu_id"].tolist() == ["A", "B"]
    assert peers["lambda"].tolist() == [1.0, 1.0]
    assert peers["alternative_rank"].tolist() == [1, 2]
    assert peers["is_primary"].tolist() == [True, False]
    assert "not a convex combination" in result.metadata["intensity_semantics"]


def test_lexicographic_peer_scan_distinguishes_radial_and_strong_efficiency() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 1.0],
                "y": [2.0, 1.0],
            }
        )
    )
    result = FreeDisposalHullDEA(orientation="input").fit(data)
    row = result.summary().set_index("dmu_id").loc["B"]

    assert bool(row["is_radially_efficient"])
    assert not bool(row["is_efficient"])
    assert np.isclose(row["max_slack"], 1.0)
    target = result.targets_for("B").query("role == 'output'")["target"].iloc[0]
    assert np.isclose(target, 2.0)


def test_reporting_tolerance_does_not_widen_strong_completion_candidates() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["near_tie", "evaluated"],
                "x": [1.001, 1.0],
                "y": [2.0, 1.0],
            }
        )
    )
    result = FDH(
        orientation="input",
        tolerance=1e-7,
        tie_tolerance=0.01,
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["evaluated"]
    peers = result.peers("evaluated").set_index("reference_dmu_id")

    assert set(peers.index) == {"near_tie", "evaluated"}
    assert bool(peers.loc["evaluated", "is_primary"])
    assert not bool(peers.loc["near_tie", "is_primary"])
    assert bool(row["is_radially_efficient"])
    assert bool(row["is_efficient"])
    assert np.isclose(row["max_slack"], 0.0)
    phase_two = result.diagnostics.query("dmu_id == 'evaluated' and phase == 2").iloc[0]
    assert phase_two["candidate_count"] == 1


def test_score_only_mode_does_not_claim_strong_efficiency() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 1.0],
                "y": [2.0, 1.0],
            }
        )
    )
    result = FDH(compute_slacks=False).fit(data)
    row = result.summary().set_index("dmu_id").loc["B"]

    assert bool(row["is_radially_efficient"])
    assert pd.isna(row["is_efficient"])
    assert result.slacks.empty
    assert result.targets.empty
    assert set(result.diagnostics["phase"]) == {1}


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_no_dominating_custom_comparator_is_reported_infeasible(
    orientation: str,
) -> None:
    if orientation == "input":
        frame = pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
            }
        )
        custom_rows = [0]
        evaluated = "evaluated"
    else:
        frame = pd.DataFrame(
            {
                "dmu": ["evaluated", "reference"],
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
            }
        )
        custom_rows = [1]
        evaluated = "evaluated"
    data = _data(frame)
    result = FDH(
        orientation=orientation,
        reference=ReferenceSpec("custom", custom_rows=custom_rows),
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc[evaluated]

    assert row["solver_status"] == "infeasible"
    assert np.isnan(row["score"])
    assert pd.isna(row["is_efficient"])
    diagnostic = result.diagnostics.query("dmu_id == @evaluated").iloc[0]
    assert diagnostic["candidate_count"] == 0


def test_external_custom_reference_flags_points_outside_technology() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "x": [2.0, 1.0],
                "y": [2.0, 2.0],
            }
        )
    )
    result = FDH(
        orientation="input",
        reference=ReferenceSpec("custom", custom_rows=[0]),
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["evaluated"]

    assert np.isclose(row["score"], 2.0)
    assert np.isclose(row["efficiency"], 2.0)
    assert not bool(row["is_within_reference_technology"])
    assert pd.isna(row["is_radially_efficient"])
    assert pd.isna(row["is_efficient"])


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_fdh_efficiency_is_no_lower_than_convex_vrs_efficiency(
    orientation: str,
) -> None:
    rng = np.random.default_rng(20260729)
    frame = pd.DataFrame(
        np.column_stack(
            [
                rng.uniform(0.5, 4.0, size=(30, 2)),
                rng.uniform(0.5, 5.0, size=(30, 2)),
            ]
        ),
        columns=["x1", "x2", "y1", "y2"],
    )
    frame.insert(0, "dmu", [f"D{row}" for row in range(len(frame))])
    data = _data(frame)

    fdh_efficiency = FDH(orientation=orientation).fit(data).summary()["efficiency"]
    vrs_efficiency = BCC(orientation=orientation).fit(data).summary()["efficiency"]

    assert np.all(fdh_efficiency >= vrs_efficiency - 1e-7)


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_scores_are_invariant_to_positive_variable_rescaling(
    orientation: str,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D"],
            "x1": [1.0, 2.0, 3.0, 2.5],
            "x2": [4.0, 2.0, 1.0, 3.0],
            "y1": [1.0, 2.0, 1.5, 2.5],
            "y2": [3.0, 1.0, 2.0, 2.0],
        }
    )
    baseline = FDH(orientation=orientation).fit(_data(frame)).summary()["score"]
    scaled_frame = frame.copy()
    scaled_frame["x1"] *= 1_000.0
    scaled_frame["y2"] *= 0.001
    scaled = FDH(orientation=orientation).fit(_data(scaled_frame)).summary()["score"]

    np.testing.assert_allclose(baseline, scaled)


def test_chunk_size_does_not_change_scores_or_peers() -> None:
    rng = np.random.default_rng(42)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{row}" for row in range(70)],
            "x1": rng.integers(1, 20, size=70),
            "x2": rng.integers(1, 20, size=70),
            "y1": rng.integers(1, 20, size=70),
            "y2": rng.integers(1, 20, size=70),
        }
    )
    data = _data(frame)
    one_at_a_time = FDH(chunk_size=1).fit(data)
    one_block = FDH(chunk_size=10_000).fit(data)

    np.testing.assert_allclose(
        one_at_a_time.summary()["score"],
        one_block.summary()["score"],
    )
    pd.testing.assert_frame_equal(
        one_at_a_time.intensities.reset_index(drop=True),
        one_block.intensities.reset_index(drop=True),
    )


def test_moderate_large_sample_uses_direct_scan_without_solver() -> None:
    rng = np.random.default_rng(7)
    n = 1_200
    frame = pd.DataFrame(
        {
            "dmu": [f"D{row}" for row in range(n)],
            "x1": rng.lognormal(size=n),
            "x2": rng.lognormal(size=n),
            "x3": rng.lognormal(size=n),
            "y1": rng.lognormal(size=n),
            "y2": rng.lognormal(size=n),
        }
    )
    result = FDH(compute_slacks=False, chunk_size=128).fit(_data(frame))

    assert len(result.summary()) == n
    assert set(result.summary()["solver_status"]) == {"optimal"}
    assert result.metadata["solver"] == "none_direct_dominance_scan"
    assert set(result.diagnostics["algorithm"]) == {"chunked_dominance_ratio_scan"}


def test_fdh_rejects_unsupported_data_and_invalid_configuration() -> None:
    negative = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, -1.0],
                "y": [1.0, 1.0],
            }
        )
    )
    with pytest.raises(DataValidationError, match="nonnegative"):
        FDH().fit(negative)

    bad_output_data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
                "bad": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="bad",
    )
    with pytest.raises(ModelSpecificationError, match="undesirable outputs"):
        FDH().fit(bad_output_data)

    with pytest.raises(ValueError, match="tolerance must be positive"):
        FDH(tolerance=0.0)
    with pytest.raises(ValueError, match="tie_tolerance must be positive"):
        FDH(tie_tolerance=0.0)
    with pytest.raises(TypeError, match="positive integer"):
        FDH(chunk_size=True)
    with pytest.raises(ValueError, match="positive integer"):
        FDH(chunk_size=0)
