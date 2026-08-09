"""Independent dense oracle for the BP-DDF implementation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

from deapack import (
    ByProductionDDF,
    DEAData,
    dataset_info,
    load_dataset,
)


@dataclass(frozen=True, slots=True)
class _DenseComponentSolution:
    intended_distance: float
    environmental_distance: float

    @property
    def joint_distance(self) -> float:
        return min(self.intended_distance, self.environmental_distance)


def _source_data() -> DEAData:
    frame = load_dataset("by_production_component_bottleneck")
    roles = dataset_info("by_production_component_bottleneck").roles
    return DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        polluting_inputs=roles["polluting_inputs"],
        outputs=roles["outputs"],
        bad_outputs=roles["bad_outputs"],
    )


def _dense_crs_unit_direction(
    data: DEAData,
    evaluated_row: int,
) -> _DenseComponentSolution:
    """Compile equations (4.6), (4.8), and (5.4) without DEAPack builders."""
    if data.bad_outputs is None:
        raise AssertionError("source fixture requires undesirable outputs")

    n_reference = data.n_dmus
    n_variables = n_reference + 1
    objective = np.zeros(n_variables, dtype=np.float64)
    objective[-1] = -1.0

    intended_inputs = np.zeros((data.n_inputs, n_variables), dtype=np.float64)
    intended_inputs[:, :n_reference] = data.inputs.T
    intended_outputs = np.zeros(
        (data.n_outputs, n_variables),
        dtype=np.float64,
    )
    intended_outputs[:, :n_reference] = -data.outputs.T
    intended_outputs[:, -1] = 1.0
    intended = linprog(
        objective,
        A_ub=np.vstack([intended_inputs, intended_outputs]),
        b_ub=np.concatenate(
            [
                data.inputs[evaluated_row],
                -data.outputs[evaluated_row],
            ]
        ),
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    assert intended.success, intended.message

    polluting = np.asarray(data.polluting_input_indices, dtype=np.int64)
    residual_inputs = np.zeros((polluting.size, n_variables), dtype=np.float64)
    residual_inputs[:, :n_reference] = -data.inputs[:, polluting].T
    residual_outputs = np.zeros(
        (data.bad_outputs.shape[1], n_variables),
        dtype=np.float64,
    )
    residual_outputs[:, :n_reference] = data.bad_outputs.T
    residual_outputs[:, -1] = 1.0
    residual = linprog(
        objective,
        A_ub=np.vstack([residual_inputs, residual_outputs]),
        b_ub=np.concatenate(
            [
                -data.inputs[evaluated_row, polluting],
                data.bad_outputs[evaluated_row],
            ]
        ),
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    assert residual.success, residual.message

    return _DenseComponentSolution(
        intended_distance=float(-intended.fun),
        environmental_distance=float(-residual.fun),
    )


def test_bp_ddf_matches_independent_compiler_on_project_case() -> None:
    data = _source_data()
    oracle = [
        _dense_crs_unit_direction(data, evaluated_row)
        for evaluated_row in range(data.n_dmus)
    ]
    result = ByProductionDDF().fit(data)
    summary = result.summary().set_index("dmu_id")

    assert summary["score_valid"].eq(True).all()
    assert summary["target_valid"].eq(True).all()
    assert summary["peer_valid"].eq(True).all()
    assert summary["dual_valid"].eq(True).all()
    assert result.diagnostics["postsolve_certified"].eq(True).all()
    assert result.metadata["solver_calls"] == 2 * data.n_dmus
    assert result.metadata["additional_solver_calls"] == 0

    np.testing.assert_allclose(
        summary["intended_distance"],
        [solution.intended_distance for solution in oracle],
        atol=1e-10,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        summary["environmental_distance"],
        [solution.environmental_distance for solution in oracle],
        atol=1e-10,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        summary["distance"],
        [solution.joint_distance for solution in oracle],
        atol=1e-10,
        rtol=0.0,
    )

    targets = result.targets_for("Focal").set_index(["role", "variable"])
    assert targets.loc[("output", "service"), "target"] > data.outputs[-1, 0]
    assert targets.loc[("bad_output", "residual"), "target"] < data.bad_outputs[-1, 0]
    peers = result.peers("Focal").set_index("subtechnology")
    assert (
        peers.loc[
            "intended_production",
            "reference_dmu_id",
        ]
        == "OutputChampion"
    )
    assert (
        peers.loc[
            "residual_generation",
            "reference_dmu_id",
        ]
        == "ResidualChampion"
    )

    assert result.metadata["source_profile_matches"] is True
    assert result.metadata["source_profile"] == (
        "murty_russell_levkoff_2012_eq_4_6_4_8_5_4"
    )
    assert result.metadata["source_profile_mismatches"] == ()
    assert result.metadata["native_score"] == "joint_beta"
    assert result.metadata["efficiency_transform_source"] == ("deapack_display_only")


def test_bp_ddf_source_profile_accepts_any_fixed_global_direction() -> None:
    result = ByProductionDDF(
        output_direction=[2.0],
        bad_output_direction={"residual": 3.0},
        reference="global",
    ).fit(_source_data())

    assert result.metadata["source_profile_matches"] is True
    assert result.metadata["direction_scope"] == "fixed_across_observations"


def test_bp_ddf_source_profile_separates_package_extensions() -> None:
    data = _source_data()
    cases = (
        (
            ByProductionDDF(intended_returns_to_scale="vrs"),
            "intended_returns_to_scale_is_not_crs",
        ),
        (
            ByProductionDDF(residual_returns_to_scale="vrs"),
            "residual_returns_to_scale_is_not_crs",
        ),
        (
            ByProductionDDF(
                output_direction="observed",
                bad_output_direction="observed",
            ),
            "direction_is_not_fixed_across_observations",
        ),
    )

    for model, expected_mismatch in cases:
        result = model.fit(data)
        assert result.metadata["source_profile_matches"] is False
        assert expected_mismatch in result.metadata["source_profile_mismatches"]


def test_bp_ddf_panel_reference_is_a_package_extension() -> None:
    frame = load_dataset("by_production_component_bottleneck").iloc[:2].copy()
    frame["period"] = [2020, 2021]
    roles = dataset_info("by_production_component_bottleneck").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        period="period",
        inputs=roles["inputs"],
        polluting_inputs=roles["polluting_inputs"],
        outputs=roles["outputs"],
        bad_outputs=roles["bad_outputs"],
    )
    result = ByProductionDDF(reference="global").fit(data)

    assert result.metadata["source_profile_matches"] is False
    assert (
        "data_are_not_one_cross_section"
        in (result.metadata["source_profile_mismatches"])
    )
