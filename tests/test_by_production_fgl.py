from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from deapack import (
    ByProductionFareGrosskopfLovellDEA,
    ByProductionFGL,
    DEAData,
    dataset_info,
    load_dataset,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import SciPyHiGHSSolver


def _single_output_example(
    *,
    output_scale: float = 1.0,
    bad_output_scale: float = 1.0,
) -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "C"],
            "energy": [1.0, 1.0],
            "electricity": np.asarray([2.0, 1.0]) * output_scale,
            "co2": np.asarray([1.0, 2.0]) * bad_output_scale,
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="energy",
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )


def _multioutput_example() -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "energy": [1.0, 1.0, 1.0],
            "y1": [2.0, 1.0, 1.0],
            "y2": [1.0, 2.0, 1.0],
            "co2": [1.0, 1.0, 2.0],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="energy",
        polluting_inputs="energy",
        outputs=["y1", "y2"],
        bad_outputs="co2",
    )


def test_by_production_fgl_decomposes_productive_and_environmental_scores() -> None:
    result = ByProductionFareGrosskopfLovellDEA().fit(_single_output_example())
    summary = result.summary().set_index("dmu_id")

    assert ByProductionFGL is ByProductionFareGrosskopfLovellDEA
    assert np.isclose(summary.loc["A", "efficiency"], 1.0)
    assert np.isclose(summary.loc["C", "productive_efficiency"], 0.5)
    assert np.isclose(summary.loc["C", "environmental_efficiency"], 0.5)
    assert np.isclose(summary.loc["C", "efficiency"], 0.5)
    assert np.isclose(summary.loc["C", "distance"], 0.5)
    assert summary.loc["C", "fgl_optimality_gap"] <= 1e-7
    assert bool(summary.loc["A", "is_fgl_efficient"])
    assert not bool(summary.loc["C", "is_fgl_efficient"])
    assert summary["is_efficient"].isna().all()

    targets = result.targets_for("C").set_index(["role", "variable"])
    assert np.isclose(targets.loc[("output", "electricity"), "factor"], 2.0)
    assert np.isclose(targets.loc[("output", "electricity"), "target"], 2.0)
    assert np.isclose(targets.loc[("bad_output", "co2"), "factor"], 0.5)
    assert np.isclose(targets.loc[("bad_output", "co2"), "target"], 1.0)
    assert set(result.peers("C")["subtechnology"]) == {
        "intended_production",
        "residual_generation",
    }


def test_fgl_native_efficiency_does_not_claim_strong_efficiency() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "energy": [1.0, 1.0],
            "labor": [1.0, 2.0],
            "electricity": [1.0, 1.0],
            "co2": [1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["energy", "labor"],
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )

    b = ByProductionFGL().fit(data).summary().set_index("dmu_id").loc["B"]

    assert bool(b["is_fgl_efficient"])
    assert pd.isna(b["is_efficient"])


def test_by_production_fgl_solves_nonradial_multioutput_problem() -> None:
    result = ByProductionFGL(fgl_tolerance=1e-9).fit(_multioutput_example())
    c = result.summary().set_index("dmu_id").loc["C"]

    assert np.isclose(c["productive_efficiency"], 2.0 / 3.0, atol=1e-7)
    assert np.isclose(c["environmental_efficiency"], 0.5)
    assert np.isclose(c["efficiency"], 7.0 / 12.0, atol=1e-7)
    targets = result.targets_for("C").set_index("variable")
    assert np.isclose(targets.loc["y1", "target"], 1.5, atol=5e-4)
    assert np.isclose(targets.loc["y2", "target"], 1.5, atol=5e-4)


def test_by_production_fgl_returned_targets_match_returned_component_peers() -> None:
    data = _multioutput_example()
    model = ByProductionFGL(fgl_tolerance=1e-9)
    result = model.fit(data)
    peers = result.peers("C")
    targets = result.targets_for("C").set_index(["role", "variable"])
    id_to_row = {dmu_id: row for row, dmu_id in enumerate(data.dmu_ids.tolist())}

    intended = np.zeros(data.n_dmus)
    for _, row in peers.query("subtechnology == 'intended_production'").iterrows():
        intended[id_to_row[row["reference_dmu_id"]]] = row["lambda"]
    residual = np.zeros(data.n_dmus)
    for _, row in peers.query("subtechnology == 'residual_generation'").iterrows():
        residual[id_to_row[row["reference_dmu_id"]]] = row["lambda"]

    output_targets = np.asarray(
        [targets.loc[("output", variable), "target"] for variable in data.output_names]
    )
    bad_targets = np.asarray(
        [
            targets.loc[("bad_output", variable), "target"]
            for variable in data.bad_output_names
        ]
    )
    assert np.all(data.inputs.T @ intended <= data.inputs[2] + model.tolerance)
    assert np.all(data.outputs.T @ intended >= output_targets - model.tolerance)
    polluting = np.asarray(data.polluting_input_indices)
    assert np.all(
        data.inputs[:, polluting].T @ residual
        >= data.inputs[2, polluting] - model.tolerance
    )
    assert data.bad_outputs is not None
    assert np.all(data.bad_outputs.T @ residual <= bad_targets + model.tolerance)
    assert result.diagnostics["max_primal_violation"].le(model.tolerance).all()


def test_by_production_fgl_fails_closed_at_cut_iteration_limit() -> None:
    result = ByProductionFGL(max_cut_iterations=1).fit(_multioutput_example())
    c = result.summary().set_index("dmu_id").loc["C"]

    assert np.isnan(c["efficiency"])
    assert c["solver_status"] == "limit_reached"
    assert c["fgl_cut_iterations"] == 1
    diagnostic = result.diagnostics.query(
        "dmu_id == 'C' and subtechnology == 'intended_production'"
    ).iloc[0]
    assert diagnostic["iterations"] == 1
    assert diagnostic["optimality_gap"] > 0


class _CorruptingFGLSolver:
    name = "corrupting_fgl_test_solver"

    def __init__(self, subtechnology: str) -> None:
        self.subtechnology = subtechnology
        self.base = SciPyHiGHSSolver()

    def solve(self, problem):
        solution = self.base.solve(problem)
        if (
            self.subtechnology in problem.name
            and solution.is_optimal
            and solution.primal is not None
        ):
            primal = solution.primal.copy()
            if self.subtechnology == "intended":
                output_count = sum(lower == 1.0 for lower, _ in problem.bounds)
                reference_count = primal.size - 2 * output_count
            else:
                output_count = sum(upper == 1.0 for _, upper in problem.bounds)
                reference_count = primal.size - output_count
            primal[:reference_count] = 0.0
            return replace(solution, primal=primal)
        return solution


@pytest.mark.parametrize("subtechnology", ["intended", "residual"])
def test_by_production_fgl_rejects_corrupted_returned_incumbent(
    subtechnology: str,
) -> None:
    result = ByProductionFGL(
        solver=_CorruptingFGLSolver(subtechnology),
    ).fit(_single_output_example())

    assert result.summary()["efficiency"].isna().all()
    assert set(result.summary()["solver_status"]) == {"numerical_error"}
    assert result.targets.empty
    assert result.intensities.empty
    failed = result.diagnostics.query(
        "subtechnology == @subtechnology_name",
        local_dict={
            "subtechnology_name": (
                "intended_production"
                if subtechnology == "intended"
                else "residual_generation"
            )
        },
    )
    assert set(failed["solver_status"]) == {"numerical_error"}
    assert failed["max_primal_violation"].gt(0).all()


def test_by_production_fgl_is_units_invariant() -> None:
    baseline = ByProductionFGL().fit(_single_output_example()).summary()["efficiency"]
    rescaled = (
        ByProductionFGL()
        .fit(
            _single_output_example(
                output_scale=100.0,
                bad_output_scale=0.01,
            )
        )
        .summary()["efficiency"]
    )

    assert np.allclose(rescaled, baseline)


def test_by_production_fgl_uses_shared_panel_references() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "year": [2020, 2021],
            "energy": [1.0, 1.0],
            "electricity": [1.0, 2.0],
            "co2": [2.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="year",
        inputs="energy",
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )

    current = ByProductionFGL(reference="contemporaneous").fit(data)
    global_result = ByProductionFGL(reference="global").fit(data)

    assert np.allclose(current.summary()["efficiency"], 1.0)
    assert np.isclose(global_result.summary().loc[0, "efficiency"], 0.5)


def test_by_production_fgl_validates_required_positive_roles() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A"],
            "energy": [1.0],
            "electricity": [1.0],
            "co2": [1.0],
        }
    )
    missing_role = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )
    with pytest.raises(ModelSpecificationError, match="polluting_inputs"):
        ByProductionFGL().fit(missing_role)

    zero_bad = frame.copy()
    zero_bad.loc[0, "co2"] = 0.0
    data = DEAData.from_frame(
        zero_bad,
        dmu="dmu",
        inputs="energy",
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )
    with pytest.raises(DataValidationError, match="strictly positive bad outputs"):
        ByProductionFGL().fit(data)

    zero_output = frame.copy()
    zero_output.loc[0, "electricity"] = 0.0
    data = DEAData.from_frame(
        zero_output,
        dmu="dmu",
        inputs="energy",
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )
    with pytest.raises(
        DataValidationError,
        match="strictly positive desirable outputs",
    ):
        ByProductionFGL().fit(data)

    zero_polluting_input = frame.copy()
    zero_polluting_input.loc[0, "energy"] = 0.0
    data = DEAData.from_frame(
        zero_polluting_input,
        dmu="dmu",
        inputs="energy",
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )
    with pytest.raises(
        DataValidationError,
        match="strictly positive polluting inputs",
    ):
        ByProductionFGL().fit(data)


@pytest.mark.parametrize(
    ("keyword", "value", "error"),
    [
        ("fgl_tolerance", np.nan, ValueError),
        ("fgl_tolerance", np.inf, ValueError),
        ("tolerance", np.nan, ValueError),
        ("peer_tolerance", np.inf, ValueError),
        ("max_cut_iterations", 1.5, TypeError),
        ("max_cut_iterations", True, TypeError),
    ],
)
def test_by_production_fgl_rejects_malformed_numeric_controls(
    keyword: str,
    value: object,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        ByProductionFGL(**{keyword: value})


def test_by_production_fgl_closes_project_component_bottleneck_case() -> None:
    frame = load_dataset("by_production_component_bottleneck")
    roles = dataset_info("by_production_component_bottleneck").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        polluting_inputs=roles["polluting_inputs"],
        outputs=roles["outputs"],
        bad_outputs=roles["bad_outputs"],
    )

    result = ByProductionFGL().fit(data)
    summary = result.summary().set_index("dmu_id")

    productive = summary["productive_efficiency"].to_numpy()
    environmental = summary["environmental_efficiency"].to_numpy()
    assert np.all((productive > 0.0) & (productive <= 1.0))
    assert np.all((environmental > 0.0) & (environmental <= 1.0))
    np.testing.assert_allclose(
        summary["efficiency"].to_numpy(),
        0.5 * (productive + environmental),
    )
    assert summary.loc["Focal", "productive_efficiency"] < 1.0
    assert summary.loc["Focal", "environmental_efficiency"] < 1.0
