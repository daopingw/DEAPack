from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import DEAData, ReferenceSpec, SolverStatus
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.models.bam import BAM, BoundedAdjustedDEA
from deapack.solvers import LPSolution

_INPUTS = np.asarray(
    [
        [20.0, 151.0],
        [19.0, 131.0],
        [25.0, 160.0],
        [27.0, 168.0],
        [22.0, 158.0],
        [55.0, 255.0],
        [33.0, 235.0],
        [31.0, 206.0],
        [30.0, 244.0],
        [50.0, 268.0],
        [53.0, 306.0],
        [38.0, 284.0],
    ]
)
_OUTPUTS = np.asarray(
    [
        [100.0, 90.0],
        [150.0, 50.0],
        [160.0, 55.0],
        [180.0, 72.0],
        [94.0, 66.0],
        [230.0, 90.0],
        [220.0, 88.0],
        [152.0, 80.0],
        [190.0, 100.0],
        [250.0, 100.0],
        [260.0, 147.0],
        [250.0, 120.0],
    ]
)
_VRS_DISTANCE = np.asarray(
    [
        0.0,
        0.0,
        0.294371564218,
        0.0,
        0.446809460063,
        0.236933479532,
        0.0,
        0.275804444444,
        0.059555873138,
        0.0,
        0.0,
        0.0,
    ]
)
_CRS_DISTANCE = np.asarray(
    [
        0.0,
        0.0,
        0.346805273834,
        0.0,
        0.532521310104,
        0.475321867058,
        0.259066901408,
        0.299958823529,
        0.116677943769,
        0.472481107634,
        0.106062778052,
        0.325024757378,
    ]
)


def _cooper_example(
    *,
    input_scales: tuple[float, float] = (1.0, 1.0),
    output_scales: tuple[float, float] = (1.0, 1.0),
) -> DEAData:
    inputs = _INPUTS * np.asarray(input_scales)
    outputs = _OUTPUTS * np.asarray(output_scales)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{position:02d}" for position in range(1, 13)],
            "x1": inputs[:, 0],
            "x2": inputs[:, 1],
            "y1": outputs[:, 0],
            "y2": outputs[:, 1],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )


@pytest.mark.parametrize(
    ("returns_to_scale", "expected"),
    [("vrs", _VRS_DISTANCE), ("crs", _CRS_DISTANCE)],
)
def test_twelve_dmu_independent_bam_oracle(
    returns_to_scale: str,
    expected: np.ndarray,
) -> None:
    result = BAM(returns_to_scale=returns_to_scale).fit(_cooper_example())
    summary = result.summary()

    np.testing.assert_allclose(summary["distance"], expected, atol=5e-11, rtol=0.0)
    np.testing.assert_allclose(summary["efficiency"], 1.0 - expected, atol=5e-11)
    np.testing.assert_allclose(summary["score"], summary["efficiency"])
    assert (summary["solver_status"] == "optimal").all()
    assert result.metadata["native_score"] == "bam_efficiency"
    assert result.metadata["method_id"] == "static.bam"


def test_alias_slack_account_and_zero_room_policy() -> None:
    assert BAM is BoundedAdjustedDEA
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "x": [1.0, 2.0, 3.0],
            "constant_input": [5.0, 5.0, 5.0],
            "y": [3.0, 2.0, 1.0],
            "constant_output": [7.0, 7.0, 7.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x", "constant_input"],
        outputs=["y", "constant_output"],
    )

    result = BoundedAdjustedDEA().fit(data)
    summary = result.summary()
    zero_components = result.slacks.query(
        "variable in ['constant_input', 'constant_output']"
    )

    assert np.isfinite(summary["efficiency"]).all()
    assert (zero_components["slack"] == 0.0).all()
    assert (zero_components["weight"] == 0.0).all()
    assert (zero_components["slack_upper_bound"] == 0.0).all()
    assert (zero_components["normalized_slack"] == 0.0).all()
    assert result.metadata["zero_range_policy"] == (
        "zero_weight_and_zero_slack_upper_bound"
    )

    components = result.slacks.groupby("dmu_id")["normalized_slack"].sum()
    expected_distance = components / (data.n_inputs + data.n_outputs)
    observed_distance = summary.set_index("dmu_id")["distance"]
    np.testing.assert_allclose(observed_distance, expected_distance)


def test_nirs_can_use_a_subunit_reference_activity() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "x": [1.0, 3.0, 2.0],
            "y": [0.1, 4.0, 1.0],
        }
    )
    data = DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")

    vrs = BAM(returns_to_scale="vrs").fit(data)
    nirs = BAM(returns_to_scale="nirs").fit(data)
    vrs_row = vrs.summary().set_index("dmu_id").loc["C"]
    nirs_row = nirs.summary().set_index("dmu_id").loc["C"]

    assert nirs_row["distance"] > vrs_row["distance"]
    assert nirs.peers("C")["lambda"].sum() < 1.0 - 1e-8
    assert 0.0 <= nirs_row["distance"] <= 1.0


def test_ndrs_can_scale_up_a_productive_small_activity() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "x": [1.0, 4.0, 5.0],
            "y": [2.0, 5.0, 8.0],
        }
    )
    data = DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")

    vrs = BAM(returns_to_scale="vrs").fit(data)
    ndrs = BAM(returns_to_scale="ndrs").fit(data)
    vrs_row = vrs.summary().set_index("dmu_id").loc["B"]
    ndrs_row = ndrs.summary().set_index("dmu_id").loc["B"]

    assert np.isclose(vrs_row["distance"], 0.25)
    assert np.isclose(ndrs_row["distance"], 0.5)
    assert np.isclose(ndrs.peers("B")["lambda"].sum(), 4.0)
    assert 0.0 <= ndrs_row["distance"] <= 1.0


def test_bam_is_invariant_to_positive_changes_of_units() -> None:
    baseline = BAM(returns_to_scale="crs").fit(_cooper_example())
    rescaled = BAM(returns_to_scale="crs").fit(
        _cooper_example(
            input_scales=(1e20, 1e-20),
            output_scales=(1e-20, 1e20),
        )
    )

    np.testing.assert_allclose(
        baseline.summary()["distance"],
        rescaled.summary()["distance"],
        atol=1e-10,
    )
    assert rescaled.metadata["numerical_formulation"] == (
        "row_scaled_balances_with_bounded_normalized_slack_variables"
    )


def test_bam_does_not_clean_a_real_slack_after_a_small_unit_change() -> None:
    def fit(scale: float):
        data = DEAData.from_frame(
            pd.DataFrame(
                {
                    "dmu": ["A", "B"],
                    "x": np.asarray([1.0, 2.0]) * scale,
                    "y": [1.0, 1.0],
                }
            ),
            dmu="dmu",
            inputs="x",
            outputs="y",
        )
        return BAM().fit(data)

    baseline = fit(1.0)
    rescaled = fit(1e-12)
    for result, expected_slack in ((baseline, 1.0), (rescaled, 1e-12)):
        row = result.summary().set_index("dmu_id").loc["B"]
        slack = result.slacks.query("dmu_id == 'B' and role == 'input'").iloc[0]
        assert row["distance"] == pytest.approx(0.5, abs=1e-12)
        assert row["max_normalized_slack"] == pytest.approx(1.0, abs=1e-12)
        assert not bool(row["is_efficient"])
        assert slack["slack"] == pytest.approx(expected_slack, rel=1e-12)
        assert slack["normalized_slack"] == pytest.approx(1.0, abs=1e-12)
    np.testing.assert_allclose(
        baseline.slacks["normalized_slack"],
        rescaled.slacks["normalized_slack"],
        atol=1e-10,
    )


def test_normalized_tolerance_does_not_erase_a_physical_slack_or_target() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["lower_bound", "peer", "evaluated"],
            "x": [1.0, 99.0, 100.0],
            "y": [0.1, 1.0, 1.0],
        }
    )
    data = DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")

    result = BAM(tolerance=0.02).fit(data)
    row = result.summary().set_index("dmu_id").loc["evaluated"]
    slack = result.slacks.query("dmu_id == 'evaluated' and role == 'input'").iloc[0]
    target = result.targets.query("dmu_id == 'evaluated' and role == 'input'").iloc[0]

    assert np.isclose(slack["slack"], 1.0)
    assert 0.0 < slack["normalized_slack"] < result.metadata["tolerance"]
    assert np.isclose(target["target"], 99.0)
    assert np.isclose(target["observed"] - target["target"], slack["slack"])
    assert np.isclose(row["max_slack"], 1.0)
    assert bool(row["is_efficient"])


class _FailingSolver:
    name = "bam_failure_fixture"

    def solve(self, problem):
        return LPSolution(
            status=SolverStatus.LIMIT_REACHED,
            objective=None,
            primal=None,
            message="injected BAM failure",
            iterations=0,
            equality_marginals=np.zeros(problem.a_eq.shape[0]),
            inequality_marginals=(
                None if problem.a_ub is None else np.zeros(problem.a_ub.shape[0])
            ),
        )


def test_solver_failure_propagates_without_partial_efficiency_claims() -> None:
    result = BAM(solver=_FailingSolver()).fit(_cooper_example())
    summary = result.summary()

    assert (summary["solver_status"] == "limit_reached").all()
    assert summary["score"].isna().all()
    assert summary["efficiency"].isna().all()
    assert summary["distance"].isna().all()
    assert summary["is_efficient"].isna().all()
    assert result.slacks.empty
    assert result.targets.empty
    assert result.intensities.empty
    assert result.duals.empty
    assert set(result.diagnostics["message"]) == {"injected BAM failure"}


class _AlternateMaterialPeerSolver:
    name = "bam_alternate_material_peer_fixture"

    def solve(self, problem):
        dmu_id = problem.name.split(":", maxsplit=1)[0]
        lambdas = {
            "A": [1.0, 0.0, 0.0],
            "C": [0.0, 1.0, 0.0],
            "B": [1e-8, 1.0 - 1e-8, 0.0],
        }[dmu_id]
        primal = np.asarray([*lambdas, 0.0, 0.0, 0.0, 0.0])
        return LPSolution(
            status=SolverStatus.OPTIMAL,
            objective=0.0,
            primal=primal,
            message="exact alternate optimum",
            iterations=0,
        )


def test_bam_retains_a_small_peer_that_materially_explains_the_target() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "C", "B"],
                "x1": [1e9, 0.0, 10.0],
                "x2": [1.0, 1.0, 1.0],
                "y1": [1e9, 0.0, 10.0],
                "y2": [1.0, 1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )
    result = BAM(
        solver=_AlternateMaterialPeerSolver(),
        tolerance=1e-7,
        peer_tolerance=1e-10,
    ).fit(data)
    peers = result.peers("B").set_index("reference_dmu_id")
    targets = result.targets_for("B").set_index(["role", "variable"])

    assert set(peers.index) == {"A", "C"}
    assert peers.loc["A", "lambda"] == pytest.approx(1e-8, abs=1e-16)
    assert peers.loc["C", "lambda"] == pytest.approx(1.0 - 1e-8, abs=1e-16)
    assert peers.loc["A", "lambda"] * 1e9 == pytest.approx(
        targets.loc[("input", "x1"), "target"],
        abs=1e-12,
    )
    assert peers.loc["A", "lambda"] * 1e9 == pytest.approx(
        targets.loc[("output", "y1"), "target"],
        abs=1e-12,
    )


def test_bam_rejects_non_global_or_ambiguous_reference_populations() -> None:
    with pytest.raises(ModelSpecificationError, match="one global sample"):
        BAM(reference=ReferenceSpec("custom", custom_rows=[0])).fit(_cooper_example())

    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "year": [2020, 2021],
            "x": [1.0, 2.0],
            "y": [1.0, 2.0],
        }
    )
    panel = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="year",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(ModelSpecificationError, match="requires reference='global'"):
        BAM().fit(panel)

    result = BAM(reference="global").fit(panel)
    assert result.metadata["reference_kind"] == "global"


def test_bam_rejects_implicit_undesirable_output_treatment() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 2.0],
            "y": [1.0, 2.0],
            "bad": [2.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="bad",
    )

    with pytest.raises(ModelSpecificationError, match="undesirable outputs"):
        BAM().fit(data)


def test_bam_rejects_signed_data_in_the_initial_canonical_leaf() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [-1.0, 2.0],
            "y": [1.0, 2.0],
        }
    )
    data = DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")

    with pytest.raises(DataValidationError, match="nonnegative"):
        BAM().fit(data)
