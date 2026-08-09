from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    PeriodProductionSpec,
    load_dataset,
)
from deapack.visualization import (
    PlotNotAvailableError,
    prepare_trajectory_data,
    trajectory_plot_applicable,
)


def _dynamic_data(*, carryover_kind: str = "free") -> DynamicData:
    frame = load_dataset("dynamic_carryover_portfolio")
    spec = DynamicSBMSpec(
        production=PeriodProductionSpec(
            inputs="operating_input", outputs="service_output"
        ),
        carryovers=(CarryOverSpec("redeployable_stock", kind=carryover_kind),),
    )
    return DynamicData.from_frame(
        frame,
        spec=spec,
        dmu="unit_id",
        period="period",
    )


def _all_carryover_data() -> DynamicData:
    frame = load_dataset("dynamic_carryover_portfolio").copy(deep=True)
    for variable in ("good", "bad", "free", "fixed"):
        frame[variable] = frame["redeployable_stock"]
    spec = DynamicSBMSpec(
        production=PeriodProductionSpec(
            inputs="operating_input", outputs="service_output"
        ),
        carryovers=tuple(
            CarryOverSpec(variable, kind=variable)
            for variable in ("good", "bad", "free", "fixed")
        ),
    )
    return DynamicData.from_frame(
        frame,
        spec=spec,
        dmu="unit_id",
        period="period",
    )


@pytest.fixture(scope="module")
def dynamic_result():
    return DynamicSBM(
        orientation="input",
        returns_to_scale="crs",
    ).fit(_dynamic_data())


def test_trajectory_discovery_is_backend_independent() -> None:
    command = (
        "import sys; "
        "from deapack import CarryOverSpec, DynamicData, DynamicSBM, "
        "DynamicSBMSpec, PeriodProductionSpec, load_dataset; "
        "frame=load_dataset('dynamic_carryover_portfolio'); "
        "spec=DynamicSBMSpec(production=PeriodProductionSpec(inputs='operating_input', "
        "outputs='service_output'), carryovers=(CarryOverSpec('redeployable_stock', "
        "kind='free'),)); "
        "data=DynamicData.from_frame(frame, spec=spec, dmu='unit_id', "
        "period='period'); result=DynamicSBM().fit(data); "
        "assert [plot.kind for plot in result.available_plots()] == "
        "['performance', 'trajectory']; "
        "assert not any(name == 'matplotlib' or name.startswith('matplotlib.') "
        "for name in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", command], check=True)


def test_project_carryover_path_and_period_accounts_are_reconstructed(
    dynamic_result,
) -> None:
    before_summary = dynamic_result.summary()
    before_targets = dynamic_result.targets.copy(deep=True)
    before_slacks = dynamic_result.slacks.copy(deep=True)
    before_components = dynamic_result.components.copy(deep=True)
    before_links = dynamic_result.links.copy(deep=True)

    prepared = prepare_trajectory_data(
        dynamic_result,
        dmu_id="path_03",
        variable="redeployable_stock",
    )

    assert prepared.horizon_efficiency == pytest.approx(0.5658489658489658)
    assert prepared.period_count == 3
    assert prepared.transition_count == 2
    assert prepared.role == "free_carryover"
    assert prepared.carryover_kind == "free"
    assert prepared.carryover_score_policy == ("feasibility_only_not_in_reported_score")
    assert prepared.terminal_boundary_status == (
        "observed_terminal_no_outgoing_continuity"
    )
    assert prepared.quantity["period"].tolist() == [1, 2, 3]
    assert prepared.quantity["observed"].tolist() == [7.0, 7.0, 7.0]
    assert prepared.quantity["outgoing_target"].tolist() == pytest.approx(
        [4.714285714285714, 4.714285714285714, 4.714285714285714]
    )
    np.testing.assert_allclose(
        prepared.quantity["inherited_target"],
        [np.nan, 4.714285714285714, 4.714285714285714],
        equal_nan=True,
    )
    assert prepared.quantity["included_in_reported_score"].eq(False).all()
    assert prepared.transitions["source_target"].tolist() == pytest.approx(
        [4.714285714285714, 4.714285714285714]
    )
    assert prepared.transitions["inherited_target"].tolist() == pytest.approx(
        [4.714285714285714, 4.714285714285714]
    )
    assert prepared.transitions["continuity_residual"].abs().max() <= 1e-12
    assert prepared.period_accounts["efficiency"].tolist() == pytest.approx(
        [11.0 / 17.5, 12.0 / 21.38888888888889, 13.0 / 25.59375]
    )
    assert prepared.selection_status == ("solver_selected_not_uniqueness_certified")

    assert_frame_equal(dynamic_result.summary(), before_summary)
    assert_frame_equal(dynamic_result.targets, before_targets)
    assert_frame_equal(dynamic_result.slacks, before_slacks)
    assert_frame_equal(dynamic_result.components, before_components)
    assert_frame_equal(dynamic_result.links, before_links)


def test_prepared_trajectory_frames_are_detached(dynamic_result) -> None:
    prepared = prepare_trajectory_data(dynamic_result, dmu_id="path_03")
    original = dynamic_result.targets.loc[
        dynamic_result.targets["dmu_id"].eq("path_03")
        & dynamic_result.targets["variable"].eq("redeployable_stock")
        & dynamic_result.targets["period"].eq(1),
        "target",
    ].iloc[0]

    prepared.quantity.loc[0, "outgoing_target"] = -999.0
    prepared.transitions.loc[0, "source_target"] = -999.0
    prepared.period_accounts.loc[0, "efficiency"] = -999.0

    current = dynamic_result.targets.loc[
        dynamic_result.targets["dmu_id"].eq("path_03")
        & dynamic_result.targets["variable"].eq("redeployable_stock")
        & dynamic_result.targets["period"].eq(1),
        "target",
    ].iloc[0]
    assert current == original


@pytest.mark.parametrize("orientation", ["output", "non-oriented"])
def test_horizon_efficiency_is_not_replaced_by_period_arithmetic_mean(
    orientation: str,
) -> None:
    result = DynamicSBM(
        orientation=orientation,
        returns_to_scale="crs",
    ).fit(_dynamic_data())
    prepared = prepare_trajectory_data(result, dmu_id="path_03")
    summary_value = result.summary().set_index("dmu_id").loc["path_03", "efficiency"]

    assert prepared.horizon_efficiency == pytest.approx(summary_value)
    assert prepared.horizon_efficiency != pytest.approx(
        prepared.period_accounts["efficiency"].mean()
    )


def test_free_adjusted_variant_reads_score_inclusion_from_result_rows() -> None:
    result = DynamicSBM(
        orientation="input",
        returns_to_scale="crs",
        score_variant="free_adjusted_post",
    ).fit(_dynamic_data())
    prepared = prepare_trajectory_data(result, dmu_id="path_03")

    assert prepared.carryover_score_policy == "included_in_reported_score"
    assert prepared.quantity["included_in_reported_score"].eq(True).all()
    assert prepared.horizon_efficiency == pytest.approx(
        result.summary().set_index("dmu_id").loc["path_03", "efficiency"]
    )


def test_fixed_carryover_uses_source_no_slack_commitment_semantics() -> None:
    result = DynamicSBM(
        orientation="input",
        returns_to_scale="crs",
    ).fit(_dynamic_data(carryover_kind="fixed"))

    assert trajectory_plot_applicable(result)
    assert [plot.kind for plot in result.available_plots()] == [
        "performance",
        "trajectory",
    ]
    prepared = prepare_trajectory_data(
        result,
        dmu_id="path_03",
        variable="redeployable_stock",
    )

    assert prepared.role == "fixed_carryover"
    assert prepared.carryover_kind == "fixed"
    assert prepared.carryover_score_policy == ("fixed_commitment_not_in_reported_score")
    assert prepared.quantity["outgoing_target"].tolist() == pytest.approx(
        prepared.quantity["observed"].tolist()
    )
    assert prepared.quantity["included_in_optimization_objective"].eq(False).all()
    assert prepared.quantity["included_in_reported_score"].eq(False).all()


@pytest.mark.parametrize("orientation", ["input", "output", "non-oriented"])
@pytest.mark.parametrize("score_variant", ["base", "free_adjusted_post"])
def test_all_carryover_score_policies_follow_source_semantics(
    orientation: str,
    score_variant: str,
) -> None:
    result = DynamicSBM(
        orientation=orientation,
        returns_to_scale="crs",
        score_variant=score_variant,
    ).fit(_all_carryover_data())

    for variable in ("good", "bad", "free", "fixed"):
        prepared = prepare_trajectory_data(
            result,
            dmu_id="path_03",
            variable=variable,
        )
        if variable == "fixed":
            expected_policy = "fixed_commitment_not_in_reported_score"
        elif (
            (variable == "free" and score_variant == "free_adjusted_post")
            or (variable == "good" and orientation in {"output", "non-oriented"})
            or (variable == "bad" and orientation in {"input", "non-oriented"})
        ):
            expected_policy = "included_in_reported_score"
        else:
            expected_policy = "feasibility_only_not_in_reported_score"
        assert prepared.carryover_score_policy == expected_policy


@pytest.mark.parametrize("forgery", ["summary", "period", "observed"])
def test_displayed_scores_and_observations_require_cross_account_reconstruction(
    dynamic_result,
    forgery: str,
) -> None:
    if forgery == "summary":
        summary = dynamic_result.summary()
        summary.loc[summary["dmu_id"].eq("path_03"), ["score", "efficiency"]] = 0.99
        corrupted = replace(dynamic_result, summary_frame=summary)
        message = "horizon score does not reconstruct"
    elif forgery == "period":
        components = dynamic_result.components.copy(deep=True)
        mask = components["dmu_id"].eq("path_03") & components["component_type"].eq(
            "period"
        )
        components.loc[mask, "efficiency"] = 0.99
        corrupted = replace(dynamic_result, components=components)
        message = "period efficiencies do not reconstruct"
    else:
        targets = dynamic_result.targets.copy(deep=True)
        mask = (
            targets["dmu_id"].eq("path_03")
            & targets["variable"].eq("redeployable_stock")
            & targets["period"].eq(2)
        )
        targets.loc[mask, "observed"] = 999.0
        corrupted = replace(dynamic_result, targets=targets)
        message = "observed quantities do not reconstruct"

    with pytest.raises(PlotNotAvailableError, match=message):
        prepare_trajectory_data(corrupted, dmu_id="path_03")


def test_carryover_targets_and_score_flags_are_reconstructed_from_slacks(
    dynamic_result,
) -> None:
    targets = dynamic_result.targets.copy(deep=True)
    target_mask = targets["dmu_id"].eq("path_03") & targets["variable"].eq(
        "redeployable_stock"
    )
    targets.loc[target_mask, "target"] += 1.0
    links = dynamic_result.links.copy(deep=True)
    link_mask = links["dmu_id"].eq("path_03") & links["carryover"].eq(
        "redeployable_stock"
    )
    links.loc[link_mask, "source_target"] += 1.0
    nonterminal = link_mask & links["target_period"].notna()
    links.loc[nonterminal, "next_period_target"] += 1.0
    forged_targets = replace(dynamic_result, targets=targets, links=links)
    with pytest.raises(
        PlotNotAvailableError,
        match="reconstruct from carry-over slacks",
    ):
        prepare_trajectory_data(forged_targets, dmu_id="path_03")

    slacks = dynamic_result.slacks.copy(deep=True)
    slack_mask = slacks["dmu_id"].eq("path_03") & slacks["variable"].eq(
        "redeployable_stock"
    )
    slacks.loc[
        slack_mask,
        [
            "included_in_optimization_objective",
            "included_in_reported_score",
        ],
    ] = True
    forged_flags = replace(dynamic_result, slacks=slacks)
    with pytest.raises(PlotNotAvailableError, match="flags do not reconstruct"):
        prepare_trajectory_data(forged_flags, dmu_id="path_03")

    variant = dynamic_result.slacks.copy(deep=True)
    variant.loc[slack_mask, "score_variant"] = "free_adjusted_post"
    forged_variant = replace(dynamic_result, slacks=variant)
    with pytest.raises(PlotNotAvailableError, match="score variants do not agree"):
        prepare_trajectory_data(forged_variant, dmu_id="path_03")

    selection = dynamic_result.slacks.copy(deep=True)
    selection.loc[slack_mask, "selection_status"] = "forged"
    forged_selection = replace(dynamic_result, slacks=selection)
    with pytest.raises(PlotNotAvailableError, match="path-selection status"):
        prepare_trajectory_data(forged_selection, dmu_id="path_03")


def test_fixed_commitment_and_boundary_labels_fail_closed() -> None:
    fixed = DynamicSBM(
        orientation="input",
        returns_to_scale="crs",
    ).fit(_dynamic_data(carryover_kind="fixed"))
    targets = fixed.targets.copy(deep=True)
    target_mask = (
        targets["dmu_id"].eq("path_03")
        & targets["variable"].eq("redeployable_stock")
        & targets["period"].eq(2)
    )
    targets.loc[target_mask, "target"] += 1.0
    links = fixed.links.copy(deep=True)
    link_mask = (
        links["dmu_id"].eq("path_03")
        & links["carryover"].eq("redeployable_stock")
        & links["source_period"].eq(2)
    )
    links.loc[link_mask, "source_target"] += 1.0
    links.loc[link_mask, "next_period_target"] += 1.0
    forged_fixed = replace(fixed, targets=targets, links=links)
    with pytest.raises(PlotNotAvailableError, match="preserve observed commitments"):
        prepare_trajectory_data(forged_fixed, dmu_id="path_03")

    fabricated_slack = fixed.slacks.iloc[[0]].copy(deep=True)
    fabricated_slack["dmu_id"] = "path_03"
    fabricated_slack["role"] = "fixed_carryover"
    fabricated_slack["variable"] = "redeployable_stock"
    fixed_slacks = pd.concat([fixed.slacks, fabricated_slack], ignore_index=True)
    with pytest.raises(PlotNotAvailableError, match="must not fabricate"):
        prepare_trajectory_data(
            replace(fixed, slacks=fixed_slacks),
            dmu_id="path_03",
        )

    summary = fixed.summary()
    summary.loc[summary["dmu_id"].eq("path_03"), "max_fixed_account_residual"] = 1.0
    with pytest.raises(PlotNotAvailableError, match="fixed carry-over account"):
        prepare_trajectory_data(
            replace(fixed, summary_frame=summary),
            dmu_id="path_03",
        )

    boundary = fixed.links.copy(deep=True)
    boundary_mask = (
        boundary["dmu_id"].eq("path_03")
        & boundary["carryover"].eq("redeployable_stock")
        & boundary["source_period"].eq(1)
    )
    boundary.loc[boundary_mask, "boundary_status"] = pd.NA
    missing_boundary = replace(fixed, links=boundary)
    with pytest.raises(PlotNotAvailableError, match="boundary"):
        prepare_trajectory_data(missing_boundary, dmu_id="path_03")


def test_unknown_dmu_variable_and_incompatible_plot_arguments_fail_closed(
    dynamic_result,
) -> None:
    with pytest.raises(PlotNotAvailableError, match="unknown trajectory dmu_id"):
        prepare_trajectory_data(dynamic_result, dmu_id="unknown")
    with pytest.raises(PlotNotAvailableError, match="unknown trajectory variable"):
        prepare_trajectory_data(
            dynamic_result,
            dmu_id="path_03",
            variable="inventory_that_does_not_exist",
        )
    with pytest.raises(PlotNotAvailableError, match="requires dmu_id"):
        dynamic_result.plot(kind="trajectory")
    with pytest.raises(PlotNotAvailableError, match="complete fitted horizon"):
        dynamic_result.plot(kind="trajectory", dmu_id="path_03", period=2)
    with pytest.raises(PlotNotAvailableError, match="complete fitted horizon"):
        dynamic_result.plot(kind="trajectory", dmu_id="path_03", metric="efficiency")
    with pytest.raises(PlotNotAvailableError, match="only view='auto'"):
        dynamic_result.plot(kind="trajectory", dmu_id="path_03", view="points")


def test_non_dynamic_sbm_result_cannot_inherit_trajectory_semantics(
    dynamic_result,
) -> None:
    incompatible = replace(
        dynamic_result,
        metadata={
            **dict(dynamic_result.metadata),
            "method_id": "dynamic.network_sbm.tone_tsutsui_2014",
        },
    )

    assert not trajectory_plot_applicable(incompatible)
    with pytest.raises(PlotNotAvailableError, match="classic Tone--Tsutsui"):
        prepare_trajectory_data(incompatible, dmu_id="path_03")


def test_uncertified_horizon_cannot_release_trajectory(dynamic_result) -> None:
    summary = dynamic_result.summary()
    summary.loc[summary["dmu_id"].eq("path_03"), "score_valid"] = False
    invalid_summary = replace(dynamic_result, summary_frame=summary)
    diagnostics = dynamic_result.diagnostics.copy(deep=True)
    diagnostics.loc[
        diagnostics["dmu_id"].eq("path_03"), "economic_postsolve_certified"
    ] = False
    invalid_diagnostics = replace(dynamic_result, diagnostics=diagnostics)

    for result in (invalid_summary, invalid_diagnostics):
        with pytest.raises(PlotNotAvailableError, match="requires"):
            prepare_trajectory_data(result, dmu_id="path_03")

    all_invalid = dynamic_result.summary()
    all_invalid["score_valid"] = False
    assert not trajectory_plot_applicable(
        replace(dynamic_result, summary_frame=all_invalid)
    )

    missing_status = dynamic_result.summary().drop(columns="score_status")
    with pytest.raises(PlotNotAvailableError, match="defined certified horizon"):
        prepare_trajectory_data(
            replace(dynamic_result, summary_frame=missing_status),
            dmu_id="path_03",
        )


def test_ambiguous_carryover_identity_fails_closed(dynamic_result) -> None:
    targets = dynamic_result.targets.copy(deep=True)
    duplicate_role = targets.loc[
        targets["dmu_id"].eq("path_03")
        & targets["role"].eq("free_carryover")
        & targets["variable"].eq("redeployable_stock")
    ].copy()
    duplicate_role["role"] = "good_carryover"
    ambiguous = replace(
        dynamic_result,
        targets=pd.concat([targets, duplicate_role], ignore_index=True),
    )

    with pytest.raises(PlotNotAvailableError, match="ambiguous"):
        prepare_trajectory_data(
            ambiguous,
            dmu_id="path_03",
            variable="redeployable_stock",
        )


@pytest.mark.parametrize(
    ("table_name", "mutation", "message"),
    [
        (
            "targets",
            "duplicate",
            "one row per non-missing period",
        ),
        (
            "targets",
            "nonfinite",
            "observed and target quantities must be finite",
        ),
        (
            "components",
            "missing",
            "periods do not match the fitted horizon",
        ),
        (
            "links",
            "duplicate",
            "one row per non-missing period",
        ),
        (
            "slacks",
            "missing",
            "periods do not match the fitted horizon",
        ),
    ],
)
def test_incomplete_or_malformed_semantic_tables_fail_closed(
    dynamic_result,
    table_name: str,
    mutation: str,
    message: str,
) -> None:
    frame = getattr(dynamic_result, table_name).copy(deep=True)
    if table_name == "targets":
        mask = (
            frame["dmu_id"].eq("path_03")
            & frame["variable"].eq("redeployable_stock")
            & frame["period"].eq(2)
        )
    elif table_name == "components":
        mask = (
            frame["dmu_id"].eq("path_03")
            & frame["component_type"].eq("period")
            & frame["period"].eq(2)
        )
    elif table_name == "slacks":
        mask = (
            frame["dmu_id"].eq("path_03")
            & frame["variable"].eq("redeployable_stock")
            & frame["period"].eq(2)
        )
    else:
        mask = (
            frame["dmu_id"].eq("path_03")
            & frame["carryover"].eq("redeployable_stock")
            & frame["source_period"].eq(2)
        )
    if mutation == "duplicate":
        frame = pd.concat([frame, frame.loc[mask]], ignore_index=True)
    elif mutation == "missing":
        frame = frame.loc[~mask].copy()
    else:
        frame.loc[mask, "target"] = np.nan
    corrupted = replace(dynamic_result, **{table_name: frame})

    with pytest.raises(PlotNotAvailableError, match=message):
        prepare_trajectory_data(corrupted, dmu_id="path_03")


def test_broken_continuity_and_fabricated_terminal_successor_fail_closed(
    dynamic_result,
) -> None:
    broken = dynamic_result.links.copy(deep=True)
    first = (
        broken["dmu_id"].eq("path_03")
        & broken["carryover"].eq("redeployable_stock")
        & broken["source_period"].eq(1)
    )
    broken.loc[first, "next_period_target"] += 1.0
    broken_result = replace(dynamic_result, links=broken)
    with pytest.raises(PlotNotAvailableError, match="outgoing and inherited"):
        prepare_trajectory_data(broken_result, dmu_id="path_03")

    fabricated = dynamic_result.links.copy(deep=True)
    terminal = (
        fabricated["dmu_id"].eq("path_03")
        & fabricated["carryover"].eq("redeployable_stock")
        & fabricated["source_period"].eq(3)
    )
    fabricated.loc[terminal, "target_period"] = 5
    fabricated.loc[terminal, "next_period_target"] = 17.5
    fabricated.loc[terminal, "continuity_residual"] = 0.0
    fabricated_result = replace(dynamic_result, links=fabricated)
    with pytest.raises(PlotNotAvailableError, match="must not fabricate"):
        prepare_trajectory_data(fabricated_result, dmu_id="path_03")


def test_fitted_period_order_is_required_and_not_inferred(dynamic_result) -> None:
    missing_order = replace(
        dynamic_result,
        metadata={
            key: value
            for key, value in dict(dynamic_result.metadata).items()
            if key != "period_order"
        },
    )
    duplicate_order = replace(
        dynamic_result,
        metadata={
            **dict(dynamic_result.metadata),
            "period_order": (1, 2, 2, 4),
        },
    )

    for result in (missing_order, duplicate_order):
        with pytest.raises(PlotNotAvailableError, match="period"):
            prepare_trajectory_data(result, dmu_id="path_03")

    missing_tolerance = replace(
        dynamic_result,
        metadata={
            key: value
            for key, value in dict(dynamic_result.metadata).items()
            if key != "tolerance"
        },
    )
    with pytest.raises(PlotNotAvailableError, match="numerical tolerance"):
        prepare_trajectory_data(missing_tolerance, dmu_id="path_03")


def test_trajectory_long_horizon_fails_closed(
    dynamic_result,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.visualization.trajectory as trajectory_module

    monkeypatch.setattr(trajectory_module, "MAX_TRAJECTORY_PERIODS", 2)

    assert not trajectory_plot_applicable(dynamic_result)
    with pytest.raises(PlotNotAvailableError, match="limited to 2"):
        prepare_trajectory_data(dynamic_result, dmu_id="path_03")


def test_matplotlib_trajectory_renders_joint_path_without_showing(
    dynamic_result,
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
    before_targets = dynamic_result.targets.copy(deep=True)

    def _show_is_forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("plot() must not call pyplot.show()")

    monkeypatch.setattr(pyplot, "show", _show_is_forbidden)
    figure = dynamic_result.plot(
        kind="trajectory",
        dmu_id="path_03",
        variable="redeployable_stock",
    )

    assert isinstance(figure, figure_type)
    assert len(figure.axes) == 2
    assert figure._suptitle.get_text() == "Certified carry-over trajectory for path_03"
    assert "Observed plan" in figure.axes[0].get_title()
    assert figure.axes[1].get_title() == (
        "Complete period operating-plan account (all scored dimensions)"
    )
    assert any(
        "not independent annual recommendations" in text.get_text()
        for text in figure.texts
    )
    assert any(
        "does not enter the reported score" in text.get_text() for text in figure.texts
    )
    assert any(
        "not an attribution to the selected carry-over" in text.get_text()
        for text in figure.texts
    )
    assert {
        key: matplotlib.rcParams[key]
        for key in ("axes.edgecolor", "font.size", "grid.color")
    } == before_rc
    assert_frame_equal(dynamic_result.targets, before_targets)
    pyplot.close(figure)
