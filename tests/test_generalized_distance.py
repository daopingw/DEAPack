from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
import pytest

from deapack import (
    GDF,
    DEAData,
    GeneralizedDistanceDEA,
    RadialDEA,
    ReferenceSpec,
    SolverOptions,
    SolverStatus,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver

SCORE_ATOL = 5e-7
TARGET_ATOL = 1e-6

_INPUTS = np.array(
    [
        [5.0, 3.0],
        [2.0, 4.0],
        [4.0, 2.0],
        [4.0, 8.0],
        [7.0, 9.0],
    ]
)
_OUTPUTS = np.array(
    [
        [7.0, 4.0],
        [10.0, 8.0],
        [8.0, 10.0],
        [5.0, 4.0],
        [3.0, 6.0],
    ]
)
_DMUS = np.array(["1", "2", "3", "4", "5"], dtype=object)
_TARGET_KEYS = (
    ("input", "x1"),
    ("input", "x2"),
    ("output", "y1"),
    ("output", "y2"),
)


def _five_dmu_data(
    *,
    order: np.ndarray | None = None,
    input_scales: tuple[float, float] = (1.0, 1.0),
    output_scales: tuple[float, float] = (1.0, 1.0),
) -> DEAData:
    positions = np.arange(5) if order is None else np.asarray(order)
    inputs = _INPUTS[positions] * np.asarray(input_scales)
    outputs = _OUTPUTS[positions] * np.asarray(output_scales)
    frame = pd.DataFrame(
        {
            "dmu": _DMUS[positions],
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


def _target_values(result, dmu_id: str, column: str) -> np.ndarray:
    indexed = result.targets.query("dmu_id == @dmu_id").set_index(["role", "variable"])
    return np.asarray([indexed.loc[key, column] for key in _TARGET_KEYS], dtype=float)


def _slack_values(result, dmu_id: str) -> np.ndarray:
    indexed = result.slacks.query("dmu_id == @dmu_id").set_index(["role", "variable"])
    return np.asarray([indexed.loc[key, "slack"] for key in _TARGET_KEYS], dtype=float)


def _stage_lambdas(result, dmu_id: str, stage: str) -> pd.Series:
    rows = result.intensities.query("dmu_id == @dmu_id and stage == @stage").set_index(
        "reference_dmu_id"
    )
    return rows["lambda"].sort_index()


class _FailingPhaseTwoSolver:
    name = "gdf_phase_two_failure_fixture"

    def __init__(self) -> None:
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        if problem.name.endswith(":gdf-slacks"):
            return LPSolution(
                status=SolverStatus.LIMIT_REACHED,
                objective=None,
                primal=None,
                message="injected GDF phase-two failure",
                iterations=0,
            )
        return self._delegate.solve(problem)


class _AlwaysFailingSolver:
    name = "gdf_phase_one_failure_fixture"

    def solve(self, problem):
        return LPSolution(
            status=SolverStatus.LIMIT_REACHED,
            objective=None,
            primal=None,
            message="injected GDF phase-one failure",
            iterations=0,
        )


def test_crs_alpha_half_matches_the_fixed_five_dmu_oracle() -> None:
    result = GDF(alpha=0.5, returns_to_scale="crs").fit(_five_dmu_data())
    summary = result.summary().set_index("dmu_id")
    expected = np.array([7 / 11, 1.0, 1.0, 1 / 4, 6 / 23])

    np.testing.assert_allclose(
        summary.loc[_DMUS, "score"],
        expected,
        atol=SCORE_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(summary.loc[_DMUS, "efficiency"], expected)
    np.testing.assert_allclose(
        summary.loc[_DMUS, "generalized_distance"],
        expected,
    )
    assert "standard_hyperbolic_efficiency" not in summary
    np.testing.assert_allclose(
        summary.loc[_DMUS, "resource_commitment"],
        np.sqrt(expected),
    )
    np.testing.assert_allclose(
        summary.loc[_DMUS, "service_commitment"],
        1 / np.sqrt(expected),
    )
    assert summary["distance"].isna().all()

    h_1 = math.sqrt(7 / 11)
    h_5 = math.sqrt(6 / 23)
    np.testing.assert_allclose(
        _stage_lambdas(result, "1", "phase_one_reference_activity"),
        [h_1 / 6, 7 * h_1 / 6],
        atol=TARGET_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(
        _stage_lambdas(result, "5", "phase_one_reference_activity"),
        [11 * h_5 / 6, 5 * h_5 / 6],
        atol=TARGET_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(
        _target_values(result, "1", "target"),
        [5 * h_1, 3 * h_1, 11 * h_1, 13 * h_1],
        atol=TARGET_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(
        _target_values(result, "5", "target"),
        [7 * h_5, 9 * h_5, 25 * h_5, 23 * h_5],
        atol=TARGET_ATOL,
        rtol=0,
    )
    assert result.metadata["solver_strategy"] == "exact_crs_input_radial_transform"
    assert result.metadata["total_feasibility_solves"] == 5


def test_vrs_alpha_half_matches_the_fixed_five_dmu_oracle() -> None:
    result = GDF(alpha=0.5, returns_to_scale="vrs").fit(_five_dmu_data())
    summary = result.summary().set_index("dmu_id")
    root_30 = math.sqrt(30)
    expected = np.array([(13 - 2 * root_30) / 3, 1.0, 1.0, 1 / 4, 9 / 25])

    np.testing.assert_allclose(
        summary.loc[_DMUS, "score"],
        expected,
        atol=SCORE_ATOL,
        rtol=0,
    )
    assert summary["search_converged"].all()
    assert (summary["search_absolute_gap"] <= SCORE_ATOL).all()
    assert (summary["feasibility_solves"] > 1).all()

    np.testing.assert_allclose(
        _stage_lambdas(result, "1", "phase_one_reference_activity"),
        [(root_30 - 5) / 2, (7 - root_30) / 2],
        atol=TARGET_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(
        _stage_lambdas(result, "5", "phase_one_reference_activity"),
        [1.0],
        atol=TARGET_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(
        _target_values(result, "1", "target"),
        [9 - root_30, root_30 - 3, root_30 + 3, 15 - root_30],
        atol=TARGET_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(
        _target_values(result, "5", "target"),
        [4.0, 2.0, 8.0, 10.0],
        atol=TARGET_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(
        _slack_values(result, "1"),
        [
            (8 * root_30 - 42) / 3,
            0.0,
            0.0,
            (93 - 11 * root_30) / 7,
        ],
        atol=TARGET_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(
        _slack_values(result, "5"),
        [1 / 5, 17 / 5, 3.0, 0.0],
        atol=TARGET_ATOL,
        rtol=0,
    )
    assert result.metadata["solver_strategy"] == ("monotone_lp_feasibility_bisection")


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
@pytest.mark.parametrize(
    ("alpha", "orientation"),
    [(0.0, "input"), (1.0, "output")],
)
def test_alpha_endpoints_are_exact_radial_equivalents(
    returns_to_scale: str,
    alpha: float,
    orientation: str,
) -> None:
    data = _five_dmu_data()
    gdf = GDF(
        alpha=alpha,
        returns_to_scale=returns_to_scale,
        compute_slacks=False,
    ).fit(data)
    radial = RadialDEA(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        compute_slacks=False,
    ).fit(data)
    gdf_summary = gdf.summary().set_index("dmu_id")
    radial_summary = radial.summary().set_index("dmu_id")

    np.testing.assert_allclose(
        gdf_summary.loc[_DMUS, "score"],
        radial_summary.loc[_DMUS, "efficiency"],
        atol=1e-9,
        rtol=0,
    )
    if alpha == 0.0:
        np.testing.assert_allclose(
            gdf_summary.loc[_DMUS, "resource_commitment"],
            gdf_summary.loc[_DMUS, "score"],
        )
        np.testing.assert_allclose(
            gdf_summary.loc[_DMUS, "service_commitment"],
            1.0,
        )
    else:
        np.testing.assert_allclose(
            gdf_summary.loc[_DMUS, "resource_commitment"],
            1.0,
        )
        np.testing.assert_allclose(
            gdf_summary.loc[_DMUS, "service_commitment"],
            radial_summary.loc[_DMUS, "score"],
        )


def test_crs_score_is_independent_of_alpha() -> None:
    data = _five_dmu_data()
    expected = RadialDEA(
        orientation="input",
        returns_to_scale="crs",
        compute_slacks=False,
    ).fit(data)
    expected_score = expected.summary().set_index("dmu_id").loc[_DMUS, "efficiency"]

    for alpha in (0.0, 0.2, 0.5, 0.83, 1.0):
        observed = GDF(
            alpha=alpha,
            returns_to_scale="crs",
            compute_slacks=False,
        ).fit(data)
        np.testing.assert_allclose(
            observed.summary().set_index("dmu_id").loc[_DMUS, "score"],
            expected_score,
            atol=1e-9,
            rtol=0,
        )


def test_path_phase_one_activity_and_slack_completed_target_are_not_conflated() -> None:
    result = GDF(alpha=0.5, returns_to_scale="vrs").fit(_five_dmu_data())
    dmu_1 = result.targets.query("dmu_id == '1'").set_index(["role", "variable"])

    assert {
        "path_target",
        "phase_one_reference_activity",
        "target",
    }.issubset(dmu_1.columns)
    assert dmu_1.loc[("output", "y2"), "path_target"] != pytest.approx(
        dmu_1.loc[("output", "y2"), "phase_one_reference_activity"],
        abs=1e-3,
    )
    np.testing.assert_allclose(
        dmu_1["phase_one_reference_activity"],
        dmu_1["target"],
        atol=TARGET_ATOL,
        rtol=0,
    )

    stages = set(result.intensities["stage"])
    assert stages == {
        "phase_one_reference_activity",
        "slack_completed_target",
    }
    phase_one = _stage_lambdas(result, "1", "phase_one_reference_activity")
    phase_two = _stage_lambdas(result, "1", "slack_completed_target")
    assert phase_one is not phase_two
    assert set(phase_one.index) == {"2", "3"}
    assert set(phase_two.index) == {"2", "3"}
    assert result.metadata["target_stages"] == {
        "path_target": "algebraic_performance_contract",
        "phase_one_reference_activity": ("feasible_peer_activity_from_score_stage"),
        "target": "row_scaled_slack_completed_peer_activity",
    }


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_zero_components_are_allowed_when_each_row_has_positive_totals(
    returns_to_scale: str,
) -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "x1": [1.0, 0.0, 1.0],
                "x2": [0.0, 1.0, 1.0],
                "y1": [1.0, 0.0, 1.0],
                "y2": [0.0, 1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )

    result = GDF(
        alpha=0.5,
        returns_to_scale=returns_to_scale,
        compute_slacks=False,
    ).fit(data)

    np.testing.assert_allclose(result.summary()["score"], 1.0, atol=SCORE_ATOL)
    assert set(result.summary()["solver_status"]) == {"optimal"}


@pytest.mark.parametrize(
    ("role", "frame", "message"),
    [
        (
            "input",
            pd.DataFrame({"dmu": ["A"], "x1": [0.0], "x2": [0.0], "y": [1.0]}),
            "strictly positive input",
        ),
        (
            "output",
            pd.DataFrame({"dmu": ["A"], "x": [1.0], "y1": [0.0], "y2": [0.0]}),
            "strictly positive output",
        ),
    ],
)
def test_zero_aggregate_resource_or_service_rows_are_rejected(
    role: str,
    frame: pd.DataFrame,
    message: str,
) -> None:
    inputs = ["x1", "x2"] if role == "input" else "x"
    outputs = "y" if role == "input" else ["y1", "y2"]
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=inputs,
        outputs=outputs,
    )

    with pytest.raises(DataValidationError, match=message):
        GDF().fit(data)


@pytest.mark.parametrize(
    ("alpha", "error"),
    [
        (True, TypeError),
        ("0.5", TypeError),
        (math.nan, ValueError),
        (math.inf, ValueError),
        (-1e-12, ValueError),
        (1.0 + 1e-12, ValueError),
    ],
)
def test_alpha_validation_is_closed_interval_and_finite(
    alpha: object,
    error: type[Exception],
) -> None:
    with pytest.raises(error, match="alpha"):
        GeneralizedDistanceDEA(alpha=alpha)


@pytest.mark.parametrize("returns_to_scale", ["nirs", "ndrs"])
def test_restricted_returns_are_rejected_until_they_have_a_separate_derivation(
    returns_to_scale: str,
) -> None:
    with pytest.raises(ModelSpecificationError, match="only CRS and VRS"):
        GeneralizedDistanceDEA(returns_to_scale=returns_to_scale)


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"tolerance": math.nan}, ValueError),
        ({"tolerance": math.inf}, ValueError),
        ({"peer_tolerance": 0.0}, ValueError),
        ({"search_tolerance": -1.0}, ValueError),
        ({"max_search_iterations": 1.5}, TypeError),
        ({"max_bracket_expansions": 0}, ValueError),
    ],
)
def test_numerical_controls_require_finite_positive_values(
    kwargs: dict[str, object],
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        GeneralizedDistanceDEA(**kwargs)


def test_nonfinite_data_and_bad_outputs_are_rejected() -> None:
    nonfinite = pd.DataFrame({"dmu": ["A"], "x": [math.inf], "y": [1.0]})
    with pytest.raises(DataValidationError, match="input values must be finite"):
        DEAData.from_frame(
            nonfinite,
            dmu="dmu",
            inputs="x",
            outputs="y",
        )

    with_bad_output = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0], "bad": [0.1]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="bad",
    )
    with pytest.raises(ModelSpecificationError, match="desirable outputs only"):
        GDF().fit(with_bad_output)


def test_external_reference_retains_delta_above_one_with_nullable_flags() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "x": [2.0, 1.0],
                "y": [2.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    result = GDF(
        alpha=0.5,
        returns_to_scale="vrs",
        reference=ReferenceSpec("custom", custom_rows=[0]),
    ).fit(data)
    evaluated = result.summary().set_index("dmu_id").loc["evaluated"]

    assert evaluated["score"] == pytest.approx(4.0, abs=SCORE_ATOL)
    assert evaluated["generalized_distance"] == pytest.approx(
        4.0,
        abs=SCORE_ATOL,
    )
    assert evaluated["score_status"] == "outside_reference_technology"
    assert not bool(evaluated["is_within_reference_technology"])
    assert pd.isna(evaluated["is_gdf_efficient"])
    assert pd.isna(evaluated["is_efficient"])
    assert set(result.peers("evaluated")["reference_dmu_id"]) == {"reference"}


def test_structurally_unattainable_external_output_fails_closed() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "x1": [1.0, 1.0],
                "x2": [1.0, 1.0],
                "y1": [1.0, 0.0],
                "y2": [0.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )
    result = GDF(
        alpha=0.5,
        returns_to_scale="vrs",
        reference=ReferenceSpec("custom", custom_rows=[0]),
        max_bracket_expansions=8,
        compute_slacks=False,
    ).fit(data)
    evaluated = result.summary().set_index("dmu_id").loc["evaluated"]

    assert pd.isna(evaluated["score"])
    assert evaluated["score_status"] == "unattainable_path"
    assert not bool(evaluated["is_within_reference_technology"])
    assert pd.isna(evaluated["is_gdf_efficient"])
    assert pd.isna(evaluated["is_efficient"])
    assert evaluated["feasibility_solves"] == 0
    diagnostic = result.diagnostics.query("dmu_id == 'evaluated'").iloc[0]
    assert diagnostic["solver_strategy"] == "structural_support_precheck"
    assert result.peers("evaluated").empty
    assert result.targets_for("evaluated").empty


def test_phase_two_failure_preserves_phase_one_score_and_peers() -> None:
    data = _five_dmu_data()
    expected = GDF(
        alpha=0.5,
        returns_to_scale="crs",
        compute_slacks=False,
    ).fit(data)
    result = GDF(
        alpha=0.5,
        returns_to_scale="crs",
        solver=_FailingPhaseTwoSolver(),
    ).fit(data)
    summary = result.summary().set_index("dmu_id")

    np.testing.assert_allclose(
        summary.loc[_DMUS, "score"],
        expected.summary().set_index("dmu_id").loc[_DMUS, "score"],
    )
    assert set(summary["solver_status"]) == {"optimal"}
    assert set(summary["target_status"]) == {"failed:limit_reached"}
    assert result.targets["target"].isna().all()
    assert result.slacks["slack"].isna().all()
    assert set(result.intensities["stage"]) == {"phase_one_reference_activity"}
    assert set(result.diagnostics["phase"]) == {1, 2}
    assert set(result.diagnostics.query("phase == 2")["solver_status"]) == {
        "limit_reached"
    }


def test_phase_one_solver_failure_is_not_misclassified_as_inefficiency() -> None:
    result = GDF(
        alpha=0.5,
        returns_to_scale="vrs",
        solver=_AlwaysFailingSolver(),
    ).fit(_five_dmu_data())
    summary = result.summary()

    assert summary["score"].isna().all()
    assert set(summary["solver_status"]) == {"limit_reached"}
    assert set(summary["score_status"]) == {"feasibility_solver_failed"}
    assert summary["is_within_reference_technology"].isna().all()
    assert summary["is_gdf_efficient"].isna().all()
    assert summary["is_efficient"].isna().all()
    assert result.targets.empty
    assert result.slacks.empty
    assert result.intensities.empty
    assert set(result.diagnostics["phase"]) == {1}


def test_metadata_is_json_safe_and_discloses_score_and_target_semantics() -> None:
    result = GDF(alpha=0.5, returns_to_scale="vrs").fit(_five_dmu_data())
    metadata = dict(result.metadata)

    json.dumps(metadata, allow_nan=False)
    assert metadata["method_id"] == "static.generalized_distance.chavas_cox"
    assert metadata["native_score"] == "delta"
    assert metadata["efficiency_transform"] == "identity"
    assert metadata["exact_endpoint_equivalences"] == {
        "alpha_0": "input_radial_theta",
        "alpha_1": "reciprocal_output_radial_phi",
    }
    assert metadata["conditional_standard_hyperbolic_relation_at_alpha_half"] == {
        "relation": (
            "delta_equals_h_squared_only_for_a_matched_source_native_reciprocal_path"
        ),
        "public_leaf": "deferred_to_next_version",
    }
    assert "hyperbolic_relation_at_alpha_half" not in metadata
    assert metadata["slack_target_unit_invariant"] is True
    assert metadata["duals_available"] is False
    assert result.duals.empty


def test_scores_and_path_targets_respect_quantity_unit_changes() -> None:
    input_scales = (100.0, 0.1)
    output_scales = (10.0, 0.01)
    baseline = GDF(
        alpha=0.37,
        returns_to_scale="vrs",
        compute_slacks=False,
    ).fit(_five_dmu_data())
    converted = GDF(
        alpha=0.37,
        returns_to_scale="vrs",
        compute_slacks=False,
    ).fit(
        _five_dmu_data(
            input_scales=input_scales,
            output_scales=output_scales,
        )
    )

    np.testing.assert_allclose(
        converted.summary()["score"],
        baseline.summary()["score"],
        atol=SCORE_ATOL,
        rtol=0,
    )
    scale_by_variable = {
        ("input", "x1"): input_scales[0],
        ("input", "x2"): input_scales[1],
        ("output", "y1"): output_scales[0],
        ("output", "y2"): output_scales[1],
    }
    joined = baseline.targets.merge(
        converted.targets,
        on=["dmu_id", "period", "role", "variable"],
        suffixes=("_base", "_converted"),
    )
    expected_converted = np.asarray(
        [
            row.path_target_base * scale_by_variable[(row.role, row.variable)]
            for row in joined.itertuples()
        ]
    )
    np.testing.assert_allclose(
        joined["path_target_converted"],
        expected_converted,
        atol=2e-5,
        rtol=5e-7,
    )


def test_row_scaled_slack_completion_preserves_strong_efficiency_under_units() -> None:
    results = []
    for scale in (1.0, 1e-12):
        data = DEAData.from_frame(
            pd.DataFrame(
                {
                    "dmu": ["A", "B"],
                    "x": [1.0, 1.0],
                    "y1": [1.0, 1.0],
                    "y2": [scale, 2.0 * scale],
                }
            ),
            dmu="dmu",
            inputs="x",
            outputs=["y1", "y2"],
        )
        results.append(GDF(alpha=0.5, returns_to_scale="vrs").fit(data))

    for result, scale in zip(results, (1.0, 1e-12), strict=True):
        evaluated = result.summary().set_index("dmu_id").loc["A"]
        assert evaluated["score"] == pytest.approx(1.0, abs=SCORE_ATOL)
        assert bool(evaluated["is_gdf_efficient"])
        assert not bool(evaluated["is_efficient"])
        assert evaluated["max_scaled_slack"] == pytest.approx(0.5)
        y2_target = result.targets.query(
            "dmu_id == 'A' and role == 'output' and variable == 'y2'"
        ).iloc[0]
        assert y2_target["target"] == pytest.approx(2.0 * scale)


def test_explicit_empty_solver_options_inherit_gdf_numerical_defaults() -> None:
    data = _five_dmu_data()
    implicit = GDF(alpha=0.37, returns_to_scale="vrs").fit(data)
    explicit = GDF(
        alpha=0.37,
        returns_to_scale="vrs",
        solver_options=SolverOptions(),
    ).fit(data)

    np.testing.assert_allclose(
        explicit.summary()["score"],
        implicit.summary()["score"],
        atol=1e-12,
        rtol=0,
    )
    assert (
        explicit.metadata["solver_primal_feasibility_tolerance"]
        == implicit.metadata["solver_primal_feasibility_tolerance"]
        == 1e-8
    )
    assert (
        explicit.metadata["solver_dual_feasibility_tolerance"]
        == implicit.metadata["solver_dual_feasibility_tolerance"]
        == 1e-8
    )


def test_scores_are_invariant_to_observation_row_order() -> None:
    baseline = GDF(
        alpha=0.37,
        returns_to_scale="vrs",
        compute_slacks=False,
    ).fit(_five_dmu_data())
    permuted = GDF(
        alpha=0.37,
        returns_to_scale="vrs",
        compute_slacks=False,
    ).fit(_five_dmu_data(order=np.array([3, 0, 4, 1, 2])))

    baseline_score = baseline.summary().set_index("dmu_id")["score"].sort_index()
    permuted_score = permuted.summary().set_index("dmu_id")["score"].sort_index()
    np.testing.assert_allclose(
        permuted_score,
        baseline_score,
        atol=SCORE_ATOL,
        rtol=0,
    )
