from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from deapack import DDF, RDM, DEAData, DEAResult, load_dataset
from deapack.solvers import SciPyHiGHSSolver
from deapack.visualization import PlotNotAvailableError
from deapack.visualization.directional_improvement import (
    directional_ddf_improvement_plot_applicable,
    directional_ddf_improvement_route,
    prepare_directional_ddf_improvement_data,
)


def _data() -> DEAData:
    return DEAData.from_frame(
        load_dataset("slacks_2x2"),
        dmu="dmu",
        inputs=["labor", "capital"],
        outputs=["service", "quality"],
    )


@pytest.fixture(scope="module")
def ddf_result() -> DEAResult:
    return DDF(
        input_direction="observed",
        output_direction="observed",
        returns_to_scale="vrs",
    ).fit(_data())


def _metadata_copy(result: DEAResult) -> dict[str, object]:
    return json.loads(json.dumps(result.metadata))


def test_preparer_reconstructs_the_declared_and_slack_completed_plan(
    ddf_result: DEAResult,
) -> None:
    before_summary = ddf_result.summary()
    before_targets = ddf_result.targets.copy(deep=True)
    before_slacks = ddf_result.slacks.copy(deep=True)
    prepared = prepare_directional_ddf_improvement_data(ddf_result, dmu_id="E")

    assert directional_ddf_improvement_route(ddf_result)
    assert directional_ddf_improvement_plot_applicable(ddf_result)
    assert [plot.kind for plot in ddf_result.available_plots()] == [
        "performance",
        "improvement",
        "references",
    ]
    assert prepared.beta == pytest.approx(0.2472527472527472)
    assert prepared.max_reconstruction_residual <= 1e-12
    assert prepared.dmu_label == "E"
    assert prepared.period_label is None
    assert prepared.variable_count == 4
    assert prepared.slack_completed_variable_count == 2
    variables = prepared.variables.set_index(["role", "variable"])
    expected = {
        ("input", "labor"): (2.0, 1.5054945054945055, 1.5054945054945055),
        ("input", "capital"): (2.8, 2.1076923076923078, 2.1076923076923078),
        ("output", "service"): (1.3, 1.6214285714285714, 1.6527472527472529),
        ("output", "quality"): (0.62, 0.7732967032967033, 0.8305494505494505),
    }
    for key, (observed, directional_target, target) in expected.items():
        assert variables.loc[key, "observed"] == pytest.approx(observed)
        assert variables.loc[key, "directional_target"] == pytest.approx(
            directional_target
        )
        assert variables.loc[key, "target"] == pytest.approx(target)
    assert variables.loc[("output", "service"), "slack_completion"] == (
        pytest.approx(0.031318681318681346)
    )
    assert variables.loc[("output", "quality"), "slack_completion"] == (
        pytest.approx(0.05725274725274716)
    )
    assert (
        prepared.variables["slack_completion"] / prepared.variables["slack_scale"]
    ).to_numpy() == pytest.approx(
        prepared.variables["scaled_slack_completion"].to_numpy()
    )

    pd.testing.assert_frame_equal(ddf_result.summary(), before_summary)
    pd.testing.assert_frame_equal(ddf_result.targets, before_targets)
    pd.testing.assert_frame_equal(ddf_result.slacks, before_slacks)
    prepared.variables.loc[0, "target"] = -999.0
    pd.testing.assert_frame_equal(ddf_result.targets, before_targets)


def test_input_only_and_custom_global_directions_keep_their_fitted_meaning() -> None:
    output_only = DDF(
        input_direction="zeros",
        output_direction="observed",
    ).fit(_data())
    output_plan = prepare_directional_ddf_improvement_data(output_only, dmu_id="E")
    assert (
        output_plan.variables.query("role == 'input'")["directional_change"]
        .eq(0.0)
        .all()
    )

    custom = DDF(
        input_direction={"labor": 0.5, "capital": 1.25},
        output_direction={"service": 0.2, "quality": 0.1},
    ).fit(_data())
    custom_plan = prepare_directional_ddf_improvement_data(custom, dmu_id="E")
    assert custom_plan.variables["direction"].tolist() == pytest.approx(
        [0.5, 1.25, 0.2, 0.1]
    )


def test_nonlocal_directions_are_verified_from_public_ledgers() -> None:
    mean_result = DDF(input_direction="mean", output_direction="mean").fit(_data())
    assert directional_ddf_improvement_plot_applicable(mean_result)
    prepare_directional_ddf_improvement_data(mean_result, dmu_id="E")

    input_directions = np.tile([0.5, 1.25], (_data().n_dmus, 1))
    output_directions = np.tile([0.2, 0.1], (_data().n_dmus, 1))
    by_observation = DDF(
        input_direction=input_directions,
        output_direction=output_directions,
    ).fit(_data())
    assert directional_ddf_improvement_plot_applicable(by_observation)
    prepare_directional_ddf_improvement_data(by_observation, dmu_id="E")

    targets = by_observation.targets.copy(deep=True)
    selected = (
        targets["dmu_id"].eq("A")
        & targets["role"].eq("input")
        & targets["variable"].eq("labor")
    )
    targets.loc[selected, "direction"] += 0.25
    tampered = replace(by_observation, targets=targets)
    assert not directional_ddf_improvement_plot_applicable(tampered)
    with pytest.raises(PlotNotAvailableError, match="numeric fingerprint"):
        prepare_directional_ddf_improvement_data(tampered, dmu_id="E")


def test_target_account_does_not_depend_on_peer_or_dual_publication(
    ddf_result: DEAResult,
) -> None:
    summary = ddf_result.summary()
    summary[["peer_valid", "dual_valid"]] = False
    summary[["peer_status", "dual_status"]] = "publication_withheld"
    result = replace(
        ddf_result,
        summary_frame=summary,
        intensities=pd.DataFrame({"unrelated": [1]}),
        duals=pd.DataFrame({"unrelated": [1]}),
    )

    assert directional_ddf_improvement_plot_applicable(result)
    prepared = prepare_directional_ddf_improvement_data(result, dmu_id="E")
    assert prepared.target_status == "certified_slack_completion"


def test_nonmaximum_scaled_slack_is_reconstructed_row_by_row(
    ddf_result: DEAResult,
) -> None:
    slacks = ddf_result.slacks.copy(deep=True)
    selected = slacks["dmu_id"].eq("E") & slacks["variable"].eq("service")
    slacks.loc[selected, "scaled_slack"] = 0.0
    result = replace(ddf_result, slacks=slacks)

    with pytest.raises(PlotNotAvailableError, match="does not reconstruct"):
        prepare_directional_ddf_improvement_data(result, dmu_id="E")


def test_neighboring_directional_contracts_do_not_inherit_the_route() -> None:
    no_completion = DDF(compute_slacks=False).fit(_data())
    range_result = RDM().fit(_data())

    for result in (no_completion, range_result):
        assert not directional_ddf_improvement_plot_applicable(result)
        assert "improvement" not in {plot.kind for plot in result.available_plots()}


def test_prepared_labels_are_bounded_control_free_and_preserve_acronyms() -> None:
    frame = load_dataset("slacks_2x2").rename(columns={"labor": "CO2"})
    raw_dmu = "E\n" + "x" * 80
    frame.loc[frame["dmu"].eq("E"), "dmu"] = raw_dmu
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["CO2", "capital"],
        outputs=["service", "quality"],
    )
    result = DDF().fit(data)
    prepared = prepare_directional_ddf_improvement_data(result, dmu_id=raw_dmu)

    assert "\n" not in prepared.dmu_label
    assert len(prepared.dmu_label) == 36
    assert prepared.dmu_label.endswith("…")
    assert prepared.variables.iloc[0]["variable_label"] == "CO2"


@pytest.mark.parametrize(
    ("fault", "message"),
    [
        ("method", "exact ordinary static"),
        ("expanded_technology", "black-box operating account"),
        ("expanded_estimator", "black-box operating account"),
        ("primary_status", "optimal primary"),
        ("completion_valid", "certified slack completion"),
        ("phase_certificate", "both phases"),
        ("directional_change", "does not reconstruct"),
        ("slack", "does not reconstruct"),
        ("scaled_slack", "does not reconstruct"),
        ("negative_quantity", "must be nonnegative"),
    ],
)
def test_semantic_certificate_and_ledger_tampering_fails_closed(
    ddf_result: DEAResult,
    fault: str,
    message: str,
) -> None:
    result = ddf_result
    if fault in {"method", "expanded_technology", "expanded_estimator"}:
        metadata = _metadata_copy(ddf_result)
        if fault == "method":
            metadata["method_id"] = "static.directional_distance.specialized"
        elif fault == "expanded_technology":
            metadata["expanded_spec"]["technology"]["family"] = "other"
        else:
            metadata["expanded_spec"]["estimator"]["family"] = "sfa"
        result = replace(ddf_result, metadata=metadata)
    elif fault in {"primary_status", "completion_valid"}:
        summary = ddf_result.summary()
        if fault == "primary_status":
            summary["primary_solver_status"] = "failed"
        else:
            summary["completion_valid"] = False
        result = replace(ddf_result, summary_frame=summary)
    elif fault == "phase_certificate":
        diagnostics = ddf_result.diagnostics.copy(deep=True)
        selected = diagnostics["phase"].eq(2)
        diagnostics.loc[selected, "economic_postsolve_certified"] = False
        result = replace(ddf_result, diagnostics=diagnostics)
    elif fault in {"directional_change", "negative_quantity"}:
        targets = ddf_result.targets.copy(deep=True)
        selected = targets["variable"].eq("labor")
        if fault == "directional_change":
            targets.loc[selected, "directional_change"] += 0.1
        else:
            delta = -2.0 - float(targets.loc[selected, "observed"].iloc[0])
            targets.loc[selected, "observed"] = -2.0
            targets.loc[selected, "target"] += delta
        result = replace(ddf_result, targets=targets)
    else:
        slacks = ddf_result.slacks.copy(deep=True)
        selected = slacks["variable"].eq("service")
        if fault == "slack":
            slacks.loc[selected, "slack"] += 0.1
        else:
            slacks.loc[:, "scaled_slack"] = 0.123
        result = replace(ddf_result, slacks=slacks)

    assert not directional_ddf_improvement_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match=message):
        prepare_directional_ddf_improvement_data(result, dmu_id="E")


def test_discovery_rejects_a_large_table_level_fault_before_deep_preparation(
    ddf_result: DEAResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.visualization.directional_improvement as module

    template = ddf_result.summary().iloc[[4]].copy(deep=True)
    summary = pd.concat([template] * 2_000, ignore_index=True)
    summary["dmu_id"] = [f"D{position:04d}" for position in range(len(summary))]
    summary["period"] = None
    result = replace(
        ddf_result,
        summary_frame=summary,
        targets=ddf_result.targets.drop(columns="direction"),
    )

    def _deep_preparation_is_forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("table preflight must reject before candidate preparation")

    monkeypatch.setattr(
        module,
        "prepare_directional_ddf_improvement_data",
        _deep_preparation_is_forbidden,
    )
    assert not module.directional_ddf_improvement_plot_applicable(result)


def test_discovery_indexes_many_locally_invalid_candidates_once(
    ddf_result: DEAResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.visualization.directional_improvement as module

    count = 2_000
    dmu_ids = [f"D{position:04d}" for position in range(count)]
    summary = pd.concat(
        [ddf_result.summary().query("dmu_id == 'E'")] * count,
        ignore_index=True,
    )
    summary["dmu_id"] = dmu_ids

    def repeat_rows(frame: pd.DataFrame) -> pd.DataFrame:
        repeated = pd.concat([frame] * count, ignore_index=True)
        repeated["dmu_id"] = np.repeat(dmu_ids, len(frame))
        return repeated

    targets = repeat_rows(ddf_result.targets_for("E"))
    slacks = repeat_rows(ddf_result.slacks.query("dmu_id == 'E'"))
    diagnostics = repeat_rows(ddf_result.diagnostics.query("dmu_id == 'E'"))
    diagnostics["economic_postsolve_certified"] = False
    result = replace(
        ddf_result,
        summary_frame=summary,
        targets=targets,
        slacks=slacks,
        diagnostics=diagnostics,
    )

    def _reconstruction_is_forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("invalid local certificates must stop before ledgers")

    monkeypatch.setattr(module, "_reconstruct_plan", _reconstruction_is_forbidden)
    assert not module.directional_ddf_improvement_plot_applicable(result)


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


def test_discovery_preparation_and_rendering_add_no_solver_calls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("MPL_IGNORE_SYSTEM_FONTS", "1")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    pyplot = pytest.importorskip("matplotlib.pyplot")
    solver = _CountingSolver()
    result = DDF(solver=solver).fit(_data())
    fitted_calls = solver.calls

    assert directional_ddf_improvement_plot_applicable(result)
    prepare_directional_ddf_improvement_data(result, dmu_id="E")
    figure = result.plot(kind="improvement", dmu_id="E")
    assert solver.calls == fitted_calls
    assert result.metadata["additional_solver_calls"] == 0
    pyplot.close(figure)


def test_directional_improvement_discovery_is_backend_lazy() -> None:
    code = """
import sys
from deapack import DEAData, DDF, load_dataset
frame = load_dataset('slacks_2x2')
data = DEAData.from_frame(
    frame,
    dmu='dmu',
    inputs=['labor', 'capital'],
    outputs=['service', 'quality'],
)
result = DDF().fit(data)
assert 'improvement' in {plot.kind for plot in result.available_plots()}
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


def test_renderer_is_a_managerial_original_unit_ledger(
    ddf_result: DEAResult,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("MPL_IGNORE_SYSTEM_FONTS", "1")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    pyplot = pytest.importorskip("matplotlib.pyplot")

    def _show_is_forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("plot() must not call pyplot.show()")

    monkeypatch.setattr(pyplot, "show", _show_is_forbidden)
    figure = ddf_result.plot(kind="improvement", dmu_id="E")
    text = " ".join(
        item.get_text()
        for item in [
            *figure.texts,
            *(label for axis in figure.axes for label in axis.texts),
        ]
    )
    assert figure._suptitle.get_text() == "Directional benchmark account for E"
    assert len(figure.axes) == 1
    assert not figure.axes[0].axison
    for phrase in (
        "DEA-certified benchmark account for a declared programme",
        "β = 0.247253",
        "largest multiple represented as feasible by the fitted DEA technology",
        "βg is reported below in each variable's original unit",
        "Observed operation",
        "Target promised by βg",
        "Selected completed target",
        "Declared resource saving",
        "Declared service addition",
        "Slack completion",
        "no common quantity axis",
        "conditional on the fitted DEA technology",
        "not a generic inefficiency percentage",
        "not a unique plan",
        "engineering prescription",
        "causal explanation",
        "least-cost plan",
        "Method: static.directional_distance",
        "RTS: VRS",
    ):
        assert phrase in text
    assert "1 / (1 + β)" not in text
    assert re.search(r"\bpeer\b", text.casefold()) is None
    assert re.search(r"\bdual\b", text.casefold()) is None
    pyplot.close(figure)
