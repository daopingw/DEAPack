from __future__ import annotations

import subprocess
import sys
import textwrap
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from deapack import (
    SBM,
    AdditiveDEA,
    DEAData,
    DEAResult,
    InputSBM,
    OutputSBM,
    ReferenceSpec,
    UndesirableSlacksBasedDEA,
    dataset_info,
    load_dataset,
)
from deapack.visualization import (
    PlotNotAvailableError,
    available_plots,
    prepare_sbm_improvement_data,
    sbm_improvement_plot_applicable,
)

_FOCAL_DMU = "Uneven"
_ALTERNATE_DMU = "Balanced"
_FOCAL_INPUT = "resource_a"


def _data() -> DEAData:
    frame = load_dataset("sbm_slack_contrast")
    roles = dataset_info("sbm_slack_contrast").roles
    return DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )


def _fit(model: type[SBM] = SBM) -> DEAResult:  # type: ignore[valid-type]
    return model(returns_to_scale="crs").fit(_data())


def _environmental_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "C"],
                "resource": [1.0, 2.0],
                "service": [2.0, 1.0],
                "residual": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )


@pytest.fixture(scope="module")
def joint_result() -> DEAResult:
    return _fit()


@pytest.fixture(scope="module")
def environmental_result() -> DEAResult:
    return UndesirableSlacksBasedDEA(returns_to_scale="vrs").fit(_environmental_data())


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_thaw(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return {_thaw(item) for item in value}
    return value


def _replace_nested(mapping: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    selected = mapping
    for key in path[:-1]:
        selected = selected[key]
    selected[path[-1]] = value


def test_sbm_improvement_discovery_is_backend_independent() -> None:
    command = textwrap.dedent(
        """
        import sys
        from deapack import DEAData, SBM, dataset_info, load_dataset

        frame = load_dataset('sbm_slack_contrast')
        roles = dataset_info('sbm_slack_contrast').roles
        data = DEAData.from_frame(
            frame,
            dmu=roles['dmu'],
            inputs=roles['inputs'],
            outputs=roles['outputs'],
        )
        result = SBM(returns_to_scale='crs').fit(data)
        assert [plot.kind for plot in result.available_plots()] == [
            'performance', 'improvement', 'references',
        ]
        assert not any(
            name == 'matplotlib' or name.startswith('matplotlib.')
            for name in sys.modules
        )
        """
    )
    subprocess.run([sys.executable, "-c", command], check=True)


def test_global_plot_registry_describes_the_improvement_account() -> None:
    plots = available_plots()

    assert [plot.kind for plot in plots] == [
        "performance",
        "frontier",
        "trajectory",
        "process",
        "improvement",
        "metafrontier",
        "references",
    ]
    improvement = next(plot for plot in plots if plot.kind == "improvement")
    assert improvement.title == "Variable-specific operating plan"
    assert improvement.default_metric is None
    assert improvement.views == ("auto",)


def test_exact_joint_sbm_plan_is_reconstructed_without_mutation(
    joint_result: DEAResult,
) -> None:
    before_summary = joint_result.summary()
    before_targets = joint_result.targets.copy(deep=True)
    before_slacks = joint_result.slacks.copy(deep=True)
    before_diagnostics = joint_result.diagnostics.copy(deep=True)

    prepared = prepare_sbm_improvement_data(joint_result, dmu_id=_FOCAL_DMU)

    assert prepared.orientation == "non-oriented"
    assert prepared.returns_to_scale == "crs"
    assert prepared.efficiency == pytest.approx(5.0 / 18.0)
    assert prepared.input_account == pytest.approx(5.0 / 12.0)
    assert prepared.output_expansion_account == pytest.approx(1.5)
    assert prepared.variable_count == 4
    assert prepared.scored_variable_count == 4
    assert prepared.selection_status == "solver_selected_primary_optimum"
    assert prepared.max_reconstruction_residual <= 1e-12
    assert prepared.variables[["role", "variable"]].apply(tuple, axis=1).tolist() == [
        ("input", "resource_a"),
        ("input", "resource_b"),
        ("output", "core_service"),
        ("output", "quality_service"),
    ]
    assert prepared.variables["observed"].tolist() == [2.0, 3.0, 2.0, 1.0]
    assert prepared.variables["target"].tolist() == pytest.approx([1.0, 1.0, 2.0, 2.0])
    assert prepared.variables["signed_proportional_change"].tolist() == pytest.approx(
        [-0.5, -2.0 / 3.0, 0.0, 1.0]
    )

    assert_frame_equal(joint_result.summary(), before_summary)
    assert_frame_equal(joint_result.targets, before_targets)
    assert_frame_equal(joint_result.slacks, before_slacks)
    assert_frame_equal(joint_result.diagnostics, before_diagnostics)


def test_prepared_variable_ledger_is_detached(joint_result: DEAResult) -> None:
    prepared = prepare_sbm_improvement_data(joint_result, dmu_id=_FOCAL_DMU)
    original = joint_result.targets.loc[
        joint_result.targets["dmu_id"].eq(_FOCAL_DMU)
        & joint_result.targets["variable"].eq(_FOCAL_INPUT),
        "target",
    ].iloc[0]

    prepared.variables.loc[0, "target"] = -999.0

    assert (
        joint_result.targets.loc[
            joint_result.targets["dmu_id"].eq(_FOCAL_DMU)
            & joint_result.targets["variable"].eq(_FOCAL_INPUT),
            "target",
        ].iloc[0]
        == original
    )


def test_exact_two_plant_environmental_plan_reconstructs_all_accounts(
    environmental_result: DEAResult,
) -> None:
    prepared = prepare_sbm_improvement_data(environmental_result, dmu_id="C")

    assert prepared.orientation == "non-oriented"
    assert prepared.returns_to_scale == "vrs"
    assert prepared.efficiency == pytest.approx(2.0 / 7.0)
    assert prepared.input_account == pytest.approx(0.5)
    assert prepared.output_expansion_account == pytest.approx(1.75)
    assert prepared.variable_count == 3
    assert prepared.scored_variable_count == 3
    assert prepared.max_reconstruction_residual <= 1e-12
    assert prepared.variables[["role", "variable"]].apply(tuple, axis=1).tolist() == [
        ("input", "resource"),
        ("output", "service"),
        ("bad_output", "residual"),
    ]
    assert prepared.variables["observed"].tolist() == [2.0, 1.0, 2.0]
    assert prepared.variables["target"].tolist() == [1.0, 2.0, 1.0]
    assert prepared.variables["normalized_slack"].tolist() == [0.5, 1.0, 0.5]
    assert prepared.variables["signed_proportional_change"].tolist() == [
        -0.5,
        1.0,
        -0.5,
    ]
    assert prepared.variables["average_weight"].tolist() == [1.0, 0.5, 0.5]
    assert dict(prepared.provenance)["Method"] == ("environmental.sbm.separable_strong")


def test_certified_external_environmental_sbm_plan_can_be_displayed() -> None:
    result = UndesirableSlacksBasedDEA(
        returns_to_scale="vrs",
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
    ).fit(_environmental_data())
    row = result.summary().set_index("dmu_id").loc["C"]

    assert not bool(row["self_in_reference"])
    assert bool(row["is_within_reference_technology"])
    assert row["membership_status"] == "certified_by_sbm_balance_account"
    prepared = prepare_sbm_improvement_data(result, dmu_id="C")
    assert prepared.efficiency == pytest.approx(2.0 / 7.0)


def test_environmental_preparation_is_detached_and_does_not_mutate_result(
    environmental_result: DEAResult,
) -> None:
    before_summary = environmental_result.summary()
    before_targets = environmental_result.targets.copy(deep=True)
    before_slacks = environmental_result.slacks.copy(deep=True)
    before_diagnostics = environmental_result.diagnostics.copy(deep=True)

    prepared = prepare_sbm_improvement_data(environmental_result, dmu_id="C")
    prepared.variables.loc[
        prepared.variables["role"].eq("bad_output"), "target"
    ] = -999.0

    assert_frame_equal(environmental_result.summary(), before_summary)
    assert_frame_equal(environmental_result.targets, before_targets)
    assert_frame_equal(environmental_result.slacks, before_slacks)
    assert_frame_equal(environmental_result.diagnostics, before_diagnostics)


def test_environmental_result_discovers_the_existing_improvement_kind(
    environmental_result: DEAResult,
) -> None:
    assert sbm_improvement_plot_applicable(environmental_result)
    assert [plot.kind for plot in environmental_result.available_plots()] == [
        "performance",
        "improvement",
    ]


@pytest.mark.parametrize(
    ("model", "orientation", "scored_roles", "efficiency"),
    [
        (InputSBM, "input", {"input"}, 5.0 / 12.0),
        (OutputSBM, "output", {"output"}, 1.0 / 3.0),
        (SBM, "non-oriented", {"input", "output"}, 5.0 / 18.0),
    ],
)
def test_all_three_mainstream_orientations_keep_their_management_mandate(
    model: type[Any],
    orientation: str,
    scored_roles: set[str],
    efficiency: float,
) -> None:
    prepared = prepare_sbm_improvement_data(_fit(model), dmu_id=_FOCAL_DMU)

    assert prepared.orientation == orientation
    assert prepared.efficiency == pytest.approx(efficiency)
    scored = prepared.variables.loc[prepared.variables["included_in_objective"], "role"]
    assert set(scored) == scored_roles


def test_input_orientation_labels_output_rows_as_feasibility_only() -> None:
    prepared = prepare_sbm_improvement_data(_fit(InputSBM), dmu_id=_FOCAL_DMU)
    output_rows = prepared.variables.loc[prepared.variables["role"].eq("output")]

    assert not output_rows["included_in_objective"].any()
    assert prepared.efficiency == pytest.approx(5.0 / 12.0)
    assert prepared.scored_variable_count == 2


def test_additive_result_does_not_receive_the_improvement_plot() -> None:
    additive = AdditiveDEA().fit(_data())
    assert not sbm_improvement_plot_applicable(additive)
    assert "improvement" not in {plot.kind for plot in additive.available_plots()}
    with pytest.raises(PlotNotAvailableError, match="classic static SBM"):
        prepare_sbm_improvement_data(additive, dmu_id=_FOCAL_DMU)


@pytest.mark.parametrize(
    "method_id",
    [
        "environmental.sbm.nonseparable_hybrid.tone_2003",
        "environmental.ddf.weak_disposal.activity_specific",
        "network.sbm.tone_tsutsui_2009",
        "dynamic.sbm.tone_tsutsui_2010",
    ],
)
def test_exact_method_gate_rejects_neighboring_nonseparable_weak_and_structural_models(
    environmental_result: DEAResult,
    method_id: str,
) -> None:
    metadata = _thaw(environmental_result.metadata)
    metadata["method_id"] = method_id
    result = replace(environmental_result, metadata=metadata)

    assert not sbm_improvement_plot_applicable(result)
    assert "improvement" not in {plot.kind for plot in result.available_plots()}
    with pytest.raises(PlotNotAvailableError, match="exact strong-separable"):
        prepare_sbm_improvement_data(result, dmu_id="C")


def test_improvement_dispatch_rejects_inapplicable_controls(
    joint_result: DEAResult,
) -> None:
    with pytest.raises(PlotNotAvailableError, match="requires dmu_id"):
        joint_result.plot(kind="improvement")
    with pytest.raises(PlotNotAvailableError, match="metric and variable"):
        joint_result.plot(kind="improvement", dmu_id=_FOCAL_DMU, metric="efficiency")
    with pytest.raises(PlotNotAvailableError, match="metric and variable"):
        joint_result.plot(kind="improvement", dmu_id=_FOCAL_DMU, variable=_FOCAL_INPUT)
    with pytest.raises(PlotNotAvailableError, match="view='auto'"):
        joint_result.plot(kind="improvement", dmu_id=_FOCAL_DMU, view="points")


def test_panel_observation_requires_an_explicit_period() -> None:
    original = load_dataset("sbm_slack_contrast")
    first = original.copy()
    first["period"] = 2020
    second = original.copy()
    second["period"] = 2021
    frame = pd.concat([first, second], ignore_index=True)
    roles = dataset_info("sbm_slack_contrast").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        period="period",
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    result = SBM(returns_to_scale="crs", reference="contemporaneous").fit(data)

    with pytest.raises(PlotNotAvailableError, match="requires period"):
        prepare_sbm_improvement_data(result, dmu_id=_FOCAL_DMU)
    prepared = prepare_sbm_improvement_data(result, dmu_id=_FOCAL_DMU, period=2021)
    assert prepared.period == 2021


def test_unknown_observation_lists_available_choices(joint_result: DEAResult) -> None:
    with pytest.raises(PlotNotAvailableError, match="available observations"):
        prepare_sbm_improvement_data(joint_result, dmu_id="missing")


@pytest.mark.parametrize(
    ("table", "column"),
    [
        ("targets", "target"),
        ("targets", "observed"),
        ("slacks", "slack"),
        ("slacks", "normalized_slack"),
        ("slacks", "normalizer"),
    ],
)
def test_nonfinite_or_inconsistent_plan_quantities_fail_closed(
    joint_result: DEAResult,
    table: str,
    column: str,
) -> None:
    frame = getattr(joint_result, table).copy(deep=True)
    mask = frame["dmu_id"].eq(_FOCAL_DMU) & frame["variable"].eq(_FOCAL_INPUT)
    frame.loc[mask, column] = np.nan if column != "target" else -999.0
    result = replace(joint_result, **{table: frame})

    assert sbm_improvement_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError):
        prepare_sbm_improvement_data(result, dmu_id=_FOCAL_DMU)
    assert (
        prepare_sbm_improvement_data(result, dmu_id=_ALTERNATE_DMU).dmu_id
        == _ALTERNATE_DMU
    )


def test_score_or_postsolve_certificate_corruption_fails_closed(
    joint_result: DEAResult,
) -> None:
    summary = joint_result.summary()
    summary.loc[summary["dmu_id"].eq(_FOCAL_DMU), "score_valid"] = False
    invalid_score = replace(joint_result, summary_frame=summary)
    with pytest.raises(PlotNotAvailableError, match="score_valid=True"):
        prepare_sbm_improvement_data(invalid_score, dmu_id=_FOCAL_DMU)

    diagnostics = joint_result.diagnostics.copy(deep=True)
    diagnostics.loc[
        diagnostics["dmu_id"].eq(_FOCAL_DMU), "economic_postsolve_certified"
    ] = False
    invalid_certificate = replace(joint_result, diagnostics=diagnostics)
    with pytest.raises(PlotNotAvailableError, match="both LP and operating-account"):
        prepare_sbm_improvement_data(invalid_certificate, dmu_id=_FOCAL_DMU)


def test_metadata_and_result_tables_must_independently_agree(
    joint_result: DEAResult,
) -> None:
    cases: list[DEAResult] = []

    metadata = _thaw(joint_result.metadata)
    metadata["orientation"] = "input"
    cases.append(replace(joint_result, metadata=metadata))

    metadata = _thaw(joint_result.metadata)
    metadata["expanded_spec"]["data_roles"]["variables"]["inputs"] = ["wrong"]
    cases.append(replace(joint_result, metadata=metadata))

    metadata = _thaw(joint_result.metadata)
    metadata["expanded_spec"]["graph"]["kind"] = "general_network"
    cases.append(replace(joint_result, metadata=metadata))

    metadata = _thaw(joint_result.metadata)
    metadata["specialization_id"] = "paper_specific_leaf"
    cases.append(replace(joint_result, metadata=metadata))

    targets = joint_result.targets.copy(deep=True)
    targets.loc[targets["dmu_id"].eq(_FOCAL_DMU), "selection_status"] = "unsupported"
    cases.append(replace(joint_result, targets=targets))

    slacks = joint_result.slacks.copy(deep=True)
    duplicate = slacks.loc[
        slacks["dmu_id"].eq(_FOCAL_DMU) & slacks["variable"].eq(_FOCAL_INPUT)
    ]
    cases.append(
        replace(joint_result, slacks=pd.concat([slacks, duplicate], ignore_index=True))
    )

    slacks = joint_result.slacks.copy(deep=True)
    slacks.loc[
        slacks["dmu_id"].eq(_FOCAL_DMU) & slacks["variable"].eq(_FOCAL_INPUT),
        "average_weight",
    ] = 0.75
    cases.append(replace(joint_result, slacks=slacks))

    slacks = joint_result.slacks.copy(deep=True)
    slacks.loc[
        slacks["dmu_id"].eq(_FOCAL_DMU) & slacks["variable"].eq(_FOCAL_INPUT),
        "included_in_objective",
    ] = False
    cases.append(replace(joint_result, slacks=slacks))

    for result in cases:
        with pytest.raises(PlotNotAvailableError):
            prepare_sbm_improvement_data(result, dmu_id=_FOCAL_DMU)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("specialization_id",), "paper_specific_leaf"),
        (("method_specialization",), "paper_specific_leaf"),
        (("bad_output_disposability",), "weak"),
        (("separability",), "nonseparable"),
        (("null_jointness",), True),
        (("bad_output_constraint",), "B lambda - s_b = b_o"),
        (("bad_output_slack",), "expansion_shortfall"),
        (("output_aggregation",), "desirable_outputs_only"),
        (("expanded_spec", "graph", "kind"), "general_network"),
        (
            ("expanded_spec", "data_roles", "bad_outputs"),
            "weakly_disposable_undesirable_residuals",
        ),
        (("expanded_spec", "data_roles", "variables", "bad_outputs"), ()),
        (("expanded_spec", "data_roles", "counts", "bad_outputs"), 0),
        (
            ("expanded_spec", "performance", "orientation"),
            "non_oriented",
        ),
        (
            ("expanded_spec", "performance", "output_aggregation"),
            "desirable_outputs_only",
        ),
        (
            ("expanded_spec", "technology", "bad_output_disposal"),
            "weak_common_factor",
        ),
    ],
)
def test_environmental_metadata_semantics_fail_closed(
    environmental_result: DEAResult,
    path: tuple[str, ...],
    value: Any,
) -> None:
    metadata = _thaw(environmental_result.metadata)
    _replace_nested(metadata, path, value)
    result = replace(environmental_result, metadata=metadata)

    assert not sbm_improvement_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError):
        prepare_sbm_improvement_data(result, dmu_id="C")


@pytest.mark.parametrize(
    ("table", "column", "value"),
    [
        ("targets", "target", 3.0),
        ("targets", "observed", np.nan),
        ("targets", "selection_status", "unsupported"),
        ("targets", "role", "output"),
        ("slacks", "slack", np.nan),
        ("slacks", "normalizer", np.nan),
        ("slacks", "normalized_slack", np.nan),
        ("slacks", "average_weight", 1.0),
        ("slacks", "included_in_objective", False),
        ("slacks", "role", "output"),
    ],
)
def test_environmental_bad_output_tables_fail_closed(
    environmental_result: DEAResult,
    table: str,
    column: str,
    value: Any,
) -> None:
    frame = getattr(environmental_result, table).copy(deep=True)
    mask = frame["dmu_id"].eq("C") & frame["role"].eq("bad_output")
    frame.loc[mask, column] = value
    result = replace(environmental_result, **{table: frame})

    assert sbm_improvement_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError):
        prepare_sbm_improvement_data(result, dmu_id="C")
    assert prepare_sbm_improvement_data(result, dmu_id="A").dmu_id == "A"


@pytest.mark.parametrize("table", ["targets", "slacks"])
@pytest.mark.parametrize("mutation", ["missing", "duplicate"])
def test_environmental_role_completeness_fails_closed(
    environmental_result: DEAResult,
    table: str,
    mutation: str,
) -> None:
    frame = getattr(environmental_result, table).copy(deep=True)
    mask = frame["dmu_id"].eq("C") & frame["role"].eq("bad_output")
    if mutation == "missing":
        frame = frame.loc[~mask].copy(deep=True)
    else:
        frame = pd.concat([frame, frame.loc[mask]], ignore_index=True)
    result = replace(environmental_result, **{table: frame})

    with pytest.raises(PlotNotAvailableError, match="variable roles"):
        prepare_sbm_improvement_data(result, dmu_id="C")


@pytest.mark.parametrize(
    "column",
    [
        "input_inefficiency",
        "desirable_output_inefficiency",
        "bad_output_inefficiency",
        "output_inefficiency",
        "output_account_factor",
        "score",
        "efficiency",
    ],
)
def test_environmental_summary_accounts_are_independently_reconstructed(
    environmental_result: DEAResult,
    column: str,
) -> None:
    summary = environmental_result.summary()
    mask = summary["dmu_id"].eq("C")
    summary.loc[mask, column] = summary.loc[mask, column] + 0.125
    result = replace(environmental_result, summary_frame=summary)

    assert sbm_improvement_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="reconstruct"):
        prepare_sbm_improvement_data(result, dmu_id="C")


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("bad_output_disposability", "weak"),
        ("null_jointness", True),
        ("score_valid", False),
        ("is_within_reference_technology", False),
        ("membership_status", "outside_reference_technology"),
        ("target_valid", False),
        ("target_status", "unavailable_uncertified_target"),
    ],
)
def test_environmental_summary_semantics_fail_closed(
    environmental_result: DEAResult,
    column: str,
    value: Any,
) -> None:
    summary = environmental_result.summary()
    summary.loc[summary["dmu_id"].eq("C"), column] = value
    result = replace(environmental_result, summary_frame=summary)

    with pytest.raises(PlotNotAvailableError):
        prepare_sbm_improvement_data(result, dmu_id="C")


@pytest.mark.parametrize(
    "column",
    ["postsolve_certified", "economic_postsolve_certified"],
)
def test_environmental_certificates_fail_closed(
    environmental_result: DEAResult,
    column: str,
) -> None:
    diagnostics = environmental_result.diagnostics.copy(deep=True)
    diagnostics.loc[diagnostics["dmu_id"].eq("C"), column] = False
    result = replace(environmental_result, diagnostics=diagnostics)

    assert sbm_improvement_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="both LP and operating-account"):
        prepare_sbm_improvement_data(result, dmu_id="C")


def test_one_corrupted_dmu_does_not_hide_another_valid_plan(
    joint_result: DEAResult,
) -> None:
    summary = joint_result.summary()
    summary.loc[summary["dmu_id"].eq(_FOCAL_DMU), "score_valid"] = False
    result = replace(joint_result, summary_frame=summary)

    assert sbm_improvement_plot_applicable(result)
    assert [plot.kind for plot in result.available_plots()] == [
        "performance",
        "improvement",
        "references",
    ]
    assert (
        prepare_sbm_improvement_data(result, dmu_id=_ALTERNATE_DMU).dmu_id
        == _ALTERNATE_DMU
    )


def test_no_certified_plan_means_no_improvement_discovery(
    joint_result: DEAResult,
) -> None:
    summary = joint_result.summary()
    summary["score_valid"] = False
    result = replace(joint_result, summary_frame=summary)

    assert not sbm_improvement_plot_applicable(result)
    assert "improvement" not in {plot.kind for plot in result.available_plots()}


def test_matplotlib_improvement_plan_renders_without_showing_or_global_mutation(
    joint_result: DEAResult,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("MPL_IGNORE_SYSTEM_FONTS", "1")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    pyplot = pytest.importorskip("matplotlib.pyplot")
    figure_type = pytest.importorskip("matplotlib.figure").Figure
    before_rc = {
        key: matplotlib.rcParams[key]
        for key in ("axes.edgecolor", "font.size", "grid.color")
    }
    before_targets = joint_result.targets.copy(deep=True)
    before_slacks = joint_result.slacks.copy(deep=True)

    def _show_is_forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("plot() must not call pyplot.show()")

    monkeypatch.setattr(pyplot, "show", _show_is_forbidden)
    figure = joint_result.plot(kind="improvement", dmu_id=_FOCAL_DMU)

    assert isinstance(figure, figure_type)
    assert len(figure.axes) == 2
    assert figure._suptitle.get_text() == (
        f"Selected variable-specific operating plan for {_FOCAL_DMU}"
    )
    assert "operating gaps" in figure.axes[0].get_title(loc="left")
    assert "feasible benchmark plan" in figure.axes[1].get_title(loc="left")
    figure_text = " ".join(text.get_text() for text in figure.texts)
    assert "alternative peers or targets may fit the same score" in figure_text
    assert "not causal or prescriptive claims" in figure_text
    assert {
        key: matplotlib.rcParams[key]
        for key in ("axes.edgecolor", "font.size", "grid.color")
    } == before_rc
    assert_frame_equal(joint_result.targets, before_targets)
    assert_frame_equal(joint_result.slacks, before_slacks)
    pyplot.close(figure)
