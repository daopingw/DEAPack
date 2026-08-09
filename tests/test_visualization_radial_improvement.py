from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace

import pandas as pd
import pytest

from deapack import BCC, DEAData, RadialDEA, ReferenceSpec, load_dataset
from deapack.results import DEAResult
from deapack.solvers import SciPyHiGHSSolver
from deapack.visualization._types import PlotNotAvailableError
from deapack.visualization.radial_improvement import (
    prepare_radial_improvement_data,
    radial_improvement_plot_applicable,
    radial_improvement_route,
)

_VARIABLE_COLUMNS = [
    "role",
    "variable",
    "variable_label",
    "order",
    "observed",
    "radial_change",
    "radial_target",
    "slack_completion",
    "target",
]


def _three_branch_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "C"],
                "resource": [1.0, 2.0, 1.0],
                "service": [1.0, 1.0, 0.5],
            }
        ),
        dmu="unit",
        inputs="resource",
        outputs="service",
    )


@pytest.fixture(scope="module")
def input_result() -> DEAResult:
    return BCC(orientation="input").fit(_three_branch_data())


@pytest.fixture(scope="module")
def output_result() -> DEAResult:
    return BCC(orientation="output").fit(_three_branch_data())


def _metadata_copy(result: DEAResult) -> dict[str, object]:
    return json.loads(json.dumps(result.metadata))


def test_input_plan_separates_score_one_from_service_slack(
    input_result: DEAResult,
) -> None:
    before_summary = input_result.summary()
    before_targets = input_result.targets.copy(deep=True)
    before_slacks = input_result.slacks.copy(deep=True)

    prepared = prepare_radial_improvement_data(input_result, dmu_id="C")

    assert radial_improvement_route(input_result)
    assert radial_improvement_plot_applicable(input_result)
    assert prepared.native_score == pytest.approx(1.0)
    assert prepared.efficiency == pytest.approx(1.0)
    assert prepared.orientation == "input"
    assert prepared.returns_to_scale == "vrs"
    assert prepared.reference_kind == "global"
    assert prepared.is_radially_efficient
    assert not prepared.is_efficient
    assert prepared.target_status == "certified_slack_completion"
    assert prepared.max_reconstruction_residual == pytest.approx(0.0)
    assert prepared.period is None
    assert prepared.period_label is None
    assert prepared.dmu_label == "C"
    assert prepared.variable_count == 2
    assert prepared.slack_completed_variable_count == 1
    assert prepared.variables.columns.tolist() == _VARIABLE_COLUMNS

    variables = prepared.variables.set_index(["role", "variable"])
    assert variables.loc[("input", "resource"), _VARIABLE_COLUMNS[4:]].tolist() == (
        pytest.approx([1.0, 0.0, 1.0, 0.0, 1.0])
    )
    assert variables.loc[("output", "service"), _VARIABLE_COLUMNS[4:]].tolist() == (
        pytest.approx([0.5, 0.0, 0.5, 0.5, 1.0])
    )
    assert prepared.provenance == (
        ("Method", "static.radial"),
        ("Orientation", "input"),
        ("RTS", "VRS"),
        ("Reference", "global"),
    )

    pd.testing.assert_frame_equal(input_result.summary(), before_summary)
    pd.testing.assert_frame_equal(input_result.targets, before_targets)
    pd.testing.assert_frame_equal(input_result.slacks, before_slacks)
    prepared.variables.loc[0, "target"] = -999.0
    pd.testing.assert_frame_equal(input_result.targets, before_targets)


def test_output_plan_separates_score_one_from_resource_slack(
    output_result: DEAResult,
) -> None:
    prepared = prepare_radial_improvement_data(output_result, dmu_id="B")

    assert prepared.native_score == pytest.approx(1.0)
    assert prepared.efficiency == pytest.approx(1.0)
    assert prepared.orientation == "output"
    assert prepared.is_radially_efficient
    assert not prepared.is_efficient
    variables = prepared.variables.set_index(["role", "variable"])
    assert variables.loc[("input", "resource"), _VARIABLE_COLUMNS[4:]].tolist() == (
        pytest.approx([2.0, 0.0, 2.0, 1.0, 1.0])
    )
    assert variables.loc[("output", "service"), _VARIABLE_COLUMNS[4:]].tolist() == (
        pytest.approx([1.0, 0.0, 1.0, 0.0, 1.0])
    )


def test_multidimensional_plan_reconstructs_each_original_unit_account() -> None:
    frame = load_dataset("slacks_2x2")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["labor", "capital"],
        outputs=["service", "quality"],
    )
    result = BCC(orientation="input").fit(data)
    prepared = prepare_radial_improvement_data(result, dmu_id="E")

    assert prepared.variable_count == 4
    variable_keys = prepared.variables[["role", "variable"]].to_records(index=False)
    assert variable_keys.tolist() == [
        ("input", "labor"),
        ("input", "capital"),
        ("output", "service"),
        ("output", "quality"),
    ]
    variables = prepared.variables
    input_rows = variables["role"].eq("input")
    output_rows = variables["role"].eq("output")
    assert variables.loc[input_rows, "radial_target"].to_numpy() == pytest.approx(
        variables.loc[input_rows, "observed"].to_numpy() * prepared.native_score
    )
    assert variables.loc[output_rows, "radial_target"].to_numpy() == pytest.approx(
        variables.loc[output_rows, "observed"].to_numpy()
    )
    assert variables.loc[input_rows, "target"].to_numpy() == pytest.approx(
        (
            variables.loc[input_rows, "radial_target"]
            - variables.loc[input_rows, "slack_completion"]
        ).to_numpy()
    )
    assert variables.loc[output_rows, "target"].to_numpy() == pytest.approx(
        (
            variables.loc[output_rows, "radial_target"]
            + variables.loc[output_rows, "slack_completion"]
        ).to_numpy()
    )
    assert result.summary().set_index("dmu_id").loc["E", "max_slack"] == (
        pytest.approx(variables["slack_completion"].max())
    )
    assert "scaled_slack_completion" not in variables


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
@pytest.mark.parametrize("orientation", ["input", "output"])
def test_contract_supports_all_classical_rts_and_orientations(
    returns_to_scale: str,
    orientation: str,
) -> None:
    result = RadialDEA(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
    ).fit(_three_branch_data())

    assert radial_improvement_route(result)
    assert radial_improvement_plot_applicable(result)
    prepared = prepare_radial_improvement_data(result, dmu_id="A")
    assert prepared.orientation == orientation
    assert prepared.returns_to_scale == returns_to_scale


def test_panel_requires_and_preserves_period_selection() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "C", "A", "B", "C"],
            "year": [2020, 2020, 2020, 2021, 2021, 2021],
            "resource": [1.0, 2.0, 1.0, 1.2, 2.4, 1.2],
            "service": [1.0, 1.0, 0.5, 1.2, 1.2, 0.6],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        period="year",
        inputs="resource",
        outputs="service",
    )
    result = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        reference=ReferenceSpec("contemporaneous"),
    ).fit(data)

    assert radial_improvement_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="requires period"):
        prepare_radial_improvement_data(result, dmu_id="C")
    prepared = prepare_radial_improvement_data(result, dmu_id="C", period=2021)
    assert prepared.period == 2021
    assert prepared.period_label == "2021"
    assert prepared.reference_kind == "contemporaneous"
    assert prepared.variables.set_index("role").loc["output", "target"] == (
        pytest.approx(1.2)
    )


def test_peer_and_dual_publication_are_not_required(input_result: DEAResult) -> None:
    summary = input_result.summary()
    summary[["peer_valid", "dual_valid"]] = False
    summary[["peer_status", "dual_status"]] = "publication_withheld"
    result = replace(
        input_result,
        summary_frame=summary,
        intensities=pd.DataFrame({"unrelated": [1]}),
        duals=pd.DataFrame({"unrelated": [1]}),
    )

    assert radial_improvement_plot_applicable(result)
    assert prepare_radial_improvement_data(result, dmu_id="C").target_status == (
        "certified_slack_completion"
    )


def test_score_only_radial_fit_does_not_advertise_improvement() -> None:
    result = RadialDEA(compute_slacks=False).fit(_three_branch_data())

    assert radial_improvement_route(result)
    assert not radial_improvement_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="slack completion"):
        prepare_radial_improvement_data(result, dmu_id="C")


@pytest.mark.parametrize(
    ("fault", "message"),
    [
        ("method", "exact method_id"),
        ("expanded_orientation", "black-box radial account"),
        ("within_reference", "within the fitted reference"),
        ("score_valid", "defined valid radial score"),
        ("classification", "classification does not reconstruct"),
        ("phase_certificate", "both phases"),
        ("target", "does not reconstruct"),
        ("slack", "does not reconstruct"),
        ("summary_max_slack", "does not reconstruct"),
    ],
)
def test_semantic_certificate_and_ledger_tampering_fails_closed(
    input_result: DEAResult,
    fault: str,
    message: str,
) -> None:
    result = input_result
    if fault in {"method", "expanded_orientation"}:
        metadata = _metadata_copy(input_result)
        if fault == "method":
            metadata["method_id"] = "static.radial.neighbor"
        else:
            metadata["expanded_spec"]["performance"]["orientation"] = "output"
        result = replace(input_result, metadata=metadata)
    elif fault in {
        "within_reference",
        "score_valid",
        "classification",
        "summary_max_slack",
    }:
        summary = input_result.summary()
        if fault == "within_reference":
            summary["is_within_reference_technology"] = False
        elif fault == "score_valid":
            summary["score_valid"] = False
        elif fault == "classification":
            summary["is_efficient"] = ~summary["is_efficient"].astype(bool)
        else:
            summary["max_slack"] = 0.25
        result = replace(input_result, summary_frame=summary)
    elif fault == "phase_certificate":
        diagnostics = input_result.diagnostics.copy(deep=True)
        selected = diagnostics["phase"].eq(2)
        diagnostics.loc[selected, "economic_postsolve_certified"] = False
        result = replace(input_result, diagnostics=diagnostics)
    elif fault == "target":
        targets = input_result.targets.copy(deep=True)
        selected = targets["role"].eq("output")
        targets.loc[selected, "target"] += 0.1
        result = replace(input_result, targets=targets)
    else:
        slacks = input_result.slacks.copy(deep=True)
        selected = slacks["role"].eq("output")
        slacks.loc[selected, "slack"] += 0.1
        result = replace(input_result, slacks=slacks)

    if fault == "method":
        assert not radial_improvement_route(result)
    assert not radial_improvement_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match=message):
        prepare_radial_improvement_data(result, dmu_id="C")


def test_scaled_slack_magnitudes_are_not_republished_as_original_unit_evidence(
    input_result: DEAResult,
) -> None:
    baseline = prepare_radial_improvement_data(input_result, dmu_id="C")
    slacks = input_result.slacks.copy(deep=True)
    slacks.loc[:, "scaled_slack"] = 123.0
    result = replace(input_result, slacks=slacks)

    prepared = prepare_radial_improvement_data(result, dmu_id="C")
    pd.testing.assert_frame_equal(prepared.variables, baseline.variables)
    assert "scaled_slack_completion" not in prepared.variables


def test_prepared_labels_are_bounded_control_free_and_preserve_acronyms() -> None:
    raw_dmu = "C\n" + "x" * 80
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", raw_dmu],
            "CO2": [1.0, 2.0, 1.0],
            "service_name_with_a_control\n" + "z" * 50: [1.0, 1.0, 0.5],
        }
    )
    output = frame.columns[-1]
    data = DEAData.from_frame(frame, dmu="unit", inputs="CO2", outputs=output)
    result = BCC(orientation="input").fit(data)
    prepared = prepare_radial_improvement_data(result, dmu_id=raw_dmu)

    assert "\n" not in prepared.dmu_label
    assert len(prepared.dmu_label) == 36
    assert prepared.dmu_label.endswith("…")
    assert prepared.variables.iloc[0]["variable_label"] == "CO2"
    output_label = prepared.variables.iloc[1]["variable_label"]
    assert "\n" not in output_label
    assert len(output_label) == 32
    assert output_label.endswith("…")


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


def test_discovery_and_preparation_add_no_solver_calls() -> None:
    solver = _CountingSolver()
    result = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        solver=solver,
    ).fit(_three_branch_data())
    fitted_calls = solver.calls

    assert radial_improvement_route(result)
    assert radial_improvement_plot_applicable(result)
    prepare_radial_improvement_data(result, dmu_id="C")
    assert solver.calls == fitted_calls
    assert result.metadata["solver_calls"] == fitted_calls


def test_radial_improvement_discovery_is_backend_lazy() -> None:
    code = """
import sys
import pandas as pd
from deapack import BCC, DEAData
from deapack.visualization.radial_improvement import (
    prepare_radial_improvement_data,
    radial_improvement_plot_applicable,
)
data = DEAData.from_frame(
    pd.DataFrame({
        'unit': ['A', 'B', 'C'],
        'resource': [1.0, 2.0, 1.0],
        'service': [1.0, 1.0, 0.5],
    }),
    dmu='unit',
    inputs='resource',
    outputs='service',
)
result = BCC(orientation='input').fit(data)
assert radial_improvement_plot_applicable(result)
prepare_radial_improvement_data(result, dmu_id='C')
assert not any(
    name == 'matplotlib' or name.startswith('matplotlib.')
    for name in sys.modules
)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
