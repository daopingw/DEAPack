from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import ChungFareGrosskopfDDF, DEAData, DEAResult, ReferenceSpec


def _analytical_data(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
    bad_output_scale: float = 1.0,
) -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "organization": ["Old", "New"],
                "resource": np.asarray([1.0, 1.0]) * input_scale,
                "service": np.asarray([1.0, 2.0]) * output_scale,
                "residual": np.asarray([2.0, 1.0]) * bad_output_scale,
            }
        ),
        dmu="organization",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )


def _dense_cfg_distances(
    data: DEAData,
    *,
    reference_rows: Sequence[int],
) -> np.ndarray:
    """Compile the fixed-input CFG programme without production helpers."""
    if data.bad_outputs is None:
        raise AssertionError("the analytical fixture must declare bad outputs")

    rows = np.asarray(reference_rows, dtype=np.int64)
    reference_inputs = data.inputs[rows]
    reference_outputs = data.outputs[rows]
    reference_bad_outputs = data.bad_outputs[rows]
    n_lambda = rows.size
    n_variables = n_lambda + 1
    distances = np.empty(data.n_dmus, dtype=np.float64)

    for observation in range(data.n_dmus):
        objective = np.zeros(n_variables, dtype=np.float64)
        objective[-1] = -1.0

        input_rows = np.zeros(
            (data.n_inputs, n_variables),
            dtype=np.float64,
        )
        input_rows[:, :n_lambda] = reference_inputs.T

        output_rows = np.zeros(
            (data.n_outputs, n_variables),
            dtype=np.float64,
        )
        output_rows[:, :n_lambda] = -reference_outputs.T
        output_rows[:, -1] = data.outputs[observation]

        bad_output_rows = np.zeros(
            (data.n_bad_outputs, n_variables),
            dtype=np.float64,
        )
        bad_output_rows[:, :n_lambda] = reference_bad_outputs.T
        bad_output_rows[:, -1] = data.bad_outputs[observation]

        solution = linprog(
            objective,
            A_ub=np.vstack([input_rows, output_rows]),
            b_ub=np.concatenate(
                [
                    data.inputs[observation],
                    -data.outputs[observation],
                ]
            ),
            A_eq=bad_output_rows,
            b_eq=data.bad_outputs[observation],
            bounds=[(0.0, None)] * n_lambda + [(None, None)],
            method="highs",
        )
        assert solution.success, solution.message
        distances[observation] = float(solution.x[-1])

    return distances


def _distance_vector(result: DEAResult) -> np.ndarray:
    return (
        result.summary().set_index("dmu_id").loc[["Old", "New"], "distance"].to_numpy()
    )


def test_exact_pooled_cfg_distances_and_management_targets() -> None:
    result = ChungFareGrosskopfDDF().fit(_analytical_data())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["Old", "distance"] == pytest.approx(float(Fraction(3, 5)))
    assert summary.loc["New", "distance"] == pytest.approx(0.0)
    assert summary.loc["Old", "efficiency"] == pytest.approx(float(Fraction(5, 8)))
    assert summary.loc["New", "efficiency"] == pytest.approx(1.0)
    assert not bool(summary.loc["Old", "is_directionally_efficient"])
    assert bool(summary.loc["New", "is_directionally_efficient"])
    assert not bool(summary.loc["Old", "is_efficient"])
    assert pd.isna(summary.loc["New", "is_efficient"])

    targets = result.targets_for("Old").set_index(["role", "variable"])
    assert targets.loc[("input", "resource"), "target"] == pytest.approx(
        float(Fraction(4, 5))
    )
    assert targets.loc[("output", "service"), "target"] == pytest.approx(
        float(Fraction(8, 5))
    )
    assert targets.loc[("bad_output", "residual"), "target"] == pytest.approx(
        float(Fraction(4, 5))
    )

    slacks = result.slacks.query("dmu_id == 'Old'").set_index(["role", "variable"])
    assert slacks.loc[("input", "resource"), "slack"] == pytest.approx(
        float(Fraction(1, 5))
    )
    assert slacks.loc[("output", "service"), "slack"] == pytest.approx(0.0)

    assert result.metadata["method_id"] == (
        "environmental.ddf.output.chung_fare_grosskopf_1997"
    )
    assert result.metadata["preset_id"] == (
        "environmental.ddf.output.chung_fare_grosskopf_1997"
    )
    assert result.metadata["returns_to_scale"] == "crs"
    assert result.metadata["input_direction"] == "zeros"
    assert result.metadata["output_direction"] == "observed"
    assert result.metadata["bad_output_direction"] == "observed"
    assert result.metadata["allow_negative_distance"] is True
    assert result.metadata["expanded_spec"]["evaluation_protocol"]["kind"] == (
        "self_appraisal"
    )


def test_negative_external_reference_distance_is_not_reported_as_efficiency() -> None:
    result = ChungFareGrosskopfDDF(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(_analytical_data())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["Old", "distance"] == pytest.approx(0.0)
    assert summary.loc["New", "distance"] == pytest.approx(-float(Fraction(3, 5)))
    assert np.isnan(summary.loc["New", "efficiency"])
    assert pd.isna(summary.loc["New", "is_directionally_efficient"])
    assert pd.isna(summary.loc["New", "is_efficient"])
    assert not bool(summary.loc["New", "self_in_reference"])
    assert not bool(summary.loc["New", "is_within_reference_technology"])
    assert summary.loc["New", "membership_status"] == ("outside_reference_technology")
    assert not bool(summary.loc["New", "efficiency_denominator_valid"])
    assert result.metadata["expanded_spec"]["evaluation_protocol"]["kind"] == (
        "mixed_self_and_external_reference_appraisal"
    )

    targets = result.targets_for("New").set_index(["role", "variable"])
    assert targets.loc[("input", "resource"), "target"] == pytest.approx(
        float(Fraction(4, 5))
    )
    assert targets.loc[("output", "service"), "target"] == pytest.approx(
        float(Fraction(4, 5))
    )
    assert targets.loc[("bad_output", "residual"), "target"] == pytest.approx(
        float(Fraction(8, 5))
    )

    slacks = result.slacks.query("dmu_id == 'New'").set_index(["role", "variable"])
    assert slacks.loc[("input", "resource"), "slack"] == pytest.approx(
        float(Fraction(1, 5))
    )
    assert slacks.loc[("output", "service"), "slack"] == pytest.approx(0.0)


def test_positive_cfg_distance_does_not_imply_external_technology_membership() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["Reference", "Assessed"],
                "resource": [10.0, 5.0],
                "service": [100.0, 1.0],
                "residual": [10.0, 10.0],
            }
        ),
        dmu="dmu",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )
    result = ChungFareGrosskopfDDF(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(data)
    assessed = result.summary().set_index("dmu_id").loc["Assessed"]

    assert assessed["score_valid"]
    assert assessed["distance"] == pytest.approx(float(Fraction(99, 101)))
    assert not bool(assessed["self_in_reference"])
    assert not bool(assessed["is_within_reference_technology"])
    assert assessed["membership_status"] == "outside_reference_technology"
    assert not bool(assessed["efficiency_denominator_valid"])
    assert np.isnan(assessed["efficiency"])
    assert pd.isna(assessed["is_directionally_efficient"])
    assert pd.isna(assessed["is_efficient"])
    assert assessed["target_valid"]
    membership = result.diagnostics.query("dmu_id == 'Assessed' and phase == 0")
    assert len(membership) == 1
    assert membership.iloc[0]["solver_status"] == "infeasible"
    assert result.metadata["membership_solver_calls"] == 1
    assert result.metadata["solver_calls"] == 5


def test_disallowing_negative_distance_reports_external_infeasibility() -> None:
    result = ChungFareGrosskopfDDF(
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
        allow_negative_distance=False,
    ).fit(_analytical_data())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["Old", "solver_status"] == "optimal"
    assert summary.loc["Old", "distance"] == pytest.approx(0.0)
    assert summary.loc["New", "solver_status"] == "infeasible"
    assert np.isnan(summary.loc["New", "distance"])
    assert np.isnan(summary.loc["New", "efficiency"])
    assert result.metadata["phase_one_solver_calls"] == 2
    assert result.metadata["phase_two_solver_calls"] == 1
    assert result.metadata["solver_calls"] == 3


@pytest.mark.parametrize(
    ("reference_rows", "expected"),
    [
        ((0, 1), np.asarray([3.0 / 5.0, 0.0])),
        ((0,), np.asarray([0.0, -3.0 / 5.0])),
    ],
)
def test_public_full_and_score_only_runs_match_independent_dense_lp(
    reference_rows: tuple[int, ...],
    expected: np.ndarray,
) -> None:
    data = _analytical_data()
    reference = (
        "global"
        if reference_rows == (0, 1)
        else ReferenceSpec(kind="custom", custom_rows=reference_rows)
    )
    independently_compiled = _dense_cfg_distances(
        data,
        reference_rows=reference_rows,
    )
    full = ChungFareGrosskopfDDF(reference=reference).fit(data)
    score_only = ChungFareGrosskopfDDF(
        reference=reference,
        compute_slacks=False,
    ).fit(data)

    assert independently_compiled == pytest.approx(expected, abs=1e-10)
    assert _distance_vector(full) == pytest.approx(
        independently_compiled,
        abs=1e-9,
    )
    assert _distance_vector(score_only) == pytest.approx(
        independently_compiled,
        abs=1e-9,
    )
    assert score_only.slacks.empty
    assert score_only.targets.empty

    assert full.metadata["phase_one_solver_calls"] == data.n_dmus
    assert full.metadata["phase_two_solver_calls"] == data.n_dmus
    assert full.metadata["solver_calls"] == 2 * data.n_dmus
    assert score_only.metadata["phase_one_solver_calls"] == data.n_dmus
    assert score_only.metadata["phase_two_solver_calls"] == 0
    assert score_only.metadata["solver_calls"] == data.n_dmus
    for result in (full, score_only):
        assert result.metadata["compiled_reference_sets"] == 1
        assert result.metadata["planned_reference_sets"] == 1
        assert set(result.diagnostics["solver_status"]) == {"optimal"}
    assert set(full.diagnostics["phase"]) == {1, 2}
    assert set(score_only.diagnostics["phase"]) == {1}


def test_observed_cfg_direction_and_slack_completion_are_units_invariant() -> None:
    baseline_data = _analytical_data()
    rescaled_data = _analytical_data(
        input_scale=1_000.0,
        output_scale=0.01,
        bad_output_scale=100.0,
    )
    baseline = ChungFareGrosskopfDDF().fit(baseline_data)
    rescaled = ChungFareGrosskopfDDF().fit(rescaled_data)

    assert _distance_vector(rescaled) == pytest.approx(
        _distance_vector(baseline),
        abs=1e-9,
    )
    assert _distance_vector(rescaled) == pytest.approx(
        _dense_cfg_distances(rescaled_data, reference_rows=(0, 1)),
        abs=1e-9,
    )

    sort_columns = ["dmu_id", "role", "variable"]
    baseline_slacks = baseline.slacks.sort_values(sort_columns).reset_index(drop=True)
    rescaled_slacks = rescaled.slacks.sort_values(sort_columns).reset_index(drop=True)
    assert rescaled_slacks["scaled_slack"].to_numpy() == pytest.approx(
        baseline_slacks["scaled_slack"].to_numpy(),
        abs=1e-9,
    )
    assert baseline.metadata["slack_phase"] == "maximize_row_scaled_sum"
    assert baseline.metadata["slack_target_unit_invariant"] is True
