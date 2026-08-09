import numpy as np
import pandas as pd
import pytest

from deapack import (
    RAM,
    AdditiveDEA,
    DEAData,
    RangeAdjustedDEA,
    ReferenceSpec,
    SolverOptions,
    SolverStatus,
    WeightedAdditiveDEA,
)
from deapack.exceptions import ModelSpecificationError
from deapack.solvers import LPSolution


def _two_input_example(*, scale_first_input: float = 1.0) -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "x1": np.asarray([1.0, 3.0, 3.0]) * scale_first_input,
            "x2": [3.0, 1.0, 3.0],
            "y": [1.0, 1.0, 1.0],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )


def test_additive_reports_native_distance_slacks_and_targets() -> None:
    result = AdditiveDEA().fit(_two_input_example())
    summary = result.summary().set_index("dmu_id")

    assert np.isclose(summary.loc["A", "distance"], 0.0)
    assert np.isclose(summary.loc["B", "distance"], 0.0)
    assert np.isclose(summary.loc["C", "score"], 2.0)
    assert np.isclose(summary.loc["C", "distance"], 2.0)
    assert np.isnan(summary.loc["C", "efficiency"])
    assert not bool(summary.loc["C", "is_efficient"])

    c_slacks = result.slacks.query("dmu_id == 'C'")
    assert np.isclose(c_slacks["slack"].sum(), 2.0)
    c_targets = result.targets_for("C").set_index(["role", "variable"])
    selected_input_target = (
        c_targets.loc[("input", "x1"), "target"],
        c_targets.loc[("input", "x2"), "target"],
    )
    assert selected_input_target in {(1.0, 3.0), (3.0, 1.0)}
    assert result.metadata["efficiency_transform"] is None
    assert result.metadata["native_score"] == "weighted_slack_sum"


def test_named_weights_can_remove_an_input_unit_change() -> None:
    baseline = AdditiveDEA().fit(_two_input_example())
    scaled = AdditiveDEA(
        input_weights={"x1": 0.01, "x2": 1.0},
        output_weights={"y": 1.0},
    ).fit(_two_input_example(scale_first_input=100.0))

    baseline_distance = baseline.summary().set_index("dmu_id").loc["C", "distance"]
    scaled_distance = scaled.summary().set_index("dmu_id").loc["C", "distance"]
    assert np.isclose(baseline_distance, scaled_distance)
    assert scaled.metadata["weighting"] == "user"
    assert dict(scaled.metadata["input_weights"]) == {"x1": 0.01, "x2": 1.0}


def test_additive_captures_output_shortfall() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 1.0],
            "y": [2.0, 1.0],
        }
    )
    data = DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")

    result = AdditiveDEA().fit(data)
    b_output = result.slacks.query("dmu_id == 'B' and role == 'output'")

    assert np.isclose(result.summary().loc[1, "distance"], 1.0)
    assert np.isclose(b_output["slack"].iloc[0], 1.0)
    assert np.isclose(result.targets_for("B")["target"].iloc[1], 2.0)


def test_additive_uses_the_shared_panel_reference_plan() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "year": [2020, 2021],
            "x": [1.0, 2.0],
            "y": [1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="year",
        inputs="x",
        outputs="y",
    )

    current = AdditiveDEA(reference="contemporaneous").fit(data)
    global_result = AdditiveDEA(reference="global").fit(data)

    assert np.isclose(current.summary().loc[1, "distance"], 0.0)
    assert np.isclose(global_result.summary().loc[1, "distance"], 1.0)
    assert global_result.metadata["compiled_reference_sets"] == 1
    assert current.metadata["source_profile_matches"] is False
    assert current.metadata["source_profile_mismatches"] == (
        "data_are_not_one_cross_section",
        "reference_is_not_the_full_self_inclusive_sample",
    )
    assert global_result.metadata["source_profile_matches"] is False
    assert global_result.metadata["source_profile_mismatches"] == (
        "data_are_not_one_cross_section",
    )


def test_source_profile_uses_effective_unit_weights_and_global_reference() -> None:
    data = _two_input_example()

    explicit_unit_weights = AdditiveDEA(
        input_weights={"x1": 1.0, "x2": 1.0},
        output_weights={"y": 1.0},
    ).fit(data)
    custom_full_sample = AdditiveDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=(0, 1, 2)),
    ).fit(data)

    assert explicit_unit_weights.metadata["source_profile_matches"] is True
    assert explicit_unit_weights.metadata["source_profile_mismatches"] == ()
    assert explicit_unit_weights.metadata["weighting"] == "unit"
    assert explicit_unit_weights.metadata["weight_source"] == "user_declared"
    assert custom_full_sample.metadata["source_profile_matches"] is False
    assert custom_full_sample.metadata["source_profile_mismatches"] == (
        "reference_is_not_the_full_self_inclusive_sample",
    )


def test_weight_validation_and_discoverability_alias() -> None:
    assert WeightedAdditiveDEA is AdditiveDEA

    with pytest.raises(ModelSpecificationError, match="name every input"):
        AdditiveDEA(input_weights={"x1": 1.0}).fit(_two_input_example())

    with pytest.raises(ModelSpecificationError, match="strictly positive"):
        AdditiveDEA(input_weights=[1.0, 0.0]).fit(_two_input_example())

    with pytest.raises(ModelSpecificationError, match="solver dual"):
        AdditiveDEA(
            input_weights={"x1": 1e-8, "x2": 1.0},
            output_weights={"y": 1.0},
        ).fit(_two_input_example())

    for keyword in ("tolerance", "peer_tolerance"):
        with pytest.raises(ValueError, match="finite and positive"):
            AdditiveDEA(**{keyword: np.nan})


def test_small_relative_weight_requires_a_matching_solver_dual_tolerance() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    model = AdditiveDEA(
        input_weights={"x": 1e-8},
        output_weights={"y": 1.0},
        tolerance=1e-9,
    )
    with pytest.raises(ModelSpecificationError, match="solver dual"):
        model.fit(data)

    resolved = AdditiveDEA(
        input_weights={"x": 1e-8},
        output_weights={"y": 1.0},
        tolerance=1e-9,
        solver_options=SolverOptions(
            primal_feasibility_tolerance=1e-9,
            dual_feasibility_tolerance=1e-9,
        ),
    ).fit(data)
    row = resolved.summary().set_index("dmu_id").loc["B"]
    assert row["distance"] == pytest.approx(1e-8, abs=1e-16)
    assert not bool(row["is_efficient"])
    assert resolved.metadata["solver_dual_feasibility_tolerance"] == 1e-9


def test_small_common_weights_do_not_create_a_false_efficiency_status() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )

    result = AdditiveDEA(
        input_weights={"x": 1e-8},
        output_weights={"y": 1e-8},
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["B"]

    assert row["distance"] == pytest.approx(1e-8, abs=1e-16)
    assert row["max_scaled_slack"] == pytest.approx(1.0, abs=1e-12)
    assert not bool(row["is_efficient"])
    assert result.peers("B")["reference_dmu_id"].tolist() == ["A"]


def test_extreme_reciprocal_unit_change_preserves_strong_status() -> None:
    baseline_frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x1": [1.0, 1.0],
            "x2": [1.0, 2.0],
            "y": [1.0, 1.0],
        }
    )
    baseline_data = DEAData.from_frame(
        baseline_frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    transformed_frame = baseline_frame.assign(
        x2=baseline_frame["x2"] * 1e-8,
    )
    transformed_data = DEAData.from_frame(
        transformed_frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )

    baseline = AdditiveDEA().fit(baseline_data)
    transformed = AdditiveDEA(
        input_weights={"x1": 1.0, "x2": 1e8},
        output_weights={"y": 1.0},
    ).fit(transformed_data)
    baseline_row = baseline.summary().set_index("dmu_id").loc["B"]
    transformed_row = transformed.summary().set_index("dmu_id").loc["B"]

    assert baseline_row["distance"] == pytest.approx(1.0, abs=1e-12)
    assert transformed_row["distance"] == pytest.approx(1.0, abs=1e-12)
    assert baseline_row["max_scaled_slack"] == pytest.approx(1.0, abs=1e-12)
    assert transformed_row["max_scaled_slack"] == pytest.approx(1.0, abs=1e-12)
    assert not bool(transformed_row["is_efficient"])
    transformed_slack = transformed.slacks.query(
        "dmu_id == 'B' and role == 'input' and variable == 'x2'"
    ).iloc[0]
    assert transformed_slack["slack"] == pytest.approx(1e-8, abs=1e-16)
    assert transformed_slack["scaled_slack"] == pytest.approx(1.0, abs=1e-12)


def test_vrs_translation_preserves_additive_and_ram_strong_status() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["lower", "peer", "evaluated"],
            "x1": [1.0, 1.0, 1.0],
            "x2": [0.0, 0.999, 1.0],
            "y": [0.1, 1.0, 1.0],
        }
    )

    def fit_pair(translation: float):
        translated = frame.assign(x2=frame["x2"] + translation)
        data = DEAData.from_frame(
            translated,
            dmu="dmu",
            inputs=["x1", "x2"],
            outputs="y",
        )
        return AdditiveDEA().fit(data), RAM().fit(data)

    base_additive, base_ram = fit_pair(0.0)
    shifted_additive, shifted_ram = fit_pair(10_000.0)
    for baseline, shifted, expected_distance in (
        (base_additive, shifted_additive, 0.001),
        (base_ram, shifted_ram, 0.001 / 3.0),
    ):
        baseline_row = baseline.summary().set_index("dmu_id").loc["evaluated"]
        shifted_row = shifted.summary().set_index("dmu_id").loc["evaluated"]
        assert baseline_row["distance"] == pytest.approx(
            expected_distance,
            abs=1e-12,
        )
        assert shifted_row["distance"] == pytest.approx(
            expected_distance,
            abs=1e-12,
        )
        assert baseline_row["max_scaled_slack"] == pytest.approx(0.001, abs=1e-12)
        assert shifted_row["max_scaled_slack"] == pytest.approx(0.001, abs=1e-12)
        assert not bool(baseline_row["is_efficient"])
        assert not bool(shifted_row["is_efficient"])


def test_small_peer_intensity_is_retained_when_it_materially_explains_target() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "C", "B"],
                "x": [1e9, 1.0, 10.0],
                "y": [2e9, 1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )

    result = AdditiveDEA().fit(data)
    peers = result.peers("B").set_index("reference_dmu_id")
    target = result.targets_for("B").set_index(["role", "variable"])

    assert set(peers.index) == {"A", "C"}
    assert 0.0 < peers.loc["A", "lambda"] < 1e-7
    reconstructed_input = (
        peers.loc["A", "lambda"] * 1e9 + peers.loc["C", "lambda"] * 1.0
    )
    reconstructed_output = (
        peers.loc["A", "lambda"] * 2e9 + peers.loc["C", "lambda"] * 1.0
    )
    assert reconstructed_input == pytest.approx(
        target.loc[("input", "x"), "target"],
        rel=1e-8,
    )
    assert reconstructed_output == pytest.approx(
        target.loc[("output", "y"), "target"],
        rel=1e-8,
    )


def test_ram_reports_bounded_efficiency_and_range_distance() -> None:
    result = RangeAdjustedDEA().fit(_two_input_example())
    summary = result.summary().set_index("dmu_id")

    assert RAM is RangeAdjustedDEA
    assert np.isclose(summary.loc["C", "distance"], 1.0 / 3.0)
    assert np.isclose(summary.loc["C", "score"], 2.0 / 3.0)
    assert np.isclose(summary.loc["C", "efficiency"], 2.0 / 3.0)
    assert result.metadata["native_score"] == "ram_efficiency"
    assert dict(result.metadata["output_ranges"]) == {"y": 0.0}


def test_ram_is_units_and_translation_invariant() -> None:
    baseline = RAM().fit(_two_input_example()).summary()["efficiency"]
    scaled = RAM().fit(_two_input_example(scale_first_input=100.0))

    translated_frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "x1": [-9.0, -7.0, -7.0],
            "x2": [103.0, 101.0, 103.0],
            "y": [6.0, 6.0, 6.0],
        }
    )
    translated_data = DEAData.from_frame(
        translated_frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    translated = RAM().fit(translated_data)

    assert np.allclose(scaled.summary()["efficiency"], baseline)
    assert np.allclose(translated.summary()["efficiency"], baseline)


def test_panel_ram_requires_explicit_global_reference() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "year": [2020, 2021],
            "x": [1.0, 2.0],
            "y": [1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="year",
        inputs="x",
        outputs="y",
    )

    with pytest.raises(ModelSpecificationError, match="requires reference='global'"):
        RAM().fit(data)

    result = RAM(reference="global").fit(data)
    assert result.metadata["reference_kind"] == "global"
    assert result.metadata["range_scope"] == "data"


class _NonoptimalMarginalSolver:
    name = "nonoptimal_marginal_fixture"

    def solve(self, problem):
        return LPSolution(
            status=SolverStatus.LIMIT_REACHED,
            objective=None,
            primal=None,
            message=f"injected failure for {problem.name}",
            iterations=0,
            equality_marginals=np.zeros(problem.a_eq.shape[0]),
            inequality_marginals=(
                None if problem.a_ub is None else np.zeros(problem.a_ub.shape[0])
            ),
        )


@pytest.mark.parametrize("model", [AdditiveDEA, RAM])
def test_nonoptimal_additive_family_results_do_not_publish_duals(model) -> None:
    result = model(solver=_NonoptimalMarginalSolver()).fit(_two_input_example())

    assert result.summary()["score"].isna().all()
    assert result.duals.empty
