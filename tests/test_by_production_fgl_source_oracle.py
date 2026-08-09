"""Independent dense oracle for the BP-FGL implementation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

from deapack import (
    ByProductionFGL,
    DEAData,
    ReferenceSpec,
    dataset_info,
    load_dataset,
)


@dataclass(frozen=True, slots=True)
class _DenseFGLSolution:
    expansion_factor: float
    productive_efficiency: float
    environmental_efficiency: float
    intended_intensities: np.ndarray
    residual_intensities: np.ndarray

    @property
    def overall_efficiency(self) -> float:
        return 0.5 * (self.productive_efficiency + self.environmental_efficiency)


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


def _dense_scalar_crs_fgl(
    data: DEAData,
    evaluated_row: int,
) -> _DenseFGLSolution:
    """Compile equations (4.6), (4.8), and (5.9)--(5.10) independently."""
    if data.n_outputs != 1 or data.bad_outputs is None:
        raise AssertionError("the source compiler requires one good and one bad output")
    if data.bad_outputs.shape[1] != 1:
        raise AssertionError("the source compiler requires one bad output")

    n_reference = data.n_dmus
    n_variables = n_reference + 1

    intended_objective = np.zeros(n_variables, dtype=np.float64)
    intended_objective[-1] = -1.0
    intended_inputs = np.zeros((data.n_inputs, n_variables), dtype=np.float64)
    intended_inputs[:, :n_reference] = data.inputs.T
    intended_outputs = np.zeros((1, n_variables), dtype=np.float64)
    intended_outputs[:, :n_reference] = -data.outputs.T
    intended_outputs[0, -1] = data.outputs[evaluated_row, 0]
    intended = linprog(
        intended_objective,
        A_ub=np.vstack([intended_inputs, intended_outputs]),
        b_ub=np.concatenate([data.inputs[evaluated_row], np.zeros(1)]),
        bounds=[(0.0, None)] * n_reference + [(1.0, None)],
        method="highs",
    )
    assert intended.success, intended.message

    polluting = np.asarray(data.polluting_input_indices, dtype=np.int64)
    residual_objective = np.zeros(n_variables, dtype=np.float64)
    residual_objective[-1] = 1.0
    residual_inputs = np.zeros((polluting.size, n_variables), dtype=np.float64)
    residual_inputs[:, :n_reference] = -data.inputs[:, polluting].T
    residual_outputs = np.zeros((1, n_variables), dtype=np.float64)
    residual_outputs[:, :n_reference] = data.bad_outputs.T
    residual_outputs[0, -1] = -data.bad_outputs[evaluated_row, 0]
    residual = linprog(
        residual_objective,
        A_ub=np.vstack([residual_inputs, residual_outputs]),
        b_ub=np.concatenate([-data.inputs[evaluated_row, polluting], np.zeros(1)]),
        bounds=[(0.0, None)] * n_reference + [(0.0, 1.0)],
        method="highs",
    )
    assert residual.success, residual.message

    expansion = float(intended.x[-1])
    return _DenseFGLSolution(
        expansion_factor=expansion,
        productive_efficiency=1.0 / expansion,
        environmental_efficiency=float(residual.x[-1]),
        intended_intensities=np.asarray(intended.x[:n_reference]),
        residual_intensities=np.asarray(residual.x[:n_reference]),
    )


def test_bp_fgl_matches_independent_compiler_on_project_case() -> None:
    data = _source_data()
    independent = [_dense_scalar_crs_fgl(data, row) for row in range(data.n_dmus)]
    result = ByProductionFGL().fit(data)
    summary = result.summary().set_index("dmu_id")

    expected_productive = np.asarray(
        [item.productive_efficiency for item in independent]
    )
    expected_environmental = np.asarray(
        [item.environmental_efficiency for item in independent]
    )
    expected_overall = np.asarray([item.overall_efficiency for item in independent])
    np.testing.assert_allclose(summary["productive_efficiency"], expected_productive)
    np.testing.assert_allclose(
        summary["environmental_efficiency"], expected_environmental
    )
    np.testing.assert_allclose(summary["efficiency"], expected_overall)

    targets = result.targets_for("Focal").set_index(["role", "variable"])
    assert targets.loc[("output", "service"), "target"] > data.outputs[-1, 0]
    assert targets.loc[("bad_output", "residual"), "target"] < data.bad_outputs[-1, 0]
    peers = result.peers("Focal").set_index("subtechnology")
    assert peers.loc["intended_production", "reference_dmu_id"] == "OutputChampion"
    assert peers.loc["residual_generation", "reference_dmu_id"] == "ResidualChampion"

    assert result.metadata["source_profile_matches"] is True
    assert result.metadata["source_profile"] == (
        "murty_russell_levkoff_2012_eq_4_6_4_8_5_9_5_10"
    )
    assert result.metadata["source_profile_mismatches"] == ()
    assert result.metadata["distance_transform_source"] == "deapack_display_only"


def test_bp_fgl_source_profile_separates_package_extensions() -> None:
    data = _source_data()
    cases = (
        (
            ByProductionFGL(intended_returns_to_scale="vrs"),
            "intended_returns_to_scale_is_not_crs",
        ),
        (
            ByProductionFGL(residual_returns_to_scale="vrs"),
            "residual_returns_to_scale_is_not_crs",
        ),
        (
            ByProductionFGL(
                reference=ReferenceSpec(
                    kind="custom",
                    custom_rows=tuple(range(data.n_dmus)),
                )
            ),
            "reference_is_not_the_full_self_inclusive_sample",
        ),
    )

    for model, expected_mismatch in cases:
        result = model.fit(data)
        assert result.metadata["source_profile_matches"] is False
        assert expected_mismatch in result.metadata["source_profile_mismatches"]


def test_bp_fgl_panel_is_a_package_extension() -> None:
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
    result = ByProductionFGL(reference="global").fit(data)

    assert result.metadata["source_profile_matches"] is False
    assert (
        "data_are_not_one_cross_section"
        in (result.metadata["source_profile_mismatches"])
    )
