from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from deapack import DEAData
from deapack.analysis.hicks_moorsteen import (
    HicksMoorsteenDEA,
    HicksMoorsteenProductivityIndex,
    MoorsteenBjurekDEA,
    MoorsteenBjurekProductivityIndex,
)
from deapack.enums import SolverStatus
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LinearProgram, LPSolution
from deapack.specs import SolverOptions


def _data(
    frame: pd.DataFrame,
    *,
    inputs: str | list[str] = "x",
    outputs: str | list[str] = "y",
    bad_outputs: str | None = None,
    period_order: list[object] | None = None,
) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        period_order=period_order,
        inputs=inputs,
        outputs=outputs,
        bad_outputs=bad_outputs,
    )


def _analytic_panel() -> DEAData:
    return _data(
        pd.DataFrame(
            {
                "dmu": ["A", "A"],
                "period": [0, 1],
                "x": [2.0, 1.0],
                "y": [3.0, 6.0],
            }
        )
    )


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_single_input_output_oracle_and_all_source_distances(
    returns_to_scale: str,
) -> None:
    result = HicksMoorsteenProductivityIndex(returns_to_scale=returns_to_scale).fit(
        _analytic_panel()
    )
    row = result.summary().iloc[0]

    assert row["output_quantity_index_s"] == pytest.approx(2.0)
    assert row["output_quantity_index_t"] == pytest.approx(2.0)
    assert row["output_quantity_index"] == pytest.approx(2.0)
    assert row["input_quantity_index_s"] == pytest.approx(0.5)
    assert row["input_quantity_index_t"] == pytest.approx(0.5)
    assert row["input_quantity_index"] == pytest.approx(0.5)
    assert row["productivity_change"] == pytest.approx(4.0)
    assert row["score"] == pytest.approx(4.0)

    expected_distances = {
        "distance_output_s_xs_ys": 1.0,
        "distance_output_s_xs_yt": 2.0,
        "distance_output_t_xt_ys": 0.5,
        "distance_output_t_xt_yt": 1.0,
        "distance_input_s_xs_ys": 1.0,
        "distance_input_s_xt_ys": 0.5,
        "distance_input_t_xs_yt": 2.0,
        "distance_input_t_xt_yt": 1.0,
    }
    for column, expected in expected_distances.items():
        assert row[column] == pytest.approx(expected)


def test_registry_quantity_components_and_api_placement_match_runtime() -> None:
    registry_path = (
        Path(__file__).resolve().parents[1]
        / "specs"
        / "registry"
        / "methods"
        / "productivity"
        / "productivity.hicks_moorsteen.bjurek_1996.json"
    )
    record = json.loads(registry_path.read_text(encoding="utf-8"))
    runtime_columns = set(HicksMoorsteenDEA().fit(_analytic_panel()).summary().columns)
    side_quantity_fields = {
        "output_quantity_index_s",
        "output_quantity_index_t",
        "input_quantity_index_s",
        "input_quantity_index_t",
    }
    complete_quantity_fields = side_quantity_fields | {
        "output_quantity_index",
        "input_quantity_index",
    }
    legacy_fields = {
        "base_reference_output_quantity_index",
        "comparison_reference_output_quantity_index",
        "base_reference_input_quantity_index",
        "comparison_reference_input_quantity_index",
    }
    result_components = set(record["result_contract"]["components"])
    exact_claim = next(
        claim
        for claim in record["validation"]["oracle"]["analytical_certificate"]["claims"]
        if claim["claim_id"].endswith("exact_bilateral_quantity_account")
    )
    oracle_components = set(exact_claim["result_components"])

    assert complete_quantity_fields <= runtime_columns
    assert complete_quantity_fields <= result_components
    assert complete_quantity_fields <= oracle_components
    assert legacy_fields.isdisjoint(runtime_columns)
    assert legacy_fields.isdisjoint(result_components)
    assert legacy_fields.isdisjoint(oracle_components)
    assert {
        placement["doc_id"]: (placement["path"], placement["role"])
        for placement in record["placement"]["docs"]
        if placement["state"] == "present"
    } == {
        "docs.analysis.hicks_moorsteen": (
            "docs/analysis/hicks-moorsteen.md",
            "analysis",
        ),
        "docs.api.analysis": ("docs/api/analysis.md", "api"),
    }


def test_positive_radial_factor_below_solver_tolerance_remains_in_domain() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "A"],
                "period": [0, 1],
                "x": [1.0, 1e-8],
                "y": [1.0, 1.0],
            }
        )
    )
    row = (
        HicksMoorsteenDEA(
            returns_to_scale="crs",
            tolerance=1e-7,
        )
        .fit(data)
        .summary()
        .iloc[0]
    )

    assert bool(row["score_valid"])
    assert row["solver_status"] == "optimal"
    assert row["distance_input_t_xs_yt"] == pytest.approx(1e8)
    assert row["productivity_change"] == pytest.approx(1e8)


@pytest.mark.parametrize("magnitude", [1e10, 1e12])
def test_extreme_independent_quantity_units_preserve_hicks_moorsteen_account(
    magnitude: float,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["D", "Z", "D", "Z"],
            "period": [0, 0, 1, 1],
            "x1": [5.0, 20.0, 6.0, 24.0],
            "x2": [4.0, 20.0, 6.0, 24.0],
            "y1": [4.0, 1.0, 6.0, 1.0],
            "y2": [6.0, 1.0, 15.0, 1.0],
        }
    )
    scaled = frame.assign(
        x1=frame["x1"] * magnitude,
        x2=frame["x2"] / magnitude,
        y1=frame["y1"] / magnitude,
        y2=frame["y2"] * magnitude,
    )
    model = HicksMoorsteenDEA(returns_to_scale="vrs")
    baseline = (
        model.fit(_data(frame, inputs=["x1", "x2"], outputs=["y1", "y2"]))
        .summary()
        .sort_values("dmu_id")
    )
    rescaled = (
        model.fit(_data(scaled, inputs=["x1", "x2"], outputs=["y1", "y2"]))
        .summary()
        .sort_values("dmu_id")
    )
    fields = [
        "productivity_change",
        "output_quantity_index",
        "input_quantity_index",
        *(
            (f"distance_{role}")
            for role in (
                "output_s_xs_ys",
                "output_s_xs_yt",
                "output_t_xt_ys",
                "output_t_xt_yt",
                "input_s_xs_ys",
                "input_s_xt_ys",
                "input_t_xs_yt",
                "input_t_xt_yt",
            )
        ),
    ]
    assert baseline["score_valid"].all()
    assert rescaled["score_valid"].all()
    np.testing.assert_allclose(
        rescaled[fields],
        baseline[fields],
        atol=1e-10,
        rtol=1e-10,
    )


def test_public_api_matches_exact_bjurek_two_input_two_output_account() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["D", "Z", "D", "Z"],
            "period": [0, 0, 1, 1],
            "x1": [5.0, 20.0, 6.0, 24.0],
            "x2": [4.0, 20.0, 6.0, 24.0],
            "y1": [4.0, 1.0, 6.0, 1.0],
            "y2": [6.0, 1.0, 15.0, 1.0],
        }
    )
    result = HicksMoorsteenDEA(returns_to_scale="vrs").fit(
        _data(frame, inputs=["x1", "x2"], outputs=["y1", "y2"])
    )
    row = result.summary().set_index("dmu_id").loc["D"]

    expected_distances = {
        "distance_output_s_xs_ys": 1.0,
        "distance_output_s_xs_yt": 5 / 2,
        "distance_output_t_xt_ys": 2 / 3,
        "distance_output_t_xt_yt": 1.0,
        "distance_input_s_xs_ys": 1.0,
        "distance_input_s_xt_ys": 6 / 5,
        "distance_input_t_xs_yt": 2 / 3,
        "distance_input_t_xt_yt": 1.0,
    }
    for column, expected in expected_distances.items():
        assert row[column] == pytest.approx(expected, abs=1e-12)

    assert row["output_quantity_index"] == pytest.approx(
        np.sqrt(15) / 2,
        abs=1e-12,
    )
    assert row["input_quantity_index"] == pytest.approx(
        3 / np.sqrt(5),
        abs=1e-12,
    )
    assert row["productivity_change"] == pytest.approx(
        5 * np.sqrt(3) / 6,
        abs=1e-12,
    )


def test_named_classes_are_exact_historical_aliases() -> None:
    assert HicksMoorsteenDEA is HicksMoorsteenProductivityIndex
    assert MoorsteenBjurekDEA is HicksMoorsteenProductivityIndex
    assert MoorsteenBjurekProductivityIndex is HicksMoorsteenProductivityIndex


def test_quantity_indexes_reconstruct_from_eight_shephard_distances() -> None:
    result = HicksMoorsteenDEA().fit(_analytic_panel())
    row = result.summary().iloc[0]

    output_s = row["distance_output_s_xs_yt"] / row["distance_output_s_xs_ys"]
    output_t = row["distance_output_t_xt_yt"] / row["distance_output_t_xt_ys"]
    input_s = row["distance_input_s_xt_ys"] / row["distance_input_s_xs_ys"]
    input_t = row["distance_input_t_xt_yt"] / row["distance_input_t_xs_yt"]
    expected_output = np.sqrt(output_s * output_t)
    expected_input = np.sqrt(input_s * input_t)

    assert row["output_quantity_index"] == pytest.approx(expected_output)
    assert row["input_quantity_index"] == pytest.approx(expected_input)
    assert row["productivity_change"] == pytest.approx(expected_output / expected_input)
    assert abs(row["identity_residual"]) <= 1e-14
    assert row["reconstruction_residual"] == row["identity_residual"]


def test_diagnostics_and_intensities_retain_all_eight_distance_systems() -> None:
    result = HicksMoorsteenDEA().fit(_analytic_panel())
    roles = {
        "output_s_xs_ys",
        "output_s_xs_yt",
        "output_t_xt_ys",
        "output_t_xt_yt",
        "input_s_xs_ys",
        "input_s_xt_ys",
        "input_t_xs_yt",
        "input_t_xt_yt",
    }

    assert len(result.diagnostics) == 8
    assert set(result.diagnostics["distance_role"]) == roles
    assert set(result.diagnostics["orientation"]) == {"input", "output"}
    assert (result.diagnostics["solver_status"] == "optimal").all()
    np.testing.assert_allclose(
        result.diagnostics["shephard_distance"] * result.diagnostics["radial_factor"],
        1.0,
        atol=1e-12,
        rtol=0,
    )

    assert len(result.intensities) == 8
    assert set(result.intensities["distance_role"]) == roles
    assert set(result.intensities["reference_dmu_id"]) == {"A"}
    np.testing.assert_allclose(result.intensities["lambda"], 1.0)


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_invariance_to_input_and_output_units(returns_to_scale: str) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x1": [2.0, 3.0, 1.8, 2.8],
            "x2": [4.0, 2.0, 3.5, 1.9],
            "y1": [3.0, 2.0, 3.6, 2.4],
            "y2": [1.0, 4.0, 1.2, 4.8],
        }
    )
    original = _data(frame, inputs=["x1", "x2"], outputs=["y1", "y2"])
    rescaled_frame = frame.copy()
    rescaled_frame["x1"] *= 10.0
    rescaled_frame["x2"] *= 0.1
    rescaled_frame["y1"] *= 0.2
    rescaled_frame["y2"] *= 50.0
    rescaled = _data(
        rescaled_frame,
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )
    model = HicksMoorsteenDEA(returns_to_scale=returns_to_scale)
    baseline = model.fit(original).summary().sort_values("dmu_id")
    changed_units = model.fit(rescaled).summary().sort_values("dmu_id")

    columns = [
        "productivity_change",
        "output_quantity_index",
        "input_quantity_index",
        *[
            column
            for column in baseline.columns
            if column.startswith("distance_output_")
            or column.startswith("distance_input_")
        ],
    ]
    np.testing.assert_allclose(
        baseline[columns],
        changed_units[columns],
        atol=1e-9,
        rtol=1e-9,
    )


def test_reversing_the_bilateral_comparison_gives_the_reciprocal() -> None:
    data_forward = _analytic_panel()
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "period": [0, 1],
            "x": [2.0, 1.0],
            "y": [3.0, 6.0],
        }
    )
    data_reverse = _data(frame, period_order=[1, 0])
    forward = HicksMoorsteenDEA().fit(data_forward).summary().iloc[0]
    reverse = HicksMoorsteenDEA().fit(data_reverse).summary().iloc[0]

    assert reverse["productivity_change"] == pytest.approx(
        1.0 / forward["productivity_change"]
    )
    assert reverse["output_quantity_index"] == pytest.approx(
        1.0 / forward["output_quantity_index"]
    )
    assert reverse["input_quantity_index"] == pytest.approx(
        1.0 / forward["input_quantity_index"]
    )


def test_panel_matching_uses_ids_and_declared_period_order() -> None:
    ordered = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": ["FY20", "FY20", "FY22", "FY22"],
            "x": [2.0, 3.0, 1.0, 2.4],
            "y": [3.0, 2.0, 5.0, 2.5],
        }
    )
    shuffled = ordered.iloc[[3, 0, 2, 1]].reset_index(drop=True)
    period_order = ["FY20", "FY22"]
    expected = (
        HicksMoorsteenDEA()
        .fit(_data(ordered, period_order=period_order))
        .summary()
        .sort_values("dmu_id")
        .reset_index(drop=True)
    )
    actual = (
        HicksMoorsteenDEA()
        .fit(_data(shuffled, period_order=period_order))
        .summary()
        .sort_values("dmu_id")
        .reset_index(drop=True)
    )

    assert actual[["dmu_id", "base_period", "comparison_period"]].equals(
        expected[["dmu_id", "base_period", "comparison_period"]]
    )
    np.testing.assert_allclose(
        actual[
            [
                "productivity_change",
                "output_quantity_index",
                "input_quantity_index",
            ]
        ],
        expected[
            [
                "productivity_change",
                "output_quantity_index",
                "input_quantity_index",
            ]
        ],
        atol=1e-10,
        rtol=1e-10,
    )


def test_unbalanced_adjacent_panel_policy_is_explicit() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "A", "B", "D"],
            "period": [0, 0, 0, 1, 1, 1],
            "x": [1.0, 2.0, 3.0, 0.9, 1.8, 4.0],
            "y": [1.0, 2.0, 3.0, 1.2, 2.4, 4.4],
        }
    )
    data = _data(frame)
    result = HicksMoorsteenDEA(unbalanced="drop").fit(data)

    assert set(result.summary()["dmu_id"]) == {"A", "B"}
    assert result.metadata["unmatched_adjacent_periods"] == (
        {
            "base_period": 0,
            "comparison_period": 1,
            "base_only": ("C",),
            "comparison_only": ("D",),
        },
    )
    with pytest.raises(DataValidationError, match="unbalanced adjacent periods"):
        HicksMoorsteenDEA(unbalanced="raise").fit(data)


class _FailingSolver:
    name = "test-failing-solver"

    def solve(self, problem: LinearProgram) -> LPSolution:
        del problem
        return LPSolution(
            status=SolverStatus.INFEASIBLE,
            objective=None,
            primal=None,
            message="intentional test failure",
            iterations=0,
        )


def test_solver_failures_are_retained_by_distance_role() -> None:
    result = HicksMoorsteenDEA(solver=_FailingSolver()).fit(_analytic_panel())
    row = result.summary().iloc[0]

    assert row["solver_status"] == "infeasible"
    assert np.isnan(row["productivity_change"])
    assert row["failed_distance_count"] == 8
    assert set(row["failed_distance_roles"].split("|")) == set(
        result.diagnostics["distance_role"]
    )
    assert (result.diagnostics["solver_status"] == "infeasible").all()
    assert set(result.diagnostics["message"]) == {"intentional test failure"}
    assert result.intensities.empty


def test_nonpositive_component_distance_becomes_a_reported_numerical_failure() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "period": [0, 1],
            "x": [1.0, 1.0],
            "y1": [1.0, 0.0],
            "y2": [0.0, 1.0],
        }
    )
    result = HicksMoorsteenDEA().fit(_data(frame, outputs=["y1", "y2"]))
    row = result.summary().iloc[0]

    assert row["solver_status"] == "numerical_error"
    assert np.isnan(row["productivity_change"])
    failed = result.diagnostics.query("solver_status == 'numerical_error'")
    assert set(failed["distance_role"]) == {
        "output_s_xs_yt",
        "output_t_xt_ys",
    }


def test_result_contract_states_complete_tfp_without_extra_decomposition() -> None:
    result = HicksMoorsteenDEA().fit(_analytic_panel())
    summary = result.summary()

    assert result.metadata["method_id"] == ("productivity.hicks_moorsteen.bjurek_1996")
    assert result.metadata["preset_id"] == ("productivity.hicks_moorsteen.bjurek_1996")
    assert result.metadata["returns_to_scale"] == "vrs"
    assert result.metadata["score_direction"] == ("greater_than_one_is_improvement")
    assert result.metadata["scale_mix_decomposition"] == "not_claimed"
    assert result.metadata["transitivity"] == (
        "not_claimed_for_chained_bilateral_indexes"
    )
    assert "efficiency_change" not in summary
    assert "technical_change" not in summary
    assert "scale_efficiency_change" not in summary
    assert "mix_efficiency_change" not in summary


def test_requires_a_desirable_output_panel() -> None:
    cross_section = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A", "B"], "x": [1.0, 2.0], "y": [1.0, 2.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(ModelSpecificationError, match="requires panel data"):
        HicksMoorsteenDEA().fit(cross_section)

    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "period": [0, 1],
            "x": [1.0, 1.0],
            "y": [1.0, 1.1],
            "b": [1.0, 0.9],
        }
    )
    with pytest.raises(ModelSpecificationError, match="desirable outputs only"):
        HicksMoorsteenDEA().fit(_data(frame, bad_outputs="b"))


@pytest.mark.parametrize(
    ("field", "values", "message"),
    [
        ("x", [0.0, 0.0], "strictly positive input"),
        ("y", [0.0, 0.0], "strictly positive output"),
        ("x", [-1.0, 1.0], "nonnegative input"),
        ("y", [-1.0, 1.0], "nonnegative output"),
    ],
)
def test_quantity_domain_boundaries(
    field: str,
    values: list[float],
    message: str,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "period": [0, 1],
            "x": [1.0, 1.0],
            "y": [1.0, 1.0],
        }
    )
    frame[field] = values
    with pytest.raises(DataValidationError, match=message):
        HicksMoorsteenDEA().fit(_data(frame))


def test_configuration_boundaries_are_explicit() -> None:
    with pytest.raises(ValueError, match=r"only.*'crs' or 'vrs'"):
        HicksMoorsteenDEA(returns_to_scale="nirs")
    with pytest.raises(ValueError, match=r"only.*'crs' or 'vrs'"):
        HicksMoorsteenDEA(returns_to_scale="ndrs")
    with pytest.raises(ValueError, match="unbalanced"):
        HicksMoorsteenDEA(unbalanced="ignore")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="pass solver or solver_options"):
        HicksMoorsteenDEA(
            solver=_FailingSolver(),
            solver_options=SolverOptions(),
        )
    with pytest.raises(ValueError, match="tolerance must be positive"):
        HicksMoorsteenDEA(tolerance=0)
    for invalid in (np.nan, np.inf):
        with pytest.raises(ValueError, match="tolerance must be positive and finite"):
            HicksMoorsteenDEA(tolerance=invalid)
    with pytest.raises(ValueError, match="peer_tolerance must be positive"):
        HicksMoorsteenDEA(peer_tolerance=0)
    for invalid in (np.nan, np.inf):
        with pytest.raises(
            ValueError,
            match="peer_tolerance must be positive and finite",
        ):
            HicksMoorsteenDEA(peer_tolerance=invalid)
