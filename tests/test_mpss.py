from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from deapack import (
    CCR,
    DEAData,
    ReferenceSpec,
    SolverStatus,
    scale_efficiency,
)
from deapack.analysis.mpss import most_productive_scale_size, mpss
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver


class _CountingSolver:
    name = "mpss_counting_fixture"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


class _FailingSolver:
    name = "mpss_failure_fixture"

    def __init__(self, suffix: str) -> None:
        self._suffix = suffix
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        if problem.name.endswith(self._suffix):
            return LPSolution(
                status=SolverStatus.NUMERICAL_ERROR,
                objective=None,
                primal=None,
                message="injected failure",
                iterations=0,
            )
        return self._delegate.solve(problem)


def _banker_scale_data(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
) -> DEAData:
    """Return the A--E scale example used in the public RTS literature."""

    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "C", "D", "E"],
            "input": np.asarray([1.0, 1.5, 3.0, 4.0, 4.0]) * input_scale,
            "output": np.asarray([1.0, 2.0, 4.0, 5.0, 4.5]) * output_scale,
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs="output",
    )


def _management_teaching_data() -> DEAData:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "Q", "C", "D"],
            "resource": [1.0, 2.0, 3.0, 4.0, 5.0],
            "service": [1.5, 4.0, 5.0, 8.0, 9.0],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="resource",
        outputs="service",
    )


def _endpoint_ray_targets(result, dmu_id: str) -> pd.DataFrame:
    targets = result.targets_for(dmu_id)
    return (
        targets.loc[targets["target_kind"] == "mix_preserving_proportional_plan"]
        .set_index(["endpoint", "role", "variable"])
        .sort_index()
    )


def test_mpss_alias_is_exact() -> None:
    assert mpss is most_productive_scale_size


def test_banker_fixed_mix_oracle_recovers_smallest_and_largest_mpss() -> None:
    result = most_productive_scale_size(_banker_scale_data())
    summary = result.summary().set_index("dmu_id")

    expected_ratios = {
        "A": 4.0 / 3.0,
        "B": 1.0,
        "C": 1.0,
        "D": 16.0 / 15.0,
        "E": 32.0 / 27.0,
    }
    for dmu_id, ratio in expected_ratios.items():
        assert summary.loc[dmu_id, "maximum_productivity_ratio"] == pytest.approx(ratio)
        assert summary.loc[dmu_id, "crs_output_efficiency"] == pytest.approx(
            1.0 / ratio
        )

        targets = _endpoint_ray_targets(result, dmu_id)
        assert targets.loc[("smallest_mpss", "input", "input"), "target"] == (
            pytest.approx(1.5)
        )
        assert targets.loc[("smallest_mpss", "output", "output"), "target"] == (
            pytest.approx(2.0)
        )
        assert targets.loc[("largest_mpss", "input", "input"), "target"] == (
            pytest.approx(3.0)
        )
        assert targets.loc[("largest_mpss", "output", "output"), "target"] == (
            pytest.approx(4.0)
        )

    assert summary["current_scale_position"].to_dict() == {
        "A": "below_mpss_set",
        "B": "within_mpss_set",
        "C": "within_mpss_set",
        "D": "above_mpss_set",
        "E": "above_mpss_set",
    }
    assert bool(summary.loc["B", "is_ray_mpss"])
    assert bool(summary.loc["C", "is_ray_mpss"])
    assert not bool(summary.loc["D", "is_ray_mpss"])
    assert summary["attains_maximum_average_productivity"].equals(
        summary["is_ray_mpss"]
    )
    assert not summary["mpss_scale_interval_is_unique"].any()


def test_d_oracle_reports_source_native_scale_factors_and_intensity_sums() -> None:
    result = most_productive_scale_size(_banker_scale_data())
    row = result.summary().set_index("dmu_id").loc["D"]

    assert row["crs_intensity_sum_lower"] == pytest.approx(4.0 / 3.0)
    assert row["crs_intensity_sum_upper"] == pytest.approx(8.0 / 3.0)
    assert row["mpss_input_scale_factor_lower"] == pytest.approx(3.0 / 8.0)
    assert row["mpss_output_scale_factor_lower"] == pytest.approx(2.0 / 5.0)
    assert row["mpss_input_scale_factor_upper"] == pytest.approx(3.0 / 4.0)
    assert row["mpss_output_scale_factor_upper"] == pytest.approx(4.0 / 5.0)

    peers = result.peers("D")
    assert set(peers["endpoint"]) == {"smallest_mpss", "largest_mpss"}
    assert peers.groupby("endpoint")["normalized_vrs_weight"].sum().to_dict() == (
        pytest.approx({"smallest_mpss": 1.0, "largest_mpss": 1.0})
    )
    smallest = peers.loc[peers["endpoint"] == "smallest_mpss"].iloc[0]
    largest = peers.loc[peers["endpoint"] == "largest_mpss"].iloc[0]
    assert smallest["reference_dmu_id"] == "B"
    assert smallest["crs_intensity"] == pytest.approx(8.0 / 3.0)
    assert largest["reference_dmu_id"] == "C"
    assert largest["crs_intensity"] == pytest.approx(4.0 / 3.0)


def test_right_scale_does_not_mean_the_observed_plan_is_productive() -> None:
    data = _management_teaching_data()
    result = most_productive_scale_size(data)
    summary = result.summary().set_index("dmu_id")
    q = summary.loc["Q"]

    assert q["mpss_input_scale_factor_lower"] == pytest.approx(2.0 / 3.0)
    assert q["mpss_input_scale_factor_upper"] == pytest.approx(4.0 / 3.0)
    assert q["input_scale_position"] == "within"
    assert q["output_scale_position"] == "within"
    assert q["current_scale_position"] == (
        "within_mpss_scale_range_but_below_maximum_productivity"
    )
    assert q["maximum_productivity_ratio"] == pytest.approx(6.0 / 5.0)
    assert not bool(q["is_ray_mpss"])

    scale = scale_efficiency(data, orientation="input").summary().set_index("dmu_id")
    assert scale.loc["Q", "crs_efficiency"] == pytest.approx(5.0 / 6.0)
    assert scale.loc["Q", "vrs_efficiency"] == pytest.approx(5.0 / 6.0)
    assert scale.loc["Q", "scale_efficiency"] == pytest.approx(1.0)


def test_unique_mpss_is_distinguished_from_peer_uniqueness() -> None:
    frame = pd.DataFrame(
        {
            "unit": [str(i) for i in range(1, 8)],
            "input": [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0],
            "output": [1.0, 3.5, 6.0, 7.0, 8.0, 9.0, 10.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs="output",
    )
    result = most_productive_scale_size(data)
    summary = result.summary()

    assert summary["mpss_scale_interval_is_unique"].all()
    assert set(summary["mpss_scale_target_uniqueness"]) == {"unique"}
    assert set(summary["mpss_ray_target_uniqueness"]) == {"unique"}
    assert set(summary["endpoint_peer_uniqueness"]) == {"not_assessed"}
    targets = _endpoint_ray_targets(result, "7")
    for endpoint in ("smallest_mpss", "largest_mpss"):
        assert targets.loc[(endpoint, "input", "input"), "target"] == (
            pytest.approx(2.0)
        )
        assert targets.loc[(endpoint, "output", "output"), "target"] == (
            pytest.approx(6.0)
        )


def test_factors_are_unit_invariant_and_targets_keep_physical_units() -> None:
    baseline = most_productive_scale_size(_banker_scale_data())
    rescaled = most_productive_scale_size(
        _banker_scale_data(input_scale=1e6, output_scale=1e-4)
    )
    factor_columns = [
        "maximum_productivity_ratio",
        "crs_output_efficiency",
        "mpss_input_scale_factor_lower",
        "mpss_input_scale_factor_upper",
        "mpss_output_scale_factor_lower",
        "mpss_output_scale_factor_upper",
    ]
    assert np.allclose(
        baseline.summary()[factor_columns],
        rescaled.summary()[factor_columns],
    )

    base_targets = _endpoint_ray_targets(baseline, "D")
    scaled_targets = _endpoint_ray_targets(rescaled, "D")
    for endpoint in ("smallest_mpss", "largest_mpss"):
        assert scaled_targets.loc[(endpoint, "input", "input"), "target"] == (
            pytest.approx(
                1e6 * base_targets.loc[(endpoint, "input", "input"), "target"]
            )
        )
        assert scaled_targets.loc[(endpoint, "output", "output"), "target"] == (
            pytest.approx(
                1e-4 * base_targets.loc[(endpoint, "output", "output"), "target"]
            )
        )


def test_three_solve_kernel_reuses_compiled_reference_population() -> None:
    solver = _CountingSolver()
    result = most_productive_scale_size(_banker_scale_data(), solver=solver)

    assert solver.calls == 3 * 5
    assert result.metadata["solver_calls_per_resolved_observation"] == 3
    assert result.metadata["compiled_reference_sets"] == 1


def test_output_linearization_agrees_with_input_crs_normalization() -> None:
    data = _banker_scale_data()
    mpss_result = most_productive_scale_size(data).summary()
    input_crs = CCR(orientation="input", compute_slacks=False).fit(data).summary()

    assert np.allclose(
        mpss_result["crs_output_efficiency"],
        input_crs["efficiency"],
    )


def test_multi_input_output_endpoint_weights_are_convex_and_ray_plans_feasible() -> (
    None
):
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "C", "D"],
            "staff": [1.0, 2.0, 4.0, 6.0],
            "capital": [2.0, 4.0, 8.0, 12.0],
            "visits": [1.0, 4.0, 8.0, 9.0],
            "quality": [3.0, 12.0, 24.0, 27.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs=["staff", "capital"],
        outputs=["visits", "quality"],
    )
    result = most_productive_scale_size(data)

    weight_sums = result.intensities.groupby(["dmu_id", "endpoint"])[
        "normalized_vrs_weight"
    ].sum()
    assert np.allclose(weight_sums, 1.0)
    assert (result.slacks["slack"] >= 0.0).all()
    assert (result.slacks["scaled_slack"] >= 0.0).all()
    targets = _endpoint_ray_targets(result, "D")
    assert targets.loc[("smallest_mpss", "input", "staff"), "target"] == (
        pytest.approx(2.0)
    )
    assert targets.loc[("largest_mpss", "output", "visits"), "target"] == (
        pytest.approx(8.0)
    )


def test_panel_auto_uses_contemporaneous_compiled_reference_sets() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "A", "B"],
            "period": [2020, 2020, 2021, 2021],
            "input": [1.0, 2.0, 1.0, 2.0],
            "output": [1.0, 3.0, 2.0, 5.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        period="period",
        inputs="input",
        outputs="output",
    )
    solver = _CountingSolver()
    result = most_productive_scale_size(data, solver=solver)

    assert solver.calls == 3 * 4
    assert result.metadata["reference_kind"] == "contemporaneous"
    assert result.metadata["compiled_reference_sets"] == 2


@pytest.mark.parametrize(
    ("suffix", "expected_phase_status"),
    [
        (":radial", "not_run"),
        (":mpss_intensity_sum_lower", "numerical_error"),
        (":mpss_intensity_sum_upper", "numerical_error"),
    ],
)
def test_component_failures_fail_closed(
    suffix: str,
    expected_phase_status: str,
) -> None:
    result = most_productive_scale_size(
        _banker_scale_data(),
        solver=_FailingSolver(suffix),
    )
    summary = result.summary()

    assert summary["is_ray_mpss"].isna().all()
    assert summary["attains_maximum_average_productivity"].isna().all()
    assert summary["mpss_input_scale_factor_lower"].isna().all()
    assert set(summary["mpss_status"]) == {"component_failure"}
    if suffix == ":radial":
        assert set(summary["solver_status"]) == {"numerical_error"}
        assert set(summary["intensity_sum_lower_status"]) == {expected_phase_status}
    else:
        assert set(summary["solver_status"]) == {"component_failure"}
        status_column = (
            "intensity_sum_lower_status"
            if suffix.endswith("lower")
            else "intensity_sum_upper_status"
        )
        assert set(summary[status_column]) == {expected_phase_status}


def test_external_reference_does_not_claim_observed_feasibility_or_mpss() -> None:
    result = most_productive_scale_size(
        _banker_scale_data(),
        reference=ReferenceSpec(kind="custom", custom_rows=(1, 2)),
    )
    summary = result.summary()

    external = summary.loc[~summary["reference_self_inclusion_holds"]]
    internal = summary.loc[summary["reference_self_inclusion_holds"]]
    assert set(internal["dmu_id"]) == {"B", "C"}
    assert external["is_within_reference_technology"].isna().all()
    assert external["is_ray_mpss"].isna().all()
    assert set(external["current_scale_position"]) == {"external_reference_comparison"}
    assert set(external["mpss_status"]) == {"external_reference_comparison"}


def test_bad_outputs_require_a_source_qualified_environmental_mpss() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B"],
            "input": [1.0, 2.0],
            "good": [1.0, 3.0],
            "bad": [2.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs="good",
        bad_outputs="bad",
    )

    with pytest.raises(ModelSpecificationError, match="environmental MPSS"):
        most_productive_scale_size(data)


def test_no_positive_reference_match_fails_without_dividing_by_zero() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B"],
            "input": [1.0, 1.0],
            "service_a": [1.0, 0.0],
            "service_b": [0.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs=["service_a", "service_b"],
    )
    result = most_productive_scale_size(
        data,
        reference=ReferenceSpec(kind="custom", custom_rows=(1,)),
    )
    a = result.summary().set_index("dmu_id").loc["A"]

    assert a["maximum_productivity_ratio"] == pytest.approx(0.0)
    assert a["maximum_productivity_ratio_status"] == "no_positive_mix_match"
    assert a["solver_status"] == "component_failure"
    assert math.isnan(a["crs_output_efficiency"])


def test_signed_data_are_not_silently_translated() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B"],
            "input": [1.0, -0.5],
            "output": [1.0, 2.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs="output",
    )

    with pytest.raises(DataValidationError, match="nonnegative input values"):
        most_productive_scale_size(data)


@pytest.mark.parametrize("argument", [0.0, -1.0, math.inf, math.nan])
def test_tolerance_must_be_positive_and_finite(argument: float) -> None:
    with pytest.raises(ValueError, match="tolerance must be positive and finite"):
        most_productive_scale_size(_banker_scale_data(), tolerance=argument)


def test_metadata_states_fixed_mix_global_scope_and_no_orientation_switch() -> None:
    result = most_productive_scale_size(_banker_scale_data())
    metadata = result.metadata

    assert metadata["method_id"] == "analysis.mpss.banker_1984"
    assert metadata["mix_policy"] == "observed_input_and_output_proportions"
    assert metadata["orientation_parameter"] == "not_applicable"
    assert metadata["expanded_spec"]["analysis"]["scope"] == (
        "global_along_observed_mix"
    )
    assert metadata["expanded_spec"]["analysis"]["pareto_completion"] == ("not_claimed")
